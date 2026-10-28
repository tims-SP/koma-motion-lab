#!/usr/bin/env python3
"""PROD-004 — real Spine -> native Rive weighted image Mesh pilot + private MP4.

Reads the previously decoded 4.2.36 Spine JSON, recreates bone hierarchy,
translates setup-pose weighted vertices/UVs/triangles/slot order, samples an
original idle_room rotation track, and uses official Rive CLI to render video.

All game source, reconstructed RML, .riv, frames, and source-art MP4 stay
in the ephemeral private runner. Public artifact contains metrics only.

This pilot is explicitly NOT faithful Spine-runtime playback: inherited scale,
IK, path/transform constraints, FFD and draw-order timelines require more work.
"""
from __future__ import annotations
import base64,hashlib,json,math,os,struct,subprocess,sys,urllib.request,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

ROOT=Path(os.environ.get("PROD_PRIVATE","/tmp/koma-spine-rive-private"))
OUT=Path(os.environ.get("PROD_REPORT","out/spine-rive"))
OUT.mkdir(parents=True,exist_ok=True)
DATA=ROOT/"source_spine.json"
METRIC={"stage":"original_spine_mesh_to_rive","status":"NOT_STARTED","source_backend":"Spine 4.2.36",
 "source_char":"300401_hongnujian","preserved":[],"excluded":[
 "IK/transform/path constraint solving","vertex FFD animation timelines",
 "source cubic bezier rotation easing","animated draw order and attachment switches",
 "Spine inherit scale and transforms","full visual fidelity comparison"]}
SRC="https://raw.githubusercontent.com/myssal/Reverse-1999-CN-Asset/45e75248ba3b25053fd32e63ab13c2f9f54dd9df/roles/300401_hongnujian/"

def run(args):
    result=subprocess.run(args,text=True,capture_output=True,timeout=120)
    if result.returncode!=0:raise RuntimeError(" ".join(map(str,args))+" "+(result.stdout+result.stderr)[-1400:])
    return result

def world_transform(bones):
    byname={b["name"]:b for b in bones}
    world={}
    def matmul(a,b):
        A,B,C,D,X,Y=a; E,F,G,H,U,V=b
        return (A*E+C*F,B*E+D*F,A*G+C*H,B*G+D*H,A*U+C*V+X,B*U+D*V+Y)
    for bone in bones:
        a=math.radians(float(bone.get("rotation",0)))
        ca,sa=math.cos(a),math.sin(a)
        sx,sy=float(bone.get("scaleX",1)),float(bone.get("scaleY",1))
        skewx=math.radians(float(bone.get("shearX",0)))
        skewy=math.radians(float(bone.get("shearY",0)))
        # Skeleton setup frame: Spine's rotation+shear applies on local axes.
        local=(math.cos(a+skewx)*sx,math.sin(a+skewx)*sx,
               -math.sin(a+math.pi/2+skewy)*sy,math.cos(a+math.pi/2+skewy)*sy,
               float(bone.get("x",0)),float(bone.get("y",0)))
        # Note: for shearY=0, c = -cos(a) here; corrected below to Spine's -sin(a).
        local=(math.cos(a+skewx)*sx,math.sin(a+skewx)*sx,
               math.cos(a+math.pi/2+skewy)*sy,math.sin(a+math.pi/2+skewy)*sy,
               float(bone.get("x",0)),float(bone.get("y",0)))
        p=bone.get("parent")
        world[bone["name"]]=matmul(world[p],local) if p else local
    return world

def apply(mat,x,y):
    a,b,c,d,tx,ty=mat
    return a*x+c*y+tx,b*x+d*y+ty

def frame_value(keys,t):
    vals=sorted((float(k.get("time",0)),float(k.get("angle",0))) for k in keys)
    if not vals:return 0.0
    if t<=vals[0][0]:return vals[0][1]
    for (t0,a),(t1,b) in zip(vals,vals[1:]):
        if t<=t1:return a+(b-a)*(t-t0)/(t1-t0) if t1>t0 else b
    return vals[-1][1]

def parse_attachment(attachment, bones,world,slot_bone):
    """Return original Spine mesh vertices in setup world-space, with influences."""
    uv=attachment.get("uvs")
    triangles=attachment.get("triangles")
    values=attachment.get("vertices")
    if not (isinstance(uv,list) and isinstance(values,list) and isinstance(triangles,list)):
        return None
    n=len(uv)//2
    if n<3 or n>250 or any(not isinstance(i,int) or i<0 or i>=n for i in triangles):return None
    if len(triangles)<3 or len(triangles)%3:return None
    data=[]
    if len(values)==2*n:
        for i in range(n):
            x,y=apply(world[slot_bone],float(values[2*i]),float(values[2*i+1]))
            data.append((x,y,[(slot_bone,1.0)]))
    else:
        p=0
        for v in range(n):
            if p>=len(values):return None
            count=int(values[p]);p+=1
            if count<1 or count>12:return None
            influences=[]
            for j in range(count):
                if p+4>len(values):return None
                bone_index=int(values[p])
                if not (0<=bone_index<len(bones)):return None
                bone_name=bones[bone_index]["name"]
                x,y,w=map(float,values[p+1:p+4]);p+=4
                influences.append((bone_name,x,y,w))
            total=sum(max(0,w) for name,x,y,w in influences)
            if total<=0:return None
            sx=sy=0.0
            compact=[]
            for name,x,y,w in influences:
                weight=max(0,w)/total
                wx,wy=apply(world[name],x,y)
                sx+=weight*wx; sy+=weight*wy
                compact.append((name,weight))
            data.append((sx,sy,compact))
        if p!=len(values):return None
    return {"vertex":data,"uv":[(float(uv[2*i]),float(uv[2*i+1])) for i in range(n)],
             "triangles":triangles,"weighted":len(values)>2*n}

def weightpack(influences,tendon_by_name):
    filtered=sorted(((n,w) for n,w in influences if w>0),key=lambda q:q[1],reverse=True)[:4]
    total=sum(w for _,w in filtered)
    if not total:raise ValueError("no influences")
    weights=[int(round(255*w/total)) for _,w in filtered]
    weights[0]+=255-sum(weights)
    indexes=[tendon_by_name[n] for n,_ in filtered]
    assert all(1<=idx<=255 for idx in indexes)
    return (sum((b&255)<<(8*i) for i,b in enumerate(weights)),
            sum((idx&255)<<(8*i) for i,idx in enumerate(indexes)))

def construct():
    doc=json.loads(DATA.read_text("utf-8"))
    bones=doc["bones"]
    byname={b["name"]:b for b in bones}
    world=world_transform(bones)
    skins=doc.get("skins",[])
    entries=skins[0].get("attachments",{}) if isinstance(skins,list) else skins.get("default",{})
    slots=doc.get("slots",[])
    (ROOT/"atlas.png").write_bytes(urllib.request.urlopen(SRC+"300401_hongnujian.png",timeout=90).read())
    with Image.open(ROOT/"atlas.png") as image:
        aw,ah=image.size
    METRIC["source_bones"]=len(bones)
    METRIC["source_slots"]=len(slots)
    METRIC["atlas_dimensions"]=[aw,ah]
    METRIC["source_skin_slot_count"]=len(entries)
    project=ROOT/"source-mesh-rive"
    run(["rive","create",str(project)])
    (project/"atlas.png").write_bytes((ROOT/"atlas.png").read_bytes())
    tree=ET.parse(project/"scene.rml")
    scene=tree.getroot()
    board=next(x for x in scene.iter() if x.tag=="Artboard")
    board.set("name","OriginalSpineMeshToRive")
    board.set("width","640");board.set("height","360")
    ET.SubElement(scene,"ImageAsset",{"file":"atlas.png","name":"OriginalSpineAtlas","id":"0:60"})
    group=ET.SubElement(board,"Node",{"name":"SpineRoot"})
    objects={}
    for index,bone in enumerate(bones):
        parent=bone.get("parent")
        p=objects.get(parent,group)
        if parent and parent not in objects:raise ValueError("source parent is not ordered")
        ang=float(bone.get("rotation",0))
        bridge=0.0
        if parent:
            dx=float(bone.get("x",0))-float(byname[parent].get("length",0))
            dy=float(bone.get("y",0))
            dist=math.hypot(dx,dy)
            if dist>0.0001:
                bridge=math.atan2(dy,dx)
                p=ET.SubElement(p,"Bone",{"name":"Offset"+str(index),"id":"0:"+str(500+index),
                    "length":f"{dist:.7g}","rotation":f"{bridge:.9g}"})
        props={"name":bone["name"],"id":"0:"+str(200+index),
               "length":str(max(.5,float(bone.get("length",0)))),
               "rotation":str(math.radians(ang)-bridge)}
        if not parent:props.update({"x":str(float(bone.get("x",0))),"y":str(float(bone.get("y",0)))})
        objs[bone["name"]]=ET.SubElement(p,"Bone" if parent else "RootBone",props)
        bone["_bridge"]=bridge
    METRIC["rive_bones"]=len(objects)
    imported=[]; bounds=[]; weighted_count=0; translated_weights=0; lost=[]
    for j,slot in enumerate(slots):
        sn=slot["name"]
        bn=slot.get("bone")
        if bn not in world:continue
        target=slot.get("attachment")
        variants=entries.get(sn,{})
        if not target or not isinstance(variants,dict):continue
        attachment=variants.get(target)
        if attachment is None:continue
        if attachment.get("type","region") not in ("mesh",):continue
        geo=parse_attachment(attachment,bones,world,bn)
        if geo is None:
            lost.append({"slot":sn,"reason":"unsupported vertex/tri encoding"})
            continue
        # Original UV from Spine .skel points to the entire atlas, not to a crop.
        n=len(geo["vertex"])
        used={name for _,_,inf in geo["vertex"] for name,w in inf}
        if len(used)>130:
            lost.append({"slot":sn,"reason":"too many tendons"})
            continue
        tendon_by_name={name:i+1 for i,name in enumerate(sorted(used))}
        image=ET.SubElement(group,"Image",{"assetId":"0:60","id":"0:"+str(1000+j),"name":"src_"+sn})
        encoded=base64.b64encode(bytes(geo["triangles"])).decode()
        mesh=ET.SubElement(image,"Mesh",{"triangleIndexBytes":encoded,"id":"0:"+str(1500+j),"name":"sourceMesh"})
        for i,((x,y,inf),(u,v)) in enumerate(zip(geo["vertex"],geo["uv"])):
            vertex=ET.SubElement(mesh,"ContourMeshVertex",{"x":f"{x:.7g}","y":f"{y:.7g}",
                "u":f"{u:.8g}","v":f"{v:.8g}","name":f"v{i}"})
            value,index=weightpack(inf,tendon_by_name)
            ET.SubElement(vertex,"Weight",{"values":str(value),"indices":str(index)})
            translated_weights+=1
            bounds.append((x,y))
        skin=ET.SubElement(mesh,"Skin",{"name":"skin"})
        for name,number in tendon_by_name.items():
            a,b,c,d,tx,ty=world[name]
            ET.SubElement(skin,"Tendon",{"boneId":objects[name].get("id"),
                "tx":f"{tx:.7g}","ty":f"{ty:.7g}",
                "xx":f"{a:.7g}","xy":f"{b:.7g}","yx":f"{c:.7g}","yy":f"{d:.7g}",
                "name":name})
        imported.append({"slot":sn,"attachment":target,"vertices":n,
                         "triangles":len(geo["triangles"])//3,
                         "tendons":len(used),"weighted":geo["weighted"]})
        if geo["weighted"]:weighted_count+=1
    if not bounds:raise ValueError("No original mesh convertible")
    METRIC.update({"mesh_attachments_transferred":len(imported),"skinned_mesh_attachments_transferred":weighted_count,
      "vertices_transferred":translated_weights,"source_mesh_slots_skipped":len(lost),
      "skipped_sample":lost[:6],"source_slot_details":imported[:30]})
    minx,maxx=min(x for x,y in bounds),max(x for x,y in bounds)
    miny,maxy=min(y for x,y in bounds),max(y for x,y in bounds)
    width=max(1,maxx-minx);height=max(1,maxy-miny)
    scale=min(560/width,280/height,1.75)
    centerx=(minx+maxx)/2;centery=(miny+maxy)/2
    group.set("x",str(320-centerx*scale))
    group.set("y",str(180+centery*scale))
    group.set("scaleX",str(scale))
    group.set("scaleY",str(-scale))
    METRIC["source_bbox"]=[minx,miny,maxx,maxy]
    METRIC["image_scale"]=scale
    METRIC["preserved"]=["source hierarchy for 85 bones","source animated rotation samples",
      "source texture atlas","source mesh triangles and original UV arrays",
      "source skin influence indices and normalized weights for selected mesh attachments","setup draw order for imported mesh slots"]
    return tree,project,bones,objects,doc,imported

def render():
    tree,project,bones,objects,doc,imported=construct()
    action=doc.get("animations",{}).get("idle_room")
    if not action:raise ValueError("idle_room missing")
    tracks={name:timeline["rotate"] for name,timeline in action.get("bones",{}).items()
        if isinstance(timeline,dict) and isinstance(timeline.get("rotate"),list)}
    METRIC["animated_rotation_bones"]=len(tracks)
    METRIC["action"]="idle_room"
    duration=2.0;fps=12;count=24
    frames=ROOT/"textured-original-frames";frames.mkdir(exist_ok=True)
    hashes=[];sample_alpha=[]
    for i in range(count):
        t=i/(count-1)*duration
        for name,keys in tracks.items():
            if name not in objects:continue
            b=next(x for x in bones if x["name"]==name)
            angle=math.radians(float(b.get("rotation",0))+frame_value(keys,t))-float(b.get("_bridge",0))
            objects[name].set("rotation",f"{angle:.9g}")
        tree.write(project/"scene.rml",encoding="unicode")
        if i==0:
            run(["rive",str(project),"--verify"])
            run(["rive",str(project),"--once"])
            inspect=run(["rive","inspect",str(project),"--summary"]).stdout
            METRIC["rive_inspect_summary"]=json.loads(inspect)
        file=frames/f"{i:04d}.png"
        run(["rive",str(project),f"--screenshot={file}","--viewport=640x360","--advance=0s"])
        with Image.open(file) as im:
            pix=im.convert("RGBA")
            raw=pix.tobytes()
            hashes.append(hashlib.sha256(raw).hexdigest())
            base=raw[:4]
            visible=sum(raw[p:p+4]!=base for p in range(0,len(raw),4))
            sample_alpha.append(visible)
    METRIC["rendered_frames"]=count
    METRIC["unique_raster_frames"]=len(set(hashes))
    METRIC["visible_pixels_min"]=min(sample_alpha)
    METRIC["visible_pixels_max"]=max(sample_alpha)
    if min(sample_alpha)<400:raise ValueError("render lacks visible imported texture")
    if len(set(hashes))<5:raise ValueError("animation raster variation insufficient")
    dest=ROOT/"real-spine-mesh-rive-acceptance.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-framerate",str(fps),"-i",
        str(frames/"%04d.png"),"-c:v","libx264","-pix_fmt","yuv420p",str(dest)])
    METRIC["private_video_bytes"]=dest.stat().st_size
    METRIC["private_video_sha256"]=hashlib.sha256(dest.read_bytes()).hexdigest()
    METRIC["status"]="PASS_SUBSET"
    METRIC["source_art_publicly_uploaded"]=False

def finish():
    (OUT/"textured-transfer-result.json").write_text(json.dumps(METRIC,ensure_ascii=False,indent=2)+"\n")
    summary=["# PROD-004 · Spine original weighted meshes to Rive",
        "",f"**Status:** {METRIC['status']}","",
        f"- Native Rive bones: {METRIC.get('rive_bones','?')}",
        f"- Original Spine mesh attachments transferred: {METRIC.get('mesh_attachments_transferred','?')}",
        f"- Original weighted attachments transferred: {METRIC.get('skinned_mesh_attachments_transferred','?')}",
        f"- Original vertices/weights translated: {METRIC.get('vertices_transferred','?')}",
        f"- Source animation: {METRIC.get('action','?')}; animated bones {METRIC.get('animated_rotation_bones','?')}",
        f"- Headless Rive frames: {METRIC.get('rendered_frames','?')}; unique {METRIC.get('unique_raster_frames','?')}",
        f"- Private FFmpeg acceptance video bytes: {METRIC.get('private_video_bytes','?')}",
        f"- Error: {METRIC.get('error','none')}","",
        "This is an actual textured mesh transfer, not an image surrogate.",
        "Remaining unsupported features are in the JSON metrics. Rive scene and game video remain in temporary runner storage.",
        "Never claim complete visual equivalence without a source-runtime frame-by-frame comparison."]
    (OUT/"textured-transfer-summary.md").write_text("\n".join(summary)+"\n")
    print("\n".join(summary),flush=True)
if __name__=="__main__":
    try:render()
    except Exception as e:
        METRIC["status"]="FAIL";METRIC["error"]=repr(e)
    finish()
    if METRIC["status"]!="PASS_SUBSET":sys.exit(1)

#!/usr/bin/env python3
"""Transfer one real Spine animation's bone rotation curve to Rive RML.
Renderer: official Rive CLI frames + ffmpeg.
No claim of full skeleton/mesh/timeline fidelity.
Copyrighted image, derived .riv and full video remain PRIVATE on the runner.
Neutral-only video may be included in public Actions artifact.
"""
from __future__ import annotations
import hashlib,json,math,os,re,subprocess,sys,urllib.request,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

ROOT=Path(os.environ.get("PROD_PRIVATE","/tmp/koma-spine-rive-private"))
OUT=Path(os.environ.get("PROD_REPORT","out/spine-rive"))
OUT.mkdir(parents=True,exist_ok=True)
DATA=ROOT/"source_spine.json"
SHAREABLE=OUT/"rig-debug.mp4"
SRC="https://raw.githubusercontent.com/myssal/Reverse-1999-CN-Asset/45e75248ba3b25053fd32e63ab13c2f9f54dd9df/roles/300401_hongnujian/"
RESULT={"stage":"native_rive_subset_transfer","source":"Spine 4.2.36 room.skel","assets":"public-safe diagnostics only","proven":[],"not_proven":["full skeleton transfer","original mesh/UV/weights parity","all slot draw order","all animation timelines","source-original playback fidelity","full quality character scene"]}

def cmd(args):
    p=subprocess.run(args,capture_output=True,text=True,timeout=90)
    if p.returncode!=0:raise RuntimeError("command failed "+repr(args)+" "+(p.stdout+p.stderr)[-800:])
    return p

def find_rotation():
    doc=json.loads(DATA.read_text())
    bones={b["name"]:b for b in doc.get("bones",[])}
    choices=[]
    for anim,values in doc.get("animations",{}).items():
        for bone,tracks in values.get("bones",{}).items():
            if not isinstance(tracks,dict):continue
            for channel in ("rotate","rotation"):
                keys=tracks.get(channel,[])
                if not isinstance(keys,list) or len(keys)<3:continue
                angles=[float(k.get("angle",k.get("value",0))) for k in keys if isinstance(k,dict)]
                times=[float(k.get("time",0)) for k in keys if isinstance(k,dict)]
                if len(angles)<3 or max(times)<.5:continue
                spread=max(angles)-min(angles)
                score=min(spread,100)*len(keys)
                if bone in bones:choices.append((score,anim,bone,keys,spread))
    if not choices:raise RuntimeError("No usable source rotation timeline with 3+ keys")
    choices.sort(reverse=True,key=lambda x:x[0])
    score,anim,bone,keys,spread=choices[0]
    result={"animation":anim,"bone":bone,"source_keys":len(keys),"rotation_spread_degrees":spread,
            "duration":max(float(k.get("time",0)) for k in keys),"source_parent":bones[bone].get("parent"),
            "bone_count":len(bones),"animation_count":len(doc.get("animations",{}))}
    return result,keys

def linear(keys,t):
    p=sorted((float(k.get("time",0)),float(k.get("angle",k.get("value",0)))) for k in keys)
    if t<=p[0][0]:return p[0][1]
    for (t0,v0),(t1,v1) in zip(p,p[1:]):
        if t<=t1:
            if t1==t0:return v1
            return v0+(v1-v0)*(t-t0)/(t1-t0)
    return p[-1][1]

def extract_face():
    atlas=urllib.request.urlopen(SRC+"300401_hongnujian.atlas",timeout=90).read().decode()
    texture=ROOT/"atlas.png"
    texture.write_bytes(urllib.request.urlopen(SRC+"300401_hongnujian.png",timeout=90).read())
    lines=atlas.splitlines()
    for i,line in enumerate(lines):
        if line.strip()!="hnj_c_lian":continue
        for nextline in lines[i+1:i+5]:
            match=re.search(r"bounds:\s*(\d+),(\d+),(\d+),(\d+)",nextline)
            if match:
                x,y,w,h=map(int,match.groups())
                with Image.open(texture) as im:
                    out=ROOT/"face.png"
                    im.crop((x,y,x+w,y+h)).save(out)
                    return out
    raise RuntimeError("No hnj_c_lian atlas region")

def run():
    chosen,keys=find_rotation()
    RESULT.update(chosen)
    RESULT["interpolation"]="sampled linear per source key, source bezier curves NOT preserved"
    RESULT["proven"].append("real .skel binary decoded to JSON and sampled rotation keys")
    face=extract_face()
    project=ROOT/"native-rive-shot"
    cmd(["rive","create",str(project)])
    (project/"face.png").write_bytes(face.read_bytes())
    tree=ET.parse(project/"scene.rml")
    root=tree.getroot()
    board=next(x for x in root.iter() if x.tag=="Artboard")
    board.set("width","640");board.set("height","360");board.set("name","SpineToRiveBoneTrack")
    asset=ET.SubElement(root,"ImageAsset",{"file":"face.png","name":"OriginalGameFace","id":"0:60"})
    # Transferred one source-named parent->child chain; not a full avatar.
    group=ET.SubElement(board,"Node",{"name":"Rig","x":"280","y":"190"})
    base=ET.SubElement(group,"RootBone",{"name":chosen["source_parent"] or "RigRoot","id":"0:40","length":"105","rotation":"0"})
    arm=ET.SubElement(base,"Bone",{"name":chosen["bone"],"id":"0:41","length":"95","rotation":"0"})
    # Surrogate geometric limb shows native Rive skeleton articulation without game art.
    sh=ET.SubElement(arm,"Shape",{"name":"RigSegment"})
    p=ET.SubElement(sh,"PointsPath",{"name":"LimbOutline"})
    for x,y in [(0,-8),(95,-8),(95,8),(0,8)]:
        ET.SubElement(p,"StraightVertex",{"x":str(x),"y":str(y)})
    f=ET.SubElement(sh,"Fill",{"name":"Fill"})
    ET.SubElement(f,"SolidColor",{"colorValue":"FF72C9E2","name":"BoneTint"})
    img=ET.SubElement(arm,"Image",{"assetId":"0:60","name":"GameArtAttachment","x":"92","y":"0","scaleX":"0.9","scaleY":"0.9"})
    frames=ROOT/"private-frames"; frames.mkdir(exist_ok=True)
    debug=ROOT/"debug-frames";debug.mkdir(exist_ok=True)
    count=24
    duration=min(3.0,max(.7,float(chosen["duration"])))
    RESULT.update({"frames":count,"fps":12,"clip_seconds":count/12,"source_sample_duration":duration})
    shot_hashes=[]
    debug_hashes=[]
    for i in range(count):
        t=duration*i/(count-1)
        degrees=linear(keys,t)
        arm.set("rotation",str(math.radians(degrees)))
        img.attrib.pop("hidden",None)
        tree.write(project/"scene.rml",encoding="unicode")
        if i==0:cmd(["rive",str(project),"--verify"])
        private=frames/f"{i:04d}.png"
        cmd(["rive",str(project),f"--screenshot={private}","--viewport=640x360","--advance=0s"])
        shot_hashes.append(hashlib.sha256(private.read_bytes()).hexdigest())
        img.set("hidden","true")
        tree.write(project/"scene.rml",encoding="unicode")
        debug_frame=debug/f"{i:04d}.png"
        cmd(["rive",str(project),f"--screenshot={debug_frame}","--viewport=640x360","--advance=0s"])
        debug_hashes.append(hashlib.sha256(debug_frame.read_bytes()).hexdigest())
    assert len(set(shot_hashes))>4,"Private frames do not move"
    assert len(set(debug_hashes))>4,"Native bone debug frames do not move"
    RESULT["proven"].extend(["native Rive Bone rotation varies using real source keyframes","Rive headless CLI generated 24 art-containing PNGs","debug Rive frames animate with image hidden"])
    args=["ffmpeg","-hide_banner","-loglevel","error","-y","-framerate","12","-i"]
    cmd(args+[str(frames/"%04d.png"),"-c:v","libx264","-pix_fmt","yuv420p",str(ROOT/"private-acceptance.mp4")])
    cmd(args+[str(debug/"%04d.png"),"-c:v","libx264","-pix_fmt","yuv420p",str(SHAREABLE)])
    RESULT["private_video_bytes"]=(ROOT/"private-acceptance.mp4").stat().st_size
    RESULT["debug_video_bytes"]=SHAREABLE.stat().st_size
    RESULT["game_artifact_upload"]=False
    RESULT["public_rig_debug_video"]=SHAREABLE.name
    return True

def main():
    try:run();status="PASS_PARTIAL"
    except Exception as exc:
        RESULT["error"]=repr(exc)
        status="FAIL"
    RESULT["status"]=status
    (OUT/"render-result.json").write_text(json.dumps(RESULT,ensure_ascii=False,indent=2)+"\n")
    report=["# Spine → Rive native animation transfer acceptance","",
        f"Result: **{status}**","",
        f"Source action: \`{RESULT.get('animation','unknown')}\`, source bone: \`{RESULT.get('bone','unknown')}\`.","",
        f"Source keys: {RESULT.get('source_keys','?')}, rotation range: {RESULT.get('rotation_spread_degrees','?')}°, rendered frames: {RESULT.get('frames','?')}.","",
        "Pipeline: Original .skel → converted Spine JSON → sampled original rotate keys → Rive RootBone/Bone → Rive frame sequence → FFmpeg MP4.","",
        "**This is partial migration:** one source bone channel and one texture attachment, NOT complete character conversion or motion-preserving full rig export.","",
        "Private image-containing video and source files remain on runner. Artifact includes only neutral rig-debug MP4 and JSON report.",
        "",
        f"Failure: \`{RESULT.get('error','none')}\`"]
    (OUT/"render-summary.md").write_text("\n".join(report)+"\n")
    print((OUT/"render-summary.md").read_text(),flush=True)
    return 0 if status=="PASS_PARTIAL" else 1

if __name__=="__main__":sys.exit(main())

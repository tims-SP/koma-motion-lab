#!/usr/bin/env python3
"""PROD-003: real Spine full bone hierarchy → native Rive bone objects.

Bakes original animation rotation channels at fixed times into RML; the result
is a full skeleton *diagnostic video*, not a full textured avatar: mesh/IK/slot
mapping and source curve interpolation still need a production adapter.
"""
from __future__ import annotations
import hashlib,json,math,os,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(os.environ.get("PROD_PRIVATE","/tmp/koma-spine-rive-private"))
OUT=Path(os.environ.get("PROD_REPORT","out/spine-rive"))
D=json.loads((ROOT/"source_spine.json").read_text())
METRIC={"stage":"full native bone hierarchy","source_version":D.get("skeleton",{}).get("spine","unknown"),"status":"NOT_RUN"}
def cmd(*args):
    r=subprocess.run(args,capture_output=True,text=True,timeout=120)
    if r.returncode!=0:raise RuntimeError(str(args)+" -> "+(r.stdout+r.stderr)[-1000:])
    return r

def sample_curve(keys,t,field):
    valid=[(float(k.get("time",0)),float(k.get(field,0))) for k in keys if isinstance(k,dict)]
    if not valid:return 0.
    valid.sort()
    if t<=valid[0][0]:return valid[0][1]
    for (a,x),(b,y) in zip(valid,valid[1:]):
        if t<=b:return x+(y-x)*(t-a)/(b-a) if b>a else y
    return valid[-1][1]

def main():
    bones=D["bones"]
    indexed={b["name"]:b for b in bones}
    anim_name="idle_room" if "idle_room" in D.get("animations",{}) else next(iter(D.get("animations",{})))
    anim=D["animations"][anim_name]
    animated=anim.get("bones",{})
    rot_channels={n:track["rotate"] for n,track in animated.items() if isinstance(track,dict) and isinstance(track.get("rotate"),list)}
    durations=[float(k.get("time",0)) for keys in rot_channels.values() for k in keys]
    if not durations or max(durations)<.1:raise RuntimeError("Original action has no meaningful rotation keys")
    max_time=min(max(durations),2.4)
    METRIC.update({"source_bones":len(bones),"action":anim_name,
      "animated_rotation_bones":len(rot_channels),"source_duration":max_time})
    project=ROOT/"full-native-bones"
    cmd("rive","create",str(project))
    tree=ET.parse(project/"scene.rml")
    root=tree.getroot()
    board=next(x for x in root.iter() if x.tag=="Artboard")
    board.set("name","FullSpineSkeleton")
    board.set("width","640");board.set("height","360")
    group=ET.SubElement(board,"Node",{"name":"SpineRoot","x":"320","y":"180","scaleX":"0.34","scaleY":"-0.34"})
    objs={}
    for n,b in enumerate(bones):
        parent_name=b.get("parent")
        if parent_name not in objs and parent_name is not None:
            raise RuntimeError(f"Bone parent order missing: {b['name']} / {parent_name}")
        p=objs[parent_name] if parent_name in objs else group
        native="Bone" if parent_name else "RootBone"
        x=float(b.get("x",0))
        y=float(b.get("y",0))
        # Rive Bone translation is anchored at parent tip; Spine uses parent origin.
        if parent_name:
            x-=float(indexed[parent_name].get("length",0))
        length=max(1.,abs(float(b.get("length",1))))
        if parent_name:
            # Rive Bone has rotation/length but no authored x/y. Introduce a
            # translated Node and keep the Bone under that container.
            p=ET.SubElement(p,"Node",{"name":f"Offset_{n}","x":f"{x:.5f}","y":f"{y:.5f}"})
        attr={"id":f"0:{200+n}","name":b["name"],
              "length":f"{length:.5f}","rotation":str(math.radians(float(b.get("rotation",0))))}
        if not parent_name:
            attr.update({"x":f"{x:.5f}","y":f"{y:.5f}"})
        obj=ET.SubElement(p,native,attr)
        objs[b["name"]]=obj
        if float(b.get("length",0))>12:
            shape=ET.SubElement(obj,"Shape",{"name":f"visual_{n}"})
            path=ET.SubElement(shape,"PointsPath",{"name":"bone_line"})
            for px,py in [(0,-2),(length,-2),(length,2),(0,2)]:
                ET.SubElement(path,"StraightVertex",{"x":str(px),"y":str(py)})
            fill=ET.SubElement(shape,"Fill",{"name":"Fill"})
            ET.SubElement(fill,"SolidColor",{"colorValue":"FF6BC6E4","name":"Color"})
    METRIC["created_rive_bones"]=len(objs)
    frames=ROOT/"full-native-frames";frames.mkdir(exist_ok=True)
    hashes=[]
    for frame in range(24):
        t=max_time*frame/23
        for n,keys in rot_channels.items():
            if n not in objs:continue
            base=float(indexed[n].get("rotation",0))
            objs[n].set("rotation",str(math.radians(base+sample_curve(keys,t,"angle"))))
        tree.write(project/"scene.rml",encoding="unicode")
        if frame==0:cmd("rive",str(project),"--verify")
        dest=frames/f"{frame:04d}.png"
        cmd("rive",str(project),f"--screenshot={dest}","--viewport=640x360","--advance=0s")
        hashes.append(hashlib.sha256(dest.read_bytes()).hexdigest())
    unique=len(set(hashes))
    if unique<4:raise RuntimeError(f"Full skeleton animations not visually moving: {unique}/24")
    dest=OUT/"full-skeleton-debug.mp4"
    cmd("ffmpeg","-hide_banner","-loglevel","error","-y","-framerate","12","-i",str(frames/"%04d.png"),
        "-c:v","libx264","-pix_fmt","yuv420p",str(dest))
    METRIC.update({"status":"PASS","visual_unique_frames":unique,"frames":24,
        "debug_video_bytes":dest.stat().st_size,"source_art_exported":False,
        "excluded":["mesh weights","UV textures","IK/transform/path constraints","source exact bezier curves","slot draw order"],
        "notes":"Native full bone hierarchy with rotation tracks only. This video is a structural diagnostic, not avatar fidelity proof."})

def finish():
    (OUT/"full-skeleton-result.json").write_text(json.dumps(METRIC,ensure_ascii=False,indent=2)+"\n")
    (OUT/"full-skeleton-summary.md").write_text("# Full native Rive skeleton transfer\n\n"+
       "\n".join(f"- {k}: {v}" for k,v in METRIC.items())+"\n")
    print((OUT/"full-skeleton-summary.md").read_text())
if __name__=="__main__":
    try:main();finish()
    except Exception as e:
        METRIC["status"]="FAIL";METRIC["error"]=repr(e);finish();sys.exit(1)

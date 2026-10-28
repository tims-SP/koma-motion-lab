#!/usr/bin/env python3
"""ASSET-PROD-001: real Reverse:1999 asset sampling and Rive shot on ephemeral CI.
Never publishes copyrighted source or rendered frames to a public repository/artifact.
"""
from __future__ import annotations
import hashlib, json, os, re, struct, subprocess, sys, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path

UPSTREAM="myssal/Reverse-1999-CN-Asset"
COMMIT="45e75248ba3b25053fd32e63ab13c2f9f54dd9df"
SPINE="roles/300301_hujisheng"
CUBISM="live2d/roles/300301_hujisheng"
MODEL="300301_hujisheng"
ROOT=Path(os.environ.get("WORK_ROOT", "/tmp/koma-reverse1999-production"))
REPORT=Path(os.environ.get("REPORT_ROOT", "out/reverse1999"))
RAW=ROOT/"upstream"
FRAMES=ROOT/"frames"
REPORT.mkdir(parents=True,exist_ok=True)
RAW.mkdir(parents=True,exist_ok=True)
FRAMES.mkdir(parents=True,exist_ok=True)
results={"source_repo":UPSTREAM,"source_commit":COMMIT,
         "asset_id":MODEL,"rights":"Third-party game files; repo has no observed LICENSE; not redistributed",
         "tests":{},"checks":{},"files":[],"missing_references":[]}

def record(name,success,info=None):
    results["tests"][name]={"ok":bool(success),"details":info}
    print(f'{"PASS" if success else "FAIL"} {name}: {str(info)[:190]}',flush=True)

def load_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":"koma-motion-lab-asset-probe","Accept":"application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.load(response)

def github_listing(path):
    quoted=urllib.parse.quote(path,safe="/")
    url=f"https://api.github.com/repos/{UPSTREAM}/contents/{quoted}?ref={COMMIT}"
    data=load_json(url)
    return {item["name"]:item for item in data}

def fetch_file(path,meta):
    if not path.startswith(("roles/300301_hujisheng/","live2d/roles/300301_hujisheng/","mappings/")):
        raise ValueError("Unapproved path "+path)
    if meta["type"]!="file" or meta["size"]>8_000_000:
        raise ValueError("Not a small regular file "+path)
    req=urllib.request.Request(
        f"https://raw.githubusercontent.com/{UPSTREAM}/{COMMIT}/{urllib.parse.quote(path,safe='/')}",
        headers={"User-Agent":"koma-motion-lab-asset-probe"})
    with urllib.request.urlopen(req, timeout=90) as res:
        data=res.read(8_000_001)
    if len(data)!=meta["size"]:raise ValueError(f"byte length mismatch {path}")
    digest=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
    if digest!=meta["sha"]:raise ValueError(f"Git SHA-1 mismatch {path}")
    local=RAW/path
    local.parent.mkdir(parents=True,exist_ok=True)
    local.write_bytes(data)
    results["files"].append({"path":path,"bytes":len(data),"git_blob_sha":digest,"sha256":hashlib.sha256(data).hexdigest()})
    return local

def grab_listing(parent,name,listing):
    if name not in listing:raise ValueError(f"Missing expected file: {parent}/{name}")
    return fetch_file(parent+"/"+name,listing[name])

def require(condition, message):
    if not condition:raise ValueError(message)

def metadata_probe():
    spine=github_listing(SPINE)
    cubism=github_listing(CUBISM)
    tex=github_listing(CUBISM+"/textures")
    motions=github_listing(CUBISM+"/motions")
    expressions=github_listing(CUBISM+"/expressions")
    mapping=github_listing("mappings")
    results["checks"]["inventory"]={
        "spine":sorted(spine),
        "cubism":sorted(cubism),
        "textures":sorted(tex),
        "motion_count":len(motions),
        "expression_count":len(expressions)}
    for name in (MODEL+".atlas",MODEL+".png",MODEL+"_fight.skel",MODEL+"_room.skel",MODEL+"_ui.skel"):
        grab_listing(SPINE,name,spine)
    for name in (MODEL+".model3.json",MODEL+".moc3"):
        grab_listing(CUBISM,name,cubism)
    grab_listing(CUBISM+"/textures",MODEL+".png",tex)
    grab_listing(CUBISM+"/motions","b_idle.motion3.json",motions)
    grab_listing(CUBISM+"/expressions","e_idle.exp3.json",expressions)
    grab_listing("mappings","ArcanistMap.json",mapping)
    record("downloaded_both_formats",True,{"files":len(results["files"]),"bytes":sum(f["bytes"] for f in results["files"])})
    model=json.loads((RAW/CUBISM/(MODEL+".model3.json")).read_text("utf-8"))
    refs=model["FileReferences"]
    expected=[refs["Moc"],*refs["Textures"],refs["DisplayInfo"]]
    expected += [x["File"] for variants in refs.get("Motions",{}).values() for x in variants]
    expected += [x["File"] for x in refs.get("Expressions",[])]
    missing=[]
    for path in expected:
        root=CUBISM+"/"+path
        prefix,name=root.rsplit("/",1)
        catalog={CUBISM:cubism,CUBISM+"/textures":tex,CUBISM+"/motions":motions,CUBISM+"/expressions":expressions}.get(prefix,{})
        if name not in catalog:missing.append(path)
    results["missing_references"]=sorted(set(missing))
    record("cubism_references",not missing,{"references":len(expected),"missing":missing[:5]})
    moc=(RAW/CUBISM/(MODEL+".moc3")).read_bytes()
    record("cubism_binary_header",moc.startswith(b"MOC3"),{"header_hex":moc[:12].hex(),"bytes":len(moc)})
    # An existing compressed .skel binary is not a Rive RML project.
    skel=(RAW/SPINE/(MODEL+"_fight.skel")).read_bytes()
    record("spine_binary_present",len(skel)>100,{"head_hex":skel[:24].hex(),"bytes":len(skel)})
    atlas=(RAW/SPINE/(MODEL+".atlas")).read_text("utf-8")
    names=re.findall(r"^([A-Za-z0-9_]+)\s*\n\s*bounds:",atlas,re.M)
    results["checks"]["spine_atlas_regions"]=len(names)
    record("spine_atlas_regions",len(names)>20,{"regions":len(names),"first":names[:8]})
    mappingdata=json.loads((RAW/"mappings/ArcanistMap.json").read_text("utf-8"))
    found=[a for a in mappingdata if any(str(x.get("id"))=="300301" for x in a.get("live2d",[]))]
    record("character_mapping",bool(found),{"characters":[a.get("name") for a in found]})
    from PIL import Image
    for name in (MODEL+".png",):
        with Image.open(RAW/SPINE/name) as im:
            record("spine_texture_decode",im.width>100 and im.height>100,{"size":im.size,"mode":im.mode})
        with Image.open(RAW/CUBISM/"textures"/name) as im:
            record("cubism_texture_decode",im.width>100 and im.height>100,{"size":im.size,"mode":im.mode})
    return atlas

def parse_regions(atlas):
    # Atlas regions in this repository use the modern bounds syntax.
    names={}
    lines=atlas.splitlines()
    for i,line in enumerate(lines):
        name=line.strip()
        if not name or not re.match(r"^[\w]+$",name):continue
        if i+1<len(lines) and lines[i+1].strip().startswith("bounds:"):
            m=re.search(r"bounds:\s*(\d+),(\d+),(\d+),(\d+)",lines[i+1])
            if m: names[name]=tuple(map(int,m.groups()))
    return names

def render_rive_project(frame_count=16):
    from PIL import Image,ImageDraw
    atlas=(RAW/SPINE/(MODEL+".atlas")).read_text("utf-8")
    regions=parse_regions(atlas)
    # These parts are representative production textures, not the original spine rig.
    targets={"face":"hjs_z_lian","torso":"hjs_b_qugan"}
    require(all(n in regions for n in targets.values()),"selected face / torso regions unavailable")
    texture=Image.open(RAW/SPINE/(MODEL+".png")).convert("RGBA")
    assets={}
    for label,region in targets.items():
        x,y,w,h=regions[region]
        require(x+w<=texture.width and y+h<=texture.height,"atlas crop out of range")
        part=texture.crop((x,y,x+w,y+h))
        require(part.getbbox() is not None,"extracted image is entirely transparent")
        assets[label]=part
    # This is a *pipeline integration* clip, not the game's original animation.
    # Render each shot frame using Rive CLI, then encode a temporary local MP4.
    project=ROOT/"rive-shot"
    subprocess.run(["rive","create",str(project)],check=True,capture_output=True,text=True)
    for name,im in assets.items(): im.save(project/f"{name}.png")
    # Original/generated background, not copied from the game.
    bg=Image.new("RGBA",(640,360),(31,37,53,255))
    brush=ImageDraw.Draw(bg)
    for y in range(360):
        brush.line([(0,y),(639,y)],fill=(34+int(y/50),39+int(y/35),56+int(y/25),255))
    bg.save(project/"background.png")
    template=ET.parse(project/"scene.rml")
    rawroot=template.getroot()
    board=next(e for e in rawroot.iter() if e.tag=="Artboard")
    board.set("width","640");board.set("height","360");board.set("name","Reverse1999TexturePilot")
    for id,name in (("0:60","background"),("0:61","torso"),("0:62","face")):
        ET.SubElement(rawroot,"ImageAsset",{"file":name+".png","id":id,"name":name})
    def add_image(name,asset_id,x,y,sx,sy,rotation=0):
        return ET.SubElement(board,"Image",{"assetId":asset_id,"name":name,
            "x":str(x),"y":str(y),"scaleX":str(sx),"scaleY":str(sy),"rotation":str(rotation)})
    # Rive editor optional. Compose the extracted, sprite-atlas texture fragments.
    add_image("background","0:60",320,180,1,1)
    add_image("torso","0:61",310,245,1.6,1.6)
    face=add_image("face","0:62",309,130,1.85,1.85)
    xml=project/"scene.rml"
    frame_metrics=[]
    for i in range(frame_count):
        import math
        phase=i/(frame_count-1)
        face.set("rotation",f"{0.08*math.sin(phase*math.pi*2):.6f}")
        face.set("y",str(round(130+8*math.sin(phase*math.pi*2))))
        face.set("x",str(round(309+4*math.sin(phase*math.pi*2))))
        template.write(xml,encoding="unicode",xml_declaration=False)
        cmd=["rive",str(project),f"--screenshot={FRAMES/f'frame_{i:04d}.png'}","--viewport=640x360","--advance=0s"]
        if i==0:
            res=subprocess.run(["rive",str(project),"--verify"],capture_output=True,text=True,timeout=60)
            require(res.returncode==0,"Rive source verify error "+res.stdout[-200:]+res.stderr[-200:])
        res=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
        require(res.returncode==0,f"Rive frame {i} failed: "+(res.stdout+res.stderr)[-500:])
        frame_metrics.append(hashlib.sha256((FRAMES/f"frame_{i:04d}.png").read_bytes()).hexdigest())
    record("rive_texture_shot_frames",len(set(frame_metrics))>=4,{"rendered":len(frame_metrics),"unique":len(set(frame_metrics))})
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-framerate","12","-i",str(FRAMES/"frame_%04d.png"),"-c:v","libx264","-pix_fmt","yuv420p",str(ROOT/"pilot.mp4")],check=True,timeout=120)
    record("ffmpeg_private_mp4", (ROOT/"pilot.mp4").stat().st_size>1000,
           {"size":(ROOT/"pilot.mp4").stat().st_size,"frames":frame_count,"fps":12,"source_rig_reused":False})
    results["checks"]["private_media_sha256"]=hashlib.sha256((ROOT/"pilot.mp4").read_bytes()).hexdigest()
    results["checks"]["production_limit"]="Texture parts only; no automatic Spine/Cubism rig import or high-quality retarget demonstrated"

def main():
    failure=None
    try:
        metadata_probe()
        render_rive_project()
    except Exception as exc:
        failure=repr(exc)
        record("production_pipeline",False,failure)
    # Published outputs: metadata, SHA hashes, tech conclusions ONLY.
    results["checks"]["copyright_review"]="No LICENSE in upstream root. Public availability is not a reuse/redistribution license."
    results["checks"]["distribution"]="No game artwork, source binaries, preview PNG, MP4 or embedded .riv uploaded to GitHub."
    results["checks"]["rive_compatibility"]="PNG textures are usable as ImageAssets. Precompiled .moc3 and .skel require native runtimes or substantial conversion, not Rive direct import."
    (REPORT/"results.json").write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n")
    passed=[k for k,v in results["tests"].items() if v["ok"]]
    failed=[k for k,v in results["tests"].items() if not v["ok"]]
    lines=["# ASSET-PROD-001 · Reverse:1999 production asset pilot","",
      f"Source: \`{UPSTREAM}@{COMMIT}\`. Selected character: \`{MODEL}\`.","",
      f"**Passed checks:** {len(passed)}. **Failed checks:** {len(failed)}.","",
      "| Check | Result |","|---|---|"]
    lines += [f'| {name} | {"PASS" if v["ok"] else "FAIL"} |' for name,v in results["tests"].items()]
    lines += ["","## Scope and limitations",
      "- Two existing asset pipelines: binary Spine and compiled Live2D Cubism.",
      "- Actual texture parts can be imported into Rive via ImageAsset and rendered headlessly.",
      "- This is not original rig reuse, automatic rig transfer, or high-quality anime character animation.",
      "- Source asset files and pilot media remain only in the temporary CI runner and are not uploaded.",
      "- The asset repository has no observed LICENSE; no redistribution permission is inferred.",
      "","## Debug details",f"\`{failure or 'No runtime failure'}\`"]
    (REPORT/"summary.md").write_text("\n".join(lines)+"\n")
    print((REPORT/"summary.md").read_text())
    return 1 if failure or failed else 0

if __name__=="__main__": sys.exit(main())

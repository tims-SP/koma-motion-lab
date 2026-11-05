#!/usr/bin/env python3
"""Create the P0 ArtMesh motion-review GIF from real headless-browser PNGs.

Authoritative proof is the 37 SHA-256-verified RGBA frames. GIF is a palette
preview on the P0 review background, not an alternative transparent source.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

def sha(file):
    h=hashlib.sha256()
    with Path(file).open("rb") as fp:
        for block in iter(lambda:fp.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def create(frames_root,output):
    frames_root=Path(frames_root).resolve()
    report=json.loads((frames_root/"canvas-qa.json").read_text())
    angles=[i*2.5 for i in range(37)]
    if report.get("status")!="CAPTURED_FOR_ANATOMICAL_INSPECTION" or \
       report.get("frameCount")!=37:
        raise ValueError("37 real browser frames are required")
    records={item["yaw"]:item for item in report["outputs"]}
    if sorted(records)!=angles:
        raise ValueError("Frame angles are incomplete")
    images=[]
    sample=Image.new("RGB",(512*5,512),(45,57,72))
    for i,angle in enumerate(angles):
        rec=records[angle]
        source=Path(rec["path"])
        if not source.is_relative_to(frames_root):
            raise ValueError("Unexpected frame source root")
        if sha(source)!=rec["sha256"]:
            raise ValueError("Frame digest mismatch: "+str(angle))
        rgba=Image.open(source).convert("RGBA")
        if rgba.size!=(1024,1024):
            raise ValueError("Not original 1024 canvas")
        bg=Image.new("RGBA",rgba.size,(47,57,74,255))
        bg.alpha_composite(rgba)
        small=bg.convert("RGB").resize((512,512),Image.Resampling.LANCZOS)
        images.append(small)
        if i in (0,9,18,27,36):
            sample.paste(small,((0,9,18,27,36).index(i)*512,0))
    # A single color table avoids visual flicker from per-frame adaptive
    # palettes; original 1024 RGBA frames remain available separately.
    global_palette=sample.quantize(colors=254,method=Image.Quantize.MEDIANCUT)
    palette_frames=[im.quantize(palette=global_palette,dither=Image.Dither.NONE)
                    for im in images]
    sequence=palette_frames+palette_frames[-2:0:-1]
    output=Path(output).resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    sequence[0].save(output,save_all=True,append_images=sequence[1:],
                     duration=110,disposal=2,loop=0,optimize=True)
    with Image.open(output) as gif:
        if gif.n_frames!=len(sequence):
            raise ValueError("GIF frame count mismatch")
    qa={"schema":"KOMA-P0-ARTMESH-MOTION-REVIEW-GIF-QA-V1",
        "characterId":"p0_character_001","status":"REAL_BROWSER_FRAMES_PACKAGED",
        "sourceRole":"39 distinct original-P0-view-derived RGBA semantic layers",
        "sourceFrameCount":len(images),"GIFFrames":len(sequence),
        "resolution":[512,512],"sourcePNGResolution":[1024,1024],
        "GIFFile":str(output),"GIFBytes":output.stat().st_size,
        "GIFSHA256":sha(output),"previewSource":"real HTML browser Canvas2D",
        "transparentSourceIncludedSeparately":True,
        "artisticQuality":"REQUIRES_SEMANTIC_TEXTURE_CORRESPONDENCE",
        "framesSHA256":[{"angle":a,"sha256":records[a]["sha256"]} for a in angles]}
    outfile=output.parent/"turn-gif-qa.json"
    outfile.write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:qa[k] for k in
           ("status","sourceFrameCount","GIFFrames","resolution",
            "GIFFile","GIFBytes","GIFSHA256","artisticQuality")},
           indent=2,ensure_ascii=False))
    return qa

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--frames",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    create(args.frames,args.output)

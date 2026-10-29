#!/usr/bin/env python3
"""GODOT-004 high-resolution native Live2D fidelity diagnostics.

Genuine images rendered by Godot + GDCubism at 1920x1080 under Mesa/Xvfb.
Motion validity, background responsiveness, and fine-detail *review* only;
do not claim official Cubism pixel equivalence without a reference capture.
"""
import json
import math
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageStat

OUT=Path("out/godot-004")
DARK_BG=(18,28,43)
STILLS=sorted(OUT.glob("dark-still*.png"))
WHITE=sorted(OUT.glob("white-still*.png"))
SPECS=[("nod",90,[0,20,40,65,89]),("idle",120,[0,25,50,75,119])]
errors=[]
report={"stage":"GODOT-004","status":"FAIL",
        "reference_parity":"NOT_TESTED_NO_OFFICIAL_CORE_REFERENCE",
        "real_assets":"301003_x original MOC3, corrected Meta only in genuine motions",
        "expected_size":[1920,1080], "motion_results":{}}

def get_image(path):
    with Image.open(path) as f:
        return f.convert("RGB")
def mean_diff(a,b):
    return sum(ImageStat.Stat(ImageChops.difference(a,b)).mean)/3
def image_bbox(im,bg=DARK_BG):
    # coarse foreground bounds only, not proof of correct clipping/render order
    small=im.resize((480,270),Image.Resampling.LANCZOS)
    px=small.load()
    coord=[(x,y) for y in range(270) for x in range(480)
           if sum(abs(px[x,y][c]-bg[c]) for c in range(3))>90]
    if not coord:
        return None,0.
    return [min(x for x,y in coord)*4,min(y for x,y in coord)*4,
            (max(x for x,y in coord)+1)*4,(max(y for x,y in coord)+1)*4],len(coord)/(480*270)
def movie_info(filename,expected):
    if not filename.exists() or filename.stat().st_size<5000:
        errors.append(f"missing video {filename.name}")
        return {}
    p=subprocess.run(["ffprobe","-v","error","-count_frames","-select_streams","v:0",
                      "-show_entries","stream=width,height,nb_read_frames,avg_frame_rate",
                      "-of","json",str(filename)],capture_output=True,check=True,text=True)
    v=json.loads(p.stdout).get("streams",[])
    if not v:
        errors.append(f"no video stream {filename.name}")
        return {}
    stream=v[0]
    if (int(stream.get("width",0)),int(stream.get("height",0)))!=(1920,1080):
        errors.append(f"video resolution mismatch {filename.name}")
    if int(stream.get("nb_read_frames",0))!=expected:
        errors.append(f"video frame count mismatch {filename.name}")
    return stream

if len(STILLS)!=8: errors.append(f"dark static frame count {len(STILLS)}, expected 8")
if len(WHITE)!=1: errors.append(f"white static frame count {len(WHITE)}, expected 1")
all_frames={}
if len(STILLS)==8 and len(WHITE)==1:
    base=get_image(STILLS[0])
    base_last=get_image(STILLS[-1])
    white=get_image(WHITE[0])
    if any(im.size!=(1920,1080) for im in (base,base_last,white)):
        errors.append("still frame dimensions incorrect")
    static_delta=mean_diff(base,base_last)
    report["static_control_change"]=round(static_delta,5)
    if static_delta>0.06: errors.append("static control changed during recording")
    corner_dark=base.getpixel((2,2))
    corner_white=white.getpixel((2,2))
    report["background_corner_dark"]=corner_dark
    report["background_corner_white"]=corner_white
    if sum(corner_white)-sum(corner_dark)<450:
        errors.append("white background did not render correctly")
    bbox,coverage=image_bbox(base)
    report["static_subject_bbox"]=bbox
    report["static_foreground_coverage"]=round(coverage,5)
    if bbox is None: errors.append("no original character foreground")
    elif min(bbox[0],bbox[1],1920-bbox[2],1080-bbox[3])<40:
        errors.append("1080p subject too close to output edge")
    if bbox:
        headbox=(max(0,bbox[0]-35),max(0,bbox[1]-25),
                 min(1920,bbox[2]+35),min(1080,bbox[1]+int((bbox[3]-bbox[1])*.38)))
        all_frames["dark"]=base
        all_frames["white"]=white
        report["head_crop_bbox"]=headbox
        # Black / white contrast shows alpha halos, holes, bad masks; not official parity.
        im_b=base.crop(headbox);im_w=white.crop(headbox)
        review=Image.new("RGB",(960,660),(28,30,36))
        label=ImageDraw.Draw(review)
        for n,(img,name) in enumerate(((im_b,"DARK BACKGROUND"),(im_w,"WHITE BACKGROUND"))):
            img.thumbnail((470,620),Image.Resampling.LANCZOS)
            img=img.resize((470,620),Image.Resampling.LANCZOS)
            review.paste(img,(n*480+5,30))
            label.text((n*480+10,8),name,fill="white")
        review.save(OUT/"mask-contrast-head.jpg",quality=95,subsampling=0)

for name,n,indices in SPECS:
    paths=sorted(OUT.glob(name+"-frame*.png"))
    if len(paths)!=n:
        errors.append(f"{name} PNG count {len(paths)}, expected {n}")
    if not paths:
        continue
    probes=[get_image(paths[min(i,len(paths)-1)]) for i in indices]
    if any(im.size!=(1920,1080) for im in probes):
        errors.append(f"{name} PNG resolution mismatch")
    base_probes=all_frames.get("dark")
    info={"frame_count":len(paths),"movie":movie_info(OUT/(name+"-1080p.mp4"),n)}
    if base_probes is not None:
        diffs=[round(mean_diff(base_probes,im),4) for im in probes]
        info["global_difference_from_static"]=diffs
        bx=report.get("static_subject_bbox")
        if bx:
            local=[round(mean_diff(base_probes.crop(tuple(bx)),im.crop(tuple(bx))),4)
                   for im in probes]
            info["subject_roi_difference_from_static"]=local
            if max(local)<0.05:
                errors.append(f"{name}: no movement within subject region")
    report["motion_results"][name]=info
    all_frames[name]=probes
    if "head_crop_bbox" in report:
        left,top,right,bottom=report["head_crop_bbox"]
        board=Image.new("RGB",(3*480,2*370),(25,27,33))
        pen=ImageDraw.Draw(board)
        for j,(img,index) in enumerate(zip(probes,indices)):
            crop=img.crop((left,top,right,bottom))
            crop=crop.resize((470,340),Image.Resampling.LANCZOS)
            board.paste(crop,((j%3)*480+5,(j//3)*370+25))
            pen.text(((j%3)*480+10,(j//3)*370+6),f"{name} frame {index}",fill="white")
        board.save(OUT/(name+"-head-detail.jpg"),quality=94,subsampling=0)

report["errors"]=errors
report["status"]="PASS_HIRES_MULTIMOTION_REVIEW_REQUIRED" if not errors else "FAIL"
OUT.mkdir(parents=True,exist_ok=True)
(OUT/"quality-audit.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
print("GODOT004_QUALITY_AUDIT",json.dumps(report,ensure_ascii=False))
sys.exit(1 if errors else 0)

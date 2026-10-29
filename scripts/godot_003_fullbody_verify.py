#!/usr/bin/env python3
"""Validate full-body framing and visible nod in *real* GDCubism/PNG frames.

This is NOT a substitute for reference-frame parity with the official Cubism
renderer. It checks that all major portions of the subject are inside frame,
the static control is stable, 90 frames decode, and visible movement exists.
"""
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageStat
import json
import subprocess
import sys

OUT=Path("out/godot-002")
MOTION=sorted(OUT.glob("fullbody-anim*.png"))
STILL=sorted(OUT.glob("fullbody-static*.png"))
error=[]
if len(MOTION)!=90: error.append(f"expected 90 real motion frames, got {len(MOTION)}")
if len(STILL)!=8: error.append(f"expected 8 static-control frames, got {len(STILL)}")
report={"stage":"GODOT-003 fullbody", "status":"FAIL",
        "frame_count":len(MOTION),"static_count":len(STILL),
        "camera":{"zoom":1.0,"shift_y":210},
        "official_cubism_visual_parity":"NOT_TESTED"}
if MOTION and STILL:
    frames=[]
    for i in (0,22,45,67,89):
        with Image.open(MOTION[min(i,len(MOTION)-1)]) as a:
            frames.append(a.convert("RGB"))
    with Image.open(STILL[0]) as a:
        still=a.convert("RGB")
    with Image.open(STILL[-1]) as a:
        static_last=a.convert("RGB")
    if any(im.size!=(960,540) for im in [still,*frames]):
        error.append("wrong frame resolution")
    static_delta=sum(ImageStat.Stat(ImageChops.difference(still,static_last)).mean)/3
    report["static_control_difference"]=round(static_delta,5)
    if static_delta>0.05: error.append("static baseline unstable")
    small=still.resize((240,135))
    pix=small.load()
    coords=[(x,y) for y in range(135) for x in range(240)
            if sum(abs(pix[x,y][k]-(18,28,43)[k]) for k in range(3))>90]
    if not coords:
        error.append("no foreground")
        bbox=None
    else:
        bbox=[min(x for x,y in coords)*4,min(y for x,y in coords)*4,
              (max(x for x,y in coords)+1)*4,(max(y for x,y in coords)+1)*4]
        report["visible_bbox"]=bbox
        report["foreground_coverage"]=round(len(coords)/(240*135),4)
        if bbox[1]<20 or bbox[3]>520 or bbox[0]<20 or bbox[2]>940:
            error.append("character clipped or less than 20px from edge")
    signals=[]
    for frame in frames:
        d=ImageChops.difference(still,frame)
        signals.append(round(sum(ImageStat.Stat(d).mean)/3,4))
    report["motion_vs_static_rgb_mean"]=signals
    if max(signals)<0.09: error.append("insufficient animated difference")
    if bbox:
        # Independent close-up motion signal in model rectangle.
        local=[]
        for frame in frames:
            d=ImageChops.difference(still,frame).crop(tuple(bbox))
            local.append(round(sum(ImageStat.Stat(d).mean)/3,4))
        report["subject_roi_difference"]=local
        if max(local)<0.30: error.append("no detectable nod inside subject area")
    # Actual review sheet for manual head, torso, garment, boot checks.
    show=[still]+frames
    board=Image.new("RGB",(1440,600),(29,32,40))
    pen=ImageDraw.Draw(board)
    labels=["fullbody / still"]+["nod / frame "+str(i) for i in (0,22,45,67,89)]
    for i,img in enumerate(show):
        x=(i%3)*480; y=(i//3)*300
        board.paste(img.resize((480,270),Image.Resampling.LANCZOS),(x,y+25))
        pen.text((x+7,y+5),labels[i],fill="white")
    board.save(OUT/"fullbody-contact.jpg",quality=93,subsampling=0)
movie=OUT/"fullbody-nod.mp4"
if not movie.is_file() or movie.stat().st_size<5000:
    error.append("encoded fullbody mp4 absent")
else:
    p=subprocess.run(["ffprobe","-v","error","-count_frames","-select_streams","v:0",
                      "-show_entries","stream=width,height,nb_read_frames,avg_frame_rate",
                      "-of","json",str(movie)],capture_output=True,text=True,check=True)
    info=json.loads(p.stdout).get("streams",[])
    report["ffprobe"]=info
    if not info or int(info[0].get("nb_read_frames",0))!=90:
        error.append("encoded frame count mismatch")
report["errors"]=error
report["status"]="PASS_FRAMED_CHARACTER_AND_VISIBLE_MOTION_NOT_PARITY" if not error else "FAIL"
(OUT/"fullbody-verify.json").write_text(json.dumps(report,indent=2)+"\n")
print("GODOT003_FULLBODY_VERIFICATION",json.dumps(report))
sys.exit(1 if error else 0)

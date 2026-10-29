#!/usr/bin/env python3
"""CORE-002: isolated camera / source animation / spatial skin deformation gates."""
from __future__ import annotations
import json
from pathlib import Path
from PIL import Image, ImageChops
root=Path(__file__).resolve().parents[1]
base=root/"out"/"core002"
bg=(242,244,248)

def pixel_fraction(a,b,threshold=18):
    d=ImageChops.difference(a,b).convert("L")
    return sum(1 for v in d.getdata() if v>threshold)/(a.width*a.height)

def check(name):
    images=sorted((base/name).glob("*.png"))
    if len(images)!=48:
        raise SystemExit(f"FAIL {name}: {len(images)} frames, expected 48")
    picks=[Image.open(images[i]).convert("RGB") for i in (0,12,24,36,47)]
    if any(x.size!=(960,540) for x in picks): raise SystemExit("Bad viewport")
    # crop overlay so only rendered geometry can satisfy motion check
    crops=[im.crop((0,110,960,540)) for im in picks]
    cover=[pixel_fraction(x,Image.new("RGB",x.size,bg),24) for x in crops]
    motion=[pixel_fraction(crops[i],crops[i+1]) for i in range(4)]
    if max(cover)<0.025:
        raise SystemExit(f"FAIL {name}: blank geometry {cover}")
    if max(motion)<0.006:
        raise SystemExit(f"FAIL {name}: camera-only/no posed skin detected {motion}")
    if name=="yaw" and cover[-1]<0.015:
        raise SystemExit(f"FAIL {name}: front mesh collapses at 90 deg")
    # reach has start == end; 0 vs 24 must move with fixed camera
    if name=="reach" and pixel_fraction(crops[0],crops[2])<0.006:
        raise SystemExit("FAIL reach: spatial bone rotation does not change image")
    if name=="walk" and pixel_fraction(crops[0],crops[2])<0.006:
        raise SystemExit("FAIL walk: source bone clip did not move character")
    return {"coverage":cover,"consecutive_frame_change":motion}

metrics={x:check(x) for x in ("yaw","walk","reach")}
sheet=Image.new("RGB",(960*3,540*3))
for row,name in enumerate(("yaw","walk","reach")):
    for col,j in enumerate((0,24,47)):
        im=Image.open(base/name/f"{j:04d}.png").convert("RGB")
        sheet.paste(im,(col*960,row*540))
sheet.save(base/"contact.png")
report={"status":"PASS_STRUCTURAL_AND_ISOLATED_MOTION_QA",
        "scenarios":metrics,
        "animation_source":"Godot source Animation subresources; linear sample only",
        "original_runtime_pixel_parity":"NOT_TESTED",
        "2d_uv_image_fidelity":"NOT_TESTED",
        "side_and_back_artwork":"FAIL_UNPAINTED_PROXY",
        "complex_3d_motion":"NOT_TESTED",
        "anime_aesthetic":"NOT_TESTED"}
(base/"qa.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))

#!/usr/bin/env python3
"""Image-level fail-closed QA. These are smoke gates, not anime-art acceptance."""
from __future__ import annotations
import json
from pathlib import Path
from PIL import Image, ImageChops
root=Path(__file__).resolve().parents[1]
out=root/"out"
frames=sorted((out/"frames").glob("*.png"))
if len(frames)!=48: raise SystemExit(f"FAIL: expected 48 frames; got {len(frames)}")
bg=(242,244,248)
images=[Image.open(frames[i]).convert("RGB") for i in (0,23,47)]
if any(im.size!=(960,540) for im in images): raise SystemExit("FAIL: unexpected frame size")
# Exclude the overlay, which would otherwise produce fake motion.
crops=[im.crop((0,110,960,540)) for im in images]
def fraction(a,b,threshold):
    d=ImageChops.difference(a,b).convert("L")
    return sum(1 for p in d.getdata() if p>threshold)/(a.width*a.height)
coverage=[fraction(im,Image.new("RGB",im.size,bg),24) for im in crops]
motion01=fraction(crops[0],crops[1],18)
motion12=fraction(crops[1],crops[2],18)
if min(coverage)<0.015: raise SystemExit(f"FAIL: blank/too small character: {coverage}")
if min(motion01,motion12)<0.002: raise SystemExit(f"FAIL: no geometry/camera movement: {motion01}, {motion12}")
sheet=Image.new("RGB",(960*3,540))
for i,im in enumerate(images):sheet.paste(im,(i*960,0))
sheet.save(out/"contact.png")
report={"status":"PASS_STRUCTURAL_RENDER_SMOKE_ONLY","frame_count":48,
        "character_coverage_excluding_overlay":coverage,
        "frame_change_fractions":[motion01,motion12],
        "reference_pixel_parity":"NOT_TESTED",
        "source_skeleton_runtime_parity":"NOT_TESTED",
        "side_back_artwork_fidelity":"FAIL_NO_ARTWORK",
        "full_3d_motion":"NOT_TESTED",
        "anime_visual_acceptance":"NOT_TESTED",
        "actual_source":"MIT Godot GBot"}
(out/"qa.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))

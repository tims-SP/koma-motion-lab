#!/usr/bin/env python3
"""CORE-006 independent source-front and articulated-part image QA.

Detects failures missed by geometry-only checks. Visual quality remains an
independent manual/vision gate; numbers never certify anime-art quality.
"""
from __future__ import annotations
import json
from pathlib import Path
from PIL import Image,ImageChops

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"out"/"core006"
BG=(242,244,248)
MODES=("head_yaw","elbow_bend","camera_turn")
PICKS=(0,12,24,36,47)

def image(path):
    im=Image.open(path).convert("RGB")
    if im.size!=(960,540):raise ValueError(f"Bad image size {path}: {im.size}")
    return im

def crop(im):
    # Do not allow changes in the always-visible HTML info overlay to
    # masquerade as character deformation.
    return im.crop((0,110,960,540))

def frac(a,b,threshold=18):
    diff=ImageChops.difference(a,b).convert("L")
    h=diff.histogram()
    return sum(h[threshold+1:])/(a.width*a.height)

front_source=crop(image(BASE/"source_front.png"))
front_part=crop(image(BASE/"part_front.png"))
exact=frac(front_source,front_part,0)
if exact>0.0005:raise SystemExit(f"FAIL_FRONT_ART_PRESERVATION_CHANGED_PIXELS: {exact:.6f}")

comparison={}
background=Image.new("RGB",front_source.size,BG)
for name in MODES:
    frames=sorted((BASE/name).glob("*.png"))
    if len(frames)!=48:raise SystemExit(f"FAIL_FRAME_COUNT {name}: {len(frames)}")
    shots=[crop(image(frames[i])) for i in PICKS]
    coverage=[frac(f,background,24) for f in shots]
    changed=[frac(shots[i],shots[i+1]) for i in range(len(shots)-1)]
    from_start=frac(shots[0],shots[2])
    if min(coverage)<0.014:
        raise SystemExit(f"FAIL_BLANK_CHARACTER {name}: {coverage}")
    # Deliberately small thresholds because fixed-camera elbow deformation is
    # localized; the video itself must still be inspected for quality.
    if name=="head_yaw" and from_start<0.00075:
        raise SystemExit(f"FAIL_HEAD_SKIN_NOT_DEFORMING {from_start}")
    if name=="elbow_bend" and from_start<0.00035:
        raise SystemExit(f"FAIL_ELBOW_SKIN_NOT_DEFORMING {from_start}")
    if name=="camera_turn" and from_start<0.004:
        raise SystemExit(f"FAIL_CAMERA_NOT_MOVING {from_start}")
    if max(changed)>0.28:
        raise SystemExit(f"FAIL_SUDDEN_LARGE_IMAGE_CHANGE {name}: {changed}")
    comparison[name]={
      "coverage_excluding_overlay":coverage,
      "sampled_adjacent_changed_fraction":changed,
      "start_to_mid_changed_fraction":from_start
    }
# 4 rows: source/original front pair, head, elbow, camera. Full video pngs.
board=Image.new("RGB",(960*3,540*4))
front_views=[BASE/"source_front.png",BASE/"part_front.png",BASE/"part_front.png"]
for col,p in enumerate(front_views):board.paste(image(p),(960*col,0))
for row,name in enumerate(MODES,1):
    for col,i in enumerate((0,24,47)):
        board.paste(image(BASE/name/f"{i:04d}.png"),(960*col,540*row))
board.save(BASE/"contact.png")
preview=board.copy()
preview.thumbnail((1580,1250))
preview.save(BASE/"contact_preview.jpg",quality=83,optimize=True)
report={
 "status":"PASS_ARTMESH_SOURCE_FRONT_AND_ISOLATED_BONE_MOTION_SMOKE",
 "source":"MIT licensed Godot GBot Polygon2D art/UV and Bone2D",
 "source_front_same_engine_art_changed_pixel_fraction":exact,
 "sampled_motion":comparison,
 "source_runtime_original_frame_parity":"NOT_TESTED",
 "source_original_front_projection_quality":"NOT_YET_VISUALLY_ACCEPTED",
 "head_side_and_elbow_side_artwork":"MISSING_TEST_CANARY",
 "head_bone_roll_and_arm_3d_axis":"FUNCTIONAL_ONLY",
 "true_part_surface_correspondence":"NOT_IMPLEMENTED",
 "anime_visual_quality":"NOT_ACCEPTED",
 "rig_animation_runtime_parity":"NOT_TESTED",
 "limits":["Front exactness is same renderer reference, NOT original Godot reference",
           "Side/back uses explicit synthetic diagnostic map",
           "Bone driven pixel change is NOT natural deformation",
           "No head hair segmentation or view-dependent facial redraw yet"]
}
(BASE/"qa.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print("CORE006_QA",json.dumps(report,indent=2))

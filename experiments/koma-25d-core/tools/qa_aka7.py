#!/usr/bin/env python3
"""CORE-007: source-photo integrity, continuity and method distinction smoke QA."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageChops
root=Path(__file__).resolve().parents[1]
out=root/"out"/"core007"/"review"
report=json.loads((out/"render.json").read_text())
source=Image.open(out/"source_front.png").convert("RGBA")
base=Image.new("RGBA",source.size,(241,242,246,255))
base.alpha_composite(source)
canonical=base.convert("RGB")
original=Image.open(out/"original_psd.png")
if original.width<1200 or original.height<1200:
    raise SystemExit("FAIL: source image is unexpectedly small")
def load(path):
    im=Image.open(path).convert("RGB")
    if im.size!=(640,640):raise SystemExit(f"FAIL: bad frame size {path}")
    return im
def fraction(a,b,threshold=15):
    d=ImageChops.difference(a,b).convert("L")
    h=d.histogram()
    return sum(h[threshold+1:])/(a.width*a.height)
summary={}
for mode in ("flat","curved"):
    frames=sorted((out/mode).glob("*.png"))
    if len(frames)!=36:raise SystemExit(f"FAIL: {mode} produced {len(frames)} frames")
    start=load(frames[0]);end=load(frames[-1]);mid=load(frames[18])
    front=fraction(canonical,start,0)
    if front>0:raise SystemExit(f"FAIL: rest angle source-pixel mismatch {mode} {front}")
    if fraction(start,end,0)>0:raise SystemExit(f"FAIL: head turn didn't return to original {mode}")
    diff=fraction(start,mid)
    if diff<0.015:raise SystemExit(f"FAIL: animated character static {mode} {diff}")
    previous=start
    adjacent=[]
    for p in frames[1:]:
        image=load(p)
        adjacent.append(fraction(previous,image))
        previous=image
    if max(adjacent)>0.20:raise SystemExit(f"FAIL: abrupt frame jump {mode}")
    # Check actual palette and subject, not just motion.
    arr=np.asarray(mid).astype(np.int16)
    background=np.array([241,242,246],dtype=np.int16)
    mask=np.max(np.abs(arr-background),axis=2)>25
    if mask.mean()<0.055:raise SystemExit(f"FAIL: blank subject {mode}")
    if arr[mask].mean()<50:raise SystemExit(f"FAIL: missing color {mode}")
    summary[mode]={"front_exact_by_explicit_anchor":front==0,
       "start_end_changed":fraction(start,end,0),
       "midpoint_changed_fraction":diff,
       "max_adjacent_changed_fraction":max(adjacent),
       "mean_adjacent_changed_fraction":sum(adjacent)/len(adjacent),
       "mid_subject_coverage":float(mask.mean())}
different=fraction(load(out/"flat"/"0018.png"),load(out/"curved"/"0018.png"))
if different<0.001:raise SystemExit(f"FAIL: flat and curve experiments identical {different}")
report.update({
 "status":"STRUCTURAL_ART_LAYERS_AND_ANIMATION_SMOKE_PASS",
 "motion_metrics":summary,
 "flat_vs_curve_midpoint_changed_fraction":different,
 "artist_view_quality":"PENDING_MANUAL_VIDEO_INSPECTION",
 "exact_front_statement":"SOURCE_0_DEG_FRAME_COPIED_AS_EXPLICIT_ANCHOR; not runtime fidelity",
 "camera_rotation_degree_max":34,
 "original_INX_RIG_APPLIED_TO_ANIMATION":False,
 "claimed_3d_character":False
})
(out/"qa7.json").write_text(json.dumps(report,indent=2)+"\n")
print("CORE007_ANIME_LAYER_QA",json.dumps(report,indent=2))

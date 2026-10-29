#!/usr/bin/env python3
"""CORE-004 controlled multi-view image interpolation benchmark.

Use actual rendered (CC0) 0/45/90/135/180 angular views as source images,
compare regular crossfade with an established optical-flow warp (Farneback),
and score BOTH against withheld true 3D views. This is a 2D image-space
benchmark. It does not solve 2D-to-surface registration or animate a rig.
"""
from __future__ import annotations
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageChops, ImageEnhance

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"out"/"core004"
REF=OUT/"reference"
BLEND=OUT/"blend"
WARP=OUT/"flow"
for p in [BLEND,WARP]: p.mkdir(parents=True,exist_ok=True)
ANCHORS=(0,18,36,54,72)
BG=np.array([239,241,245],dtype=np.uint8)

def rgb(arr):return cv2.cvtColor(arr,cv2.COLOR_BGR2RGB)
def read(i):
    frame=cv2.imread(str(REF/f"{i:04d}.png"),cv2.IMREAD_COLOR)
    if frame is None or frame.shape!=(640,640,3):raise ValueError(f"Bad input frame {i}")
    return frame
def dump(dest,i,frame):
    if not cv2.imwrite(str(dest/f"{i:04d}.png"),frame):
        raise IOError(f"Could not write {dest} {i}")
def mae(reference,est):
    # Evaluate on source subject union (rather than bg-dominated mean).
    a=rgb(reference).astype(np.int16)
    b=rgb(est).astype(np.int16)
    mask=(np.max(np.abs(a-BG.astype(np.int16)),axis=2)>24)|(
      np.max(np.abs(b-BG.astype(np.int16)),axis=2)>24)
    if mask.sum()<5000:raise ValueError("Model too small/blank for meaningful evaluation")
    return float(np.abs(a-b)[mask].mean()),float(mask.mean())

def build():
    originals=[read(i) for i in range(73)]
    source_sheet=Image.new("RGB",(640*5,640))
    for k,idx in enumerate(ANCHORS):
        source_sheet.paste(Image.open(REF/f"{idx:04d}.png").convert("RGB"),(640*k,0))
    source_sheet.save(OUT/"source_views.png")

    optical={}
    for a,b in zip(ANCHORS[:-1],ANCHORS[1:]):
        gray_a=cv2.cvtColor(originals[a],cv2.COLOR_BGR2GRAY)
        gray_b=cv2.cvtColor(originals[b],cv2.COLOR_BGR2GRAY)
        flow_ab=cv2.calcOpticalFlowFarneback(gray_a,gray_b,None,0.5,4,23,4,7,1.4,0)
        flow_ba=cv2.calcOpticalFlowFarneback(gray_b,gray_a,None,0.5,4,23,4,7,1.4,0)
        optical[a]=(flow_ab,flow_ba)
    h,w=640,640
    xx,yy=np.meshgrid(np.arange(w,dtype=np.float32),np.arange(h,dtype=np.float32))
    trace=[]
    for i,ref in enumerate(originals):
        a=max(t for t in ANCHORS if t<=i)
        b=min(t for t in ANCHORS if t>=i)
        if a==b:
            simple=ref.copy();deform=ref.copy()
        else:
            alpha=(i-a)/(b-a)
            simple=cv2.addWeighted(originals[a],1-alpha,originals[b],alpha,0)
            ab,ba=optical[a]
            map_ax=xx+alpha*ab[...,0]
            map_ay=yy+alpha*ab[...,1]
            map_bx=xx+(1-alpha)*ba[...,0]
            map_by=yy+(1-alpha)*ba[...,1]
            p=cv2.remap(originals[a],map_ax,map_ay,cv2.INTER_LINEAR,
                        borderMode=cv2.BORDER_CONSTANT,borderValue=(245,241,239))
            q=cv2.remap(originals[b],map_bx,map_by,cv2.INTER_LINEAR,
                        borderMode=cv2.BORDER_CONSTANT,borderValue=(245,241,239))
            deform=cv2.addWeighted(p,1-alpha,q,alpha,0)
        dump(BLEND,i,simple)
        dump(WARP,i,deform)
        baseline,cover_a=mae(ref,simple)
        estimate,cover_b=mae(ref,deform)
        trace.append({"frame":i,"yaw_deg":i*2.5,"source_coverage":cover_a,
                      "blend_subject_rgb_mae":baseline,
                      "flow_subject_rgb_mae":estimate})
    withheld=[v for v in trace if v["frame"] not in ANCHORS]
    result={
      "status":"REFERENCE_BENCHMARK_COMPUTED_NOT_2D_RIG_ART_ACCEPTED",
      "source":"CC0 VRoid Studio beta Sendagaya_Shino",
      "license":"CC0 (not the restrictive stable AvatarSample_A/B/C)",
      "baseline":"screen_space_crossfade_5_orbit_views",
      "alternative":"OpenCV_Farneback_flow_5_views",
      "reference":"original textured full 3D VRM render at every angle",
      "angles_deg":[0,45,90,135,180],
      "withheld_views":len(withheld),
      "mean_subject_mae_blend":float(np.mean([p["blend_subject_rgb_mae"] for p in withheld])),
      "mean_subject_mae_flow":float(np.mean([p["flow_subject_rgb_mae"] for p in withheld])),
      "max_subject_mae_blend":float(max(p["blend_subject_rgb_mae"] for p in withheld)),
      "max_subject_mae_flow":float(max(p["flow_subject_rgb_mae"] for p in withheld)),
      "baseline_source_view_exact_by_construction":True,
      "anime_look":"VISUAL_INSPECTION_REQUIRED",
      "source_2d_layered_mesh":"NOT_CREATED",
      "skin_uv_registration":"NOT_CREATED",
      "production_quality":"NOT_ACCEPTED",
      "per_frame":trace}
    (OUT/"qa.json").write_text(json.dumps(result,indent=2)+"\n")
    selection=[0,9,18,27,36,45,54,63,72]
    montage=Image.new("RGB",(640*len(selection),640*3))
    for col,i in enumerate(selection):
        for row,folder in enumerate((REF,BLEND,WARP)):
            montage.paste(Image.open(folder/f"{i:04d}.png").convert("RGB"),(col*640,row*640))
    montage.save(OUT/"contact.png")
    reduced=montage.copy()
    reduced.thumbnail((2250,760))
    reduced.save(OUT/"contact_preview.jpg",quality=82)
    print("CORE004_REFERENCE_QA",json.dumps({k:v for k,v in result.items() if k!="per_frame"},indent=2))
    return result

if __name__=="__main__":
    build()

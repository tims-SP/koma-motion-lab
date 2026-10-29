#!/usr/bin/env python3
"""CORE-005: held-out multiview reference comparison with real 2D silhouette geometry.

Metrics deliberately separate silhouette IoU from whole-body appearance.
A good IoU does not imply the Japanese-anime artwork is acceptable.
"""
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"out"/"core005"
REFERENCE=ROOT/"out"/"core004"/"reference"
BLEND=ROOT/"out"/"core004"/"blend"
BG=np.array((239,241,245),dtype=np.int16)
MODES=("visual_hull","fixed_extrusion","blend")

def load(path):
    a=cv2.imread(str(path),cv2.IMREAD_COLOR)
    if a is None or a.shape!=(640,640,3):
        raise ValueError("Image missing/corrupt "+str(path))
    return cv2.cvtColor(a,cv2.COLOR_BGR2RGB)

def mask(rgb):
    return np.max(np.abs(rgb.astype(np.int16)-BG),axis=2)>26

def compare(a,b):
    x=mask(a);y=mask(b)
    intersection=int(np.logical_and(x,y).sum())
    union=int(np.logical_or(x,y).sum())
    if union<4500:raise ValueError("No real subject in scored image")
    region=np.logical_or(x,y)
    return {
        "silhouette_iou":intersection/union,
        "subject_rgb_mae":float(np.abs(a.astype(np.int16)-b.astype(np.int16))[region].mean()),
        "subject_coverage":float(y.mean()),
        "reference_coverage":float(x.mean())
    }

scored={}
for name in MODES:
    frames=[]
    for i in range(73):
        ref=load(REFERENCE/f"{i:04d}.png")
        candidate=load((BASE/name if name!="blend" else BLEND)/f"{i:04d}.png")
        metrics=compare(ref,candidate)
        metrics["frame"]=i;metrics["yaw_deg"]=i*2.5
        frames.append(metrics)
    scored[name]=frames
angles=(0,9,18,27,36,45,54,63,72)
keyframes=(0,18,36,54,72)
summary={}
for name,frames in scored.items():
    withheld=[p for p in frames if p["frame"] not in keyframes]
    summary[name]={
      "withheld_mean_iou":float(np.mean([p["silhouette_iou"] for p in withheld])),
      "withheld_mean_subject_mae":float(np.mean([p["subject_rgb_mae"] for p in withheld])),
      "by_angle":{str(i*2.5):frames[i] for i in angles}
    }
side_ref=summary["visual_hull"]["by_angle"]["90.0"]
side_naive=summary["fixed_extrusion"]["by_angle"]["90.0"]
front=summary["visual_hull"]["by_angle"]["0.0"]
reported={
 "experiment":"KOMA_CORE005",
 "status":"GEOMETRY_AND_IMAGE_METRICS_COMPUTED_ART_NOT_ACCEPTED",
 "source":"5 CC0 anime 2D rendered views from original true 3D reference",
 "geometry_inputs":"ONLY_FRONT_AND_SIDE_2D_SILHOUETTES",
 "appearance_inputs":"FRONT_SIDE_BACK_2D_PNG",
 "ground_truth":"INDEPENDENT_ORIGINAL_3D_RENDER",
 "comparison":"single-character fixed depth vs 2-silhouette visual hull vs 2D crossfade",
 "angles":list(float(i*2.5) for i in angles),
 "methods":summary,
 "profile_iou_gain_over_naive_at_90":side_ref["silhouette_iou"]-side_naive["silhouette_iou"],
 "front_iou":front["silhouette_iou"],
 "profile_gate":"PASS" if side_ref["silhouette_iou"]>side_naive["silhouette_iou"]+0.05 else "FAIL",
 "reference_front_pixel_parity":"NOT_VERIFIED",
 "source_art_and_mesh_are_live2d":"NO",
 "two_dimensional_bone_3d_skinning":"NOT_IMPLEMENTED",
 "anime_style_final_acceptance":"NOT_ACCEPTED_PENDING_DIRECT_VIDEO_INSPECTION",
 "technical_limitations":["Voxel visual hull cannot recover concave surfaces",
                         "No part-specific regions; limbs/hair may share spurious volume",
                         "Static T-pose only, no skin weights or animation",
                         "World-projected textures can introduce seams/ghosting",
                         "Source 2D key views were rendered from a 3D reference"]
}
BASE.mkdir(exist_ok=True,parents=True)
(BASE/"qa.json").write_text(json.dumps(reported,indent=2)+"\n")
sheet=Image.new("RGB",(640*len(angles),640*4))
for row,name in enumerate(("reference","blend","fixed_extrusion","visual_hull")):
    folder=REFERENCE if name=="reference" else BLEND if name=="blend" else BASE/name
    for col,i in enumerate(angles):
        im=Image.open(folder/f"{i:04d}.png").convert("RGB")
        sheet.paste(im,(640*col,640*row))
sheet.save(BASE/"contact.png")
preview=sheet.copy()
preview.thumbnail((2380,1120))
preview.save(BASE/"contact_preview.jpg",quality=84,optimize=True)
print("CORE005_QA_SUMMARY",json.dumps({k:v for k,v in reported.items() if k!="methods"},indent=2))
for mode,info in summary.items():
    print("CORE005_SCORE",mode,info["withheld_mean_iou"],info["withheld_mean_subject_mae"])
    print("CORE005_90",mode,info["by_angle"]["90.0"])

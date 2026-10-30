#!/usr/bin/env python3
"""CORE018: Native-vs-custom EAR TIP silhouette alignment; NEVER full model parity.

Reference PNGs: pinned real Inox2D OpenGL full model HeadYaw neutral (.5) and
max (1.0), pitch .5, 720x880; custom PNGs: independent original ear-only mesh
source TGA/UV and native HeadYaw transform results, transparent RGBA, same size.
The script fits ONE global screen offset at neutral only. No separate max fit.
"""
from pathlib import Path
import argparse,json
import numpy as np
import cv2
from PIL import Image
ROIS={"image_left_ear":(250,30,365,110),"image_right_ear":(365,30,455,110)}
def read(folder,tag,reference):
    name=(f"native_{tag}.png" if reference else f"custom_INX_ears_{tag}_transparent.png")
    im=np.asarray(Image.open(folder/name).convert("RGB" if reference else "RGBA"))
    assert im.shape[:2]==(880,720)
    return im
def move(a,x,y):
    return cv2.warpAffine(a,np.float32([[1,0,x],[0,1,y]]),(720,880),
        flags=cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
def measure(ref,custom,dx,dy):
    a=move(custom,dx,dy)
    out={}
    native_fg=np.max(ref,axis=2)>50
    ear_fg=a[:,:,3]>50
    for key,(x0,y0,x1,y1) in ROIS.items():
        m=ear_fg[y0:y1,x0:x1];n=native_fg[y0:y1,x0:x1]
        overlap=m&n;union=m|n
        v=ref[y0:y1,x0:x1].astype(np.int16)
        c=a[y0:y1,x0:x1,:3].astype(np.int16)
        out[key]={"silhouette_iou":round(float(overlap.sum()/max(1,union.sum())),4),
                  "native_foreground_pixels":int(n.sum()),"custom_foreground_pixels":int(m.sum()),
                  "overlap_pixels":int(overlap.sum()),"native_color_vs_custom_in_overlap_mae":
                  round(float(np.mean(np.abs(v[overlap]-c[overlap]))),2) if overlap.any() else None}
    return out
def main(ref_dir,custom_dir,out):
    out.mkdir(parents=True,exist_ok=True)
    r={t:read(ref_dir,t,True) for t in ("neutral","maximum")}
    c={t:read(custom_dir,t,False) for t in ("neutral","maximum")}
    choices=[]
    for x in range(-16,17):
        for y in range(-12,13):
            m=measure(r["neutral"],c["neutral"],x,y)
            avg=sum(v["silhouette_iou"] for v in m.values())/len(m)
            choices.append((avg,x,y))
    _,dx,dy=max(choices)
    d={"schema":"core018-actual-pinned-inox-reference/1",
       "fitted_neutral_translation_px":{"x":dx,"y":dy},
       "rois":ROIS,"native_head_yaw_x":[.5,1.0],"native_pitch_y":.5,
       "original_INX_source_mesh_uv":True,"fit_applied_to_max_without_refitting":True,
       "full_character_pixel_parity":"NOT_PROVEN_EAR_ONLY_VS_FULL_NATIVE_MODEL",
       "side_back_painting":"NOT_AVAILABLE","results":{}}
    for tag in ("neutral","maximum"):
        d["results"][tag]={"raw":measure(r[tag],c[tag],0,0),
                            "fixed_neutral_offset":measure(r[tag],c[tag],dx,dy)}
    (out/"source_ear_tip_alignment.json").write_text(json.dumps(d,indent=2)+"\n")
    print("CORE018_NEUTRAL_ONLY_ALIGNMENT",json.dumps(d)[:3600])
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--native-reference",type=Path,required=True)
    parser.add_argument("--independent-ear-renders",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    a=parser.parse_args()
    main(a.native_reference,a.independent_ear_renders,a.output)

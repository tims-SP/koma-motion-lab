#!/usr/bin/env python3
"""Score independent real native fixed-parameter screenshots (no fake angle labels)."""
import argparse,json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import numpy as np
ap=argparse.ArgumentParser()
ap.add_argument("--input",type=Path,required=True)
a=ap.parse_args();out=a.input
values=[0,25,50,75,100]
imgs=[]
for value in values:
    p=out/f"native_param_{value:03d}.png"
    if not p.exists():raise RuntimeError(f"Missing native screenshot {p}")
    im=Image.open(p).convert("RGB")
    if im.size!=(1024,900):raise RuntimeError(f"Wrong actual X11 frame size {p}: {im.size}")
    imgs.append(im)
# Crop only the known native app head. Data derived from the successful
# independently decoded dynamic Inox2D video, not arbitrary synthetic art.
box=(205,18,490,303)
heads=[im.crop(box) for im in imgs]
arr=[np.array(im).astype(np.int16) for im in heads]
contrast=[float(a.std()) for a in arr]
foreground=[float(np.max(a,axis=2).mean()) for a in arr]
base=arr[0]
scores=[]
for i,(v,image) in enumerate(zip(values,arr)):
    changed=float(np.mean(np.max(np.abs(image-base),axis=2)>22))
    l1=float(np.mean(np.abs(image-base)))
    scores.append({"native_normalized_yaw":v/100,"changed_area_vs_zero":changed,"mean_abs_rgb_vs_zero":l1})
if min(contrast)<30:raise RuntimeError("A native screenshot is blank")
if min(foreground)<20:raise RuntimeError("Head subject is absent from screenshot")
if scores[-1]["changed_area_vs_zero"]<0.03:
    raise RuntimeError(f"Full native parameter did not actually deform art: {scores}")
if len(set(hashlib.sha256(im.tobytes()).hexdigest() for im in heads))!=5:
    raise RuntimeError("One or more native parameter screenshots repeat exactly")
# Contact sheet: 5 native parameter snapshots and proof they are actual
# different native render outputs. Titles refer to *parameter*, not degrees.
w=330;h=354
board=Image.new("RGB",(5*w,h),(240,241,245))
draw=ImageDraw.Draw(board)
for i,(im,s) in enumerate(zip(heads,scores)):
    enlarged=im.resize((324,324),Image.Resampling.LANCZOS)
    board.paste(enlarged,(w*i+3,27))
    draw.text((i*w+9,6),
              f"INX HeadYaw={s['native_normalized_yaw']:.2f}  (NOT degrees)",
              fill=(25,30,40))
board.save(out/"fixed_parameter_contact.png")
board.save(out/"fixed_parameter_contact.jpg",quality=88,optimize=True)
report={
 "status":"REAL_INX_FIXED_PARAMETER_SCREENSHOTS_PASS_SMOKE_NOT_ART",
 "source":"Full seagetch Aka.inx, verified LFS SHA256",
 "renderer":"Pinned Inox2D Rust OpenGL, Mesa Xvfb, unmodified source mesh",
 "independent_renderer_processes":5,
 "head_image_crop":[205,18,490-205,303-18],
 "parameter_grid":scores,"min_contrast":min(contrast),
 "maximum_native_parameter_is_not_physical_yaw_degrees":True,
 "observed_novel_45deg_side_art":"NOT_PROVEN",
 "original_INOCHI_D_SDK_parity":"NOT_TESTED",
 "image_quality":"PENDING_DIRECT_VISUAL_AUDIT"
}
(out/"fixed_parameter_qa.json").write_text(json.dumps(report,indent=2)+"\n")
print("CORE008_FIXED_PARAMETER_QA",json.dumps(report))

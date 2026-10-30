#!/usr/bin/env python3
"""Crop ONLY actual MP4 from native Inox2D Xvfb recording for face inspection.

No synthetic/crossfaded frames. Refuses a bad or empty head crop.
"""
import argparse,subprocess,json,math,io
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageChops

ap=argparse.ArgumentParser()
ap.add_argument("--movie",type=Path,required=True)
ap.add_argument("--out",type=Path,required=True)
a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
source=a.movie
probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries",
    "stream=width,height,r_frame_rate","-of","json",str(source)],text=True))
w,h=(int(probe["streams"][0][k]) for k in ("width","height"))
if w!=1024 or h!=900:raise RuntimeError("Source not known native video")
frame_bytes=subprocess.check_output(["ffmpeg","-hide_banner","-loglevel","error",
  "-i",str(source),"-frames:v","1","-f","image2pipe","-vcodec","png","-"])
frame=np.asarray(Image.open(io.BytesIO(frame_bytes)).convert("RGB"))
# Detect colorful original puppet against the known black X11 native window.
# Confine to the upper 35% to avoid body/tail pulling the crop away from head.
top=frame[:int(.37*h)]
hsv=np.max(top,axis=2).astype(np.int16)
foreground=(hsv>48)&((top.max(axis=2)-top.min(axis=2))>22)
ys,xs=np.where(foreground)
if len(xs)<400:raise RuntimeError("Native character head not found in real video")
center_x=int(np.median(xs))
top_y=int(np.percentile(ys,4))
side=370
left=max(0,min(w-side,center_x-side//2))
upper=max(0,min(h-side,top_y-12))
crop=(left,upper,side,side)
outmp4=a.out/"native_head_closeup.mp4"
subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
 "-i",str(source),"-vf",f"crop={side}:{side}:{left}:{upper},scale=640:640:flags=lanczos",
 "-an","-c:v","libx264","-crf","16","-pix_fmt","yuv420p",str(outmp4)],check=True)
frames_dir=a.out/"decoded";frames_dir.mkdir(exist_ok=True)
subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
 "-i",str(outmp4),"-vf","fps=4",str(frames_dir/"head_%03d.png")],check=True)
paths=sorted(frames_dir.glob("head_*.png"))
if len(paths)<12:raise RuntimeError("Cannot sample native cropped MP4")
imgs=[Image.open(p).convert("RGB") for p in paths]
sel=sorted(set([0,len(imgs)//6,len(imgs)//3,len(imgs)//2,2*len(imgs)//3,5*len(imgs)//6,len(imgs)-1]))
contact=Image.new("RGB",(360*len(sel),360),(0,0,0))
draw=ImageDraw.Draw(contact)
for i,n in enumerate(sel):
 im=imgs[n].resize((360,360),Image.Resampling.LANCZOS)
 contact.paste(im,(i*360,0))
 draw.text((i*360+8,8),f"decoded head frame {n}",fill="white",stroke_width=2,stroke_fill="black")
contact.save(a.out/"native_head_contact.png")
preview=contact.copy();preview.thumbnail((1850,430))
preview.save(a.out/"native_head_contact_preview.jpg",quality=82,optimize=True)
a0=np.asarray(imgs[0]).astype(np.int16)
deltas=[float((np.max(np.abs(np.asarray(i).astype(np.int16)-a0),axis=2)>20).mean()) for i in imgs]
if max(deltas)<0.008:raise RuntimeError("Head crop shows no measurable changes; cannot claim visible head pose")
report={
 "status":"NATIVE_INX_HEAD_VIDEO_CROPPED_AND_DECODED",
 "source":"Actual MP4 from pinned Inox2D OpenGL renderer, no generated art",
 "input_movie":"native_head_yaw.mp4",
 "head_crop_xywh":crop,
 "output":"native_head_closeup.mp4",
 "input_size":[w,h],"crop_output_size":[640,640],
 "decoded_samples":len(imgs),"contact_indices":sel,
 "max_changed_fraction_from_first":max(deltas),
 "frame_changes_from_first":deltas,
 "native_deformation":"Head:: Yaw-Pitch normalized parameter",
 "physical_yaw_degrees":"UNKNOWN_UNCALIBRATED",
 "visual_quality":"REQUIRES_DIRECT_INSPECTION"
}
(a.out/"head_closeup_qa.json").write_text(json.dumps(report,indent=2)+"\n")
print("CORE008_NATIVE_HEAD_CLOSEUP_QA",json.dumps({k:v for k,v in report.items() if k!="frame_changes_from_first"}))

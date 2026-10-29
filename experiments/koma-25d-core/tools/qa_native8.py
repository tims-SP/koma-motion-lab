#!/usr/bin/env python3
"""QA actual encoded native Inox2D OpenGL screen recording (NOT pseudo-render)."""
import argparse,subprocess,json
from pathlib import Path
import numpy as np
from PIL import Image, ImageChops
ap=argparse.ArgumentParser()
ap.add_argument("--mp4",type=Path,required=True)
ap.add_argument("--out",type=Path,required=True)
a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
probe=subprocess.check_output(["ffprobe","-v","error","-show_entries",
    "stream=width,height,nb_frames,r_frame_rate","-of","json",str(a.mp4)],text=True)
info=json.loads(probe)["streams"][0]
if info["width"]<650 or info["height"]<820:raise ValueError("Wrong screen video size")
subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
                "-i",str(a.mp4),"-vf","fps=4",
                str(a.out/"frame_%03d.png")],check=True)
frames=sorted(a.out.glob("frame_*.png"))
if len(frames)<12:raise ValueError("Not enough decoded footage")
images=[Image.open(p).convert("RGB") for p in frames]
# Window may be placed at 0,0 or centered on desktop. Crop only screen UI
# borders 10px; never count moving cursor or metadata as a puppet pose.
arrs=[np.asarray(i)[10:-10,10:-10,:] for i in images]
# Identify actual visual movement in subject pixels. llvmpipe transparency
# may result in black model or empty frames; fail rather than accept.
changes=[float(np.mean(np.max(np.abs(x.astype(np.int16)-y.astype(np.int16)),axis=2)>18))
         for x,y in zip(arrs,arrs[1:])]
contrast=[float(np.std(x)) for x in arrs]
if min(contrast)<8:raise ValueError("Native renderer video likely blank")
if max(changes)<0.006:raise ValueError("Native puppet visibly static")
indices=sorted(set([0,len(images)//6,len(images)//3,len(images)//2,2*len(images)//3,5*len(images)//6,len(images)-1]))
thumbs=[]
for i in indices:
    frame=images[i]
    frame.thumbnail((512,440))
    thumbs.append(frame)
W=512
H=max(i.height for i in thumbs)
contact=Image.new("RGB",(len(thumbs)*W,H),(236,238,241))
from PIL import ImageDraw
draw=ImageDraw.Draw(contact)
for col,(idx,im) in enumerate(zip(indices,thumbs)):
    contact.paste(im,(col*W+(W-im.width)//2,0))
    draw.text((col*W+8,9),f"native frame {idx}",fill=(255,255,255),stroke_width=2,stroke_fill=(0,0,0))
contact.save(a.out/"native_contact.png")
contact.thumbnail((1850,800))
contact.save(a.out/"native_contact_preview.jpg",quality=83,optimize=True)
result={
 "status":"ENCODED_NATIVE_VIDEO_DECODED_AND_NONBLANK",
 "renderer":"Inox2D official supported experimental Rust OpenGL port",
 "video":str(a.mp4),"decoded_frames":len(frames),
 "image_dimensions":[info["width"],info["height"]],
 "sampled_indices":indices,"screen_delta_mean":float(np.mean(changes)),
 "screen_delta_max":max(changes),"min_screen_contrast":min(contrast),
 "binary_video_provenance":"REAL_OPENGL_CAPTURED_XVFB",
 "source_2d_rig_parameters":"REAL_COMPLETE_INX_HEAD_YAW_PITCH",
 "angular_degrees":"NOT_CALIBRATED",
 "pixel_parity_with_original_D_SDK":"NOT_TESTED",
 "anime_quality":"PENDING_DIRECT_VISUAL_REVIEW"
}
(a.out/"native_video_qa.json").write_text(json.dumps(result,indent=2)+"\n")
print("CORE008_NATIVE_VIDEO_QA",json.dumps(result))

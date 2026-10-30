#!/usr/bin/env python3
"""CORE021: fail-closed true source Aka HeadYaw default [0,0] native OpenGL QC.

13 real native OpenGL captures at raw Yaw [-1,-.5,0,.25,.5,.75,1,...-1],
with native raw Pitch exactly 0 (source default), not normalized 0.
No external imagegen and NO 3D turn is claimed.
"""
import hashlib,json,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path("experiments/koma-25d-core/out/core021")
ORDER=[-1.,-.5,0.,.25,.5,.75,1.,.75,.5,.25,0.,-.5,-1.]
assert len(ORDER)==13
poses=[]
for i,x in enumerate(ORDER):
    p=ROOT/f"native_{i:03d}.png"
    assert p.exists(),f"Missing ACTUAL GPU frame {p}"
    im=Image.open(p).convert("RGB")
    assert im.size==(720,880)
    arr=np.asarray(im,dtype=np.uint8)
    warm=((arr[:,:,0].astype(np.int16)-arr[:,:,2].astype(np.int16)>20)&(arr[:,:,0]>115))
    fg=arr.max(axis=2)>48
    assert 700<int(warm.sum())<95000,(i,x,"real ear ink absent?")
    assert 1000<int(fg.sum())<100000,(i,x,"missing ears or full puppet leaked")
    poses.append({"index":i,"raw_yaw":x,"raw_pitch":0.,
                 "actual_png_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
                 "foreground":int(fg.sum())})
for a,b in [(0,12),(1,11),(2,10),(3,9),(4,8),(5,7)]:
    assert poses[a]["actual_png_sha256"]==poses[b]["actual_png_sha256"],(a,b)
assert len({p["actual_png_sha256"] for p in poses[:7]})>=6
assert poses[2]["actual_png_sha256"]!=poses[4]["actual_png_sha256"],"TRUE default differs from raw (0.5,0)!"
video=ROOT/"actual_native_default_13frame_GL_H264.mp4"
probe=subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
 "-show_entries","stream=nb_frames,r_frame_rate,width,height","-of","json",str(video)],
 check=True,capture_output=True,text=True)
v=json.loads(probe.stdout)["streams"][0]
assert (v["width"],v["height"],v["r_frame_rate"])==(720,880,"24/1")
assert int(v["nb_frames"])==78,v
sample_indexes=[0,12,24,36,48,60,72,77]
for i in sample_indexes:
    out=ROOT/f"decoded_native_{i:03d}.png"
    subprocess.run(["ffmpeg","-v","error","-y","-i",str(video),
      "-vf",f"select=eq(n\\,{i})","-vsync","0","-frames:v","1",str(out)],check=True)
    assert Image.open(out).size==(720,880)
contact=Image.new("RGB",(4*360,2*455),(230,234,238))
d=ImageDraw.Draw(contact)
for j,i in enumerate(sample_indexes):
    im=Image.open(ROOT/f"decoded_native_{i:03d}.png").convert("RGB")
    im.thumbnail((345,420))
    xx=(j%4)*360+7;yy=(j//4)*455+27
    contact.paste(im,(xx,yy))
    d.text((xx,yy-20),f"GL video n={i}",fill=(24,32,44))
contact.save(ROOT/"decoded_true_default_contact.jpg",quality=88)
qa={"schema":"core021-authentic-default-Aka-ear-GL/1",
 "source_sha256":"dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f",
 "original_external_parameter_min":[-1,-1],"max":[1,1],"defaults":[0,0],
 "native_input_yaw_pitch_pairs":[[p,0] for p in ORDER],
 "actual_native_OpenGL_poses":13,"actual_native_unique_forward":len({p["actual_png_sha256"] for p in poses[:7]}),
 "true_default_included":True,"raw_pitch_is_zero":True,
 "full_original_rig_parameter_eval":True,
 "rendered_draw_only_original_ear_artmesh":True,
 "original_uv_and_source_art_replaced":False,
 "actual_H264":{"frames":int(v["nb_frames"]),"fps":24,
   "sha256":hashlib.sha256(video.read_bytes()).hexdigest(),
   "decoded_frame_indexes":sample_indexes},
 "production_3d_head_360":"NOT_DONE",
 "original_two_ear_pixel_parity_to_independent_renderer":"NOT_EVALUATED_IN_THIS_GPU_JOB",
 "capture":poses}
(ROOT/"native_default_gpu_qa.json").write_text(json.dumps(qa,indent=2)+"\n")
print("CORE021_NATIVE_DEFAULT_SOURCE_AND_FINAL_H264_DECODE_PASS",json.dumps({k:v for k,v in qa.items() if k!="capture"}))

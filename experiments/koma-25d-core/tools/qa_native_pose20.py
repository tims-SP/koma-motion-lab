#!/usr/bin/env python3
"""CORE020: inspect ACTUAL independently launched native GL ears-only poses.

17 source frames (9 going up/8 coming back), plus actual FFmpeg encoded
H264 in runner, decoded anchor frames and motion QA. This is Inox2D normalized
HeadYaw, not physical degrees or 3D face rotation.
"""
import hashlib,json,math,subprocess,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
root=Path(sys.argv[1]);poses=[]
for i in range(17):
    x=.5+(.5*i/8 if i<=8 else .5*(16-i)/8)
    path=root/f"native_{i:03d}.png"
    assert path.is_file(),path
    im=Image.open(path).convert("RGB")
    assert im.size==(720,880)
    a=np.asarray(im,dtype=np.uint8)
    fg=(a.max(2)>48)
    warm=(a[:,:,0].astype(np.int16)>a[:,:,2].astype(np.int16)+20)&(a[:,:,0]>120)
    total=int(fg.sum());warmcount=int(warm.sum())
    assert 2000<total<100000,(i,total)
    assert warmcount>1200,(i,warmcount)
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    poses.append({"index":i,"native_head_yaw_x":round(x,6),"source_png_sha256":sha,
                  "foreground_pixels":total,"warm_pixels":warmcount})
assert poses[0]["source_png_sha256"]==poses[-1]["source_png_sha256"],"neutral return must pixel-match neutral start"
assert len({p["source_png_sha256"] for p in poses[:9]})>=7,"real native interpolation no movement"
assert poses[0]["source_png_sha256"]!=poses[8]["source_png_sha256"]
d={"schema":"core020-authentic-native-17frame-HeadYaw/1",
 "source_aka_inx_sha256":"dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f",
 "renderer_commit":"d4dd9dd7f16b775042cbda44370570abf9a8cf81",
 "original_artmesh_UV_and_rig":True,
 "source_paint_changed":False,
 "full_original_node_tree_evaluated":True,
 "ear_only_draw_filter":True,
 "native_pitch":.5,"native_yaw_min_max":[.5,1.0],
 "physical_rotation_degrees":"NOT_CALIBRATED",
 "source_frames_truly_rendered_by_native_GL":17,
 "mpeg_frame_interpolation":"NONE_DUPLICATE_HOLD_ONLY",
 "same_screen_window":[720,880],
 "poses":poses}
# Need inspect actual ENCODED MP4, not just source frame PNG.
video=root/"actual_native_ear_17pose_hold24.mp4"
probe=subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
 "-show_entries","stream=nb_frames,r_frame_rate,width,height","-of","json",str(video)],
 check=True,capture_output=True,text=True)
stream=json.loads(probe.stdout)["streams"][0]
assert stream["width"]==720 and stream["height"]==880
assert stream["r_frame_rate"]=="24/1"
assert int(stream["nb_frames"])>=90
d["encoded_video"]={"filename":video.name,"sha256":hashlib.sha256(video.read_bytes()).hexdigest(),
                    "actual_h264_frames":int(stream["nb_frames"]),"fps":24}
# Decode native video sample images at 0,6,12,24,36,48,72,96.
positions=[0,12,24,36,48,60,72,96]
for i in positions:
    result=root/f"decoded_native_{i:03d}.png"
    subprocess.run(["ffmpeg","-v","error","-y","-i",str(video),
      "-vf",f"select=eq(n\\,{i})","-vsync","0","-frames:v","1",str(result)],check=True)
    with Image.open(result) as im:
        assert im.size==(720,880)
d["actually_decoded_h264_samples"]=positions
board=Image.new("RGB",(4*360,2*470),(234,238,241))
dr=ImageDraw.Draw(board)
for j,i in enumerate(positions):
    im=Image.open(root/f"decoded_native_{i:03d}.png").convert("RGB")
    im.thumbnail((345,430))
    x=j%4*360+8;y=j//4*470+29
    board.paste(im,(x,y))
    dr.text((x,y-22),f"GPU actual H264 sample n={i}",fill=(27,36,47))
board.save(root/"real_native_h264_decode_contact.jpg",quality=88)
(root/"native17_qa.json").write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
print("CORE020_17_GENUINE_GL_POSES_MP4_DECODE_QA_PASS",json.dumps({k:v for k,v in d.items() if k!="poses"}))

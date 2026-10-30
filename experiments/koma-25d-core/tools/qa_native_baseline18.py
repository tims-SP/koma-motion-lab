#!/usr/bin/env python3
"""CORE018 real Inox2D OpenGL screenshot checks; NOT a source parity assertion."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(folder):
    d={}
    colors=[]
    for tag in ("neutral","maximum"):
        p=folder/f"native_{tag}.x11.png"
        assert p.is_file(),f"Missing actual native screenshot {p}"
        im=Image.open(p).convert("RGB")
        assert im.size==(1024,900)
        crop=im.crop((0,0,720,880))
        arr=np.array(crop)
        contrast=float(arr.std())
        warm=(arr[:,:,0]>arr[:,:,1]+25)&(arr[:,:,1]>arr[:,:,2]+25)&(arr[:,:,0]>120)
        gold=int(warm.sum())
        assert contrast>25 and gold>400, f"Native source invisible tag={tag}, contrast={contrast:.2f}, orange pixels={gold}"
        out=folder/f"native_{tag}.png"
        crop.save(out)
        d[tag]={"source_X11_sha256":sha(p),"cropped_png_sha256":sha(out),
                "size":list(crop.size),"rgb_stddev":round(contrast,2),
                "warm_pixels":gold}
        colors.append(arr)
    differ=float(np.mean(np.max(np.abs(colors[0].astype(np.int16)-colors[1].astype(np.int16)),axis=2)>16))
    assert differ>0.003,f"No motion in native pose: {differ:.6f}"
    board=Image.new("RGB",(980,620),(233,236,240))
    dr=ImageDraw.Draw(board)
    for i,tag in enumerate(("neutral","maximum")):
        frame=Image.open(folder/f"native_{tag}.png").convert("RGB")
        frame.thumbnail((480,570))
        board.paste(frame,(i*490+(490-frame.width)//2,34))
        dr.text((i*490+14,9),f"actual Inox2D native HeadYaw {'0.50 neutral' if i==0 else '1.00 max'}",fill=(32,42,57))
    board.save(folder/"native_opengl_pose_contact.jpg",quality=88,optimize=True)
    q={"status":"REAL_PINNED_INOX2D_OPENGL_REFERENCE_FRAMES_CAPTURED",
       "source":"original Aka.inx SHA256 dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f",
       "native_renderer_pinned_commit":"d4dd9dd7f16b775042cbda44370570abf9a8cf81",
       "renderer":"upstream Inox2D OpenGL sample with deterministic parameter test patch",
       "x11_software_gl":True,"raw_reference_png_not_encoded_MP4":True,
       "model_native_head_yaw":[0.5,1.0],"pitch_normalized":0.0,
       "native_head_yaw_3d_degrees":"NOT_KNOWN",
       "side_rear_new_skin":"NOT_AVAILABLE",
       "ear_only_zero_pose_custom_pixel_parity":"NOT_YET_TESTED",
       "screen_change_fraction":differ,"frames":d}
    (folder/"native_reference_qa.json").write_text(json.dumps(q,indent=2)+"\n")
    print("CORE018_REAL_NATIVE_REFERENCE_QA",json.dumps(q)[:3200])
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--input",type=Path,required=True)
    a=p.parse_args();main(a.input)

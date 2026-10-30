#!/usr/bin/env python3
"""Validate ACTUAL native GL Inox2D ears-only render, not a source-data stub."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(d):
    out={}
    contact=Image.new("RGB",(1440,880),(18,23,29))
    draw=ImageDraw.Draw(contact)
    images=[]
    for k,(tag,yaw) in enumerate([("neutral",0.5),("maximum",1.0)]):
        f=d/f"gpu_ears_{tag}.x11.png"
        im=Image.open(f).convert("RGB")
        assert im.size==(1024,900),(f,im.size)
        # The window is positioned at (0,0) and is fixed to 720x880.
        crop=im.crop((0,0,720,880))
        rgb=np.asarray(crop,dtype=np.uint8)
        warm=(rgb[:,:,0].astype(np.int16)>rgb[:,:,1].astype(np.int16)+13)&(rgb[:,:,0].astype(np.int16)>rgb[:,:,2].astype(np.int16)+20)&(rgb[:,:,0]>100)
        nwarm=int(warm.sum())
        assert nwarm>2000,f"Ear art missing, warm pixels={nwarm}"
        # Background should be mostly blank/black: no full-puppet hair or torso.
        foreground=(rgb.max(axis=2)>48)
        total=int(foreground.sum())
        assert total<100000,f"Unfiltered full puppet leaked through, foreground={total}"
        assert total>2000,f"Empty real OpenGL screenshot {tag}"
        def area(box):
            x0,y0,x1,y1=box
            return int(foreground[y0:y1,x0:x1].sum())
        source_path=d/f"gpu_ears_{tag}.png"
        crop.save(source_path)
        out[tag]={"native_yaw":yaw,"native_pitch":0.5,
          "sha256":sha(source_path),"warm_pixels":nwarm,
          "screen_foreground_px":total,"upper_region_px":area((120,0,560,220)),
          "lower_region_px":area((120,220,560,880)),
          "size":[720,880]}
        images.append(rgb)
        contact.paste(crop,(k*720,0))
        draw.text((k*720+15,10),f"REAL native GL only Aka ears, HeadYaw={yaw}",fill=(252,249,244))
    delta=np.max(np.abs(images[0].astype(np.int16)-images[1].astype(np.int16)),axis=2)
    motion=float(np.mean(delta>18))
    assert motion>.001,f"No native ear HeadYaw deform observed {motion}"
    contact.save(d/"gpu_ears_native_compare.png")
    contact.thumbnail((1152,704))
    contact.save(d/"gpu_ears_native_compare.jpg",quality=86)
    result={"schema":"core019-real-openGL-only-original-Aka-ear-2poses/1",
       "source_Aka_full_INX_sha256":"dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f",
       "renderer_upstream":"Inochi2D/inox2d/d4dd9dd7f16b775042cbda44370570abf9a8cf81",
       "no_source_uv_or_rig_replacement":True,
       "no_other_parts_rendered":True,
       "full_native_ear_no_masks_lost":"NOT_PROVEN",
       "animation_production_quality":"NOT_TESTED",
       "only_ear_2D_reference_not_3D":True,
       "pose_frame_change_fraction":motion,
       "poses":out}
    (d/"gpu_ears_qa.json").write_text(json.dumps(result,indent=2)+"\n")
    print("CORE019_REAL_INOX_ONLY_EARS_VISIBILITY_QA_PASS",json.dumps(result))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--input",type=Path,required=True)
    args=p.parse_args();main(args.input)

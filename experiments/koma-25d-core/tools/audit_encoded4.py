#!/usr/bin/env python3
"""Decode and independently sample the ACTUAL finished MP4s, not PNG frames.

Sourced clips are saved to a draft Release. The audit image is extracted
only after ffmpeg encoding, ensuring the final viewing path is inspected.
"""
from __future__ import annotations
import base64,io,subprocess,textwrap
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops

root=Path(__file__).resolve().parents[1]
out=root/"out"/"core004"
decoded=out/"encoded_samples"
decoded.mkdir(exist_ok=True,parents=True)
names=("reference","blend","flow","profile_turn")
frames=(9,36,63)
width,height=480,480
sheet=Image.new("RGB",(width*3,height*4),"white")
audit={}
for row,name in enumerate(names):
    movie=out/(name+".mp4")
    if not movie.is_file() or movie.stat().st_size<10000:
        raise RuntimeError(f"missing or too small video {movie}")
    template=str(decoded/(name+"_%02d.png"))
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(movie),
         "-vf","select=eq(n\\,9)+eq(n\\,36)+eq(n\\,63)",
         "-vsync","0",template]
    subprocess.run(cmd,check=True)
    files=sorted(decoded.glob(name+"_*.png"))
    if len(files)!=3:raise RuntimeError(f"{name}: MP4 sampling found {len(files)}")
    cover=[]
    for col,(filename,idx) in enumerate(zip(files,frames)):
        im=Image.open(filename).convert("RGB")
        if im.width<500 or im.height<480:raise RuntimeError("Unexpected decoded movie size")
        bg=Image.new("RGB",im.size,(239,241,245))
        diff=ImageChops.difference(im,bg).convert("L")
        active=sum(v for index,v in enumerate(diff.histogram()) if index>28)/(im.width*im.height)
        if active<0.02:raise RuntimeError(f"Decoded {name} frame {idx} mostly blank ({active})")
        cover.append(round(active,4))
        im.thumbnail((width-10,height-26))
        sheet.paste(im,(col*width+(width-im.width)//2,
                        row*height+(height-26-im.height)//2+26))
    audit[name]={"mp4_bytes":movie.stat().st_size,"sampled_frame_indices":frames,
                 "decoded_nonbackground_coverage":cover}
    ImageDraw.Draw(sheet).text((row*0+8,row*height+5),
                              f"{name} | actual encoded MP4",fill=(10,20,40))
preview=sheet.copy()
preview.thumbnail((1260,1680))
preview.save(out/"encoded_audit.jpg",quality=78,optimize=True)
(out/"encoded_audit.json").write_text(__import__("json").dumps(audit,indent=2)+"\n")
print("CORE004_ENCODED_MP4_AUDIT",__import__("json").dumps(audit))
print("KOMA_CORE004_ENCODED_VIDEO_VISUAL_BEGIN")
for line in textwrap.wrap(base64.b64encode((out/"encoded_audit.jpg").read_bytes()).decode(),120):
    print(line)
print("KOMA_CORE004_ENCODED_VIDEO_VISUAL_END")

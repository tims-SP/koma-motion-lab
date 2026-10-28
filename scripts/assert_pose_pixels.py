#!/usr/bin/env python3
"""Inspect actual PNG pixels from no-GUI Rive poses, with no image-library dependencies.

Rejects valid-but-blank screenshots, duplicate pose images, mismatched dimensions
and absent geometry. This checks visual motion, *not* professional animation quality.
"""
from pathlib import Path
import hashlib
import json
import struct
import sys
import zlib

def png_pixels(path: Path):
    payload=path.read_bytes()
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"not a PNG: {path}")
    pos=8
    ihdr=None
    compressed=[]
    while pos<len(payload):
        n=struct.unpack(">I",payload[pos:pos+4])[0]
        kind=payload[pos+4:pos+8]
        body=payload[pos+8:pos+8+n]
        pos+=12+n
        if kind==b'IHDR':ihdr=struct.unpack(">IIBBBBB",body)
        if kind==b'IDAT':compressed.append(body)
        if kind==b'IEND':break
    if ihdr is None:raise ValueError("missing IHDR")
    width,height,depth,color,compression,filter_type,interlace=ihdr
    channels={0:1,2:3,4:2,6:4}.get(color)
    if channels is None or depth!=8 or interlace!=0:
        raise ValueError(f"unsupported PNG layout: {ihdr}")
    bpp=channels; stride=width*bpp
    data=zlib.decompress(b''.join(compressed))
    i=0;prev=bytearray(stride)
    rows=[]
    for _ in range(height):
        filt=data[i];i+=1
        line=bytearray(data[i:i+stride]);i+=stride
        if len(line)!=stride:raise ValueError("truncated scanline")
        for k in range(stride):
            a=line[k-bpp] if k>=bpp else 0
            b=prev[k]
            c=prev[k-bpp] if k>=bpp else 0
            if filt==0:pass
            elif filt==1:line[k]=(line[k]+a)&255
            elif filt==2:line[k]=(line[k]+b)&255
            elif filt==3:line[k]=(line[k]+((a+b)//2))&255
            elif filt==4:
                p=a+b-c;pa=abs(p-a);pb=abs(p-b);pc=abs(p-c)
                pr=a if pa<=pb and pa<=pc else b if pb<=pc else c
                line[k]=(line[k]+pr)&255
            else:raise ValueError(f"bad png filter: {filt}")
        prev=line
        rows.append(bytes(line))
    return width,height,channels,b''.join(rows)

def main(folder):
    images={}
    for deg in ('000','045','090','135'):
        p=folder/f'weighted_arm_{deg}.png'
        images[deg]=png_pixels(p)
    dimensions={(w,h,c) for w,h,c,_ in images.values()}
    if len(dimensions)!=1:
        raise ValueError(f"image dimensions/channels mismatch: {dimensions}")
    w,h,c=next(iter(dimensions))
    # Corner pixel represents the flat canvas background in this fixture.
    results={}
    base=images['000'][3]
    for deg,(width,height,channels,raw) in images.items():
        corner=raw[:c]
        non_bg=sum(raw[p:p+c]!=corner for p in range(0,len(raw),c))
        changed=sum(raw[p:p+c]!=base[p:p+c] for p in range(0,len(raw),c))
        results[deg]={
            "pixel_sha256":hashlib.sha256(raw).hexdigest(),
            "visible_pixels":non_bg,
            "changed_vs_straight_pixels":changed,
        }
    verdict={
        "test":"actual render raster variation for weighted vector rig",
        "image_size":[w,h],
        "channels":c,
        "poses":results,
        "nonblank_all":all(x["visible_pixels"]>100 for x in results.values()),
        "different_from_000":all(results[d]["changed_vs_straight_pixels"]>100 for d in ('045','090','135')),
        "distinct_pose_rasters":len({x["pixel_sha256"] for x in results.values()})==4
    }
    verdict["pass"]=all([verdict["nonblank_all"],verdict["different_from_000"],verdict["distinct_pose_rasters"]])
    print(json.dumps(verdict,indent=2))
    (folder.parent/'pixel-metrics.json').write_text(json.dumps(verdict,indent=2)+'\n')
    return 0 if verdict["pass"] else 1

if __name__=='__main__':
    sys.exit(main(Path(sys.argv[1])))

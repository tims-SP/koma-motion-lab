#!/usr/bin/env python3
"""Generate visibly synthetic side/back canary maps, NEVER original character art.

This does not reconstruct a real anime character. The images exercise
mesh-specific side UV and source-atlas back UV at runtime.
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import json

def paint(path: Path, kind: str):
    size=512
    im=Image.new("RGBA",(size,size),(0,0,0,0))
    draw=ImageDraw.Draw(im)
    if kind=="side":
        base=(217,156,94,255)
        alt=(154,94,48,255)
    else:
        base=(91,151,202,255)
        alt=(54,91,139,255)
    block=32
    for y in range(0,size,block):
        for x in range(0,size,block):
            col=base if ((x//block+y//block)%2)==0 else alt
            draw.rectangle((x,y,x+block-1,y+block-1),fill=col)
    for x in range(0,size,64):
        draw.line((x,0,x,size),fill=(255,255,255,175),width=3)
    for y in range(0,size,64):
        draw.line((0,y,size,y),fill=(255,255,255,175),width=3)
    msg="DIAGNOSTIC "+kind.upper()
    draw.rectangle((0,215,size,290),fill=(15,25,35,245))
    draw.text((70,238),msg,fill=(255,255,255,255))
    im.save(path)

def main():
    root=Path(__file__).resolve().parents[1]
    folder=root/"viewer"/"public"/"asset"
    folder.mkdir(parents=True,exist_ok=True)
    for name in ("side","back"):paint(folder/(name+".png"),name)
    (folder/"appearance.json").write_text(json.dumps({
        "schema":"koma-multiview/1",
        "front":{"texture":"gBot.png","provenance":"ORIGINAL_SOURCE_ART",
                 "uv":"source_artmesh"},
        "side":{"texture":"side.png","provenance":"SYNTHETIC_DIAGNOSTIC_ONLY",
                "uv":"per_mesh_depth_height"},
        "back":{"texture":"back.png","provenance":"SYNTHETIC_DIAGNOSTIC_ONLY",
                "uv":"source_atlas_same_coordinates_not_registered"},
        "production_accepted":False,
        "warnings":["No authentic side/back artwork is provided",
                    "New-view UV correspondence is not artist-registered",
                    "Canary colors indicate missing artwork, not anime-style rendering"]
    },indent=2)+"\n",encoding="utf-8")
    print("WROTE_DIAGNOSTIC_CANARIES",folder)

if __name__=="__main__":main()

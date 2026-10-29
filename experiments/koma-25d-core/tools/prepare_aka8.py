#!/usr/bin/env python3
"""Create real Aka image-generation reference images from original layered PSD.

No fake profile. Source A original frontal composite; Source B labeled actual
PSD leaf parts, each on white. Check attribution + deterministic content hashes.
"""
from __future__ import annotations
import argparse, hashlib, json, re, math
from pathlib import Path
from psd_tools import PSDImage
from PIL import Image, ImageDraw, ImageFont, ImageOps
import numpy as np

BG=(241,242,246)
PART_NAMES=[
 "Face","Front Hair C","Front Hair L1","Front Hair R1",
 "Side Hair L","Side Hair R","Back Side Hair",
 "Fox: Ear L","Fox: Ear R",
 "Eye L Eyeball","Eye R Eyeball","Nose","Lip",
 "Neck","Eyebrow L","Eyebrow R"
]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def norm(s):return re.sub(r"\s+"," ",str(s).strip()).lower()
def fit(image,size,background=BG,margin=18):
    im=image.convert("RGBA")
    alpha=np.asarray(im.getchannel("A"))
    rgb=np.asarray(im.convert("RGB"))
    subject=(alpha>15)&(np.max(np.abs(rgb.astype(np.int16)-255),axis=2)>17)
    if subject.sum()<300:
        subject=(alpha>15)
    if subject.sum()<100:raise ValueError("Reference asset layer empty")
    yy,xx=np.where(subject)
    box=(max(0,int(xx.min())-margin),max(0,int(yy.min())-margin),
         min(im.width,int(xx.max())+margin+1),min(im.height,int(yy.max())+margin+1))
    piece=im.crop(box)
    tw,th=size
    ratio=min(tw/piece.width,th/piece.height)
    dims=(max(1,round(piece.width*ratio)),max(1,round(piece.height*ratio)))
    piece=piece.resize(dims,Image.Resampling.LANCZOS)
    canvas=Image.new("RGBA",size,background+(255,))
    canvas.alpha_composite(piece,((tw-dims[0])//2,(th-dims[1])//2))
    return canvas.convert("RGB"),box
def main(psd_path,out):
    out.mkdir(parents=True,exist_ok=True)
    psd=PSDImage.open(psd_path)
    composite=psd.composite()
    if composite is None:raise ValueError("PSD composite missing")
    face,box=fit(composite,(1024,1024),margin=60)
    face.save(out/"source_A_aka_front.png",optimize=True)
    face.save(out/"source_A_aka_front.jpg",quality=94,subsampling=0)
    allparts={}
    for layer in psd.descendants():
        if layer.is_group():continue
        n=norm(layer.name)
        if n not in [norm(x) for x in PART_NAMES]:continue
        image=layer.composite()
        if image is None:continue
        if n not in allparts:allparts[n]=(str(layer.name),image,layer)
    cols,rows=4,4
    tw,th=280,295
    board=Image.new("RGB",(cols*tw,rows*th),BG)
    draw=ImageDraw.Draw(board)
    selected=[]
    for index,n in enumerate(PART_NAMES):
        row,col=divmod(index,cols)
        if norm(n) not in allparts:raise ValueError("Required source PSD layer absent: "+n)
        orig,im,layer=allparts[norm(n)]
        cut,cutbox=fit(im,(tw-14,th-43),margin=8)
        board.paste(cut,(col*tw+7,row*th+31))
        label=orig[:35]
        draw.text((col*tw+9,row*th+8),f"{index+1:02d} {label}",fill=(19,28,36))
        selected.append({"part_id":orig,"psd_bounds":[layer.left,layer.top,layer.right,layer.bottom],
                         "reference_tile":index+1,"source_status":"ORIGINAL_PSD_LAYER"})
    board.save(out/"source_B_aka_parts.png",optimize=True)
    # Two-plate review with full-scale source and cropped part identities
    montage=Image.new("RGB",(1024+1120,1180),BG)
    montage.paste(face,(0,65));montage.paste(board,(1024,0))
    md=ImageDraw.Draw(montage)
    md.text((15,17),"SOURCE A: Official Aka frontal PSD composite (NOT AI generated)",fill=(20,25,40))
    md.text((1035,10),"SOURCE B: Exact original PSD component image samples",fill=(20,25,40))
    montage.thumbnail((1600,900))
    montage.save(out/"source_review.jpg",quality=82,optimize=True)
    provenance={
      "schema":"koma-original-reference/1",
      "character":"Aka","author":"seagetch","license":"CC BY 4.0",
      "source":"Inochi2D/inochi2d-docs",
      "source_revision":"593c657855d5679f01443ef311346298fd25e117",
      "source_psd":"tutorial-aka.psd",
      "source_psd_sha256":sha(psd_path),
      "source_canvas":[psd.width,psd.height],
      "image_A":"source_A_aka_front.png",
      "image_A_sha256":sha(out/"source_A_aka_front.png"),
      "image_B":"source_B_aka_parts.png",
      "image_B_sha256":sha(out/"source_B_aka_parts.png"),
      "original_psd_subject_bbox":box,
      "part_count":len(selected),"parts":selected,
      "view_direction":"nose_to_image_right",
      "view_0deg_kind":"ORIGINAL_SOURCE_ART",
      "generated_angle_status":{"30":"NOT_GENERATED","45":"NOT_GENERATED"},
      "notes":["The model's source portrait is NEVER synthesized",
               "This is a conditioning reference, NOT candidate views",
               "The original PSD complete head, including fox ears, is authoritative"]
    }
    (out/"reference_manifest.json").write_text(json.dumps(provenance,indent=2,ensure_ascii=False)+"\n")
    print("CORE008_SOURCE_REFERENCES_READY",json.dumps({k:v for k,v in provenance.items() if k!="parts"},ensure_ascii=False))
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--psd",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    a=ap.parse_args();main(a.psd,a.out)

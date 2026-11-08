#!/usr/bin/env python3
"""Inspect real See-through PSD and export constituent P0 RGBA semantic layers.

The hosted model produces artwork on a 768 canvas. Full-canvas 1024 PNGs are
registration outputs, not evidence of native model output at 1024 resolution.
Separate physical eyes, ears, ahoge and overlap-boundary review remain required.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
import cv2
from psd_tools import PSDImage

ROLES={
 "back hair":"hair.back",
 "neck":"body.neck",
 "topwear":"body.topwear",
 "ears":"ear.pair",
 "face":"face.skin",
 "nose":"nose",
 "mouth":"mouth",
 "eyewhite":"eye.sclera.pair",
 "irides":"eye.iris.pair",
 "eyebrow":"eyebrow.pair",
 "eyelash":"eye.lash.pair",
 "front hair":"hair.front",
 "headwear":"hair.clip.cross_gold"
}

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def frame(layer,canvas):
    image=layer.topil()
    if image is None: return Image.new("RGBA",canvas,(0,0,0,0))
    image=image.convert("RGBA")
    bbox=tuple(layer.bbox)
    bound=(bbox[2]-bbox[0],bbox[3]-bbox[1])
    if image.size!=bound:raise ValueError(f"PSD layer {layer.name}: {image.size} vs bbox {bound}")
    dst=Image.new("RGBA",canvas,(0,0,0,0))
    dst.alpha_composite(image,(bbox[0],bbox[1]))
    return dst

def merge(layers,canvas):
    out=Image.new("RGBA",canvas,(0,0,0,0))
    for im in layers:
        out.alpha_composite(im)
    return out

def build(psd_file,source_file,out,yaw=0):
    psd_file=Path(psd_file).resolve();source_file=Path(source_file).resolve()
    out=Path(out).resolve();out.mkdir(exist_ok=True,parents=True)
    psd=PSDImage.open(psd_file)
    if psd.size!=(768,768):
        raise ValueError("Hosted inference expected 768 PSD, got "+str(psd.size))
    layers=list(psd)
    if len(layers)<10:raise ValueError("PSD had too few semantic layers")
    records=[];full=[];unique=set()
    for i,layer in enumerate(layers):
        name=layer.name.strip().lower()
        semantic=ROLES.get(name)
        if semantic is None or semantic in unique:
            raise ValueError("Unexpected or duplicate PSD semantic layer "+repr(name))
        unique.add(semantic)
        raw=frame(layer,psd.size)
        full.append(raw)
        normalized=raw.resize((1024,1024),Image.Resampling.LANCZOS)
        path=out/"parts"/(f"{i:02d}_{semantic}.png")
        path.parent.mkdir(parents=True,exist_ok=True)
        normalized.save(path)
        alpha=np.asarray(raw.getchannel("A"))
        y,x=np.where(alpha>12)
        bounds=[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)] if len(x)>0 else None
        records.append({
            "psdLayerIndex":i,"psdLayerName":layer.name,
            "semanticCandidateId":semantic,
            "viewYawDeg":yaw,"originalLayerBBox":list(layer.bbox),
            "visiblePixelsAt768":int((alpha>12).sum()),
            "softAlphaPixelsAt768":int(((alpha>0)&(alpha<255)).sum()),
            "actualPixelBBoxAt768":bounds,
            "outputPath":str(path.relative_to(out)),
            "outputSha256":sha(path),
            "canvas":[1024,1024],
            "nativeModelResolution":[768,768],
            "sourceRole":"See-through inferred semantic PSD layer",
            "physicalNearFarSeparated":not semantic.endswith(".pair"),
            "visualReviewed":False
        })
    original=np.array(Image.open(source_file).convert("RGBA").resize((768,768),Image.Resampling.LANCZOS))
    original[original[:,:,3]==0]=0
    image_original=Image.fromarray(original,"RGBA")
    PSDflatten=psd.composite().convert("RGBA")
    exported_composite=merge(full,psd.size)
    for name,img in (("psd-flat.png",PSDflatten),("recomposed.png",exported_composite),
                     ("source-original.png",image_original)):
        img.save(out/name)
    aa=np.asarray(image_original);bb=np.asarray(PSDflatten);cc=np.asarray(exported_composite)
    vis_a=aa[:,:,3]>32;vis_b=bb[:,:,3]>32
    iou=float(np.count_nonzero(vis_a&vis_b))/max(1,int(np.count_nonzero(vis_a|vis_b)))
    diff=np.abs(aa.astype(np.float32)-cc.astype(np.float32))
    overlap=(aa[:,:,3]>245)&(cc[:,:,3]>245)
    src_vis=cc[:,:,3]>32
    src_layer_iou=float(np.count_nonzero(vis_a&src_vis))/max(1,int(np.count_nonzero(vis_a|src_vis)))
    source_color_mae=float(diff[:,:,:3][overlap].mean()) if overlap.any() else float("nan")
    psdVsParts=np.abs(bb.astype(np.int16)-cc.astype(np.int16))
    sprite=Image.new("RGB",(3*768,768),(33,43,58))
    for i,img in enumerate((image_original,PSDflatten,exported_composite)):
        bg=Image.new("RGBA",img.size,(42,55,72,255));bg.alpha_composite(img)
        sprite.paste(bg.convert("RGB"),(i*768,0))
    sprite.save(out/"front-comparison.jpg",quality=90)
    cell=240;label=34;cols=4;rows=(len(full)+cols-1)//cols
    board=Image.new("RGB",(cols*cell,rows*(cell+label)),(30,42,58))
    draw=ImageDraw.Draw(board)
    for i,(image,rec) in enumerate(zip(full,records)):
        thumb=image.resize((cell-12,cell-12),Image.Resampling.LANCZOS)
        bg=Image.new("RGBA",(cell-12,cell-12),(64,76,93,255));bg.alpha_composite(thumb)
        x=(i%cols)*cell+6;y=(i//cols)*(cell+label)+6
        board.paste(bg.convert("RGB"),(x,y))
        draw.text((x,y+cell-8),rec["semanticCandidateId"],fill="#eef3ff")
    board.save(out/"semantic-contact.jpg",quality=90)
    qa={
        "schema":"KOMA-P0-SEETHROUGH-PSD-LAYER-QA-V1",
        "characterId":"p0_character_001",
        "viewYawDeg":yaw,
        "psdSHA256":sha(psd_file),
        "sourceOriginalSHA256":sha(source_file),
        "model":"See-through v3 hosted ZeroGPU, 768 resolution",
        "layers":records,
        "totalLayers":len(records),
        "semanticItemsToPhysicallySplit":[x["semanticCandidateId"] for x in records
                                          if x["semanticCandidateId"].endswith(".pair")],
        "sourceRGBA_1024":"recovered P0 original "+str(yaw)+" degree reference",
        "exportCanvas":[1024,1024],
        "modelCanvas":[768,768],
        "metrics":{
           "PSDPreviewSourceSilhouetteIoU":round(iou,6),
           "exportedLayerRecompositionSourceSilhouetteIoU":round(src_layer_iou,6),
           "exportedLayerRecompositionSourceOpaqueRGBMAE":round(source_color_mae,5),
           "PSDPreviewVersusExportedLayerRecompositionChangedPixels":
               int(np.any(psdVsParts>2,axis=2).sum()),
           "PSDPreviewVersusExportedLayerRecompositionMAE":round(float(psdVsParts.mean()),5)
        },
        "PSDCompositePreviewRole":"DIAGNOSTIC_ONLY_DUE_TO_PREVIEW_RENDER_MISMATCH",
        "artworkCompositeAuthority":"manual alpha-composition of exported PSD semantic RGBA layers",
        "status":"LAYER_EXPORT_CANDIDATE_VISUAL_REVIEW",
        "artisticAcceptance":"PENDING"
    }
    (out/"layer-qa.json").write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":qa["status"],"totalLayers":len(records),
                      "semanticIds":[x["semanticCandidateId"] for x in records],
                      "metrics":qa["metrics"]},indent=2,ensure_ascii=False))
    return qa

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--psd",required=True)
    p.add_argument("--source",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--yaw",type=int,choices=[0,45,90],default=0)
    args=p.parse_args()
    build(args.psd,args.source,args.out,args.yaw)

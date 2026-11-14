#!/usr/bin/env python3
"""Source-exact hidden layer inpainting from See-through (SIGGRAPH 2026) PSD.

Reuses independently generated P0 Qwen RGBA candidate colors as the visible
reference and only adds See-through PSD pixels under fully opaque upper
ArtMesh layers. Source-visible composition must remain exactly identical.
"""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw
from psd_tools import PSDImage

CANVAS=(1024,1024)
PSEUDO_SOURCE_ROLES={
    "hair.back":("back hair",42),
    "hair.side":("back hair",34),
    "face.skin":("face",42),
    "eye.near":("eyewhite",16),
}

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()


def read(p):
    return json.loads(Path(p).read_text(encoding="utf8"))


def load_rgba(p):
    with Image.open(p) as im:
        if im.mode!="RGBA" or im.size!=CANVAS:
            raise ValueError("P0 source must be 1024x1024 true native RGBA")
        return im.copy()


def upper_alpha(layers,index):
    """Composite upper native ArtMesh alpha, including partial transparency."""
    result=Image.new("RGBA",CANVAS,(0,0,0,0))
    for pic in layers[index+1:]:
        result.alpha_composite(pic)
    return np.asarray(result.getchannel("A"))


def build(root,angle,psd_file,out):
    root=Path(root).resolve()
    out=Path(out).resolve()
    target={77.5:"yaw077p5",65.0:"yaw065"}[float(angle)]
    candidate=root/"p15-independent-candidates"/(target+"-artmesh")
    source=read(candidate/"qa.json")
    records=sorted(source["semanticLayerRecords"],key=lambda x:x["depthOrder"])
    if len(records)!=13 or [r["depthOrder"] for r in records]!=list(range(13)):
        raise AssertionError("P0 13 native semantic ownership layers required")
    source_art=root/source["sourceMatte"]["path"]
    if sha(source_art)!=source["sourceMatte"]["sha256"]:
        raise AssertionError("P0 approved candidate matte SHA mismatch")
    psd_file=Path(psd_file).resolve()
    provenance=read(psd_file.with_name(psd_file.name.replace("-layers.psd","-qa.json")))
    if sha(psd_file)!=provenance["psdSHA256"]:
        raise AssertionError("See-through PSD byte lineage mismatch")
    if provenance["sourceSHA256"]!=source["sourceMatte"]["sha256"]:
        raise AssertionError("See-through PSD not generated from this P0 view")
    psd=PSDImage.open(psd_file)
    if psd.size!=(768,768):
        raise ValueError("See-through source resolution expected 768 native PSD")
    layers=[load_rgba(root/r["path"]) for r in records]
    source_layers=[img.copy() for img in layers]
    source_psd={}
    for layer in psd:
        if layer.name in {name for name,_ in PSEUDO_SOURCE_ROLES.values()}:
            image=layer.composite(viewport=(0,0,768,768))
            if image is None:
                continue
            source_psd[layer.name]=image.convert("RGBA").resize(CANVAS,Image.Resampling.LANCZOS)
    rows=[]
    for i,role in enumerate(r["semanticId"] for r in records):
        if role not in PSEUDO_SOURCE_ROLES:
            continue
        from_name,radius=PSEUDO_SOURCE_ROLES[role]
        if from_name not in source_psd:
            raise ValueError("See-through inpaint source semantic layer missing "+from_name)
        existing=np.asarray(layers[i],dtype=np.uint8).copy()
        painted=np.asarray(source_psd[from_name],dtype=np.uint8)
        region=(existing[:,:,3]>0).astype(np.uint8)
        window=np.ones((7,7),np.uint8)
        expanded=cv2.dilate(region,window,iterations=max(1,int(radius/6)))>0
        upper=upper_alpha(source_layers,i)
        safe=(existing[:,:,3]==0)&(upper==255)&(painted[:,:,3]>165)&expanded
        existing[safe]=painted[safe]
        layer=Image.fromarray(existing,"RGBA")
        layers[i]=layer
        rows.append({
            "role":role,"seeThroughLayer":from_name,
            "inpaintedHiddenPixels":int(safe.sum()),
            "originalVisiblePixels":int(region.sum()),
            "futureOpaqueOcclusionPixels":int((upper==255).sum()),
            "sourcePSDLayerSHA256":sha(psd_file),
            "maskPolicy":"ONLY_INPAINT_WHERE_FULLY_OCCLUDED_BY_LATER_ARTMESH"
        })
    out.mkdir(parents=True,exist_ok=True)
    restored=Image.new("RGBA",CANVAS,(0,0,0,0))
    output_recs=[]
    for rec,img in zip(records,layers):
        file=out/"layers"/(rec["semanticId"]+".png")
        file.parent.mkdir(parents=True,exist_ok=True)
        img.save(file)
        restored.alpha_composite(img)
        output_recs.append({
            "semanticId":rec["semanticId"],"depthOrder":rec["depthOrder"],
            "path":str(file.relative_to(root)),"sha256":sha(file),
            "originalP15PartSHA256":rec["sha256"],
            "alphaPixels":int((np.asarray(img.getchannel("A"))>0).sum())
        })
    baseline=load_rgba(source_art)
    original=np.asarray(baseline,dtype=np.int16)
    found=np.asarray(restored,dtype=np.int16)
    alpha_max=int(np.abs(original[:,:,3]-found[:,:,3]).max())
    valid=original[:,:,3]>0
    rgb_max=int(np.abs(original[:,:,:3][valid]-found[:,:,:3][valid]).max())
    if alpha_max!=0 or rgb_max!=0:
        raise ValueError("Source-visible anime frame changed after hidden underpaint")
    result=out/(target+"-artmesh-underpaint.png")
    restored.save(result)
    contact=Image.new("RGB",(4*370,410),(32,43,60))
    pen=ImageDraw.Draw(contact)
    visuals=[(baseline,"Original P15 RGBA"),
             (restored,"13 ArtMesh + hidden inpaint"),
             (layers[1],"Hair back + inpaint"),
             (layers[2],"Face skin + inpaint")]
    for i,(pic,title) in enumerate(visuals):
        pane=Image.new("RGBA",CANVAS,(45,61,80,255));pane.alpha_composite(pic)
        contact.paste(pane.convert("RGB").resize((370,370),Image.Resampling.LANCZOS),(i*370,0))
        pen.text((i*370+10,381),title,fill="white")
    thumb=out/(target+"-inpainted-layer-review.jpg")
    contact.save(thumb,quality=92)
    summary={
        "schema":"KOMA-P0-P15-06-SEE_THROUGH_HIDDEN_ARTMESH_V1",
        "characterId":"p0_character_001",
        "yaw":angle,
        "sourceCandidateArtSHA256":source["sourceMatte"]["sha256"],
        "sourceSemanticCandidateQA_SHA256":sha(candidate/"qa.json"),
        "seeThroughSpace":provenance["space"],
        "seeThroughPSD_SHA256":sha(psd_file),
        "sourcePSDResolution":[768,768],
        "outputArtMeshResolution":list(CANVAS),
        "nativeSemanticLayers":len(output_recs),
        "hiddenSourceRoles":rows,
        "totalHiddenPaintedPixels":sum(v["inpaintedHiddenPixels"] for v in rows),
        "visiblePixelExactAlphaMax":alpha_max,
        "visiblePixelExactRGBMax":rgb_max,
        "nativeLayers":output_recs,
        "composite":{"path":str(result.relative_to(root)),"sha256":sha(result)},
        "contact":{"path":str(thumb.relative_to(root)),"sha256":sha(thumb)},
        "artisticAcceptance":"PENDING_INDEPENDENT_LINE_AND_OCCLUSION_REVIEW",
        "engineeringStatus":"P15_06_HIDDEN_ARTMESH_UNDERPAINT_SOURCE_EXACT"
    }
    (out/"qa.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":summary["engineeringStatus"],"yaw":angle,
                      "totalHiddenPixels":summary["totalHiddenPaintedPixels"],
                      "rolePixels":{v["role"]:v["inpaintedHiddenPixels"] for v in rows},
                      "alphaMax":alpha_max,"rgbMax":rgb_max},ensure_ascii=False))
    return summary


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True)
    p.add_argument("--angle",required=True,type=float)
    p.add_argument("--psd",required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    build(args.root,args.angle,args.psd,args.out)

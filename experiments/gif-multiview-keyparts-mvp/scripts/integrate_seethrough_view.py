#!/usr/bin/env python3
"""Register See-through inferred concealed art into original P0 45° ArtMeshes.

Canonical visible pixels are retained. Generated 768px PSD semantic layers
are normalized to 1024 canvas. Donor eye/ear pair layers are partitioned by
corresponding original-view physical identity, not a fixed global x=512 line.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
from p1_front_semantic import DEPTH,SEMANTIC,alpha_over,rescale_visible
from p2_semantic_art import assign_ownership

MODEL_MAP={
 "body.reference":("body.neck","body.topwear"),
 "hair.back":("hair.back",),
 "face.skin":("face.skin",),
 "ear.far":("ear.pair",),
 "ear.near":("ear.pair",),
 "eye.far":("eye.sclera.pair","eye.iris.pair","eye.lash.pair","eyebrow.pair"),
 "eye.near":("eye.sclera.pair","eye.iris.pair","eye.lash.pair","eyebrow.pair"),
 "nose":("nose",),"mouth":("mouth",),
 "hair.side":("hair.front",),"hair.front":("hair.front",),
 "hair.ahoge":("hair.front",),"hair.clip.cross_gold":("hair.clip.cross_gold",)
}

def digest(filename):
    h=hashlib.sha256()
    with Path(filename).open("rb") as fp:
        for chunk in iter(lambda:fp.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def read_image(path):
    with Image.open(path) as im:
        if im.size!=(1024,1024) or im.mode!="RGBA":
            raise ValueError("RGBA/1024 requirement: "+str(path))
        return np.asarray(im).copy()

def bounds(rec):
    box=rec.get("bbox")
    if not box: return None
    return ((box[0]+box[2])/2,(box[1]+box[3])/2)

def semantic_pair_cut(key,donor,parts):
    if key in ("eye.near","eye.far"):
        a,b=bounds(parts["eye.near"]),bounds(parts["eye.far"])
    elif key in ("ear.near","ear.far"):
        a,b=bounds(parts["ear.near"]),bounds(parts["ear.far"])
    else:return donor
    out=donor.copy()
    if a is None and b is None:
        out[:,:,:]=0
    elif a is not None and b is not None:
        cutoff=(a[0]+b[0])*0.5
        xx=np.arange(1024)[None,:]
        keep=(xx<cutoff) if ((key.endswith(".near") and a[0]<b[0]) or
            (key.endswith(".far") and b[0]<a[0])) else (xx>=cutoff)
        out[:,~np.broadcast_to(keep,(1024,1024))[0]] = 0
    elif (a if key.endswith(".near") else b) is None:
        out[:,:,:]=0
    return out

def composite(layers):
    result=np.zeros((1024,1024,4),dtype=np.uint8)
    for sid in SEMANTIC:result=alpha_over(result,layers[sid])
    return result

def extract(root,export,output,yaw):
    root=Path(root).resolve();export=Path(export).resolve()
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    registry=json.loads((root/"p2-views/parts.json").read_text())
    psd=json.loads((export/"layer-qa.json").read_text())
    if yaw not in (45,90) or psd.get("viewYawDeg")!=yaw:
        raise ValueError("PSDSemantic yaw differs from registered original view")
    if registry["characterId"]!="p0_character_001" or psd["characterId"]!="p0_character_001":
        raise ValueError("P0 source identity mismatch")
    by_id={r["semanticId"]:r for r in registry["parts"] if r["yawDeg"]==yaw}
    if len(by_id)!=13:raise ValueError("Expected original 13 view slots")
    model={}
    for entry in psd["layers"]:
        file=export/entry["outputPath"]
        if digest(file)!=entry["outputSha256"]:raise ValueError("Donor SHA mismatch")
        model[entry["semanticCandidateId"]]=read_image(file)
    original={sid:read_image(root/r["path"]) for sid,r in by_id.items()}
    ref=read_image(root/f"p2-views/whole/yaw{yaw:03d}.png")
    with Image.open(root/f"recovered-review/frames/head_8/yaw{yaw:03d}_whole.png") as im:
        native=np.asarray(im.convert("RGBA"))
    owner=assign_ownership(native,yaw)
    scaled=cv2.resize(owner,(1024,1024),interpolation=cv2.INTER_NEAREST)
    scaled[(scaled==255)&(ref[:,:,3]>0)]=DEPTH["hair.back"]
    scaled[ref[:,:,3]==0]=255
    xx,yy=np.meshgrid(np.arange(1024),np.arange(1024))
    mapped={};evidence=[]
    for key in SEMANTIC:
        entry=by_id[key]
        donor=np.zeros_like(ref)
        for layer in MODEL_MAP[key]:
            donor=alpha_over(donor,model[layer])
        donor=semantic_pair_cut(key,donor,by_id)
        # Neck and body preserve original seam ordering through the P0
        # independent ownership map; they are not an alternative rig source.
        actual=scaled==DEPTH[key]
        behind=(scaled>DEPTH[key]) & (scaled!=255) & (ref[:,:,3]>=245)
        # Guarantee the new texture is actually concealed in the intact
        # original source. A fully opaque higher-Z layer makes this
        # insertion pixel-invariant until that layer moves.
        fully_covered=np.zeros((1024,1024),dtype=bool)
        for higher in SEMANTIC:
            if DEPTH[higher]>DEPTH[key] and by_id[higher]["visibility"]=="visible":
                fully_covered |= original[higher][:,:,3]==255
        hidden=(behind & fully_covered &
                (donor[:,:,3]>12) & (original[key][:,:,3]<235))
        if key.startswith("eye.") or key.startswith("ear.") or key in (
            "hair.side","hair.front","nose","mouth","hair.ahoge","hair.clip.cross_gold"):
            radius=29 if key.startswith(("eye.","ear.")) else 45
            known=cv2.dilate(actual.astype(np.uint8),
                cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(radius,radius)))>0
            hidden&=known
        if key=="hair.ahoge":
            hidden&=(yy<225)
        if entry["visibility"]=="hidden":
            hidden[:]=False
        good=actual&(ref[:,:,3]>=245)&(donor[:,:,3]>240)
        shifts=np.zeros(3,np.int16)
        if good.sum()>=30:
            shifts=np.clip(np.round(np.median(
                ref[:,:,:3][good].astype(np.int16)-
                donor[:,:,:3][good].astype(np.int16),axis=0)), -26,26).astype(np.int16)
        donor[:,:,:3]=np.clip(donor[:,:,:3].astype(np.int16)+shifts,0,255).astype(np.uint8)
        result=original[key].copy()
        result[hidden]=donor[hidden]
        # Canonical pixels remain authoritative at the actual visible owner
        # region, including original alpha antialias edges.
        result[actual]=original[key][actual]
        outfile=output/"parts"/f"{key}.png"
        outfile.parent.mkdir(parents=True,exist_ok=True)
        Image.fromarray(result,"RGBA").save(outfile)
        record=copy.deepcopy(entry)
        record.update({
            "path":str(outfile.relative_to(output)),
            "frameSha256":digest(outfile),
            "originVisibleFrameSha256":entry["frameSha256"],
            "PSDSourceSHA256":psd["psdSHA256"],
            "modelNativeCanvas":[768,768],
            "addedInferredHiddenPixels":int(hidden.sum()),
            "colorAlignmentShift":shifts.tolist(),
            "underpaintProvenance":"See-through semantic inference and P0 original visible pixels",
            "visualReviewed":False
        })
        mapped[key]=result
        evidence.append(record)
    actual_composite=composite(mapped)
    baseline=composite(original)
    delta=np.abs(actual_composite.astype(np.int16)-ref.astype(np.int16))
    difference=int(np.any(delta>1,axis=2).sum())
    silhouette=(actual_composite[:,:,3]>32)
    refsil=(ref[:,:,3]>32)
    iou=float(np.count_nonzero(silhouette&refsil))/max(1,int(np.count_nonzero(silhouette|refsil)))
    hole=int(np.count_nonzero((ref[:,:,3]>=245)&(actual_composite[:,:,3]<245)))
    reconstructed=output/"registered-composite.png"
    Image.fromarray(actual_composite,"RGBA").save(reconstructed)
    contact=Image.new("RGB",(3*640,640),(32,44,61))
    labels=("Original authored P0","Source ArtMesh reconstruction","PSD underpainting in registered source view")
    dr=ImageDraw.Draw(contact)
    for i,pixels in enumerate((ref,baseline,actual_composite)):
        im=Image.fromarray(pixels,"RGBA")
        im=im.resize((600,600),Image.Resampling.LANCZOS)
        matte=Image.new("RGBA",(600,600),(48,62,82,255))
        matte.alpha_composite(im)
        contact.paste(matte.convert("RGB"),(i*640+20,18))
        dr.text((i*640+20,622),labels[i],fill="white")
    contact.save(output/"semantic-comparison.jpg",quality=92)
    manifest={
       "schema":"KOMA-P0-ARTMESH-MANIFEST-V1",
       "characterId":"p0_character_001",
       "yaw":yaw,"canvas":[1024,1024],
       "sourcePSD":psd["psdSHA256"],
       "sourceOriginalReferenceSHA256":digest(root/f"p2-views/whole/yaw{yaw:03d}.png"),
       "modelCanvas":[768,768],
       "parts":evidence,
       "referenceImage":{"path":"registered-composite.png","sha256":digest(reconstructed)}
    }
    qa={
      "schema":"KOMA-P0-P5-PSD-ARTMESH-VIEW-QA-V1",
      "characterId":"p0_character_001","yaw":yaw,
      "sourcePSD":psd["psdSHA256"],
      "sourceOriginal":digest(root/f"p2-views/whole/yaw{yaw:03d}.png"),
      "registeredParts":len(evidence),
      "originalWholeSilhouetteIoU":round(iou,6),
      "changedSourceVisiblePixels":difference,
      "transparentHolesOnOpaqueSource":hole,
      "sumAddedInferredHiddenPixels":sum(r["addedInferredHiddenPixels"] for r in evidence),
      "parts":[{"semanticId":r["semanticId"],"addedHiddenPixels":r["addedInferredHiddenPixels"],
                "frameSHA256":r["frameSha256"]} for r in evidence],
      "visibilityGate":"REGISTERED_ORIGINAL_YAW_VISIBILITY",
      "artStatus":"PENDING_INDEPENDENT_MOTION_VISUAL_REVIEW",
      "status":"VIEW_ARTMESH_PSD_CANDIDATE"
    }
    (output/"parts.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
    (output/"qa.json").write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:qa[k] for k in ("yaw","registeredParts","originalWholeSilhouetteIoU",
        "changedSourceVisiblePixels","transparentHolesOnOpaqueSource",
        "sumAddedInferredHiddenPixels","status")},indent=2,ensure_ascii=False))
    return qa

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True)
    p.add_argument("--exported",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--yaw",type=int,choices=[45,90],required=True)
    args=p.parse_args()
    extract(args.root,args.exported,args.out,args.yaw)

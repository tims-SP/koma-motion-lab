#!/usr/bin/env python3
"""Merge See-through PSD hidden-region artwork into pixel-registered P0 front semantic layers.

Original recovered P0 PNG visible pixels remain authoritative. Only regions
occluded by known opaque, nearer P0 parts can take See-through's generated
underpainting. The output is a reviewable 13-part ArtMesh candidate with
per-part origin/hashes, explicit anatomical groups, and an eye motion check.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import numpy as np
import cv2
from PIL import Image,ImageDraw

from p1_front_semantic import DEPTH,SEMANTIC,ownership,alpha_over,rescale_visible

LAYER_MAP={
 "hair.back":"hair.back",
 "face.skin":"face.skin",
 "hair.side":"hair.front",
 "hair.front":"hair.front",
 "hair.ahoge":"hair.front",
 "hair.clip.cross_gold":"hair.clip.cross_gold",
 "nose":"nose",
 "mouth":"mouth",
 "eye.near":"eye.sclera.pair",
 "eye.far":"eye.sclera.pair",
 "ear.near":"ear.pair",
 "ear.far":"ear.pair",
 "body.reference":"body.topwear"
}
EYE_COMPOSITES=["eye.sclera.pair","eye.iris.pair","eyebrow.pair","eye.lash.pair"]

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()

def load(p):
    return np.array(Image.open(p).convert("RGBA")).copy()

def pctimg(img):
    return Image.fromarray(img,"RGBA")

def source_model_rgba(root,layer_qa):
    result={}
    for item in layer_qa["layers"]:
        key=item["semanticCandidateId"]
        filename=root/item["outputPath"]
        if sha(filename)!=item["outputSha256"]:
            raise ValueError("See-through part SHA mismatch: "+key)
        img=load(filename)
        if img.shape!=(1024,1024,4):
            raise ValueError("Unexpected 1024 export: "+key)
        result[key]=img
    return result

def eye_model(model,near):
    split=512
    result=np.zeros((1024,1024,4),dtype=np.uint8)
    for key in EYE_COMPOSITES:
        rgba=model[key].copy()
        if near:rgba[:,split:]=0
        else:rgba[:,:split]=0
        result=alpha_over(result,rgba)
    return result

def ear_model(model,near):
    rgba=model["ear.pair"].copy()
    if near:rgba[:,512:]=0
    else:rgba[:,:512]=0
    return rgba

def model_source(key,model):
    if key=="eye.near":return eye_model(model,True)
    if key=="eye.far":return eye_model(model,False)
    if key=="ear.near":return ear_model(model,True)
    if key=="ear.far":return ear_model(model,False)
    if key=="body.reference":
        return alpha_over(model["body.neck"],model["body.topwear"])
    rgba=model[LAYER_MAP[key]].copy()
    yy,xx=np.indices((1024,1024))
    if key=="hair.ahoge":
        rgba[yy>210]=0
    if key=="hair.side":
        # Semantics of the original P0 side locks are preserved by ROI guidance
        # and the P1 layer's genuine visible footprint below the crown.
        rgba[(xx>=430)&(xx<=630)&(yy<500)]=0
    return rgba

def compose(layers):
    result=np.zeros((1024,1024,4),dtype=np.uint8)
    for sid in SEMANTIC:
        result=alpha_over(result,layers[sid])
    return result

def translated(img,dx):
    x=np.float32([[1,0,dx],[0,1,0]])
    return cv2.warpAffine(img,x,(1024,1024),flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))

def eye_motion(layers,dx):
    imgs={k:v.copy() for k,v in layers.items()}
    imgs["eye.near"]=translated(imgs["eye.near"],dx)
    return compose(imgs)

def fringe_motion(layers,dx):
    imgs={k:v.copy() for k,v in layers.items()}
    imgs["hair.front"]=translated(imgs["hair.front"],dx)
    return compose(imgs)

def run(root,exported,out):
    root=Path(root).resolve()
    exported=Path(exported).resolve()
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    src_manifest=json.loads((root/"p1-front/parts.json").read_text())
    model_manifest=json.loads((exported/"layer-qa.json").read_text())
    if src_manifest["characterId"]!="p0_character_001" or model_manifest["characterId"]!="p0_character_001":
        raise ValueError("Character ID mismatch")
    source=load(root/"p1-front/diagnostics/front-reference.png")
    raw=load(root/"recovered-review/frames/head_8/yaw000_whole.png")
    owners,_=ownership(root,raw)
    owner_high=cv2.resize(owners,(1024,1024),interpolation=cv2.INTER_NEAREST)
    owner_high[(owner_high==255)&(source[:,:,3]>0)]=DEPTH["hair.back"]
    owner_high[source[:,:,3]==0]=255
    model=source_model_rgba(exported,model_manifest)
    parts={p["semanticId"]:p for p in src_manifest["parts"]}
    original={sid:load(root/parts[sid]["path"]) for sid in SEMANTIC}
    layers={};records=[]
    for sid in SEMANTIC:
        idx=DEPTH[sid];src=original[sid]
        donor=model_source(sid,model)
        actual=owner_high==idx
        hidden=((owner_high>idx)&(owner_high!=255)&(source[:,:,3]==255)&
                (donor[:,:,3]>12)&(~actual))
        if sid in ("face.skin","hair.back"):
            pass
        elif sid in ("eye.near","eye.far","ear.near","ear.far",
                     "hair.side","hair.front"):
            footprint=cv2.dilate(actual.astype(np.uint8),
                cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(81,81)))>0
            hidden &= footprint
        else:
            footprint=cv2.dilate(actual.astype(np.uint8),
                cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(41,41)))>0
            hidden &= footprint
        color_shift=np.zeros(3,dtype=np.int16)
        # A per-part color adjustment on original-visible overlap keeps the
        # newly inferred hidden pixels compatible with the original artwork.
        same=actual&(source[:,:,3]>=245)&(donor[:,:,3]>=240)
        if same.sum()>=25:
            color_shift=np.clip(
                np.median(source[:,:,:3][same].astype(np.int16)-
                          donor[:,:,:3][same].astype(np.int16),axis=0).round(),
                -24,24).astype(np.int16)
        donor[:,:,:3]=np.uint8(np.clip(
            donor[:,:,:3].astype(np.int16)+color_shift,0,255))
        revised=src.copy()
        revised[hidden]=donor[hidden]
        # The source visible RGB+alpha is held invariant by construction.
        revised[actual]=src[actual]
        path=out/"parts"/(sid+".png")
        path.parent.mkdir(parents=True,exist_ok=True)
        pctimg(revised).save(path)
        layers[sid]=revised
        record=copy.deepcopy(parts[sid])
        record["path"]=str(path.relative_to(out))
        record["frameSha256"]=sha(path)
        record["additionalInferredNativePixels"]=int(hidden.sum())
        record["modelColorShiftRGB"]=color_shift.tolist()
        record["additionalModelSource"]="See-through PSD 768 source with 1024 registration"
        record["modelPSDSHA256"]=model_manifest["psdSHA256"]
        record["visualReviewed"]=False
        records.append(record)
    baseline=compose(original)
    rebuilt=compose(layers)
    src_ref=source
    changed=int(np.any(np.abs(rebuilt.astype(np.int16)-src_ref.astype(np.int16))>1,axis=2).sum())
    alpha_src=src_ref[:,:,3]>32;alpha_final=rebuilt[:,:,3]>32
    iou=float((alpha_src&alpha_final).sum())/max(1,int((alpha_src|alpha_final).sum()))
    holes=int(((src_ref[:,:,3]>=245)&(rebuilt[:,:,3]<245)).sum())
    new_eye=eye_motion(layers,10)
    old_eye=eye_motion(original,10)
    motion_holes=int(((src_ref[:,:,3]>=245)&(new_eye[:,:,3]<245)).sum())
    fringe_original=fringe_motion(original,16)
    fringe_inferred=fringe_motion(layers,16)
    original_fringe_holes=int(((src_ref[:,:,3]>=245)&(fringe_original[:,:,3]<245)).sum())
    inferred_fringe_holes=int(((src_ref[:,:,3]>=245)&(fringe_inferred[:,:,3]<245)).sum())
    actual_visible_ref=src_ref[:,:,3]>245
    restored_fringe_pixels=int(
        (actual_visible_ref&(fringe_original[:,:,3]<245)&(fringe_inferred[:,:,3]>=245)).sum())
    for name,img in (("front-source.png",src_ref),("baseline-front.png",baseline),
                     ("front-registered.png",rebuilt),
                     ("eye-shift-10px-baseline.png",old_eye),
                     ("eye-shift-10px-psd.png",new_eye),
                     ("fringe-shift-16px-baseline.png",fringe_original),
                     ("fringe-shift-16px-psd.png",fringe_inferred)):
        pctimg(img).save(out/name)
    board=Image.new("RGB",(3*640,2*640),(29,40,57))
    labels=("Original P0","P1 source-only","P1 + See-through PSD underpaint",
            "Original reference","P1 eye +10 px","PSD underpaint eye +10 px")
    draw=ImageDraw.Draw(board)
    for i,img in enumerate((src_ref,baseline,rebuilt,src_ref,old_eye,new_eye)):
        dest=Image.new("RGBA",(600,600),(46,61,79,255))
        dest.alpha_composite(pctimg(img).resize((600,600),Image.Resampling.LANCZOS))
        x=(i%3)*640+20;y=(i//3)*640+20
        board.paste(dest.convert("RGB"),(x,y))
        draw.text((x,y+605),labels[i],fill="white")
    board.save(out/"p0-psd-underpaint-review.jpg",quality=91)
    fringe_board=Image.new("RGB",(3*640,640),(29,40,57))
    fringe_draw=ImageDraw.Draw(fringe_board)
    for idx,(label,img) in enumerate((
        ("Original P0",src_ref),
        ("P1 fringe +16px",fringe_original),
        ("See-through fringe +16px",fringe_inferred))):
        background=Image.new("RGBA",(600,600),(46,61,79,255))
        background.alpha_composite(pctimg(img).resize((600,600),Image.Resampling.LANCZOS))
        fringe_board.paste(background.convert("RGB"),(idx*640+20,20))
        fringe_draw.text((idx*640+20,625),label,fill="white")
    fringe_board.save(out/"p0-fringe-motion-review.jpg",quality=92)
    qa={
      "schema":"KOMA-P0-SEE-THROUGH-ARTMESH-INTEGRATION-QA-V1",
      "characterId":"p0_character_001",
      "sourceApprovedHeroOriginalSHAverified":False,
      "referenceWholeSha256":sha(root/"p1-front/diagnostics/front-reference.png"),
      "inferencePSDSHA256":model_manifest["psdSHA256"],
      "sourceModelResolution":[768,768],"registeredCanvas":[1024,1024],
      "layerCount":len(records),"modelSourceRoles":[p["semanticCandidateId"] for p in model_manifest["layers"]],
      "inferredUnderpaintPixels":sum(p["additionalInferredNativePixels"] for p in records),
      "parts":records,
      "metrics":{
       "originalStaticSilhouetteIoU":round(iou,6),
       "staticPixelsDifferentMoreThanOne":changed,
       "staticOpaqueHoles":holes,
       "nearEyeMotionDxPx":10,
       "nearEyeMotionOpaqueHoles":motion_holes,
       "fringeMoveDxPx":16,
       "sourceFringeMotionOpaqueHoles":original_fringe_holes,
       "inferredFringeMotionOpaqueHoles":inferred_fringe_holes,
       "inferredFringePreviouslyTransparentRestoredPixels":restored_fringe_pixels,
       "sourceCompositeColorMAE":round(float(np.abs(rebuilt.astype(np.float32)-source.astype(np.float32)).mean()),6)
      },
      "status":"PASS_SEMANTIC_LAYER_REGISTRATION",
      "artStatus":"STATIC_AND_EYE_MOTION_REVIEW_CANDIDATE",
      "visualAcceptance":"PENDING",
      "futureAnglesNeedModelUnderpaint":[45,90],
      "physicalEyesAndEarsKeptSeparate":True
    }
    (out/"integration-qa.json").write_text(json.dumps(qa,ensure_ascii=False,indent=2)+"\n")
    (out/"integrated-parts.json").write_text(json.dumps({
        "schema":"KOMA-P0-ARTMESH-MANIFEST-V1","characterId":"p0_character_001",
        "canvas":[1024,1024],"yaw":0,"parts":records,
        "referenceImage":{"path":"front-source.png","sha256":sha(out/"front-source.png")}},ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:qa[k] for k in ("layerCount","inferredUnderpaintPixels","metrics","artStatus")},
                     ensure_ascii=False,indent=2))
    return qa

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",required=True)
    parser.add_argument("--exported",required=True)
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    run(args.root,args.exported,args.out)

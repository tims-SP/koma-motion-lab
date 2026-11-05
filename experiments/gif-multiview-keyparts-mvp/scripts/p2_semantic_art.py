#!/usr/bin/env python3
"""Create registered 45° and 90° P0 RGBA ArtMesh candidates from verified GIF art.

Source RGB pixels are taken from the recovered whole views. Geometry behind
occluders is reconstructed from recovered semantic GIFs and is explicitly
marked as a candidate. Camera/semantic ID/mesh vertices are shared with P1.
"""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from p1_front_semantic import (
    NATIVE,CANVAS,SEMANTIC,DEPTH,PHYSICAL,
    sha,load,make_ellipse,semantic_anchors,mesh_points,alpha_over,rescale_visible,
    realpart_bbox
)

ANGLES = (45,90)
ANATOMY = {
    45: {
      "face":[[221,159],[250,158],[281,166],[309,180],[334,224],
              [325,248],[291,283],[253,296],[224,279],[203,253],
              [193,225],[203,188]],
      "eyes":{"eye.near":((230,196),(42,28)),
              "eye.far":((310,196),(34,28))},
      "ears":{"ear.near":((189,237),(23,31)),"ear.far":None},
      "nose":((286,239),(9,14)),
      "mouth":((270,264),(16,7)),
      "clip":((331,144),(22,21)),
      "faceTransform":(.76,137,70),
      "hairTransform":(.90,24,24)
    },
    90: {
      "face":[[278,160],[308,166],[331,180],[348,202],[364,219],
              [369,233],[354,247],[348,261],[326,283],[298,282],
              [269,272],[243,248],[241,210],[256,178]],
      "eyes":{"eye.near":((292,193),(41,28)),"eye.far":None},
      "ears":{"ear.near":((225,226),(22,33)),"ear.far":None},
      "nose":((332,232),(12,15)),
      "mouth":((320,260),(13,7)),
      "clip":None,
      "faceTransform":(.76,160,70),
      "hairTransform":(.90,28,25)
    }
}
SOURCE_GROUPS={
 "face.skin":("face_15","face.skin","gifs/face.gif"),
 "eye.near":("face_15","eye.near","gifs/face.gif"),
 "eye.far":("face_15","eye.near","gifs/face.gif"),
 "ear.near":("face_15","ear.near","gifs/face.gif"),
 "ear.far":("face_15","ear.near","gifs/face.gif"),
 "nose":("face_15","nose","gifs/face.gif"),
 "mouth":("face_15","mouth","gifs/face.gif"),
 "hair.front":("hair_9","hair.front","gifs/hair.gif"),
 "hair.side":("hair_9","hair.side","gifs/hair.gif"),
 "hair.back":("hair_9","hair.back","gifs/hair.gif")
}

def warp(src,transform):
    scale,dx,dy=transform
    mat=np.float32([[scale,0,dx],[0,scale,dy]])
    return cv2.warpAffine(src,mat,(NATIVE,NATIVE),flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))

def source_underpaint(root,yaw,key):
    if key not in SOURCE_GROUPS:return None
    group,old_name,_=SOURCE_GROUPS[key]
    source=load(root/f"recovered-review/frames/{group}/yaw{yaw:03d}_{old_name}.png")
    cfg=ANATOMY[yaw]
    if key=="face.skin":
        ears=load(root/f"recovered-review/frames/face_15/yaw{yaw:03d}_ear.near.png")
        gone=cv2.dilate((ears[:,:,3]>12).astype(np.uint8),
                        np.ones((5,5),np.uint8),iterations=1)>0
        source[gone]=0
    if group=="hair_9":
        source[:70,:]=0
        if key=="hair.front":
            hsv=cv2.cvtColor(source[:,:,:3],cv2.COLOR_RGB2HSV)
            gold=((hsv[:,:,0]>=8)&(hsv[:,:,0]<=40)&
                  (hsv[:,:,1]>=65)&(source[:,:,3]>12)).astype(np.uint8)
            gold[:,:175]=0;gold[315:,:]=0
            gold=cv2.dilate(gold,np.ones((9,9),np.uint8),iterations=1)
            if gold.any():source[:,:,:3]=cv2.inpaint(source[:,:,:3],gold,4,cv2.INPAINT_TELEA)
    mat=cfg["faceTransform"] if group=="face_15" else cfg["hairTransform"]
    if key in ("eye.near","eye.far"):
        split=272 if yaw==45 else 443
        if key=="eye.near":source[:,split:]=0
        else:source[:,:split]=0
    if key in ("ear.near","ear.far") and yaw==90 and key=="ear.far":
        source[:]=0
    a=warp(source,mat)
    if key=="face.skin":
        known=a[:,:,3]>=220
        yy,xx=np.indices((NATIVE,NATIVE))
        sample=known&(yy>213)&(yy<268)&(xx>235)&(xx<325)
        pixels=a[:,:,:3][sample]
        if len(pixels)>60:
            tone=np.median(pixels,axis=0).astype(np.uint8)
            for value in cfg["eyes"].values():
                if value is None: continue
                center,shape=value
                zone=make_ellipse(center,(shape[0]+7,shape[1]+7))
                missing=zone&(a[:,:,3]<255)
                a[missing,:3]=tone
                a[missing,3]=255
    return a

def assign_ownership(src,yaw):
    conf=ANATOMY[yaw]
    yy,xx=np.indices((NATIVE,NATIVE))
    a=src[:,:,3]>0
    hsv=cv2.cvtColor(src[:,:,:3],cv2.COLOR_RGB2HSV)
    pink=(hsv[:,:,0]>=142)&(hsv[:,:,0]<=179)&(hsv[:,:,1]>=30)&(hsv[:,:,2]>=65)
    hair=cv2.dilate((pink&(yy<345)).astype(np.uint8),np.ones((5,5),np.uint8))>0
    own=np.full((NATIVE,NATIVE),DEPTH["body.reference"],np.uint8)
    own[(yy<313)&a]=DEPTH["hair.back"]
    facemask=np.zeros((NATIVE,NATIVE),np.uint8)
    cv2.fillPoly(facemask,[np.array(conf["face"],dtype=np.int32)],255)
    own[(facemask>0)&a]=DEPTH["face.skin"]
    own[hair&(yy<325)&a]=DEPTH["hair.back"]
    front=hair & ((yy<180)&(xx>175)) | (hair&(yy>=180)&(yy<255)&(xx>215))
    front&=a
    side=hair & (yy>=165)&(yy<335)&(xx<(218 if yaw==45 else 257))
    own[side&a]=DEPTH["hair.side"]
    own[front&a]=DEPTH["hair.front"]
    for name,semantic in (("ear.near","ear.near"),("ear.far","ear.far"),
                          ("eye.near","eye.near"),("eye.far","eye.far")):
        spec=conf["ears"].get(name) if semantic.startswith("ear.") else conf["eyes"].get(name)
        if spec is None:continue
        center,axes=spec
        mask=make_ellipse(center,axes)&a
        if semantic.startswith("eye."):
            mask&=(yy>168)&(yy<232)
        else:
            mask&=(yy>196)&(yy<283)&~(pink&(hsv[:,:,2]>160))
        own[mask]=DEPTH[semantic]
    own[make_ellipse(*conf["nose"])&a&~pink]=DEPTH["nose"]
    own[make_ellipse(*conf["mouth"])&a&~pink]=DEPTH["mouth"]
    if conf["clip"] is not None:
        hsv=cv2.cvtColor(src[:,:,:3],cv2.COLOR_RGB2HSV)
        gold=(hsv[:,:,0]>=8)&(hsv[:,:,0]<=40)&(hsv[:,:,1]>65)&(hsv[:,:,2]>95)
        clip=make_ellipse(*conf["clip"])&gold&a
        clip=cv2.dilate(clip.astype(np.uint8),np.ones((4,4),np.uint8))>0
        own[clip&a]=DEPTH["hair.clip.cross_gold"]
    loop=(yy<65)&(xx>125)&(xx<345)&a&pink
    # The loop is not the entire crown: retain true crown texture in front hair.
    loop&=((yy<39) | ((yy<64)&(xx>211)&(xx<277)))
    own[loop]=DEPTH["hair.ahoge"]
    own[~a]=255
    return own

def build(root):
    root=Path(root).resolve()
    output=root/"p2-views"
    output.mkdir(exist_ok=True)
    source_sha=sha(root/"whole/head-turn-8view.gif")
    source_gifs={path:sha(root/path) for path in ("gifs/face.gif","gifs/hair.gif")}
    sha_map={}
    reports={}
    manifest=[]
    whole_views=[]
    for yaw in ANGLES:
        original=load(root/f"recovered-review/frames/head_8/yaw{yaw:03d}_whole.png")
        original[original[:,:,3]==0]=0
        high=rescale_visible(original)
        own=assign_ownership(original,yaw)
        owner_high=cv2.resize(own,(CANVAS,CANVAS),interpolation=cv2.INTER_NEAREST)
        owner_high[(owner_high==255)&(high[:,:,3]>0)]=DEPTH["hair.back"]
        owner_high[high[:,:,3]==0]=255
        p2all=np.zeros_like(high)
        regs={}
        records=[]
        for semantic in SEMANTIC:
            near=source_underpaint(root,yaw,semantic)
            entry=DEPTH[semantic]
            px=np.zeros_like(high)
            keep=owner_high==entry
            px[keep]=high[keep]
            hidden_pixels=0
            if near is not None:
                visible_low=own==entry
                under=(own!=255)&(own!=entry)&(own>entry)&(original[:,:,3]==255)
                under&=near[:,:,3]>12
                if not semantic=="face.skin":
                    expanded=cv2.dilate(visible_low.astype(np.uint8),
                                        cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(31,31)))>0
                    under&=expanded
                if not visible_low.any():under[:]=False
                expanded_mask=cv2.resize(under.astype(np.uint8),(CANVAS,CANVAS),
                                         interpolation=cv2.INTER_NEAREST)>0
                expanded_mask&=(owner_high>entry)&(owner_high!=255)
                expanded_mask&=(high[:,:,3]==255)
                draft=rescale_visible(near)
                px[expanded_mask]=draft[expanded_mask]
                hidden_pixels=int(under.sum())
            if semantic=="hair.front" and yaw==45:
                clip_region=(own==DEPTH["hair.clip.cross_gold"]).astype(np.uint8)
                if clip_region.any():
                    colored=cv2.inpaint(original[:,:,:3],
                            cv2.dilate(clip_region,np.ones((5,5),np.uint8)),
                            4,cv2.INPAINT_TELEA)
                    colored=cv2.resize(colored,(CANVAS,CANVAS),
                                        interpolation=cv2.INTER_LINEAR)
                    behind=(owner_high==DEPTH["hair.clip.cross_gold"])&(
                            high[:,:,3]==255)
                    px[behind,:3]=colored[behind];px[behind,3]=255
            path=output/f"parts/yaw{yaw:03d}/{semantic}.png"
            path.parent.mkdir(parents=True,exist_ok=True)
            Image.fromarray(px,"RGBA").save(path)
            bb=realpart_bbox(px)
            flags={"yawDeg":yaw,"semanticId":semantic,
                   "visibility":"visible" if bb else "hidden",
                   "anatomicalSide":PHYSICAL.get(semantic),
                   "path":str(path.relative_to(root)),
                   "sourceGif":"whole/head-turn-8view.gif","sourceGifSha256":source_sha,
                   "sourceRole":"P0_recovered_45_90_GIF_visible_pixels_and_registered_underpaint",
                   "frameIndex":1 if yaw==45 else 2,
                   "frameSha256":sha(path),
                   "depthOrder":entry,"occludes":[],
                   "bbox":bb,"underpaintNativePixels":hidden_pixels,
                   "mesh":mesh_points(bb if bb else [450,430,530,510]),
                   "anchors":semantic_anchors(semantic,bb if bb else [450,430,530,510]),
                   "semanticReviewed":False,"visualReviewed":False}
            manifest.append(flags)
            records.append(flags)
            # Compare compositing over source output with alpha-only.
            p2all=alpha_over(p2all,px)
            regs[semantic]={"visible":bool(bb),"hiddenUnderpaint":hidden_pixels}
        out_src=output/f"whole/yaw{yaw:03d}.png"
        out_src.parent.mkdir(parents=True,exist_ok=True)
        Image.fromarray(high,"RGBA").save(out_src)
        whole_views.append({"yawDeg":yaw,"path":str(out_src.relative_to(root)),
                            "sha256":sha(out_src)})
        error=np.abs(p2all.astype(np.int16)-high.astype(np.int16))
        a=high[:,:,3]>32;b=p2all[:,:,3]>32
        iou=int((a&b).sum())/max(1,int((a|b).sum()))
        reports[str(yaw)]={"registeredParts":len(records),
                           "visibleParts":sum(p["visibility"]=="visible" for p in records),
                           "originalSourceRasterSHA256":sha(root/f"recovered-review/frames/head_8/yaw{yaw:03d}_whole.png"),
                           "compositePixelDiff":int(np.any(error>1,axis=2).sum()),
                           "channelMAE":round(float(error.mean()),6),
                           "silhouetteIoU":round(iou,6),
                           "transparentHoles":int(((high[:,:,3]>=250)&(p2all[:,:,3]<245)).sum()),
                           "physicalHidden":{p["semanticId"]:p["visibility"] for p in records if p["visibility"]=="hidden"},
                           "sourceDerivedHiddenArtPixels":regs}
        debug=output/f"diagnostics/yaw{yaw:03d}-composite.png"
        debug.parent.mkdir(parents=True,exist_ok=True)
        Image.fromarray(p2all,"RGBA").save(debug)
        comparison=Image.new("RGBA",(CANVAS*2,CANVAS),(35,49,64,255))
        comparison.alpha_composite(Image.fromarray(high,"RGBA"),(0,0))
        comparison.alpha_composite(Image.fromarray(p2all,"RGBA"),(CANVAS,0))
        comparison.save(output/f"diagnostics/yaw{yaw:03d}-pair.png")
    manifest_doc={"schema":"KOMA-P0-ARTMESH-MANIFEST-V1",
       "characterId":"p0_character_001","canvas":[CANVAS,CANVAS],
       "viewAngles":list(ANGLES),"wholeViews":whole_views,"parts":manifest,
       "sourceStatus":"REAL_SOURCE_45_90_CANDIDATE",
       "sourceApprovedHeroSHAverified":False,
       "occludedArtStatus":"SOURCE_GIF_UNDERPAINT_CANDIDATE",
       "visualReviewStatus":"REQUIRES_ART_REVIEW"}
    qa={"schema":"KOMA-P0-P2-INDEPENDENT-VIEW-RECONSTRUCTION-QA-V1",
        "characterId":"p0_character_001",
        "sourceWholeGifSHA256":source_sha,
        "sourceIndependentGifSHA256":source_gifs,
        "sourceViews":reports,
        "registeredSlots":len(manifest),
        "visibility90Clip":next(p["visibility"] for p in manifest if p["yawDeg"]==90 and p["semanticId"]=="hair.clip.cross_gold"),
        "visualStatus":"P2_INDEPENDENT_PART_ART_REVIEW_PENDING"}
    (output/"parts.json").write_text(json.dumps(manifest_doc,indent=2,ensure_ascii=False)+"\n")
    (output/"reconstruction-qa.json").write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"registeredSlots":qa["registeredSlots"],
                      "sourceViews":qa["sourceViews"],"visibility90Clip":qa["visibility90Clip"],
                      "visualStatus":qa["visualStatus"]},indent=2,ensure_ascii=False))
    return qa

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",required=True)
    args=parser.parse_args()
    build(args.root)

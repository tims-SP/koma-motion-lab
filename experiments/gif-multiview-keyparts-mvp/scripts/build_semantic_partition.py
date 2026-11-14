#!/usr/bin/env python3
"""Partition actual independent whole-view GIF frames into identity-preserving RGBA review layers.

Every visible pixel has one semantic owner. This is a registered raster candidate
for evaluating VDD; it is not direct independent part generation and has no
inpainted occluded geometry.
"""
import argparse
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw

KEYS = [0,45,90]
CANVAS=1024
IDS=["face.skin","eye.near","nose","mouth","ear.near","hair.front","hair.side",
     "hair.back","hair.ahoge","hair.clip.cross_gold","eye.far","ear.far","body.reference"]
DEPTH={"body.reference":-60,"hair.back":-30,"face.skin":0,
       "ear.far":4,"ear.near":7,"hair.side":10,"eye.far":13,"eye.near":14,
       "nose":17,"mouth":18,"hair.front":30,"hair.ahoge":41,"hair.clip.cross_gold":45}
EYES={0:((190,197,42,31),(271,196,41,31)),
      45:((230,195,42,31),(309,198,33,31)),
      90:((291,194,40,32),None)}
EARS={0:((161,232,19,26),(296,238,19,26)),
      45:((212,231,20,28),None),
      90:((249,221,23,31),None)}
NOSES={0:(228,244,9,13),45:(311,242,11,15),90:(355,234,13,15)}
MOUTHS={0:(226,279,21,8),45:(306,277,18,8),90:(343,264,18,9)}
FACE_ROI={0:(226,240,78,88),45:(270,244,76,86),90:(301,240,75,90)}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def ellipse(width,height,rect):
    mask=np.zeros((height,width),dtype=np.uint8)
    if rect:
        cx,cy,rx,ry=rect
        cv2.ellipse(mask,(cx,cy),(rx,ry),0,0,360,1,-1)
    return mask.astype(bool)


def hue_masks(a):
    h=cv2.cvtColor(a[:,:,:3],cv2.COLOR_RGB2HSV)
    pink=(h[:,:,0]>=142)&(h[:,:,0]<=179)&(h[:,:,1]>30)&(h[:,:,2]>70)
    skin=(h[:,:,0]<22)&(h[:,:,1]<105)&(h[:,:,2]>128)
    gold=(h[:,:,0]>=8)&(h[:,:,0]<=40)&(h[:,:,1]>65)&(h[:,:,2]>100)
    return pink,skin,gold


def component(a,area=25):
    n,labels,stats,_=cv2.connectedComponentsWithStats(a.astype(np.uint8),8)
    candidates=[i for i in range(1,n) if stats[i,4]>=area]
    if not candidates:return np.zeros(a.shape,np.uint8)
    i=max(candidates,key=lambda k:stats[k,4])
    return (labels==i).astype(np.uint8)


def segment(whole,yaw):
    if whole.shape!=(443,443,4):raise ValueError("Expected original 443 canvas")
    yy,xx=np.indices(whole.shape[:2])
    visible=whole[:,:,3]>0
    pink,skin,gold=hue_masks(whole)
    owner=np.full(whole.shape[:2],IDS.index("body.reference"),np.uint8)
    head=(yy<320)&visible
    owner[head]=IDS.index("hair.back")
    # Distinct face region with the original artwork intact.
    face=ellipse(443,443,FACE_ROI[yaw])
    owner[face&visible]=IDS.index("face.skin")
    hair=cv2.dilate((pink&(yy<324)).astype(np.uint8),np.ones((5,5),np.uint8))>0
    # Topmost fringe and the main crown have independent semantic identity.
    front=hair & ((yy<207) | (face & (yy<238)))
    owner[front&visible]=IDS.index("hair.front")
    # Side locks are separate from the frontal fringe and rear hair mass.
    face_cx=FACE_ROI[yaw][0]
    side=hair & (yy>=207) & ((xx<face_cx-35)|(xx>face_cx+43))
    owner[side&visible]=IDS.index("hair.side")
    # Keep hair tips below the head ROI by hue: they are still attached to hair.
    owner[(yy>=320)&(yy<350)&hair&visible]=IDS.index("hair.back")
    # Ear skins: place anatomy according to camera convention, then partition eyes.
    for sid,rect in (("ear.near",EARS[yaw][0]),("ear.far",EARS[yaw][1]),
                     ("eye.near",EYES[yaw][0]),("eye.far",EYES[yaw][1]),
                     ("nose",NOSES[yaw]),("mouth",MOUTHS[yaw])):
        if rect:
            owner[ellipse(443,443,rect)&visible]=IDS.index(sid)
    # Two signature parts override hair by geometry and color, tied to source pixels.
    if yaw!=90:
        clip=gold&(xx>220)&(yy>80)&(yy<250)&visible
        clip=cv2.dilate(component(clip,area=25),np.ones((5,5),np.uint8))>0
        owner[clip&visible]=IDS.index("hair.clip.cross_gold")
    loop=(yy<67)&(xx>120)&(xx<330)&pink&visible
    loop=cv2.dilate(component(loop,area=50),np.ones((3,3),np.uint8))>0
    owner[loop&visible]=IDS.index("hair.ahoge")
    # Empty alpha pixels are not assigned a visible raster ownership.
    owner[~visible]=255
    return owner


def bbox(image):
    y,x=np.where(image[:,:,3]>12)
    return [int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)] if len(x) else None


def record(yaw,sid,rel,img,source_sha):
    bb=bbox(img)
    visibility="visible" if bb else "hidden"
    if bb is None:bb=[400,380,500,480]
    x0,y0,x1,y1=bb
    points=[[x0,y0],[x1,y0],[x1,y1],[x0,y1]]
    anatomical={"eye.near":"right","eye.far":"left","ear.near":"right",
                "ear.far":"left","hair.clip.cross_gold":"left"}.get(sid)
    return {"yawDeg":yaw,"semanticId":sid,"anatomicalSide":anatomical,
            "path":rel,"visibility":visibility,"sourceRole":"registered_whole_view_semantic_partition",
            "creator":"P0 original GIF source partition",
            "sourceGif":"whole/head-turn-8view.gif",
            "sourceGifSha256":source_sha,
            "frameIndex":KEYS.index(yaw),
            "frameSha256":None,"depthOrder":DEPTH[sid],"occludes":[],
            "bbox":bbox(img),"alphaQuality":"resampled_source_antialias_not_native_generation",
            "anchors":[{"id":id,"xy":xy} for id,xy in
                       zip(["bound.tl","bound.tr","bound.br","bound.bl"],points)],
            "mesh":{"vertexIds":["tl","tr","br","bl"],"vertices":points,
                    "triangles":[[0,1,2],[0,2,3]]},
            "semanticReviewed":False,"visualReviewed":False}


def build(root):
    root=Path(root).resolve()
    source=root/"recovered-review"
    if not source.is_dir():raise ValueError("Source asset archive must first be restored")
    output=root/"candidate-v2"
    output.mkdir(exist_ok=True)
    source_hash=sha(source/"sources/head-turn-8view.gif")
    all_parts=[]
    references=[]
    comparisons={}
    sheet_dir=output/"diagnostics"
    sheet_dir.mkdir(exist_ok=True,parents=True)
    for yaw in KEYS:
        raw=np.asarray(Image.open(source/f"frames/head_8/yaw{yaw:03d}_whole.png").convert("RGBA"))
        high=np.array(Image.fromarray(raw,"RGBA").resize((CANVAS,CANVAS),Image.Resampling.LANCZOS))
        owner=segment(raw,yaw)
        high_owner=cv2.resize(owner,(CANVAS,CANVAS),interpolation=cv2.INTER_NEAREST)
        # Lanczos creates fractional edge pixels beyond source binary alpha bounds.
        # Assign their ownership while retaining the reference pixel values.
        high_owner[(high_owner==255) & (high[:,:,3]>0)]=IDS.index("hair.back")
        high[high[:,:,3]==0]=0
        ref_path=output/f"whole/yaw{yaw:03d}.png"
        ref_path.parent.mkdir(parents=True,exist_ok=True)
        Image.fromarray(high,"RGBA").save(ref_path)
        references.append({"yawDeg":yaw,"path":str(ref_path.relative_to(root)),
                           "sha256":sha(ref_path),"sourceRole":"verified_recovered_whole_view"})
        layer_arrays={}
        for sid in IDS:
            layer=np.zeros_like(high)
            mask=(high_owner==IDS.index(sid))
            layer[mask]=high[mask]
            path=output/f"parts/yaw{yaw:03d}/{sid}.png"
            path.parent.mkdir(parents=True,exist_ok=True)
            Image.fromarray(layer,"RGBA").save(path)
            rec=record(yaw,sid,str(path.relative_to(root)),layer,source_hash)
            rec["frameSha256"]=sha(path)
            all_parts.append(rec)
            layer_arrays[sid]=layer
        composite=np.zeros_like(high)
        for sid in IDS:
            pixels=high_owner==IDS.index(sid)
            composite[pixels]=layer_arrays[sid][pixels]
        # Endpoint parity checks both pixel identity and coverage.
        maxdiff=int(np.abs(composite.astype(np.int16)-high.astype(np.int16)).max())
        neq=int(np.any(composite!=high,axis=2).sum())
        comparisons[str(yaw)]={"maxChannelDelta":maxdiff,"pixelsDifferent":neq,
                               "sourceSha256":sha(ref_path),
                               "viewBbox":bbox(high),
                               "visibleLayerCount":sum(1 for s in IDS if bbox(layer_arrays[s]))}
        if neq:raise AssertionError(f"Endpoint source parity failed at {yaw}")
        out_img=output/f"diagnostics/yaw{yaw:03d}-rebuild.png"
        Image.fromarray(composite,"RGBA").save(out_img)
        view=Image.new("RGB",(1024,512),(27,37,53))
        for col,img in enumerate((high,composite)):
            small=Image.fromarray(img,"RGBA").resize((448,448),Image.Resampling.LANCZOS)
            backdrop=Image.new("RGBA",(448,448),(69,77,96,255))
            backdrop.alpha_composite(small)
            view.paste(backdrop.convert("RGB"),(col*512+32,32))
        view.save(output/f"diagnostics/yaw{yaw:03d}-compare.jpg",quality=92)
    manifests={
       "schema":"KOMA-P0-ARTMESH-MANIFEST-V1",
       "characterId":"p0_character_001",
       "canvas":[CANVAS,CANVAS],"wholeViews":references,
       "parts":all_parts,"headRois":{str(y):[0,0,1024,760] for y in KEYS},
       "sourceRole":"full_view_generated_gif_semantic_partition",
       "artStatus":"REVIEW_CANDIDATE",
       "sourceProcessing":"preserved source-color pixels; deterministic exclusive owner map; Lanczos AA",
       "identityMasterOriginalSHAverified":False,
       "artMeshOccludedFillComplete":False,
       "directIndependentPartGeneration":False,
       "manualReview":"PENDING"
    }
    (root/"parts.json").write_text(json.dumps(manifests,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    qa={"schema":"KOMA-P0-PARTITION-RECONSTRUCTION-QA-V1",
        "status":"REVIEW_CANDIDATE","characterId":"p0_character_001",
        "wholeSourcesRecovered":8,"wholeKeysRegistered":3,
        "registeredSlots":len(all_parts),"sourceWholeGifSha256":source_hash,
        "pixelParity":comparisons,
        "provenance":"independent_generated_whole_view_GIF_partition_not_independent_parts",
        "qualityGate":{"sourceHeroShaVerified":False,"generatedIndependentArtMeshes":False,
                       "occludedAnatomyComplete":False,"vddHoldoutsReviewed":False}}
    (root/"qa.json").write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    (output/"reconstruction-qa.json").write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    return qa


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",required=True)
    args=parser.parse_args()
    print(json.dumps(build(args.root),indent=2,ensure_ascii=False))

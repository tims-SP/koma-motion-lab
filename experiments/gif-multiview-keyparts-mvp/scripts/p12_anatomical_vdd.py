#!/usr/bin/env python3
"""P12 original P0 anatomical registration and stroke-local VDD comparison.

Leverages P8 original RGBA ArtMeshes, P5 anatomical 3D-anchor projections,
P10 high-confidence source stroke hypotheses, and P11 real profile PSD.

Every preview reuses the approved source PNGs. A candidate is adopted only
after independent raster, temporal and visual evaluation.
"""
import argparse, json, hashlib
from pathlib import Path
import numpy as np
import cv2
import p8_semantic_occlusion as p8

DETAIL_ANCHORS={"eye.near.iris","eye.far.iris","nose","mouth","ear.near","ear.far"}
DETAIL_PARTS={"eye.near","eye.far","nose","mouth","ear.near","ear.far"}
HAIR_PARTS={"hair.front","hair.side","hair.back","hair.ahoge"}

def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for x in iter(lambda:f.read(1024*1024),b""):h.update(x)
 return h.hexdigest()

def run(root,out,angles,mode):
 root=Path(root).resolve();out=Path(out).resolve()
 origin= root/"p5-see-through/mv-candidate/parts.json"
 trackfile=root/"p5-see-through/mv-candidate/landmark-qa.json"
 matchfile=root/"p10-stroke-identity/qa.json"
 psdfile=root/"p11-profile-psd/yaw090/qa.json"
 strokes=json.loads(matchfile.read_text(encoding="utf8"))
 psd=json.loads(psdfile.read_text(encoding="utf8"))
 registry=json.loads(origin.read_text(encoding="utf8"))
 assert all(x["characterId"]=="p0_character_001" for x in (strokes,psd,registry))
 assert psd["nativeLayerCount"]==13 and psd["sourceReconstructionPixelExact"]
 assert sha(root/psd["psdPath"])==psd["psdSHA256"]
 assert strokes["sourceRegistrySHA256"]==sha(origin)
 original_guidance=p8.residual_guidance
 original_tracked=p8.tracked
 involved={}
 def tracks(landmarks,role,a,b):
  anchors=original_tracked(landmarks,role,a,b)
  if mode not in ("anatomy-strokes","stroke-wide") or role not in HAIR_PARTS:
   return anchors
  pair=strokes["pairs"].get(f"{a}-{b}/{role}")
  if pair is None:return anchors
  candidates=[]
  for item in pair["accepted"]:
   if item["physicalResidual"]>24:continue
   if item["confidence"]<0.46:continue
   if mode=="anatomy-strokes" and item["confidence"]<0.56:continue
   pos=np.asarray(item["sourceXY"],np.float32)
   dst=np.asarray(item["targetXY"],np.float32)
   candidates.append(("P10:"+item["sourceId"],pos,dst))
  involved[f"{a}-{b}/{role}"]=len(candidates)
  return anchors+candidates
 def physical_guidance(flow,anchors,source_alpha,bbox):
  # Single known eyes, nose, mouth and ear anchor: only rigid translation
  # is physically verified across the view pair. An unrelated DIS field
  # can match the iris to an eyelash, generating double irises; suppress
  # this unsupported distortion but keep the original source pixels.
  if len(anchors)==1 and anchors[0][0] in DETAIL_ANCHORS:
   name,a,b=anchors[0]
   disp=(b-a).astype(np.float32)
   mapped=np.empty_like(flow,dtype=np.float32)
   mapped[:]=disp
   return mapped,{"controls":1,"anchorAligned":name,
                  "method":"single-anatomical-feature-direct-translation",
                  "displacementPixels":disp.round(3).tolist(),
                  "radius":0}
  # Preserve a single face-surface geometric transform constrained by
  # multiple verified anatomical landmarks rather than unrelated grayscale
  # flow estimates across different paintings.
  if mode=="affine-face" and len(anchors)>=3 and any(v[0]=="face.chin" for v in anchors):
   aa=np.stack([v[1] for v in anchors]).astype(np.float32)
   bb=np.stack([v[2] for v in anchors]).astype(np.float32)
   M,_=cv2.estimateAffine2D(aa,bb,method=cv2.LMEDS)
   if M is not None and np.isfinite(M).all() and abs(float(np.linalg.det(M[:,:2])))>0.08:
    h,w=flow.shape[:2]
    xx,yy=np.meshgrid(np.arange(w,dtype=np.float32),np.arange(h,dtype=np.float32))
    result=np.empty_like(flow)
    result[:,:,0]=(M[0,0]-1)*xx+M[0,1]*yy+M[0,2]
    result[:,:,1]=M[1,0]*xx+(M[1,1]-1)*yy+M[1,2]
    return result,{"controls":len(anchors),"method":"anatomically-constrained-face-affine",
                   "affineMatrix":np.round(M,3).tolist(),"radius":0}
  return original_guidance(flow,anchors,source_alpha,bbox)
 p8.tracked=tracks
 p8.residual_guidance=physical_guidance
 try:
  data=p8.render(root,out,angles,mode="confidence",publish_layers=True)
 finally:
  p8.tracked=original_tracked
  p8.residual_guidance=original_guidance
 data["schema"]="KOMA-P0-P12-ANATOMICAL-STROKE-REGISTRATION-V1"
 data["sourceStrokesSHA256"]=sha(matchfile)
 data["sourceProfilePSD_SHA256"]=psd["psdSHA256"]
 data["mode"]=mode
 data["geometry"]="P8 original DIS layers with P5 feature direct anchor correspondence and optional P10 stroke hypotheses"
 data["localStrokeCandidatesUsed"]=involved
 data["anatomicalDirectAlignment"]=sorted(DETAIL_PARTS)
 data["textureAcceptance"]="PENDING_RASTER_AND_ARTISTIC_CHECK"
 (Path(out)/"qa.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"status":"P12_ANATOMICAL_ORIGINAL_P0_RENDERED",
  "mode":mode,"frameCount":data["frameCount"],
  "strokeAnchorsUsed":sum(involved.values()),
  "profilePSDVerified":True,"keyFrames":[0,45,90]},indent=2))
 return data

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--root",required=True)
 p.add_argument("--out",required=True)
 p.add_argument("--mode",choices=["anatomy","anatomy-strokes","stroke-wide","affine-face"],default="anatomy")
 p.add_argument("--angles",default="0,22.5,45,67.5,72.5,90")
 a=p.parse_args()
 run(a.root,a.out,[float(x) for x in a.angles.split(",")],a.mode)

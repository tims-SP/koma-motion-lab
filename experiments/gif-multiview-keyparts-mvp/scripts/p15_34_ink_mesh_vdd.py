#!/usr/bin/env python3
"""P15-34 pigment-observed feature constraints on 2D P0 role meshes.

Keeps P15-33 source keyframe bytes and other ten role images unchanged.
Feature coordinates come from registered painted pixels, not alpha quantiles.
These remain automatically detected, artist-unapproved observations.
"""
from __future__ import annotations
import hashlib,json,shutil
from pathlib import Path
import numpy as np
from PIL import Image
from p15_32_mesh_vdd import R,P,ANGLES,ROLES,slug,read,write,blend,over,flow_pair,bounds
from p15_33_anchor_constraints import constrained_warp

OBS=R/"evidence/p15-34-ink-landmarks-qa.json"
BASE=R/"evidence/p15-31-native-vdd-qa.json"
SRC=P/"p15-31-per-role-vdd"
REF=P/"p15-33-anchor-mesh"
OUT=P/"p15-34-feature-mesh"
QA=R/"evidence/p15-34-feature-mesh-qa.json"

def sha(path):
 return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def make():
 observed=json.loads(OBS.read_text())
 baseline=json.loads(BASE.read_text())
 if observed["characterId"]!=baseline["characterId"] or baseline["characterId"]!="p0_character_001":
  raise AssertionError("Role source identity changed")
 if observed["verifiedIndependentArtistLandmarks"]!=0:
  raise AssertionError("Candidate observation gate changed")
 feature_lookup={f["yaw"]:f["features"] for f in observed["frames"]}
 records=[]
 for yaw in ANGLES:
  name=slug(yaw);source=REF/name;folder=OUT/name;folder.mkdir(parents=True,exist_ok=True)
  entries=next(x["parts"] for x in baseline["frames"] if x["yaw"]==yaw)
  for row in entries:shutil.copy2(source/(row["role"]+".png"),folder/(row["role"]+".png"))
  shutil.copy2(source/"composite.png",folder/"composite.png")
  records.append({"yaw":yaw,"kind":"exact-source-keyframe",
    "roles":len(entries),"sha256":sha(folder/"composite.png"),"keyframeExact":True})
 for lower,upper in zip(ANGLES[:-1],ANGLES[1:]):
  yaw=(lower+upper)/2.;name=slug(yaw);folder=OUT/name;folder.mkdir(parents=True,exist_ok=True)
  entries=next(x["parts"] for x in baseline["frames"] if x["yaw"]==lower)
  diagnostics={};clip_attach={}
  for part in entries:
   role=part["role"]
   if role not in ROLES:
    shutil.copy2(REF/name/(role+".png"),folder/(role+".png"))
  for role in ROLES:
   lpath=SRC/slug(lower)/(role+".png")
   rpath=SRC/slug(upper)/(role+".png")
   left=read(lpath);right=read(rpath)
   l=feature_lookup[lower][role];r=feature_lookup[upper][role]
   if l["sourceSHA256"]!=sha(lpath) or r["sourceSHA256"]!=sha(rpath):
    raise AssertionError("Recorded role painting source SHA changed")
   if l["featureNames"]!=r["featureNames"]:
    raise AssertionError("Painted feature identity mismatch")
   lp=np.array(l["points443"],np.float32);rp=np.array(r["points443"],np.float32)
   target=(lp+rp)*.5
   fw,bw=flow_pair(left,right)
   box=bounds(left,right)
   leftw,leftdiag=constrained_warp(left,fw,box,lp,target)
   rightw,rightdiag=constrained_warp(right,bw,box,rp,target)
   for check in (leftdiag,rightdiag):
    if check["triangleFlips"] or check["minAreaRatio"]<.28:
     raise AssertionError(f"Mesh topology invalid at {yaw} role {role}: {check}")
    if check["maxConstraintResidualPx"]>1.8:
     raise AssertionError(f"Ink tracking residual invalid at {yaw} role {role}")
   output=blend(leftw,rightw)
   write(folder/(role+".png"),output)
   old=read(REF/name/(role+".png"))
   diff=int(np.count_nonzero(np.any(output!=old,axis=2)))
   diagnostics[role]={
    "featureNames":l["featureNames"],"featureCount":len(lp),
    "target443":np.round(target,3).tolist(),
    "sourceLeftSHA256":l["sourceSHA256"],
    "sourceRightSHA256":r["sourceSHA256"],
    "sourceLocationAuthority":"visible source pigment/contour candidates",
    "artistApproved":False,"left":leftdiag,"right":rightdiag,
    "changedPixelsVsP15_33":diff,
    "sha256":sha(folder/(role+".png"))}
  canvas=np.zeros((443,443,4),np.uint8)
  for row in sorted(entries,key=lambda r:r["depthOrder"]):
   canvas=over(canvas,read(folder/(row["role"]+".png")))
  write(folder/"composite-native.png",canvas)
  image=Image.fromarray(canvas,"RGBA").resize((1024,1024),Image.Resampling.LANCZOS)
  image.save(folder/"composite.png")
  old=np.asarray(Image.open(REF/name/"composite.png").convert("RGBA"))
  changed=int(np.count_nonzero(np.any(np.asarray(image)!=old,axis=2)))
  records.append({"yaw":yaw,"kind":"ink-observed-constrained-mesh",
   "interval":[lower,upper],"sha256":sha(folder/"composite.png"),
   "roleCount":13,"meshDiagnostics":diagnostics,"changedCompositePixelsVsP15_33":changed})
 records.sort(key=lambda x:x["yaw"])
 mids=[f for f in records if f["kind"]=="ink-observed-constrained-mesh"]
 report={
  "schema":"KOMA-P15-34-INK-OBSERVED-CONSTRAINED-MESH-V1",
  "characterId":"p0_character_001","sourceP15_33RoleKeyframesUnchanged":True,
  "sourceFeatureEvidenceSHA256":sha(OBS),
  "sourceP0OriginalSHA256":observed["source45P0SHA256"],
  "angles":[f["yaw"] for f in records],"frames":records,
  "roleCount":13,"meshRoles":ROLES,"grid":[7,7],"trianglesPerMeshRole":72,
  "unmodifiedRoles":10,"keyframes":len(records)-len(mids),
  "midpoints":len(mids),
  "maximumTrackingResidualPx":max(diag[side]["maxConstraintResidualPx"]
       for f in mids for diag in f["meshDiagnostics"].values() for side in ("left","right")),
  "minimumTriangleAreaRatio":min(diag[side]["minAreaRatio"]
       for f in mids for diag in f["meshDiagnostics"].values() for side in ("left","right")),
  "triangleFlips":sum(diag[side]["triangleFlips"]
       for f in mids for diag in f["meshDiagnostics"].values() for side in ("left","right")),
  "physicalFarEyeNoseOcclusionVerified":False,
  "clipPhysicalHairLockMountVerified":False,
  "artistLandmarksApproved":False,
  "newIndependentKeyframePainting":False,
  "productionRendererChanged":False,
  "formalArtisticAcceptance":False,
  "status":"SOURCE_PAINTED_INK_MESH_ENGINEERING_CANDIDATE"}
 QA.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"status":report["status"],"frames":len(records),
  "midpoints":len(mids),"trackingResidual":report["maximumTrackingResidualPx"],
  "triangleFlips":report["triangleFlips"],
  "minTriangleAreaRatio":report["minimumTriangleAreaRatio"],
  "changedCompositePixels":[x["changedCompositePixelsVsP15_33"] for x in mids]}))
 return report
if __name__=="__main__":
 make()

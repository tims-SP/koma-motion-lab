#!/usr/bin/env python3
"""P15-38 extends a registered 13-role P0 ArtMesh arc from 45 to 65 degrees.

The 45° input is an authentic recomposition of the registered P0 source
(Alpha IoU 1), 55–65° retain P15-37 source bytes; three intervening views
use bidirectional premultiplied per-role optical-flow interpolation.
This is a 2.5D engineering candidate, not an artist-approved unseen view.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from p15_32_mesh_vdd import R,P,slug,read,write,over,flow_pair
from p15_35_depth_mount import ROLES
from p15_37_temporal_paint_vdd import premul_mix

CANONICAL=P/"p15-20-canonical-source-views/yaw045"
P0=P/"p2-views/whole/yaw045.png"
PAINTED=P/"p15-37-temporal-artmesh"
OUT=P/"p15-38-p0-registered-arc"
SOURCE_QA=R/"evidence/p15-37-temporal-artmesh-qa.json"
QA=R/"evidence/p15-38-extended-artmesh-qa.json"
P0_SHA="78a08d5f010a8f449efda915a710a2de8958c3b1a32375df491d806fca251e40"
KEYS=[45.,47.5,50.,52.5,55.]
TAIL=[56.25,57.5,58.75,60.,61.25,62.5,63.75,65.]
N=443

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read_45(role):
 source=CANONICAL/(role+".png")
 if not source.is_file():raise FileNotFoundError(source)
 with Image.open(source) as im:
  if im.size!=(1024,1024):raise AssertionError("Canonical 45 role dimensions changed")
  return np.array(im.convert("RGBA").resize((N,N),Image.Resampling.LANCZOS))

def premultiplied_flow_warp(a,flow,scale):
 aa=a.astype(np.float32)
 alpha=aa[:,:,3:4]/255.
 prem=np.concatenate((aa[:,:,:3]*alpha,alpha),axis=2)
 gy,gx=np.indices((N,N),np.float32)
 mx=gx-np.clip(flow[:,:,0],-16,16).astype(np.float32)*scale
 my=gy-np.clip(flow[:,:,1],-16,16).astype(np.float32)*scale
 w=cv2.remap(prem,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,
             borderValue=(0,0,0,0))
 al=np.clip(w[:,:,3:4],0,1)
 rgb=np.divide(w[:,:,:3],al,out=np.zeros_like(w[:,:,:3]),where=al>1e-8)
 return np.uint8(np.clip(np.rint(np.dstack((rgb,al[:,:,0]*255))),0,255))

def flow_blend(a,b,t):
 if np.count_nonzero(a[:,:,3])<5 or np.count_nonzero(b[:,:,3])<5:
  # A disappearing/appearing semantic role has no stable cross-view strokes.
  return premul_mix(a,b,t),{"method":"partial-visibility-alpha-role",
             "forwardMaxFlow":0.,"backwardMaxFlow":0.}
 fw,bw=flow_pair(a,b)
 wa=premultiplied_flow_warp(a,fw,t)
 wb=premultiplied_flow_warp(b,bw,1.-t)
 result=premul_mix(wa,wb,t)
 return result,{"method":"bidirectional-flow-premultiplied-artmesh",
    "forwardMaxFlow":round(float(np.max(np.linalg.norm(fw,axis=2))),5),
    "backwardMaxFlow":round(float(np.max(np.linalg.norm(bw,axis=2))),5),
    "flowClamp":16}

def source_45_composition_qa():
 # P0 original is RGBA, and canonical 45 SVG/PSD-sourced RGBA parts must
 # reconstruct its alpha support. No inferred identity claims.
 comp=np.zeros((1024,1024,4),np.uint8)
 for role in ROLES:
  with Image.open(CANONICAL/(role+".png")) as im:
   comp=over(comp,np.array(im.convert("RGBA")))
 original=read(P0)
 a=original[:,:,3]>16;b=comp[:,:,3]>16
 iou=float((a&b).sum()/max(1,(a|b).sum()))
 err=float(np.abs(original[:,:,:3].astype(np.float32)-
                  comp[:,:,:3].astype(np.float32))[a&b].mean())
 if iou<.9999 or err>.03:raise AssertionError("Registered P0 45 source not pixel-faithful")
 return {"registeredRoleCount":len(ROLES),
     "alphaIoUWithApprovedOriginal":round(iou,8),
     "meanRGBDeltaOnSharedOpaquePixels":round(err,6),
     "sourceP0SHA256":sha(P0)}

def make():
 parent=json.loads(SOURCE_QA.read_text())
 if parent["characterId"]!="p0_character_001" or sha(P0)!=P0_SHA:
  raise AssertionError("P0 original reference changed")
 if parent["fullKeyViewsArtApproved"] or parent["productionVddModified"]:
  raise AssertionError("Source painted art admission differs")
 origin=source_45_composition_qa()
 original={role:read_45(role) for role in ROLES}
 registered={role:read(PAINTED/"yaw55"/(role+".png")) for role in ROLES}
 records=[]
 for yaw in KEYS:
  tag=slug(yaw);dst=OUT/tag;dst.mkdir(parents=True,exist_ok=True)
  roleQA={}
  for role in ROLES:
   src=CANONICAL/(role+".png")
   target=PAINTED/"yaw55"/(role+".png")
   if yaw==45.:
    image=original[role]
    method="P0-canonical-source-normalized-native-443"
   elif yaw==55.:
    image=registered[role]
    method="P15-37-registered-source-byte-exact"
   else:
    image,flow=flow_blend(original[role],registered[role],(yaw-45)/10)
    method=flow["method"]
   file=dst/(role+".png")
   if yaw==55.:file.write_bytes(target.read_bytes())
   else:write(file,image)
   roleQA[role]={"sha256":sha(file),"source45SHA256":sha(src),
        "source55SHA256":sha(target),"method":method,
        "sourceOwner":"P0 canonical 45 then P15-37 55",
        "independentNewKeyframe":False}
  native=np.zeros((N,N,4),np.uint8)
  for role in ROLES:native=over(native,read(dst/(role+".png")))
  write(dst/"composite-native.png",native)
  whole=dst/"composite.png"
  if yaw==45.:whole.write_bytes(P0.read_bytes())
  elif yaw==55.:whole.write_bytes((PAINTED/"yaw55/composite.png").read_bytes())
  else:Image.fromarray(native,"RGBA").resize((1024,1024),Image.Resampling.LANCZOS).save(whole)
  records.append({"yaw":yaw,"kind":"registered-art-source" if yaw==45.
     else "registered-vdd-source" if yaw==55. else "cross-view-role-inbetween",
    "roleCount":13,"roles":roleQA,"compositeSHA256":sha(whole),
    "P0SourceOriginalByteExact":yaw==45.,
    "originalP15_37RoleByteExact":yaw==55.,
    "independentlyPaintedArtApproved":False})
 for yaw in TAIL:
  tag=slug(yaw);source=PAINTED/tag;dst=OUT/tag;dst.mkdir(parents=True,exist_ok=True)
  roleQA={}
  for role in ROLES:
   p=source/(role+".png");q=dst/(role+".png")
   q.write_bytes(p.read_bytes())
   roleQA[role]={"sha256":sha(q),"sourceSHA256":sha(p),
      "sourceOwner":"P15-37 registered view","method":"registered-source-byte-exact"}
  for name in ("composite.png","composite-native.png"):
   (dst/name).write_bytes((source/name).read_bytes())
  records.append({"yaw":yaw,"kind":"registered-vdd-source","roleCount":13,
    "roles":roleQA,"compositeSHA256":sha(dst/"composite.png"),
    "originalP15_37RoleByteExact":True,
    "independentlyPaintedArtApproved":False})
 records.sort(key=lambda r:r["yaw"])
 if len(records)!=13 or [r["yaw"] for r in records]!=KEYS+TAIL:
  raise AssertionError("Incomplete camera arc")
 # Alpha and luma motion diagnostics across 45°–65°: numerical only.
 hops=[]
 for a,b in zip(records,records[1:]):
  left=read(OUT/slug(a["yaw"])/"composite-native.png")
  right=read(OUT/slug(b["yaw"])/"composite-native.png")
  l=left[:,:,3]>16;r=right[:,:,3]>16
  iou=round(float(np.count_nonzero(l&r)/max(1,np.count_nonzero(l|r))),6)
  change=round(float(np.abs(left[:,:,:3].astype(np.float32)-
                        right[:,:,:3].astype(np.float32))[l&r].mean()),6)
  hops.append({"interval":[a["yaw"],b["yaw"]],
     "alphaIoU":iou,"sharedVisibleRGBDelta":change})
 report={"schema":"KOMA-P15-38-ORIGINAL-P0-EXTENDED-ARTMESH-V1",
    "characterId":"p0_character_001","sourceOriginal45":origin,
    "sourceP15_37QA_SHA256":sha(SOURCE_QA),
    "sourceP0HeroSHA256Verified":False,
    "angles":[r["yaw"] for r in records],
    "sourceKeyAngles":[45.,55.,57.5,60.,65.],
    "interpolatedNewAngles":[47.5,50.,52.5],
    "roleCount":len(ROLES),"frames":records,"adjacentMetrics":hops,
    "registeredFull45DegreeOriginalPreserved":True,
    "registeredP15_37NineFramesPreserved":True,
    "fullIndependentArtAdmission":0,"independentHiddenUnderpaintAdmission":0,
    "physical3DTopologyApproved":False,"productionRendererModified":False,
    "status":"REGISTERED_45_TO65_ARTMESH_ENGINEERING_CANDIDATE"}
 QA.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"status":report["status"],"views":len(records),"roles":len(ROLES),
     "P0_45_IoU":origin["alphaIoUWithApprovedOriginal"],
     "newAngles":report["interpolatedNewAngles"],
     "adjacentAlphaIoU":[m["alphaIoU"] for m in hops],
     "adjacentRGB":[m["sharedVisibleRGBDelta"] for m in hops]}))
 return report
if __name__=="__main__":make()

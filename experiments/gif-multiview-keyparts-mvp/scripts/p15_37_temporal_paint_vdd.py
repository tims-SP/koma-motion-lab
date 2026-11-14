#!/usr/bin/env python3
"""P15-37 continuous P0 art-painted role interpolation in the 55–65 yaw arc.

Source-of-truth: P15-35 thirteen RGBA roles at nine poses, P15-36 newly
painted registered local RGB at 57.5/60, P15-12 P5 camera landmarks.
Each preserved native-443 source role and its SHA is independently checked.
Visual quality, unseen underpainting and identity admission remain
separate gates, never inferred from pixel/geometry test scores.
"""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from p15_32_mesh_vdd import R,P,slug,read,write,over
from p15_35_depth_mount import ROLES

BASE=P/"p15-35-occlusion-mount"
NEW=P/"p15-36-qwen-local-paint"
OUT=P/"p15-37-temporal-artmesh"
Q35=R/"evidence/p15-35-occlusion-mount-qa.json"
Q36=R/"evidence/p15-36-qwen-local-repair-qa.json"
QCAM=R/"evidence/p15-12-camera-proxy-qa.json"
QA=R/"evidence/p15-37-temporal-artmesh-qa.json"
N=443
KEYS=(57.5,60.)
ANG=(55.,56.25,57.5,58.75,60.,61.25,62.5,63.75,65.)
PAINT_ROLES=("eye.far","face.skin","hair.front")
UNMODIFIED=tuple(r for r in ROLES if r not in PAINT_ROLES)

def sha(file):
 return hashlib.sha256(Path(file).read_bytes()).hexdigest()

def smooth(t):
 t=float(np.clip(t,0.,1.))
 return t*t*(3-2*t)

def spec(yaw):
 """Normalized weights of actual source drawings, separate from activation."""
 if yaw<=KEYS[0]:
  return {57.5:1.},smooth((yaw-55.)/(KEYS[0]-55.))
 if yaw<KEYS[1]:
  t=(yaw-KEYS[0])/(KEYS[1]-KEYS[0])
  return {57.5:1.-t,60.:t},1.
 return {60.:1.},1.-smooth((yaw-KEYS[1])/(65.-KEYS[1]))

def float_rgba(a):
 x=a.astype(np.float32);alpha=x[:,:,3:4]/255.
 return x[:,:,:3]*alpha,alpha

def premul_mix(a,b,t):
 """RGBA interpolation without black/white halos in transparent pixels."""
 if t<=0:return a.copy()
 if t>=1:return b.copy()
 ca,aa=float_rgba(a);cb,ab=float_rgba(b)
 alpha=aa*(1-t)+ab*t
 prem=ca*(1-t)+cb*t
 rgb=np.divide(prem,alpha,out=np.zeros_like(prem),where=alpha>1e-8)
 return np.uint8(np.clip(np.rint(np.dstack((rgb,alpha[:,:,0]*255))),0,255))

def alpha_weight(a,t):
 x=a.copy()
 x[:,:,3]=np.uint8(np.clip(np.rint(x[:,:,3].astype(np.float32)*t),0,255))
 return x

def interpolate_p5(camera,yaw):
 known=sorted((float(f["yaw"]),f) for f in camera["frames"] if
              f["anchors"]["eye.far.iris"]["xy"] is not None)
 for a,frame in known:
  if abs(a-yaw)<1e-6:return np.array(frame["anchors"]["eye.far.iris"]["xy"],np.float64)*N/1024.
 for (a,fa),(b,fb) in zip(known,known[1:]):
  if a<yaw<b:
   alpha=(yaw-a)/(b-a)
   return ((1-alpha)*np.array(fa["anchors"]["eye.far.iris"]["xy"],np.float64)+
       alpha*np.array(fb["anchors"]["eye.far.iris"]["xy"],np.float64))*N/1024.
 raise ValueError("Unregistered camera interpolation angle: "+str(yaw))

def translate(a,dxy):
 dx,dy=[float(x) for x in dxy]
 if max(abs(dx),abs(dy))>14:raise AssertionError("Unexpected large camera translation")
 return cv2.warpAffine(a,np.array([[1,0,dx],[0,1,dy]],np.float32),(N,N),
   flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))

def painted_patch(role,yaw,camera):
 refs,active=spec(yaw)
 combined=None
 trace=[]
 xy=interpolate_p5(camera,yaw)
 for key,t in refs.items():
  if t<1e-7:continue
  path=NEW/slug(key)/(role+".donor-paint.png")
  if not path.is_file():raise FileNotFoundError(path)
  origin=interpolate_p5(camera,key)
  shifted=translate(read(path),xy-origin)
  if combined is None:combined=shifted.copy()
  else:combined=premul_mix(combined,shifted,t)
  trace.append({"yaw":key,"weight":round(t,6),
                "sourceSHA256":sha(path),"cameraDisplacement443":
                np.round(xy-origin,5).tolist()})
 return combined,active,trace

def paint_frame(yaw,camera,source35,source36):
 key=slug(yaw);folder=OUT/key;folder.mkdir(parents=True,exist_ok=True)
 endpoint=yaw in (55.,65.)
 exact=yaw in KEYS
 roles={}
 witness={}
 for role in ROLES:
  src=BASE/key/(role+".png")
  if not src.is_file():raise FileNotFoundError(src)
  base=read(src)
  if role in UNMODIFIED or endpoint:
   roles[role]=base
   if not exact:(folder/(role+".png")).write_bytes(src.read_bytes())
   method="registered-source-byte-exact"
   trace=[]
  elif exact:
   painted=NEW/key/(role+".png")
   if not painted.is_file():raise FileNotFoundError(painted)
   roles[role]=read(painted)
   (folder/(role+".png")).write_bytes(painted.read_bytes())
   method="registered-painted-keypart-byte-exact"
   trace=[{"yaw":yaw,"sourceSHA256":sha(painted),"weight":1}]
  else:
   patch,active,trace=painted_patch(role,yaw,camera)
   if role=="eye.far":
    roles[role]=premul_mix(base,patch,active)
   else:
    roles[role]=over(base,alpha_weight(patch,active))
   write(folder/(role+".png"),roles[role])
   method="p5-registered-painted-local-interpolation"
  if not (folder/(role+".png")).is_file():
   write(folder/(role+".png"),roles[role])
  witness[role]={"sha256":sha(folder/(role+".png")),
    "sourceSHA256":sha(src),"method":method,"paintSources":trace}
 # The original hidden/whole far-eye pixel owner is retained per target yaw.
 for filename in ("eye.far.original.png","eye.far.hidden-underpaint.png"):
  src=BASE/key/filename;dst=folder/filename
  dst.write_bytes(src.read_bytes())
 frame=np.zeros((N,N,4),np.uint8)
 for role in ROLES:frame=over(frame,roles[role])
 write(folder/"composite-native.png",frame)
 full=Image.fromarray(frame,"RGBA").resize((1024,1024),Image.Resampling.LANCZOS)
 full.save(folder/"composite.png")
 old=np.array(Image.open(BASE/key/"composite.png").convert("RGBA"))
 newer=np.array(full)
 changed=int(np.count_nonzero(np.any(old!=newer,axis=2)))
 ea=roles["eye.far"][:,:,3].astype(np.float32)/255.
 eye_mass=float(ea.sum())
 hidden=read(folder/"eye.far.hidden-underpaint.png")[:,:,3].astype(np.float32)/255.
 clip=roles["hair.clip.cross_gold"][:,:,3].astype(np.float32)/255.
 parent=roles["hair.front"][:,:,3].astype(np.float32)/255.
 contact=float((clip*parent).sum()/max(1.,clip.sum()))
 return {"yaw":yaw,"kind":"painted-keyframe" if exact else
          "source-endpoint" if endpoint else "paint-inbetween",
  "paintWeight":round(spec(yaw)[1],6),
  "paintSources":[{"angle":k,"weight":round(v,6)} for k,v in spec(yaw)[0].items()],
  "sourceCompositeSHA256":sha(BASE/key/"composite.png"),
  "outputCompositeSHA256":sha(folder/"composite.png"),
  "changedCompositePixels":changed,
  "eyeDisplayedAlphaMass":round(eye_mass,4),
  "hiddenEyeSourceAlphaMass":round(float(hidden.sum()),4),
  "clipHairContactCoverage":round(contact,6),
  "roles":witness,
  "sourceEyeUnderpaintSHA256":sha(folder/"eye.far.original.png"),
  "hiddenEyeUnderpaintSHA256":sha(folder/"eye.far.hidden-underpaint.png"),
  "artisticAdmission":False}

def run():
 s35=json.loads(Q35.read_text());s36=json.loads(Q36.read_text());cam=json.loads(QCAM.read_text())
 if {s35["characterId"],s36["characterId"],cam["characterId"]}!={"p0_character_001"}:
  raise AssertionError("P0 identity differs")
 if s36["modelFullImagePoseApproved"] or s36["fullKeyviewArtAccepted"]:
  raise AssertionError("Drawing reference was improperly admitted")
 if s36["semanticRoleCount"]!=len(ROLES) or s35["angles"]!=list(ANG):
  raise AssertionError("Expected source roles and poses differ")
 if len(s36["frames"])!=len(KEYS):raise AssertionError("Two painting keys required")
 for entry in s36["frames"]:
  a=entry["yaw"]
  if a not in KEYS:raise AssertionError("Paint key angle changed")
  for role in PAINT_ROLES:
   row=entry["partDetails"][role]
   if sha(NEW/slug(a)/(role+".png"))!=row["targetOutputSHA256"]:
    raise AssertionError("Painted role source changed: "+role)
 records=[paint_frame(yaw,cam,s35,s36) for yaw in ANG]
 # Identity source references and temporal metrics are diagnostic, not art
 # quality certification. Record all adjacent-frame comparisons.
 hops=[]
 for a,b in zip(records,records[1:]):
  x=read(OUT/slug(a["yaw"])/"composite-native.png")
  y=read(OUT/slug(b["yaw"])/"composite-native.png")
  x0=read(BASE/slug(a["yaw"])/"composite-native.png")
  y0=read(BASE/slug(b["yaw"])/"composite-native.png")
  # Shared registered 443 canvas, conservative face/head ROI metric.
  region=np.s_[125:280,240:390,:3]
  def delta(left,right):
   return float(np.abs(left[region].astype(np.float32)-right[region].astype(np.float32)).mean())
  hops.append({"interval":[a["yaw"],b["yaw"]],
     "localRGBJump":round(delta(x,y),6),
     "sourceLocalRGBJump":round(delta(x0,y0),6),
     "eyeMassDifference":round(abs(b["eyeDisplayedAlphaMass"]-a["eyeDisplayedAlphaMass"]),4),
     "clipContactDifference":round(abs(b["clipHairContactCoverage"]-a["clipHairContactCoverage"]),6)})
 report={"schema":"KOMA-P15-37-ARTMESH-TEMPORAL-PAINT-V1",
  "characterId":"p0_character_001","sourceP15_35SHA256":sha(Q35),
  "sourceP15_36SHA256":sha(Q36),"sourceP15_12CameraSHA256":sha(QCAM),
  "sourceP0Original45SHA256":s35["sourceP0OriginalSHA256"],
  "roles":ROLES,"paintedRoles":list(PAINT_ROLES),"angles":list(ANG),
  "frames":records,"adjacentMetrics":hops,
  "sourceEndpointsExact":[55.,65.],
  "modelPaintedKeysExact":list(KEYS),
  "fullKeyViewsArtApproved":0,"independentHiddenUnderpaintApproved":0,
  "P0HeroApprovedSourceSHA256Verified":False,
  "productionVddModified":False,"independentFull345DegreeCoverage":False,
  "occludedInkAnatomyApproved":False,
  "status":"REGISTERED_PAINT_KEYPARTS_NINE_FRAME_TEMPORAL_CANDIDATE"}
 QA.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"status":report["status"],"roles":len(ROLES),
   "keyframes":[x["yaw"] for x in records if x["kind"]=="painted-keyframe"],
   "paintedMidpoints":[x["yaw"] for x in records if x["kind"]=="paint-inbetween"],
   "changedPixels":[x["changedCompositePixels"] for x in records],
   "RGBJumps":[r["localRGBJump"] for r in hops],
   "baselineJumps":[r["sourceLocalRGBJump"] for r in hops]}))
 return report
if __name__=="__main__":run()

#!/usr/bin/env python3
"""P15-35 P0 role-owned face-depth and front-hair-attachment compositor.

A deterministic 2.5D proxy uses existing face.skin RGB as far-eye cover
and reuses the full far-eye RGBA as underpaint. No synthetic skin RGB,
global eye fade, invented independent painting, or 3D-certification claim.
The gold clip is attached to a measured hair.front image-space local UV
candidate; five source keyframes remain original role-source references.
"""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from p15_32_mesh_vdd import R,P,slug,read,write,over

SRC=P/"p15-34-feature-mesh"; OUT=P/"p15-35-occlusion-mount"
MESH=R/"evidence/p15-34-feature-mesh-qa.json"
OBS=R/"evidence/p15-34-ink-landmarks-qa.json"
QA=R/"evidence/p15-35-occlusion-mount-qa.json"
ROLES=["body.reference","hair.back","face.skin","ear.far","ear.near",
 "hair.side","eye.far","eye.near","nose","mouth","hair.front",
 "hair.ahoge","hair.clip.cross_gold"]
N=443

def sha(path):
 return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def rgba(a,alpha):
 out=a.copy()
 out[:,:,3]=np.uint8(np.clip(np.rint(alpha*255.0),0,255))
 return out

def eye_depth_partition(yaw,eye,skin,nose,hair):
 """Unique masks for hair, nose, and face foreground depth proxy."""
 ea=eye[:,:,3].astype(np.float64)/255.0
 fa=skin[:,:,3].astype(np.float64)/255.0
 na=nose[:,:,3].astype(np.float64)/255.0
 ha=hair[:,:,3].astype(np.float64)/255.0
 yy,xx=np.where(ea>.06)
 if len(xx)<50:raise ValueError("Far eye source support is empty")
 left,right=float(xx.min()),float(xx.max())
 t=np.clip((float(yaw)-55)/10.,0.,1.)
 progress=t*t*(3-2*t)
 # The moving face-surface boundary is constrained to the observed eye
 # silhouette; it is a view-driven depth hypothesis, not 3D truth.
 edge=left+(right-left)*(.10+.78*progress)
 gx=np.arange(N,dtype=np.float64)[None,:]
 skin_front=np.broadcast_to(1/(1+np.exp(np.clip((gx-edge)/1.75,-70,70))),(N,N))*fa
 skin_front=np.clip(skin_front,0,1)
 # Exclusive partitions: far eye in front of face underlay, but behind
 # the moving face-surface strip, the painted nose and the painted bangs.
 bang=ea*ha
 nose_occ=ea*(1-ha)*na
 face_occ=ea*(1-ha)*(1-na)*skin_front
 visible=ea*(1-ha)*(1-na)*(1-skin_front)
 retained=ea*(1-skin_front)
 if np.max(np.abs(ea-(bang+nose_occ+face_occ+visible)))>1e-10:
  raise AssertionError("Exclusive eye occlusion partition mismatch")
 return {"eyeSource":ea,"eyeRetained":retained,"eyeVisible":visible,
         "hiddenByFace":face_occ,"hiddenByNose":nose_occ,
         "hiddenByBangs":bang,"faceSurface":skin_front,
         "edge":float(edge),"progress":float(progress)}

def alpha_center(a):
 mass=a[:,:,3].astype(np.float64)/255.
 yy,xx=np.indices(mass.shape)
 total=mass.sum()
 if total<=0:raise ValueError("Role with no alpha")
 return np.array([(mass*xx).sum()/total,(mass*yy).sum()/total],np.float64)

def parent_bbox(hair):
 yy,xx=np.where(hair[:,:,3]>30)
 if len(xx)<50:raise AssertionError("No front hair pigment")
 return np.array([float(xx.min()),float(yy.min()),float(xx.max()),
                  float(yy.max())],np.float64)

def uv_of(center,box):
 return (center-box[:2])/np.maximum(box[2:]-box[:2],1.)

def center_from_uv(uv,box):
 return box[:2]+uv*(box[2:]-box[:2])

def coverage(clip,hair):
 ca=clip[:,:,3].astype(np.float64)/255
 ha=hair[:,:,3].astype(np.float64)/255
 return float((ca*ha).sum()/max(1,ca.sum()))

def translate_rgba(a,dx,dy):
 return cv2.warpAffine(a,np.array([[1.,0.,float(dx)],[0.,1.,float(dy)]],np.float32),
        (N,N),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0,0,0,0))

def mount_clip(yaw,clip,hair,observations):
 center=alpha_center(clip)
 box=parent_bbox(hair)
 original_uv=uv_of(center,box)
 target_uv=original_uv.copy()
 if yaw not in observations:
  lower,upper=max(x for x in observations if x<yaw),min(x for x in observations if x>yaw)
  t=(yaw-lower)/(upper-lower)
  target_uv=(1-t)*observations[lower]["uv"]+t*observations[upper]["uv"]
 target=center_from_uv(target_uv,box)
 keyframe=yaw in observations
 before=coverage(clip,hair)
 picked=clip
 best=(0,0);best_score=-1e20
 for dy in range(-4,5):
  for dx in range(-4,5):
   candidate=translate_rgba(clip,dx,dy)
   contact=coverage(candidate,hair)
   c=alpha_center(candidate)
   residual=float(np.linalg.norm(c-target))
   # Hold local hair UV constant and choose stable small translations
   # for the entire nine-frame sequence, including source keyframes.
   score=contact-.008*(abs(dx)+abs(dy))-.002*residual*residual
   if score>best_score:
    best_score=score;best=(dx,dy);picked=candidate
 after=coverage(picked,hair)
 updated=alpha_center(picked)
 err=float(np.linalg.norm(uv_of(updated,box)-target_uv))
 if np.linalg.norm(updated-center)>6:raise AssertionError("Clip translation exceeded mount range")
 return picked,{"parentRole":"hair.front","mountModel":"front-hair visible alpha bounding box UV",
  "parentBounds443":np.round(box,3).tolist(),
  "sourceCenter443":np.round(center,3).tolist(),
  "parentLocalUVBefore":np.round(original_uv,5).tolist(),
  "parentLocalUVTarget":np.round(target_uv,5).tolist(),
  "parentLocalUVAfter":np.round(uv_of(updated,box),5).tolist(),
  "uvResidual":round(err,6),"clipPixelShift":list(best),
  "centerAfter443":np.round(updated,3).tolist(),
  "sourceContactCoverage":round(before,6),
  "attachedContactCoverage":round(after,6),
  "sourceKeyframeOriginalPreservedInP15_34":keyframe,
  "candidateClipOffsetAppliedAtKeyframe":bool(keyframe and best!=(0,0)),
  "physicallyApprovedMount":False}

def run():
 baseline=json.loads(MESH.read_text())
 feature=json.loads(OBS.read_text())
 if baseline["characterId"]!=feature["characterId"] or feature["characterId"]!="p0_character_001":
  raise AssertionError("P0 source registry mismatch")
 if baseline["artistLandmarksApproved"] or feature["verifiedIndependentArtistLandmarks"]:
  raise AssertionError("Art source gate must remain distinct")
 keyrefs={}
 for row in feature["frames"]:
  yaw=row["yaw"];clip=read(SRC/slug(yaw)/"hair.clip.cross_gold.png")
  hair=read(SRC/slug(yaw)/"hair.front.png")
  center=alpha_center(clip);box=parent_bbox(hair)
  keyrefs[yaw]={"uv":uv_of(center,box),"center":center}
 records=[]
 for frame in baseline["frames"]:
  yaw=float(frame["yaw"]);name=slug(yaw)
  folder=OUT/name;folder.mkdir(parents=True,exist_ok=True)
  original={role:read(SRC/name/(role+".png")) for role in ROLES}
  for role,a in original.items():
   write(folder/(role+".png"),a)
  clip,mount=mount_clip(yaw,original["hair.clip.cross_gold"],original["hair.front"],keyrefs)
  write(folder/"hair.clip.cross_gold.png",clip)
  p=eye_depth_partition(yaw,original["eye.far"],original["face.skin"],original["nose"],original["hair.front"])
  eye=original["eye.far"]
  visible=rgba(eye,p["eyeRetained"])
  hidden=rgba(eye,p["eyeSource"]-p["eyeRetained"])
  write(folder/"eye.far.png",visible)
  write(folder/"eye.far.hidden-underpaint.png",hidden)
  write(folder/"eye.far.original.png",eye)
  Image.fromarray(np.uint8(np.rint(p["faceSurface"]*255)),"L").save(folder/"face-depth-proxy.png")
  for key in ("hiddenByFace","hiddenByNose","hiddenByBangs","eyeVisible"):
   Image.fromarray(np.uint8(np.rint(p[key]*255)),"L").save(folder/(key+".png"))
  image=np.zeros((N,N,4),np.uint8)
  for role in ROLES:image=over(image,visible if role=="eye.far" else clip if role=="hair.clip.cross_gold" else original[role])
  write(folder/"composite-native.png",image)
  full=Image.fromarray(image,"RGBA").resize((1024,1024),Image.Resampling.LANCZOS)
  full.save(folder/"composite.png")
  old=np.asarray(Image.open(SRC/name/"composite.png").convert("RGBA"))
  changed=int(np.count_nonzero(np.any(old!=np.asarray(full),axis=2)))
  e=p["eyeSource"].sum()
  fractions={k:round(float(p[k].sum()/max(e,1)),6)
     for k in ("hiddenByFace","hiddenByNose","hiddenByBangs","eyeVisible")}
  retainedMass=float(p["eyeRetained"].sum())
  originalMass=float(p["eyeSource"].sum())
  record={"yaw":yaw,"sourceKind":frame["kind"],
   "sourceCompositeSHA256":sha(SRC/name/"composite.png"),
   "sourceEyeSHA256":sha(SRC/name/"eye.far.png"),
   "sourceClipSHA256":sha(SRC/name/"hair.clip.cross_gold.png"),
   "sourceSkinSHA256":sha(SRC/name/"face.skin.png"),
   "sourceHairSHA256":sha(SRC/name/"hair.front.png"),
   "sourceNoseSHA256":sha(SRC/name/"nose.png"),
   "sourceEyeMass":round(originalMass,4),
   "eyeRGBAHiddenUnderpaintMass":round(originalMass-retainedMass,4),
   "eyeSourceRGBKept":True,"wholeLayerEyeFadeApplied":False,
   "eyeAlphaPartitionFractions":fractions,
   "depthEdgeX443":round(p["edge"],4),
   "depthSweepProgress":round(p["progress"],6),
   "clipAttachment":mount,
   "changedCompositePixelsVsP15_34":changed,
   "outputSHA256":sha(folder/"composite.png"),
   "roleCount":len(ROLES),
   "sourceRolesUnmodifiedExceptEyeAndClip":True}
  records.append(record)
 fractions=[r["eyeAlphaPartitionFractions"]["eyeVisible"] for r in records]
 # A physically facing away eye should not become MORE visible in the
 # geometric hypothesis as turn angle increases.
 if any(later>before+.012 for before,later in zip(fractions,fractions[1:])):
  raise AssertionError("Far-eye geometry visibility trend unexpectedly reversed")
 qa={"schema":"KOMA-P15-35-P0-FACE-DEPTH-AND-HAIR-MOUNT-CANDIDATE-V1",
   "characterId":"p0_character_001",
   "sourceInkQA_SHA256":sha(OBS),"sourceMeshQA_SHA256":sha(MESH),
   "sourceP0OriginalSHA256":feature["source45P0SHA256"],
   "angles":[r["yaw"] for r in records],"frames":records,
   "depthMethod":"face.skin RGBA material underlay with yaw-dependent far-eye Z boundary from painted eye bbox",
   "faceMask3DModelValidated":False,"nosePhysicalVolumeVerified":False,
   "clipMount3DValidated":False,"clipMountRole":"hair.front",
   "eyeOcclusionCause":"local face-surface depth and native nose/front-hair alpha",
   "artistApprovedOcclusion":False,"artistApprovedHairLock":False,
   "underpaintRecoveredFromOriginalRGB":True,"newIndependentPaintings":0,
   "sourceArtModified":False,"productionRendererChanged":False,
   "candidateKeyframeClipPixelsMayShift":True,
   "formalArtisticAcceptance":False,
   "status":"P15_35_EXPLICIT_LOCAL_Z_OCCLUSION_AND_HAIR_UV_ENGINEERING_CANDIDATE"}
 QA.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"status":qa["status"],"frames":len(records),
   "farEyeVisibleFraction":fractions,
   "clipContactBefore":[r["clipAttachment"]["sourceContactCoverage"] for r in records],
   "clipContactAfter":[r["clipAttachment"]["attachedContactCoverage"] for r in records],
   "clipTranslations":[r["clipAttachment"]["clipPixelShift"] for r in records],
   "changedCompositePixels":[r["changedCompositePixelsVsP15_34"] for r in records]}))
 return qa

if __name__=="__main__":run()

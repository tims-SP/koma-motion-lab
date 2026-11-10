#!/usr/bin/env python3
"""Build source-linked P0 keypoint, contour, owner-ID and occlusion conditions.

Outputs are renderer-ready diagnostics. They do not imply independent source
painting, accurate hidden underpaint, or ControlNet endpoint support.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
PRIVATE=ROOT/"private-assets"
OUT=PRIVATE/"p15-13-structural"
CAMERA=ROOT/"evidence/p15-12-camera-proxy-qa.json"
ART=ROOT/"evidence/p15-12-guided-candidate-qa.json"
SEM=ROOT/"evidence/p15-10-semantic-arc-qa.json"
REPORT=ROOT/"evidence/p15-13-structural-qa.json"
ANGLES=(57.5,60.)
N=1024

def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for block in iter(lambda:f.read(1048576),b""):h.update(block)
 return h.hexdigest()

def yawname(angle):
 return "yaw"+(str(int(angle)) if float(angle).is_integer() else str(angle).replace(".","p"))

def load(f,mode="RGB"):
 with Image.open(f) as image:
  if image.size!=(N,N):raise ValueError("P0 full canvas required")
  return np.array(image.convert(mode))

def irises(rgb):
 hsv=cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV)
 m=np.uint8((hsv[:,:,0]>=118)&(hsv[:,:,0]<165)&(hsv[:,:,1]>=50)&(hsv[:,:,2]<235))
 m[:420]=0;m[515:]=0;m[:,:445]=0;m[:,775:]=0
 n,labels,stats,centers=cv2.connectedComponentsWithStats(m,8)
 values=[]
 for i in range(1,n):
  x,y,w,h,area=map(int,stats[i])
  if area>=750 and 20<=w<=115 and 20<=h<=105:
   values.append({"center":[round(float(centers[i,0]),3),round(float(centers[i,1]),3)],
     "area":area,"bounds":[x,y,w,h]})
 result=sorted(sorted(values,key=lambda r:r["area"],reverse=True)[:2],
               key=lambda r:r["center"][0])
 if len(result)!=2:raise ValueError("Two colored iris regions required")
 return result

def heatmap(anchors):
 channels=np.zeros((N,N,3),np.float32)
 for role,r in anchors.items():
  if r["xy"] is None:continue
  channel=0 if "eye." in role else (2 if "hair." in role else 1)
  x,y=[int(round(n)) for n in r["xy"]]
  impulse=np.zeros((N,N),np.float32)
  impulse[y,x]=r["visibility"]
  channels[:,:,channel]=np.maximum(channels[:,:,channel],
                                   cv2.GaussianBlur(impulse,(0,0),12.0))
 return np.uint8(np.clip(channels*(2*np.pi*12*12),0,1)*255)

def condition(yaw,roles,anchors):
 folder=OUT/yawname(yaw)
 folder.mkdir(parents=True,exist_ok=True)
 owner=np.zeros((N,N),np.uint8)
 counts={}
 for i,role in enumerate(roles,1):
  source=PRIVATE/"p15-10-semantic-pose/arc"/yawname(yaw)/"parts"/(role+".png")
  pixels=load(source,"RGBA")
  mask=pixels[:,:,3]>16
  owner[mask]=i
  counts[role]={"path":str(source.relative_to(PRIVATE)),"sha256":sha(source),
                "visiblePixels":int(mask.sum())}
 source=PRIVATE/"p15-10-semantic-pose/arc"/(yawname(yaw)+".png")
 rgb=load(source)
 gradient=cv2.Canny(cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY),60,135)
 lmap=heatmap(anchors)
 preview=cv2.addWeighted(rgb,.72,np.repeat(gradient[:,:,None],3,axis=2),.28,0)
 preview=np.uint8(np.clip(.88*preview+.12*lmap,0,255))
 images={"owner":(owner,"L"),"lineart":(gradient,"L"),
         "heatmap":(lmap,"RGB"),"preview":(preview,"RGB")}
 paths={}
 for name,(pixels,mode) in images.items():
  path=folder/(name+".png")
  Image.fromarray(pixels,mode).save(path)
  paths[name]={"path":str(path.relative_to(PRIVATE)),"sha256":sha(path)}
 return paths,counts

def run():
 camera=json.loads(CAMERA.read_text())
 art=json.loads(ART.read_text())
 sem=json.loads(SEM.read_text())
 if {camera["characterId"],art["characterId"],sem["characterId"]}!={"p0_character_001"}:
  raise AssertionError("Character identity source differs")
 roles=sem["roles"]
 if len(roles)!=13:raise AssertionError("P0 ArtMesh roles changed")
 orig=PRIVATE/"p2-views/whole/yaw045.png"
 if sha(orig)!=art["generated"][0]["secondIdentitySHA256"]:
  raise AssertionError("P0 original 45 source hash changed")
 baseline=irises(load(orig))
 source45=next(r for r in camera["frames"] if r["yaw"]==45)
 eye_roles=("eye.near.iris","eye.far.iris")
 detector_bias=[np.array(x["center"])-np.array(source45["anchors"][k]["xy"])
                for x,k in zip(baseline,eye_roles)]
 records=[]
 for yaw in ANGLES:
  frame=next(x for x in camera["frames"] if x["yaw"]==yaw)
  artwork=next(x for x in art["generated"] if x["angle"]==yaw)
  source=PRIVATE/artwork["sourcePath"]
  if sha(source)!=artwork["sourceSHA256"]:raise AssertionError("Candidate hash mismatch")
  seen=irises(load(source))
  expected=[np.array(frame["anchors"][role]["xy"])+bias
            for role,bias in zip(eye_roles,detector_bias)]
  errors=[round(float(np.linalg.norm(np.array(r["center"])-target)),3)
          for r,target in zip(seen,expected)]
  files,layers=condition(yaw,roles,frame["anchors"])
  records.append({"angle":yaw,"sourcePaintingPath":artwork["sourcePath"],
     "sourcePaintingSHA256":artwork["sourceSHA256"],
     "actualIrisColorFeatures":seen,
     "cameraProjectedIrisTargets":[[round(float(x),3) for x in row] for row in expected],
     "irisFeatureDeviationPixels":errors,"featureErrorTotalPixels":round(sum(errors),3),
     "isAnatomicalLandmarkDetection":False,
     "semanticLayers":layers,"artmeshRoleCount":len(layers),
     "farEyeVisibilityProxy":frame["anchors"]["eye.far.iris"]["visibility"],
     "hairclipVisibilityProxy":frame["anchors"]["hair.clip.center"]["visibility"],
     "outputs":files})
 report={"schema":"KOMA-P15-13-STRUCTURAL-CONDITION-V1",
  "characterId":"p0_character_001",
  "sourceCameraSHA256":sha(CAMERA),"sourcePaintedCandidatesSHA256":sha(ART),
  "sourceSemanticArcSHA256":sha(SEM),"original45SHA256":sha(orig),
  "detectorMethod":"color components calibrated against P5 original 45 annotations; diagnostic only",
  "detectorBiasPerEye":[[round(float(x),3) for x in b] for b in detector_bias],
  "sourceRoleOrder":roles,"angles":list(ANGLES),"frames":records,
  "structuralConditions":["landmark heatmap","source-owned lineart",
                           "13-role owner ID","physical clip and far-eye occlusion"],
  "imageEndpointWithHardConditioningVerified":False,
  "approvedIndependentKeyPaintings":0,"approvedHiddenUnderpainting":0,
  "status":"CAMERA_CONDITION_AND_IRIS_LOCATION_EVIDENCE_VERIFIED"}
 REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"status":report["status"],"angles":report["angles"],
  "roles":len(roles),"measuredIrisErrorPx":[r["irisFeatureDeviationPixels"] for r in records],
  "sourceRoleCounts":[len(r["semanticLayers"]) for r in records]}))
 return report

if __name__=="__main__":run()

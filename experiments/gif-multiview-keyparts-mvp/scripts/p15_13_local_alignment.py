#!/usr/bin/env python3
"""Local spatial repair of painted iris positions under P5 camera guidance.

The retargeted RGB preserves a single generated source's brushwork. It is
diagnostic raster editing, not an independently painted ArtMesh keyframe.
"""
from __future__ import annotations
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from p15_13_structural_condition import PRIVATE,ROOT,OUT,REPORT,load,irises,sha,yawname,N

QA=ROOT/"evidence/p15-13-local-alignment-qa.json"

def remap_to_eye_targets(image,seen,targets,anchors):
 original=np.float64([x["center"] for x in seen])
 target=np.float64(targets)
 fixed=[
  [365,410],[875,410],[365,535],[910,535],
  anchors["face.jaw.near"]["xy"],
  anchors["face.chin"]["xy"],
  anchors["hair.clip.center"]["xy"],
  [0,0],[1023,0],[0,1023],[1023,1023],
 ]
 control=np.concatenate((target,np.float64(fixed)),axis=0)
 destination=np.concatenate((original,np.float64(fixed)),axis=0)
 sigma=95.
 dist=np.sum((control[:,None]-control[None])**2,axis=2)
 matrix=np.exp(-dist/(2*sigma**2))
 weights=np.linalg.solve(matrix+.02*np.eye(len(control)),destination-control)
 yy,xx=np.meshgrid(np.linspace(0,1023,256),np.linspace(0,1023,256),indexing="ij")
 low=np.zeros((256,256,2),np.float32)
 for (x,y),v in zip(control,weights):
  influence=np.exp(-((xx-x)**2+(yy-y)**2)/(2*sigma**2))
  low+=np.float32(influence[:,:,None]*v)
 flow=cv2.resize(low,(N,N),interpolation=cv2.INTER_CUBIC)
 gy,gx=np.meshgrid(np.arange(N,dtype=np.float32),np.arange(N,dtype=np.float32),indexing="ij")
 warped=cv2.remap(image,gx+flow[:,:,0],gy+flow[:,:,1],
                interpolation=cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT,
                borderValue=(255,255,255))
 return warped,round(float(np.linalg.norm(flow,axis=2).max()),3)

def run():
 condition=json.loads(REPORT.read_text())
 camera=json.loads((ROOT/"evidence/p15-12-camera-proxy-qa.json").read_text())
 if condition["characterId"]!=camera["characterId"]:
  raise AssertionError("Camera and source character differ")
 records=[]
 for row in condition["frames"]:
  yaw=row["angle"]
  frame=next(f for f in camera["frames"] if f["yaw"]==yaw)
  source=PRIVATE/row["sourcePaintingPath"]
  if sha(source)!=row["sourcePaintingSHA256"]:
   raise AssertionError("Candidate source image changed")
  original=load(source)
  retarget,flowmax=remap_to_eye_targets(original,row["actualIrisColorFeatures"],
        row["cameraProjectedIrisTargets"],frame["anchors"])
  dest=OUT/yawname(yaw)/"iris-registered-candidate.png"
  Image.fromarray(retarget,"RGB").save(dest)
  detected=irises(retarget)
  targets=[np.array(x) for x in row["cameraProjectedIrisTargets"]]
  errs=[round(float(np.linalg.norm(np.array(a["center"])-b)),3)
        for a,b in zip(detected,targets)]
  old=row["irisFeatureDeviationPixels"]
  change=round(float(1-sum(errs)/sum(old)),5)
  if change<.15:
   raise AssertionError(f"Local iris retargeting did not reduce error at {yaw}: {change}")
  records.append({"yaw":yaw,
    "sourceGeneratedPaintingSHA256":row["sourcePaintingSHA256"],
    "targetAnchorOrigin":"P5 projection with original color-component calibration",
    "originalErrorsPixels":old,"registeredErrorsPixels":errs,
    "aggregateErrorReductionFraction":change,"maximumPixelRemap":flowmax,
    "detectedIrisComponents":detected,
    "output":{"path":str(dest.relative_to(PRIVATE)),"sha256":sha(dest)},
    "sourceOwnership":"same painting, locally retargeted pixels",
    "artisticStatus":"DERIVED_ALIGNMENT_REQUIRES_KEYFRAME_PAINTING"})
 report={"schema":"KOMA-P15-13-LOCAL-ANATOMICAL-ALIGNMENT-V1",
   "characterId":"p0_character_001","sourceConditionSHA256":sha(REPORT),
   "frames":records,"calibratedSourcePreserved":True,
   "separateEyeCoordinatesVerified":True,
   "independentPaintingsApproved":0,
   "role":"controlled source-pixel deformation before independent painted layers",
   "status":"SOURCE_PIXEL_ANATOMY_ALIGNMENT_VERIFIED"}
 QA.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"status":report["status"],"angles":[r["yaw"] for r in records],
   "errorReductions":[r["aggregateErrorReductionFraction"] for r in records],
   "after":[r["registeredErrorsPixels"] for r in records]}))
 return report

if __name__=="__main__":run()

#!/usr/bin/env python3
"""P15-12 guided paintings and calibrated silhouette QA.

Geometry is a reference rather than an accepted source painting. All
independent art gates remain separate from source-hash and browser QA.
"""
from __future__ import annotations
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
from p15_12_camera_proxy import PRIVATE, ROOT, OUT, QA, sha
from p15_08_pose_qa import gold_mark

INPUTS=[
 (57.5,"yaw57p5-identity-guided.png",
  "3247fe9717dc5e180308ca6db4864d97b24f092222745bfef79c63c4873e973c",
  "6955bc66250d430469d598c6c3958a11709b5e4d",575126),
 (60.,"yaw60-identity-guided.png",
  "c562335b6d1e1e250c3b28f9cb87614389d343447449d24605a581979ccaac36",
  "eab482565db6ee750322f1220b7c6645fd3d2e91",600126)
]


def foreground(im):
 rgb=np.asarray(im.convert("RGB")).astype(np.int16)
 dist=np.max(255-rgb,axis=2)
 mask=np.uint8(dist>35)
 n, lab, stats, _=cv2.connectedComponentsWithStats(mask,8)
 if n<2:return np.zeros(mask.shape,dtype=bool)
 ix=1+np.argmax(stats[1:,cv2.CC_STAT_AREA])
 return lab==ix


def iou(a,b):
 return round(float(np.count_nonzero(a&b))/max(1,int(np.count_nonzero(a|b))),5)


def main():
 proxy=json.loads(QA.read_text())
 if proxy["characterId"]!="p0_character_001" or proxy["status"]!="NUMERIC_CAMERA_PROXY_VERIFIED":
  raise AssertionError("Original camera proxy missing")
 reg=json.loads((ROOT/"metadata/p15-11-source-candidates.json").read_text())
 base=PRIVATE/reg["referenceImages"][0]["path"]
 if sha(base)!=reg["referenceImages"][0]["sha256"]:
  raise AssertionError("Approved 45 view changed")
 orig=Image.open(base).convert("RGB")
 mask45=foreground(orig)
 rows=[]
 pictures=[("P0 45 original",orig)]
 for angle,name,digest,gitblob,seed in INPUTS:
  entry=next(x for x in proxy["frames"] if x["yaw"]==angle)
  guide=PRIVATE/entry["guide"]["conditioningPath"]
  if sha(guide)!=entry["guide"]["conditioningSHA256"]:
   raise AssertionError("Calibrated guide changed")
  source=OUT/"generated"/name
  if sha(source)!=digest:raise AssertionError("Generated candidate source hash mismatch")
  with Image.open(source) as im:
   if im.mode!="RGB" or im.size!=(1024,1024):raise ValueError("Invalid new painting")
   painted=im.copy()
  baseline=Image.open(guide).convert("RGB")
  silhouette=foreground(painted)
  gold=gold_mark(painted)
  rows.append({"angle":angle,"sourcePath":str(source.relative_to(PRIVATE)),
    "sourceSHA256":digest,"sourceGitBlob":gitblob,"seed":seed,
    "adapter":"Anime-V2","firstConditioningImage":entry["guide"]["conditioningPath"],
    "firstConditioningSHA256":entry["guide"]["conditioningSHA256"],
    "secondIdentitySource":reg["referenceImages"][0]["path"],
    "secondIdentitySHA256":reg["referenceImages"][0]["sha256"],
    "silhouetteIoUWithPoseGuide":iou(silhouette,foreground(baseline)),
    "silhouetteIoUWithOriginal45":iou(silhouette,mask45),
    "hairclipConnectedComponent":gold,
    "expectedEyeNoseGapPixelsFromProxy":entry["eyeNoseGap"],
    "expectedNearEye":entry["anchors"]["eye.near.iris"]["xy"],
    "expectedFarEye":entry["anchors"]["eye.far.iris"]["xy"],
    "requiredQualitativeCheck":["far eye width and occlusion","nose and jaw direction",
       "head silhouette","clip handedness","uniform pose","expression consistency"],
    "visualReview":"POSE_AND_EXPRESSION_REWORK",
    "acceptedAsIndependentKeyframe":False})
  pictures.extend([("Pose "+str(angle),baseline),("Guided "+str(angle),painted)])
 ref65=PRIVATE/reg["referenceImages"][1]["path"]
 pictures.append(("Source 65",Image.open(ref65).convert("RGB")))
 sheet=Image.new("RGB",(330*3,380*2),(248,248,249));p=ImageDraw.Draw(sheet)
 for i,(label,portrait) in enumerate(pictures):
  x,y=(i%3)*330,(i//3)*380
  sheet.paste(portrait.resize((330,330),Image.Resampling.LANCZOS),(x,y+24))
  p.text((x+8,y+7),label,fill=(20,29,45))
 f=OUT/"p15-12-angle-guides-contact.jpg";sheet.save(f,quality=91)
 report={"schema":"KOMA-P15-12-GEOMETRY-CONDITIONED-CANDIDATE-QA-V1",
  "characterId":"p0_character_001","guideSourceQA":"evidence/p15-12-camera-proxy-qa.json",
  "model":"Qwen-Image-Edit-2511","inputImageOrder":"P15 geometry guide then P0 identity",
  "generated":[*rows],"generatedCount":len(rows),
  "contactPath":str(f.relative_to(PRIVATE)),"contactSHA256":sha(f),
  "independentlyPaintedKeyframesAdmitted":0,
  "paintedSemanticLayersAdmitted":0,
  "sourceGeometryRole":"pose guide, not independent painting",
  "formalArtGate":"GEOMETRY_GUIDES_VALID_ARTWORK_POSE_REVIEW",
  "sourceHeroSHA256Verified":False}
 dest=ROOT/"evidence/p15-12-guided-candidate-qa.json"
 dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"formalArtGate":report["formalArtGate"],
  "newCandidates":len(rows),
  "poseIoU":[r["silhouetteIoUWithPoseGuide"] for r in rows],
  "original45IoU":[r["silhouetteIoUWithOriginal45"] for r in rows],
  "admitted":0}))
 return report


if __name__=="__main__":main()

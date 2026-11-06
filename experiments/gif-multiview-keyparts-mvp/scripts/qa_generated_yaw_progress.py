#!/usr/bin/env python3
"""Audit angular silhouette progress of generated P0 RGBA views versus real keyframes.

A midway view should make appreciable progress between the adjacent independent
whole-view silhouettes. This is only a diagnostic, not absolute pose estimation:
the original approved 0/45/90 source frames remain the angle authority.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image

VIEW_MAP={
  0:"p1-front/diagnostics/front-reference.png",
  22.5:"p3-native-source-trial/yaw0225_whole.png",
  45:"p2-views/whole/yaw045.png",
  67.5:"p3-native-source-trial/yaw0675_whole.png",
  90:"p2-views/whole/yaw090.png"
}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def masks(root):
    result={}
    for a,relative in VIEW_MAP.items():
        filename=root/relative
        with Image.open(filename) as image:
            if image.mode!="RGBA" or image.size!=(1024,1024):
                raise ValueError("Unexpected generated P0 canvas")
            alpha=np.asarray(image.getchannel("A"))
        result[a]={"mask":alpha>=20,"file":str(filename),"sha256":sha(filename)}
    return result

def iou(a,b):
    return float(np.count_nonzero(a&b))/max(1,int(np.count_nonzero(a|b)))

def review(root,out,progress_min=0.30,progress_max=0.70):
    root=Path(root).resolve();files=masks(root)
    checks=[]
    for a,b,c in ((0,22.5,45),(45,67.5,90)):
        for region in ("full","head"):
            yy=np.arange(1024)[:,None]
            canvas={key:(v["mask"] if region=="full" else v["mask"]&(yy<750))
                    for key,v in files.items()}
            left=iou(canvas[a],canvas[b])
            right=iou(canvas[b],canvas[c])
            span=iou(canvas[a],canvas[c])
            leftDelta=1-left;rightDelta=1-right
            ratio=leftDelta/max(1e-8,leftDelta+rightDelta)
            checks.append({"region":region,"startYaw":a,"candidateYaw":b,"endYaw":c,
              "startCandidateIoU":round(left,6),
              "candidateEndIoU":round(right,6),
              "startEndIoU":round(span,6),
              "estimatedSilhouetteProgress":round(ratio,6),
              "candidatePoseDistinctFromStart":leftDelta>0.015,
              "midwaySilhouetteProgressPass":progress_min<=ratio<=progress_max})
    source={
       str(yaw):{"path":str(Path(rec["file"]).relative_to(root)), "sha256":rec["sha256"]}
       for yaw,rec in files.items()
    }
    report={"schema":"KOMA-P0-GENERATED-HOLDOUT-YAW-PROGRESS-QA-V1",
      "characterId":"p0_character_001",
      "sourceRole":"original_P0_keyviews_and_generated_background_removed_RGBA",
      "angleAuthority":[0,45,90],"provisionalAngles":[22.5,67.5],
      "coverageRegion":"full silhouette and head y<750",
      "progressReference":"1 - alpha-silhouette IoU against adjacent original keyframes",
      "midpointAcceptableProgress":[progress_min,progress_max],
      "checks":checks,
      "passed":sum(x["midwaySilhouetteProgressPass"] for x in checks),
      "failed":sum(not x["midwaySilhouetteProgressPass"] for x in checks),
      "sources":source,
      "status":"PASS_SILHOUETTE_VIEW_PROGRESS" if all(x["midwaySilhouetteProgressPass"] for x in checks)
       else "GENERATED_VIEW_ANGLES_REQUIRE_POSE_CONSTRAINTS",
      "artisticApproval":"PENDING"
    }
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":report["status"],"failed":report["failed"],
      "headProgress":[{"angle":x["candidateYaw"],"fraction":x["estimatedSilhouetteProgress"]}
                      for x in checks if x["region"]=="head"]},indent=2,ensure_ascii=False))
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    report=review(args.root,args.output)
    raise SystemExit(0 if report["failed"]==0 else 2)

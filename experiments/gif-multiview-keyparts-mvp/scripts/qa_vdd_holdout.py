#!/usr/bin/env python3
"""Measure P0 VDD holdout facial alpha-coverage gaps in actual browser canvas PNGs."""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ANGLES=(0,22.5,45,67.5,90)
# Authored P0 facial-core sampling ellipses at each angle, in global 1024 coords.
# They exclude silhouette tips, hair-outside regions and separate accessories.
CORE={
    0:((515,545),(60,75)),
    22.5:((575,545),(60,75)),
    45:((623,545),(60,75)),
    67.5:((671,545),(60,75)),
    90:((695,545),(45,75))
}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for part in iter(lambda:f.read(1024*1024),b""):
            h.update(part)
    return h.hexdigest()

def run(folder,out,threshold=0.005):
    folder=Path(folder).resolve()
    images={}
    records=[]
    for angle in ANGLES:
        fn=folder/("yaw"+str(angle).replace(".","p").replace("p0","")+".png")
        if not fn.is_file():
            raise FileNotFoundError(fn)
        with Image.open(fn) as img:
            if img.mode!="RGBA" or img.size!=(1024,1024):
                raise ValueError("Canvas source must be 1024 RGBA: "+str(fn))
            rgba=np.array(img)
        images[angle]=rgba
        center,axes=CORE[angle]
        mask=np.zeros((1024,1024),np.uint8)
        cv2.ellipse(mask,center,axes,0,0,360,255,-1)
        region=mask>0
        gaps=region & (rgba[:,:,3]<245)
        count=int(gaps.sum())
        n,l,stats,_=cv2.connectedComponentsWithStats(gaps.astype(np.uint8),8)
        largest=max([int(stats[k,4]) for k in range(1,n)]+[0])
        ratio=count/int(region.sum())
        records.append({
            "angle":angle,"source":str(fn),"sha256":sha(fn),
            "region":list(center)+list(axes),"regionPixels":int(region.sum()),
            "missingCoveragePixels":count,"missingCoverageRatio":round(ratio,6),
            "largestHoleClusterPixels":largest,
            "gatePass":count==0 if angle in (0,45,90) else ratio<=threshold
        })
    report={
      "schema":"KOMA-P0-VDD-FACE-ALPHA-HOLDOUT-QA-V1",
      "characterId":"p0_character_001",
      "sourceRole":"real_39_part_RGBA_Canvas2D_Rendered",
      "sourceMethods":["P1 front 13 semantic layers","P2 quarter/profile 26 semantic layers"],
      "angles":list(ANGLES),"faceROIRule":"anatomically anchored elliptical interior samples",
      "thresholdMissingCoverageRatio":threshold,
      "status":"PASS_HOLDOUT_COVERAGE" if all(x["gatePass"] for x in records) else
               "REQUIRES_VDD_BOUNDARY_REFINEMENT",
      "checks":records,
      "holdoutsFailed":[x["angle"] for x in records if not x["gatePass"]],
      "humanArtApproval":"PENDING"
    }
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:report[k] for k in
       ("status","thresholdMissingCoverageRatio","holdoutsFailed")},ensure_ascii=False))
    for record in records:
        print(f"{record['angle']:>5}°  holes={record['missingCoveragePixels']:>5}  ratio={record['missingCoverageRatio']:.4%}  pass={record['gatePass']}")
    return report

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--frames",required=True)
    parser.add_argument("--output",required=True)
    parser.add_argument("--max-gap-ratio",type=float,default=0.005)
    args=parser.parse_args()
    result=run(args.frames,args.output,args.max_gap_ratio)
    raise SystemExit(0 if result["status"]=="PASS_HOLDOUT_COVERAGE" else 2)

#!/usr/bin/env python3
"""Validate visual transition continuity of actual rendered P0 view frames."""
import argparse
import hashlib
import json
import statistics
from pathlib import Path

import numpy as np
from PIL import Image


def composite(path):
    rgba=np.asarray(Image.open(path).convert("RGBA")).astype(np.float32)
    alpha=rgba[:,:,3:4]/255
    return rgba[:,:,:3]*alpha+(1-alpha)*np.array([49,61,78],dtype=np.float32)


def frame_path(root,yaw):
    whole=int(yaw)
    tenths=int(round((yaw%1)*10))
    return root/f"yaw{whole:03d}_{tenths}.png"


def analyze(root,max_median_ratio=1.8):
    root=Path(root).resolve()
    views=[i*2.5 for i in range(37)]
    files=[frame_path(root,y) for y in views]
    for f in files:
        if not f.is_file():raise FileNotFoundError(f)
    mean_differences=[]
    previous=None
    for yaw,path in zip(views,files):
        frame=composite(path)
        if previous is not None:
            mean=float(np.abs(frame-previous).mean())
            mean_differences.append({"fromYaw":yaw-2.5,"toYaw":yaw,
                                    "meanRGBAbsoluteDelta":round(mean,4)})
        previous=frame
    median=statistics.median(p["meanRGBAbsoluteDelta"] for p in mean_differences)
    outliers=[{**p,"relativeToMedian":round(p["meanRGBAbsoluteDelta"]/median,3)}
              for p in mean_differences
              if median>0 and p["meanRGBAbsoluteDelta"]>max_median_ratio*median]
    return {
      "schema":"KOMA-P0-TURN-TEMPORAL-CONTINUITY-QA-V1",
      "characterId":"p0_character_001",
      "sourceRole":"real_recovered_gif_view_flow_proxy",
      "angles":len(views),"startYaw":views[0],"endYaw":views[-1],
      "medianAdjacentMeanRGBDelta":round(median,4),
      "maxAdjacentMeanRGBDelta":max(p["meanRGBAbsoluteDelta"] for p in mean_differences),
      "maxMedianRatio":max_median_ratio,
      "outliers":outliers,"measurements":mean_differences,
      "status":"PASS_TEMPORAL_CONTINUITY" if not outliers else "CANDIDATE_REQUIRES_TRANSITION_REFINEMENT"
    }


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--frames",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--limit",type=float,default=1.8)
    args=p.parse_args()
    report=analyze(args.frames,args.limit)
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:report[k] for k in
       ("status","angles","medianAdjacentMeanRGBDelta","maxAdjacentMeanRGBDelta","outliers")},indent=2))

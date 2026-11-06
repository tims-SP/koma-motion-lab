#!/usr/bin/env python3
"""Quantify facial ArtMesh texture fragmentation in browser-rendered P0 turns.

Unlike the silhouette/alpha gate, this checks source-dependent high-frequency
seams created when separately rasterized ArtMeshes do not share matching UV
and art boundaries. This is a diagnostic art-quality gate, not a substitute
for inspecting the actual anime frames.
"""
import argparse
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

ANGLES=(0,22.5,45,67.5,90)
FACE_CORE={
    0:((515,545),(60,75)),
    22.5:((575,545),(60,75)),
    45:((623,545),(60,75)),
    67.5:((671,545),(60,75)),
    90:((695,545),(45,75))
}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def analyze(folder,output,relative_threshold=1.8):
    folder=Path(folder)
    frames={}
    for yaw in ANGLES:
        path=folder/("yaw"+str(yaw).replace(".","p").replace("p0","")+".png")
        rgba=np.asarray(Image.open(path).convert("RGBA"))
        if rgba.shape!=(1024,1024,4):raise ValueError("unexpected RGBA canvas size")
        gray=cv2.cvtColor(rgba[:,:,:3],cv2.COLOR_RGB2GRAY)
        core=np.zeros(gray.shape,dtype=np.uint8)
        center,axes=FACE_CORE[yaw]
        cv2.ellipse(core,center,axes,0,0,360,255,-1)
        pixels=(core>0)
        canny=cv2.Canny(gray,55,135)
        edge_ratio=float((canny[pixels]>0).mean())
        laplacian=np.abs(cv2.Laplacian(gray.astype(np.float32),cv2.CV_32F,ksize=3))
        frames[yaw]={
            "angle":yaw,"sourceSHA256":sha(path),
            "faceCorePixels":int(pixels.sum()),
            "cannyEdgeDensity":round(edge_ratio,6),
            "meanAbsLaplacian":round(float(laplacian[pixels].mean()),5)
        }
    holdouts=[]
    for yaw in (22.5,67.5):
        a,b=(0,45) if yaw<45 else (45,90)
        baseline=max(frames[a]["cannyEdgeDensity"],frames[b]["cannyEdgeDensity"])
        observed=frames[yaw]["cannyEdgeDensity"]
        ratio=observed/max(1e-6,baseline)
        holdouts.append({
            **frames[yaw],"adjacentReferenceAngles":[a,b],
            "adjacentMaxEdgeDensity":baseline,
            "edgeDensityRelativeToAdjacentMax":round(ratio,4),
            "threshold":relative_threshold,
            "pass":ratio<=relative_threshold
        })
    report={
       "schema":"KOMA-P0-VDD-FACE-TEXTURE-ART-QA-V1",
       "characterId":"p0_character_001",
       "sourceMethod":"P0 real browser Canvas2D semantic-mesh renders at all five angles",
       "metric":"Canny(55,135) density in fixed face interior ellipse / max neighboring authored keyframe density",
       "thresholdRelativeEdgeDensity":relative_threshold,
       "referenceFrames":[frames[x] for x in (0,45,90)],
       "holdouts":holdouts,
       "passed":sum(i["pass"] for i in holdouts),
       "failed":sum(not i["pass"] for i in holdouts),
       "status":"PASS_TEXTURE_EDGE_DIAGNOSTIC" if all(i["pass"] for i in holdouts)
                else "REQUIRES_SEMANTIC_TEXTURE_CORRESPONDENCE",
       "manualVisualAcceptance":"PENDING"
    }
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":report["status"],"passed":report["passed"],"failed":report["failed"],
                     "holdouts":[{"angle":p["angle"],"ratio":p["edgeDensityRelativeToAdjacentMax"]}
                                for p in holdouts]},ensure_ascii=False,indent=2))
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--frames",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--relative-limit",type=float,default=1.8)
    args=p.parse_args()
    result=analyze(args.frames,args.output,args.relative_limit)
    raise SystemExit(0 if result["failed"]==0 else 2)

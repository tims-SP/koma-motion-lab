#!/usr/bin/env python3
"""Verify P0 keyview, source lineage, temporal motion and browser QA for P15-07."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from p15_07_semantic_keyframes import PRIVATE, ROOT, source_registry, PROJECT
from p8_semantic_occlusion import output_frame_id

ANGLES=[2.5*i for i in range(37)]
RENDERERS={
    "semantic":"p15-07-semantic-preview",
    "wholeGeometry":"p15-07-wholekey-preview",
}
REFERENCE={
    67.5:"p14-authored-candidates/yaw067p5-artmesh/yaw067p5-painted-semantic-composite.png",
    72.5:"p14-authored-candidates/yaw072p5-artmesh/yaw072p5-p0-source-mapped-artmesh.png",
}


def sha(f):
    h=hashlib.sha256()
    with Path(f).open("rb") as fp:
        for piece in iter(lambda:fp.read(1024*1024),b""):h.update(piece)
    return h.hexdigest()


def image(f):
    with Image.open(f) as im:
        if im.mode!="RGBA" or im.size!=(1024,1024):
            raise AssertionError(f"Expected 1024x1024 RGBA: {f}")
        return np.asarray(im).copy()


def mask_score(render,reference):
    a=render[:,:,3]>=128
    b=reference[:,:,3]>=128
    union=int(np.logical_or(a,b).sum())
    intersection=int(np.logical_and(a,b).sum())
    aarea=int(a.sum());barea=int(b.sum())
    return {
       "silhouetteIoU":round(intersection/max(1,union),6),
       "relativeAreaError":round(abs(aarea-barea)/max(1,barea),6),
       "headIoU":round(float(np.logical_and(a[:710],b[:710]).sum())/
                       max(1,int(np.logical_or(a[:710],b[:710]).sum())),6)
    }


def draw_over_white(arr):
    a=arr[:,:,3:].astype(np.float32)/255
    return arr[:,:,:3].astype(np.float32)*a+255*(1-a)


def verify():
    sources,_,roles,trace=source_registry()
    public={}
    frame_images={}
    for engine,rel in RENDERERS.items():
        base=PRIVATE/rel
        qa=json.loads((base/"qa.json").read_text())
        if qa["characterId"]!=PROJECT or len(qa["frames"] if "frames" in qa else qa["renderedFrames"])!=37:
            raise AssertionError("P15-07 complete 37-frame source manifest absent")
        rows=qa["frames"] if "frames" in qa else qa["renderedFrames"]
        by_angle={float(e.get("angle",e.get("yaw"))):e for e in rows}
        if set(by_angle)!=set(ANGLES):
            raise AssertionError("P15-07 frame angle grid changed")
        pixel_exact=[]
        samples=[]
        prev=None
        temporal=[]
        for yaw in ANGLES:
            entry=by_angle[yaw]
            f=base/output_frame_id(yaw)
            if str(f.relative_to(PRIVATE))!=entry["path"] or sha(f)!=entry["sha256"]:
                raise AssertionError(f"P15-07 frame SHA changed: {engine}/{yaw}")
            pix=image(f)
            if yaw in sources:
                expected=image(sources[yaw])
                difference=int(np.abs(pix.astype(np.int16)-expected.astype(np.int16)).max())
                if difference!=0:
                    raise AssertionError(f"Input key artwork mutated {engine}/{yaw}")
                pixel_exact.append(yaw)
            if yaw in REFERENCE:
                ref=PRIVATE/REFERENCE[yaw]
                samples.append({
                   "yaw":yaw,
                   "referenceRole":"P14_GENERATED_CANDIDATE_COMPARISON_ONLY",
                   "referenceSHA256":sha(ref),
                   "metrics":mask_score(pix,image(ref)),
                })
            if prev is not None:
                rgb_a=draw_over_white(prev)
                rgb_b=draw_over_white(pix)
                delta=float(np.abs(rgb_a-rgb_b).mean())
                alpha_a=prev[:,:,3]>=128
                alpha_b=pix[:,:,3]>=128
                temporal.append({
                    "from":yaw-2.5,"to":yaw,
                    "meanAdjacentRGBChange":round(delta,6),
                    "alphaIoU":round(float(np.logical_and(alpha_a,alpha_b).sum())/
                         max(1,int(np.logical_or(alpha_a,alpha_b).sum())),6)
                })
            prev=pix
        values=np.asarray([e["meanAdjacentRGBChange"] for e in temporal])
        median=float(np.median(values))
        outliers=[x for x in temporal if x["meanAdjacentRGBChange"]>median*2.5]
        public[engine]={
           "renderDirectory":rel,
           "sourceKeyviewsPixelExact":pixel_exact,
           "frameCount":len(ANGLES),
           "rendererQASHA256":sha(base/"qa.json"),
           "paintedReferenceComparisons":samples,
           "temporalMedianRGBChange":round(median,6),
           "temporalMaxRGBChange":round(float(values.max()),6),
           "temporalOutliers":outliers,
           "adjacentFrameMetrics":temporal,
        }
    browser=PRIVATE/"p15-07-browser/qa.json"
    if not browser.is_file():raise AssertionError("Chromium P15-07 review evidence missing")
    browser_qa=json.loads(browser.read_text())
    if browser_qa["status"]!="HTML_INTERACTIVE_SOURCE_LOAD_PASS" or browser_qa["javascriptErrors"] or browser_qa["failedRequests"]:
        raise AssertionError("P15-07 browser QA status mismatch")
    if browser_qa["screenshotCount"]<8:
        raise AssertionError("P15-07 minimum browser screenshots missing")
    audit={
      "schema":"KOMA-P15-07-SHORT-ARC-RENDERER-ACCEPTANCE-V1",
      "characterId":PROJECT,
      "sourceOriginalAngles":[0,45,90],
      "paintedCandidateInputAngles":[65.,77.5],
      "sourceKeyframeProvenance":trace,
      "sourceSemanticRoles":list(roles),
      "renderers":public,
      "browser":{
        "qaPath":"private-assets/p15-07-browser/qa.json",
        "qaSHA256":sha(browser),
        "screenshotCount":browser_qa["screenshotCount"],
        "imageLoads":browser_qa["verifiedSourceImageLoads"],
        "javascriptErrors":len(browser_qa["javascriptErrors"]),
        "failedRequests":len(browser_qa["failedRequests"])
      },
      "visualReview":{
        "reviewedAngles":[45,55,65,67.5,72.5,77.5,85,90],
        "observed45to65Transition":"source pose gap; 55 degree facial contour and accessory/neck geometry require separately authored key art",
        "observedSemanticTransitions":"source-aligned semantic layer boundaries diverge around facial contours, rear hair, ear and collar",
        "observedWholeGeometry":"outline improved around 67.5/72.5/85 degrees but whole-image transport does not preserve semantic topology",
        "requiredNextInputs":["55_degree_keyview_with_physical_face_anchors",
                              "independent_semantic_occlusion_and_hidden_fills",
                              "original_hero_source_identity_verification"],
        "artisticStatus":"REWORK_REQUIRED",
      },
      "technicalGate":"SOURCE_INTEGRITY_AND_BROWSER_PASS",
      "overallStatus":"P15_07_ENGINEERING_REVIEW_COMPLETE_ARTWORK_REFINEMENT",
      "identityHeroApprovedSha256Verified":False,
      "next":"P15-08 45-to-65 authored source registration and view-dependent stroke topology"
    }
    dest=ROOT/"evidence/p15-07-renderer-qa.json"
    dest.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({
      "status":audit["overallStatus"],
      "frames":sum(x["frameCount"] for x in public.values()),
      "browserScreenshots":audit["browser"]["screenshotCount"],
      "renderers":{k:{
        "median":v["temporalMedianRGBChange"],
        "peak":v["temporalMaxRGBChange"],
        "outliers":len(v["temporalOutliers"]),
        "paintedReferenceIoU":{str(s["yaw"]):s["metrics"]["silhouetteIoU"] for s in v["paintedReferenceComparisons"]}
      } for k,v in public.items()},
      "visualStatus":audit["visualReview"]["artisticStatus"]
    },ensure_ascii=False))
    return audit


if __name__=="__main__":
    verify()

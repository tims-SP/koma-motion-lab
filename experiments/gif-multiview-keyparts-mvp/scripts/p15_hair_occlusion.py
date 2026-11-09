#!/usr/bin/env python3
"""P15-05 original-P0 hair strand IDs, physical anchors, and depth masks.

The four hair source parts are tracked through 45/67.5/72.5/90 degrees.
Separately generated pixels are verified by SHA. P10 candidate matches and
P5 projected anchors are explicit, while geometric occlusion is measured from
the original native alpha layers.
"""
import argparse
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
from p9_color_region_correspondence import read as read_rgba, SOURCE_SIZE
from p15_anatomical_strokes import (
    sha, parse, verify_asset, alpha_centroid,
    source_anchor, shift_from_measured_alpha, trace, match_pair,
)

ROLE_SET=("hair.back","hair.side","hair.front","hair.ahoge")
KEYS=(45,67.5,72.5,90)
PAIRS=((45,67.5),(67.5,72.5),(72.5,90))
CONTEXT=("face.skin","eye.near","ear.near")
ANCHORS={
    "hair.back":("hair.back","hair.ahoge.root"),
    "hair.side":("hair.side","ear.near"),
    "hair.front":("hair.front","eye.near.iris"),
    "hair.ahoge":("hair.ahoge.root",),
}
OCCLUSION=(
    ("hair.front","eye.near"),
    ("hair.side","ear.near"),
    ("face.skin","hair.back"),
    ("hair.ahoge","hair.front"),
)
EXPECTED_DEPTH={
    "hair.back":1,"face.skin":2,"ear.near":4,
    "hair.side":5,"eye.near":7,"hair.front":10,"hair.ahoge":11
}


def registry(root):
    orig=parse(root/"p5-see-through/mv-candidate/parts.json")
    view67=parse(root/"p14-authored-candidates/yaw067p5-artmesh/qa.json")
    view72=parse(root/"p14-authored-candidates/yaw072p5-artmesh/qa.json")
    anchors=parse(root/"p5-see-through/mv-candidate/landmark-qa.json")
    regions=parse(root/"p9-region-correspondence/qa.json")
    if any(x["characterId"]!="p0_character_001" for x in (orig,view67,view72,anchors,regions)):
        raise ValueError("P0 source lineage mismatch")
    source={}
    for x in orig["parts"]:
        angle=x["yawDeg"];role=x["semanticId"]
        if angle in (45,90) and role in ROLE_SET+CONTEXT:
            source[angle,role]={"path":verify_asset(root,x,"frameSha256"),
                                "sha256":x["frameSha256"],
                                "depth":x["depthOrder"],
                                "visibility":x["visibility"]}
    for angle,view,field in ((67.5,view67,"parts"),(72.5,view72,"semanticLayerRecords")):
        for x in view[field]:
            role=x["semanticId"]
            if role in ROLE_SET+CONTEXT:
                source[angle,role]={"path":verify_asset(root,x,"sha256"),
                                    "sha256":x["sha256"],
                                    "depth":x["depthOrder"],
                                    "visibility":"visible" if x.get("alphaPixels",x.get("visibleAlphaPixels",0)) else "hidden"}
    if len(source)!=len(KEYS)*(len(ROLE_SET)+len(CONTEXT)):
        raise ValueError("P0 hair and feature-layer slot registry incomplete")
    for (angle,role),item in source.items():
        if item["depth"]!=EXPECTED_DEPTH[role]:
            raise AssertionError("P0 layer depth changed: "+role+" "+str(angle))
    return source,anchors,regions


def alpha_mask(root,source,angle,role):
    entry=source[angle,role]
    path=entry["path"]
    with Image.open(path) as im:
        alpha=np.asarray(im.getchannel("A"))
    return alpha


def occlusion_measure(front_alpha,back_alpha):
    if front_alpha.shape!=back_alpha.shape:
        raise ValueError("Same global P0 canvas required")
    top=front_alpha>=64
    behind=back_alpha>=64
    both=top & behind
    upper=int(top.sum());lower=int(behind.sum())
    return {
        "frontVisiblePixels":upper,
        "backVisiblePixels":lower,
        "overlapPixels":int(both.sum()),
        "backAlphaCoveredFraction":round(float(both.sum())/max(1,lower),6),
        "singleVisibleBoundaryPixels":int((top ^ behind).sum()),
    }


def trace_inks(root,source,regions):
    inks={}
    for role in ROLE_SET:
        p=regions["pairs"].get("45-90/"+role)
        colors=np.asarray(p["paletteLab"],dtype=np.float32) if p else np.asarray([[80,128,128]],np.float32)
        for angle in KEYS:
            im=read_rgba(source[angle,role]["path"])
            inks[angle,role]=trace(im,role,angle,colors)
    return inks


def compare_strands(root,source,anchors,regions):
    inks=trace_inks(root,source,regions)
    matches={}
    for role in ROLE_SET:
        for a,b in PAIRS:
            rgbaA=read_rgba(source[a,role]["path"])
            rgbaB=read_rgba(source[b,role]["path"])
            alphaA=alpha_centroid(rgbaA);alphaB=alpha_centroid(rgbaB)
            shift=shift_from_measured_alpha(alphaA,alphaB)
            accepted=match_pair(inks[a,role],inks[b,role],shift,limit=60)
            explicit={}
            for label in ANCHORS[role]:
                p1=source_anchor(anchors,label,a)
                p2=source_anchor(anchors,label,b)
                if p1 is not None and p2 is not None:
                    explicit[label]={"from":p1.round(3).tolist(),
                                     "to":p2.round(3).tolist(),
                                     "sourceRole":"P5_LINEAR_REFERENCE"}
            matches[str(a)+"-"+str(b)+"/"+role]={
                "semanticId":role,"angles":[a,b],
                "source":{
                    "a":{"path":str(source[a,role]["path"].relative_to(root)),
                          "sha256":source[a,role]["sha256"]},
                    "b":{"path":str(source[b,role]["path"].relative_to(root)),
                          "sha256":source[b,role]["sha256"]}
                },
                "observedCentroidShift443":shift.round(3).tolist(),
                "P5ProjectedAnchors":explicit,
                "sourceStrokeCount":len(inks[a,role]),
                "targetStrokeCount":len(inks[b,role]),
                "matchedStrokeCount":len(accepted),
                "accepted":accepted,
                "unmatchedFrom":len(inks[a,role])-len(accepted),
                "unmatchedTo":len(inks[b,role])-len(accepted),
                "artisticStatus":"SOURCE_BACKED_STROKE_CANDIDATES"
            }
    return matches


def preview(root,source,links,file):
    width=300;height=325
    picture=Image.new("RGB",(4*width,len(ROLE_SET)*height),(39,52,68))
    draw=ImageDraw.Draw(picture)
    for row,role in enumerate(ROLE_SET):
        for col,angle in enumerate(KEYS):
            p=source[angle,role]["path"]
            with Image.open(p) as layer:
                background=Image.new("RGBA",(1024,1024),(47,62,80,255))
                background.alpha_composite(layer.convert("RGBA"))
                thumb=background.convert("RGB").resize((width,width),Image.Resampling.LANCZOS)
            picture.paste(thumb,(col*width,row*height))
            draw.text((col*width+8,row*height+width+6),role+" "+str(angle),fill="white")
        for col,(a,b) in enumerate(PAIRS):
            pair=links[str(a)+"-"+str(b)+"/"+role]
            for record in pair["accepted"]:
                x1=col*width+record["sourceXY"][0]*width/SOURCE_SIZE
                y1=row*height+record["sourceXY"][1]*width/SOURCE_SIZE
                x2=(col+1)*width+record["targetXY"][0]*width/SOURCE_SIZE
                y2=row*height+record["targetXY"][1]*width/SOURCE_SIZE
                draw.line((x1,y1,x2,y2),fill="#55e6bc",width=1)
                draw.ellipse((x1-2,y1-2,x1+2,y1+2),fill="#f8d4a9")
                draw.ellipse((x2-2,y2-2,x2+2,y2+2),fill="#f8d4a9")
    file.parent.mkdir(parents=True,exist_ok=True)
    picture.save(file,quality=92)
    return sha(file)


def run(root,out,preview_path):
    root=Path(root).resolve();out=Path(out).resolve()
    source,anchors,regions=registry(root)
    links=compare_strands(root,source,anchors,regions)
    bound={}
    for angle in KEYS:
        rows={}
        for upper,lower in OCCLUSION:
            if source[angle,upper]["depth"]<=source[angle,lower]["depth"]:
                raise AssertionError("Inverse P0 depth ordering")
            top=alpha_mask(root,source,angle,upper)
            bottom=alpha_mask(root,source,angle,lower)
            rows[upper+">"+lower]={
                "frontSemanticId":upper,
                "backSemanticId":lower,
                "frontDepthOrder":source[angle,upper]["depth"],
                "backDepthOrder":source[angle,lower]["depth"],
                **occlusion_measure(top,bottom)
            }
        bound[str(angle)]=rows
    image=Path(preview_path).resolve()
    preview_hash=preview(root,source,links,image)
    unique_sources={item["sha256"] for item in source.values()}
    accepted=sum(len(x["accepted"]) for x in links.values())
    data={
        "schema":"KOMA-P0-P15-05-HAIR-INK-OCCLUSION-CORRESPONDENCE-V1",
        "characterId":"p0_character_001",
        "originalAngles":[45,90],
        "generatedIntermediateAngles":[67.5,72.5],
        "semanticRoles":list(ROLE_SET),
        "nativeCanvas":[1024,1024],
        "workingStrokeCanvas":[SOURCE_SIZE,SOURCE_SIZE],
        "sourceViewSlotsVerified":len(source),
        "sourceSHA256UniqueCount":len(unique_sources),
        "semanticStrokeViewPairs":len(links),
        "candidateStrokeMatches":accepted,
        "sourceMetadataSHA256":{
            "P5ArtMesh":sha(root/"p5-see-through/mv-candidate/parts.json"),
            "P5Landmarks":sha(root/"p5-see-through/mv-candidate/landmark-qa.json"),
            "P9Palette":sha(root/"p9-region-correspondence/qa.json"),
            "P10StrokeBaseline":sha(root/"p10-stroke-identity/qa.json")
        },
        "strandPairCorrespondence":links,
        "depthOcclusion":bound,
        "occlusionPairCount":sum(len(x) for x in bound.values()),
        "occlusionMethod":"SOURCE_RGBA_ALPHA_OVERLAP_AND_DECLARED_SEMANTIC_DEPTH",
        "preview":{
            "privateRelativePath":str(image.relative_to(root)),
            "sha256":preview_hash
        },
        "renderBaseline":"P8_SEMANTIC_OCCLUSION_ARTMESH",
        "artisticAcceptance":"PENDING_ORIGINAL_STRAND_IDENTITY_REVIEW",
        "status":"P15_05_HAIR_SOURCE_CORRESPONDENCE_REGISTERED"
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"status":data["status"],
        "sourceLayers":data["sourceViewSlotsVerified"],
        "pairs":data["semanticStrokeViewPairs"],
        "matchedStrokes":accepted,
        "occlusionChecks":data["occlusionPairCount"],
        "byPair":{k:len(v["accepted"]) for k,v in links.items()}},ensure_ascii=False))
    return data


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--preview",required=True)
    a=p.parse_args()
    run(a.root,a.out,a.preview)

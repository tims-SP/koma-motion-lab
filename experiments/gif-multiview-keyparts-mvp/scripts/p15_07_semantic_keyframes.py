#!/usr/bin/env python3
"""P15-07 view-conditioned ArtMesh interpolation with painted P0 key artworks.

P0 original 45/90 source and P15 65/77.5 painted RGBA keyviews are immutable.
Intermediate views are newly rendered from 13 independently registered parts,
using short-arc optical flow, explicit depth, and semantic visibility.
Artwork at 65/77.5 is a renderer input and cannot be used as its own holdout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from flow_render import get_flow
from p7_semantic_dense_flow import CANVAS, part_to_native, native_to_rgba
from p1_front_semantic import alpha_over
from p8_semantic_occlusion import output_frame_id

PROJECT = "p0_character_001"
ROOT = Path(__file__).resolve().parent.parent
PRIVATE = ROOT / "private-assets"
STOPS = (45.,65.,77.5,90.)
P15_KEY = {65.:"yaw065",77.5:"yaw077p5"}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for part in iter(lambda:f.read(1024*1024),b""):h.update(part)
    return h.hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def native_layer(path):
    if not Path(path).is_file(): raise FileNotFoundError(path)
    return part_to_native(path)


def source_registry():
    base=load(PRIVATE/"p5-see-through/mv-candidate/parts.json")
    if base["characterId"]!=PROJECT:raise ValueError("P0 identity registry mismatch")
    original={int(q["yawDeg"]):q for q in base["wholeViews"]}
    sources={};layers={};inputs={}
    depth_ref={e["semanticId"]:int(e["depthOrder"]) for e in base["parts"] if e["yawDeg"]==45}
    roles=tuple(k for k,v in sorted(depth_ref.items(),key=lambda t:t[1]))
    if len(roles)!=13 or set(depth_ref.values())!=set(range(13)):
        raise AssertionError("P0 canonical ArtMesh 13-layer depth mapping differs")
    for angle in (45.,90.):
        o=original[int(angle)]
        f=PRIVATE/o["path"]
        if sha(f)!=o["sha256"]:raise ValueError("Original keyview SHA mismatch")
        sources[angle]=f
        entries=[e for e in base["parts"] if e["yawDeg"]==int(angle)]
        if len(entries)!=13:raise AssertionError("Original semantic count differs")
        for e in entries:
            role=e["semanticId"];part=PRIVATE/e["path"]
            if sha(part)!=e["frameSha256"] or e["depthOrder"]!=depth_ref[role]:
                raise ValueError(f"Original P0 role provenance mismatch {angle}/{role}")
            layers[angle,role]=part
        inputs[str(angle)]={"source":"P0_ORIGINAL","path":o["path"],"sha256":o["sha256"]}
    for angle,key in P15_KEY.items():
        q=load(PRIVATE/f"p15-independent-candidates/{key}-artmesh/ingest-qa.json")
        if q["characterId"]!=PROJECT or float(q["yaw"])!=angle:
            raise ValueError("P15 painted keyview registry mismatch")
        painted=q["referencePainting"]; f=PRIVATE/painted["path"]
        if sha(f)!=painted["sha256"]:
            raise ValueError("Painted P0 source SHA mismatch")
        if q["partCount"]!=13 or q["recomposition"]["maximumAlphaDifference"]!=0 or q["recomposition"]["maximumVisibleRGBDifference"]!=0:
            raise ValueError("Painted P0 source layer reconstruction failed")
        role_records={p["semanticId"]:p for p in q["semanticLayers"]}
        if set(role_records)!=set(roles):raise ValueError("P15 canonical semantic IDs incomplete")
        for role in roles:
            item=role_records[role]
            if item["depthOrder"]!=depth_ref[role]:
                raise ValueError(f"P15 semantic depth mismatch {angle}/{role}")
            part=PRIVATE/item["path"]
            if sha(part)!=item["sourceSHA256"]:
                raise ValueError(f"P15 painted role SHA mismatch {angle}/{role}")
            layers[angle,role]=part
        sources[angle]=f
        inputs[str(angle)]={"source":"P15_PAINTED_KEYVIEW_CANDIDATE",
                            "path":painted["path"],"sha256":painted["sha256"]}
    return sources,layers,roles,inputs


def smoothstep(t,lo,hi):
    v=np.clip((t-lo)/(hi-lo),0,1)
    return v*v*(3-2*v)


def signed_distance(alpha):
    fg=np.uint8(alpha>=.5)
    ins=cv2.distanceTransform(fg,cv2.DIST_L2,3)
    outside=cv2.distanceTransform(1-fg,cv2.DIST_L2,3)
    return ins-outside


def warp_part(source,flow,t,gx,gy):
    return cv2.remap(source,gx-t*flow[:,:,0],gy-t*flow[:,:,1],
                     cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)


def blend_painted_part(wa,wb,t,blend_mode="ink-owner"):
    alpha_a=wa[:,:,3];alpha_b=wb[:,:,3]
    visible_a=bool(np.max(alpha_a)>.003)
    visible_b=bool(np.max(alpha_b)>.003)
    if not visible_a and not visible_b:
        return np.zeros_like(wa)
    if not visible_a or not visible_b:
        visible=wb if visible_b else wa
        scalar=smoothstep(t,.1,1.) if visible_b else 1-smoothstep(t,0.,.9)
        return visible*scalar
    # Signed-distance interpolates geometry while keeping a single silhouette
    # instead of stacking two semi-transparent character outlines.
    field=(1-t)*signed_distance(alpha_a)+t*signed_distance(alpha_b)
    mask=np.clip(field+.5,0,1)
    if blend_mode=="ink-owner":
        owner,backup=(wa,wb) if t<.5 else (wb,wa)
        chosen=np.where(owner[:,:,3:4]>.025,owner,backup)
    elif blend_mode=="ink-transition":
        mix=smoothstep(t,.40,.60)
        chosen=wa*(1-mix)+wb*mix
    else:raise ValueError(blend_mode)
    original_a=np.maximum(chosen[:,:,3:4],1e-5)
    rgb=np.clip(chosen[:,:,:3]/original_a,0,1)
    return np.concatenate([rgb*mask[:,:,None],mask[:,:,None]],axis=2).astype(np.float32)


def render(angles,out,blend_mode):
    sources,paths,roles,provenance=source_registry()
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    gridx,gridy=np.meshgrid(np.arange(CANVAS,dtype=np.float32),
                            np.arange(CANVAS,dtype=np.float32))
    needed=set()
    for angle in angles:
        if angle not in STOPS and angle>45:
            a,b=next(((a,b) for a,b in zip(STOPS[:-1],STOPS[1:]) if a<angle<b),(None,None))
            if a is None:raise ValueError(f"Angle {angle} outside registered interval")
            needed.add((a,b))
    flows={};samples={};stats={}
    for a,b in sorted(needed):
        stats[f"{a}-{b}"]={}
        for role in roles:
            for angle in (a,b):
                if (angle,role) not in samples:
                    samples[angle,role]=native_layer(paths[angle,role])
            x=samples[a,role];y=samples[b,role]
            if min(float(x[:,:,3].max()),float(y[:,:,3].max()))<=.003:
                flows[a,b,role]=None
                continue
            forward,reverse=get_flow(native_to_rgba(x),native_to_rgba(y),mode="dis")
            flows[a,b,role]=(forward,reverse)
            stats[f"{a}-{b}"][role]={
                "flowForwardMean":round(float(np.linalg.norm(forward,axis=2).mean()),4),
                "flowReverseMean":round(float(np.linalg.norm(reverse,axis=2).mean()),4)}
    baseline=None
    if any(a<45. for a in angles):
        baseline=load(PRIVATE/"p8-semantic-occlusion/selective-sequence/qa.json")
        if baseline["characterId"]!=PROJECT:raise ValueError("P8 baseline identity mismatch")
        existing={float(q["angle"]):q for q in baseline["frames"]}
    results=[]
    for angle in angles:
        angle=float(angle)
        if angle in sources:
            with Image.open(sources[angle]) as img:
                frame=img.convert("RGBA").copy()
            kind=provenance[str(angle)]["source"]
        elif angle<45:
            sample=existing.get(angle)
            if sample is None:raise ValueError("0–45 baseline frame unavailable")
            f=PRIVATE/sample["path"]
            if sha(f)!=sample["sha256"]:raise ValueError("P8 baseline frame changed")
            with Image.open(f) as img:frame=img.convert("RGBA").copy()
            kind="P8_ORIGINAL_SOURCE_VDD"
        else:
            a,b=next((pair for pair in needed if pair[0]<angle<pair[1]),(None,None))
            if a is None:raise ValueError(f"Intermediate view missing {angle}")
            t=(angle-a)/(b-a)
            canvas=np.zeros((CANVAS,CANVAS,4),dtype=np.uint8)
            for role in roles:
                pa,pb=samples[a,role],samples[b,role]
                flow=flows[a,b,role]
                if flow is None:
                    if np.max(pa[:,:,3])<=.003:
                        merged=pb*smoothstep(t,.1,1.)
                    elif np.max(pb[:,:,3])<=.003:
                        merged=pa*(1-smoothstep(t,0.,.9))
                    else:merged=np.zeros_like(pa)
                else:
                    fa,fb=flow
                    wa=warp_part(pa,fa,t,gridx,gridy)
                    wb=warp_part(pb,fb,1-t,gridx,gridy)
                    merged=blend_painted_part(wa,wb,t,blend_mode)
                canvas=alpha_over(canvas,native_to_rgba(merged))
            frame=Image.fromarray(canvas,"RGBA").resize((1024,1024),Image.Resampling.LANCZOS)
            kind="P15_SHORT_ARC_SEMANTIC_VDD"
        f=out/output_frame_id(angle)
        frame.save(f)
        if angle in sources:
            ref=np.asarray(Image.open(sources[angle]).convert("RGBA"))
            cur=np.asarray(frame.convert("RGBA"))
            if not np.array_equal(ref,cur):
                raise AssertionError(f"Source keyview altered {angle}")
        results.append({"yaw":angle,"path":str(f.relative_to(PRIVATE)),
                        "sha256":sha(f),"source":kind})
    qa={"schema":"KOMA-P15-07-SEMANTIC-SHORT-ARC-VDD-V1","characterId":PROJECT,
        "sourceViews":provenance,"keyAngles":list(STOPS),"sourceSemanticRoles":list(roles),
        "renderedFrames":results,"flowPairs":stats,
        "blendMode":blend_mode,
        "artisticStatus":"CANDIDATE_REVIEW",
        "sourceAdmission":"P15 independent paintings require visual identity signoff",
        "status":"P15_07_SEMANTIC_PREVIEW_RENDERED"}
    (out/"qa.json").write_text(json.dumps(qa,ensure_ascii=False,indent=2)+"\n")
    board=Image.new("RGB",(320*len(results),360),(245,245,245))
    d=ImageDraw.Draw(board)
    for i,r in enumerate(results):
        source=out/output_frame_id(r["yaw"])
        with Image.open(source) as image:
            matte=Image.new("RGBA",image.size,(250,250,250,255))
            matte.alpha_composite(image.convert("RGBA"))
        board.paste(matte.convert("RGB").resize((320,320)),(i*320,25))
        d.text((i*320+12,5),f'{r["yaw"]} degrees',fill=(0,0,0))
    contact=out/"p15-07-semantic-contact.jpg"
    board.save(contact,quality=91)
    print(json.dumps({"status":qa["status"],"frames":len(results),
                      "registeredPairs":len(needed),
                      "sourceKeys":list(STOPS),"contactSHA":sha(contact)}))
    return qa


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--angles",default="45,50,55,60,65,67.5,70,72.5,75,77.5,80,85,90")
    ap.add_argument("--out",default="private-assets/p15-07-semantic-preview")
    ap.add_argument("--mode",choices=["ink-owner","ink-transition"],default="ink-owner")
    args=ap.parse_args()
    out=Path(args.out)
    if not out.is_absolute():out=ROOT/out
    render([float(v) for v in args.angles.split(",")],out,args.mode)

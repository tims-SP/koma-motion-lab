#!/usr/bin/env python3
"""Whole-keyframe geometry reference for the P15-07 semantic ArtMesh experiment.

This reference path deliberately has no per-part occlusion reasoning. It is
compared with the semantic ArtMesh pipeline, not promoted as an engine.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from p15_07_geometry_bridge import (P, N, field, warp, compose, sha)
from p8_semantic_occlusion import output_frame_id
from p15_07_semantic_keyframes import source_registry, STOPS, PROJECT

ROOT = Path(__file__).resolve().parent.parent


def render(angles, out):
    sources, _, _, trace = source_registry()
    art = {}
    for angle in STOPS:
        with Image.open(sources[angle]) as img:
            art[angle] = np.asarray(img.convert("RGBA")).copy()
    all_pairs = list(zip(STOPS[:-1],STOPS[1:]))
    requested = {(a,b) for a,b in all_pairs
                 if any(a < angle < b for angle in angles)}
    motion={}
    for a,b in requested:
        motion[a,b]=field(art[a],art[b])
    coords=np.meshgrid(np.arange(N,dtype=np.float32),
                       np.arange(N,dtype=np.float32))
    baseline=json.loads((P/"p8-semantic-occlusion/selective-sequence/qa.json").read_text())
    if baseline["characterId"] != PROJECT:
        raise ValueError("P8 original source lineage mismatch")
    old={float(x["angle"]):x for x in baseline["frames"]}
    out=Path(out).resolve()
    out.mkdir(parents=True,exist_ok=True)
    frames=[]
    for yaw in angles:
        yaw=float(yaw)
        if yaw in art:
            frame=art[yaw].copy()
            kind="PAINTED_SOURCE"
        elif yaw<45:
            entry=old.get(yaw)
            if not entry:raise ValueError(f"P8 {yaw} source frame absent")
            f=P/entry["path"]
            if sha(f)!=entry["sha256"]:raise ValueError("P8 frame SHA mismatch")
            with Image.open(f) as im:
                frame=np.asarray(im.convert("RGBA")).copy()
            kind="P8_SOURCE_DERIVED"
        else:
            a,b=next(((a,b) for a,b in requested if a<yaw<b),(None,None))
            if a is None:raise ValueError(f"Angle {yaw} unregistered")
            t=(yaw-a)/(b-a)
            fa,fb=motion[a,b]
            wa=warp(art[a],fa,t,coords)
            wb=warp(art[b],fb,1-t,coords)
            frame=compose(wa,wb,t,"source-owner",None)
            kind="WHOLE_SOURCE_OWNER"
        out_file=out/output_frame_id(yaw)
        Image.fromarray(frame,"RGBA").save(out_file)
        if yaw in art and not np.array_equal(art[yaw],frame):
            raise AssertionError("Reference keyview changed")
        frames.append({"yaw":yaw,"kind":kind,
                       "path":str(out_file.relative_to(P)),
                       "sha256":sha(out_file)})
    qa={"schema":"KOMA-P15-07-WHOLEVIEW-GEOMETRY-REFERENCE-V1",
        "characterId":PROJECT,
        "keyAngles":list(STOPS),
        "keySources":trace,
        "rendering":"global DIS + signed-distance silhouette + source-owner texture",
        "frameCount":len(frames),"frames":frames,
        "intendedUse":"diagnostic geometry comparator",
        "artisticAcceptance":"PENDING_VISUAL_REVIEW"}
    (out/"qa.json").write_text(json.dumps(qa,ensure_ascii=False,indent=2)+"\n")
    contact=Image.new("RGB",(320*len(angles),350),(246,246,246))
    draw=ImageDraw.Draw(contact)
    for i,angle in enumerate(angles):
        with Image.open(out/output_frame_id(angle)) as src:
            im=Image.new("RGBA",src.size,"white")
            im.alpha_composite(src.convert("RGBA"))
        contact.paste(im.convert("RGB").resize((320,320)),(i*320,26))
        draw.text((i*320+6,6),f"{angle}°",fill="black")
    contact_path=out/"p15-07-whole-keyframes.jpg"
    contact.save(contact_path,quality=90)
    print(json.dumps({"status":"P15_07_WHOLE_REFERENCE_RENDERED",
                      "frames":len(frames),
                      "registeredPairs":len(requested),
                      "contactSHA256":sha(contact_path)}))
    return qa


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--angles",default=",".join(str(2.5*x) for x in range(37)))
    p.add_argument("--out",default="private-assets/p15-07-wholekey-preview")
    args=p.parse_args()
    output=Path(args.out)
    if not output.is_absolute():output=ROOT/output
    render([float(x) for x in args.angles.split(",")],output)

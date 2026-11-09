#!/usr/bin/env python3
"""Verify independent full-canvas P0 semantic paintings before ArtMesh import.

This ingestion accepts thirteen separately painted native RGBA layers and
compares their depth composite with one independently provided source painting.
The same mechanism can be exercised with older P14 sources as regression
fixtures; only original P15-06 artwork may pass the production holdout gate.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

CHARACTER="p0_character_001"
ROLES=(
    "body.reference","hair.back","face.skin","ear.far","ear.near",
    "hair.side","eye.far","eye.near","nose","mouth","hair.front",
    "hair.ahoge","hair.clip.cross_gold",
)
HOLDOUTS=(65.0,77.5)
CANVAS=(1024,1024)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf8"))


def contained(file,base):
    file=Path(file).resolve()
    base=Path(base).resolve()
    if not file.is_relative_to(base):
        raise ValueError("Semantic source path outside permitted asset workspace")
    return file


def canonical_depth(original):
    matrix={}
    for item in original["parts"]:
        if item["yawDeg"] not in (45,90):
            continue
        role=item["semanticId"]
        if role not in ROLES:
            continue
        order=int(item["depthOrder"])
        if role in matrix and matrix[role]!=order:
            raise ValueError("P0 original depth order mismatch")
        matrix[role]=order
    if set(matrix)!=set(ROLES) or len(set(matrix.values()))!=len(ROLES):
        raise ValueError("Canonical original P0 part/depth contract incomplete")
    return matrix


def open_layer(path):
    with Image.open(path) as im:
        if im.mode!="RGBA" or im.size!=CANVAS:
            raise ValueError("P0 source layer requires 1024x1024 native RGBA: "+str(path))
        return im.copy()


def composite(layers):
    result=Image.new("RGBA",CANVAS,(0,0,0,0))
    for layer in layers:
        if layer.mode!="RGBA" or layer.size!=CANVAS:
            raise ValueError("Source-native 1024x1024 RGBA only")
        result=Image.alpha_composite(result,layer)
    return result


def diff(a,b):
    aa=np.asarray(a.convert("RGBA")).astype(np.int16)
    bb=np.asarray(b.convert("RGBA")).astype(np.int16)
    if aa.shape!=bb.shape:
        raise ValueError("Unaligned original-paint composite")
    alpha=int(np.abs(aa[:,:,3]-bb[:,:,3]).max())
    visible=(aa[:,:,3]>=24)|(bb[:,:,3]>=24)
    rgb=int(np.abs(aa[:,:,:3]-bb[:,:,:3])[visible].max()) if visible.any() else 0
    mean=float(np.abs(aa[:,:,:3]-bb[:,:,:3])[visible].mean()) if visible.any() else 0
    return {"maximumAlphaDifference":alpha,"maximumVisibleRGBDifference":rgb,
            "meanVisibleRGBDifference":round(mean,4)}


def run(root,contract_path,angle,parts_path,painting_path,out,source_kind,
        source_model=None,source_seed=None):
    root=Path(root).resolve()
    p=contained(parts_path,root)
    painting_path=contained(painting_path,root)
    original=read(root/"p5-see-through/mv-candidate/parts.json")
    contract=read(contract_path)
    if contract["characterId"]!=CHARACTER or original["characterId"]!=CHARACTER:
        raise ValueError("P0 original identity mismatch")
    if source_kind=="independent-painting":
        if float(angle) not in HOLDOUTS:
            raise ValueError("Independent P15-06 angle must be 65 or 77.5")
        if not source_model or source_seed is None:
            raise ValueError("Independent painting requires model/producer provenance")
    elif source_kind!="registered-p14-fixture":
        raise ValueError("Unknown source artwork provenance")
    if p.is_symlink() or not p.is_dir():
        raise ValueError("Original painted semantic part directory required")
    order=canonical_depth(original)
    pixels={}
    meta=[]
    for role in ROLES:
        filename=contained(p/(role+".png"),root)
        if not filename.is_file():
            raise ValueError("Required isolated P0 semantic part absent: "+role)
        layer=open_layer(filename)
        alpha=np.asarray(layer.getchannel("A"))
        cnt=int((alpha>0).sum())
        if cnt==0 and role in ("face.skin","hair.front","hair.back","body.reference"):
            raise ValueError("Expected major P0 part has no visible pixels: "+role)
        meta.append({
            "semanticId":role,
            "depthOrder":order[role],
            "path":str(filename.relative_to(root)),
            "sourceSHA256":sha(filename),
            "visiblePixels":cnt,
            "partialAlphaPixels":int(((alpha>0)&(alpha<255)).sum()),
            "bboxRGBA":list(layer.getbbox()) if layer.getbbox() else None,
            "registeredCanvas":list(CANVAS),
            "sourceKind":source_kind,
        })
        pixels[role]=layer

    with Image.open(painting_path) as paint:
        if paint.mode!="RGBA" or paint.size!=CANVAS:
            raise ValueError("Original reference painting must be full-canvas RGBA")
        target=paint.copy()
    output=composite([pixels[x["semanticId"]] for x in sorted(meta,key=lambda x:x["depthOrder"])])
    delta=diff(output,target)
    # Source pixel exactness is a necessary engineering gate, not an artistic approval.
    if delta["maximumAlphaDifference"]>1 or delta["maximumVisibleRGBDifference"]>3:
        raise ValueError("Painted RGBA layers do not recompose source artwork: "+str(delta))
    candidate={
        "schema":"KOMA-P0-P15-06-INDEPENDENT-ARTMESH-INGEST-V1",
        "characterId":CHARACTER,"yaw":angle,
        "sourceKind":source_kind,
        "sourceProducer":source_model,
        "sourceSeed":source_seed,
        "referencePainting":{"path":str(painting_path.relative_to(root)),
            "sha256":sha(painting_path)},
        "semanticLayers":meta,"partCount":len(meta),
        "recomposition":delta,
        "sourceOriginalP0MetadataSHA256":sha(root/"p5-see-through/mv-candidate/parts.json"),
        "sourceHoldoutContractSHA256":sha(contract_path),
        "status":"PASS_SOURCE_ARTMESH_INGEST_FIXTURE" if source_kind=="registered-p14-fixture"
            else "P15_06_INDEPENDENT_PARTS_READY_FOR_ART_REVIEW",
        "artisticAcceptance":"PENDING" if source_kind=="independent-painting" else "NOT_APPLICABLE_FIXTURE"
    }
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"status":candidate["status"],"yaw":angle,"partCount":len(meta),
                      "recomposition":delta,"paintSHA256":candidate["referencePainting"]["sha256"]},ensure_ascii=False))
    return candidate


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",required=True)
    parser.add_argument("--contract",required=True)
    parser.add_argument("--yaw",required=True,type=float)
    parser.add_argument("--parts",required=True)
    parser.add_argument("--painting",required=True)
    parser.add_argument("--out",required=True)
    parser.add_argument("--source-kind",required=True,
                        choices=["independent-painting","registered-p14-fixture"])
    parser.add_argument("--source-producer")
    parser.add_argument("--source-seed",type=int)
    a=parser.parse_args()
    run(a.root,a.contract,a.yaw,a.parts,a.painting,a.out,a.source_kind,a.source_producer,a.source_seed)

#!/usr/bin/env python3
"""P0 mid-angle source fidelity and physical-side pose admission checks.

Audit approved original yaw45 and independent candidate yaw65 against new
Qwen painted yaw55 candidates. Geometry and source lineage are frozen here;
visual approval is recorded separately from transparent PNG engineering QA.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

BASE = Path(__file__).resolve().parent.parent
PRIVATE = BASE / "private-assets"
INPUTS = {
    "original45": "p2-views/whole/yaw045.png",
    "generated55v1": "p15-08-yaw055/yaw055-qwen2511-v1.png",
    "generated55v2": "p15-08-yaw055/yaw055-qwen2511-v2.png",
    "source65": "p15-independent-candidates/yaw065-source-rgba.png",
    "original90": "p2-views/whole/yaw090.png",
}
CANDIDATES = {
    "generated55v1": {
        "seed": 55022, "adapter": "Multiple-Angles",
        "references": ["original45", "source65"],
        "rgbSHA256": "e7cc32ae68df6780ff581a8cf7464aa863dff831b6b12f915376451a828a8dff",
        "rgbaPath": "p15-08-yaw055/yaw055-rgba-v1.png",
        "inputImageSHA256": [
            "1b5953ef9a22eb0e4356b677883143d073e03bd3c980eb8543a640353ad0b941",
            "390ba6e25d8afff96201c3e881b4c389db78be4423b80ac97b707f082fda9333",
        ],
    },
    "generated55v2": {
        "seed": 55045, "adapter": "Multiple-Angles",
        "references": ["original45"],
        "rgbSHA256": "8c088378641c9a0f020a9d5657bb14ac8e45961394cd76811cc60f1a8ca5b3bf",
        "rgbaPath": "p15-08-yaw055/yaw055-rgba-v2.png",
        "inputImageSHA256": [
            "1b5953ef9a22eb0e4356b677883143d073e03bd3c980eb8543a640353ad0b941"
        ],
    },
}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as inp:
        for block in iter(lambda: inp.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def gold_mark(image):
    """A strictly top-hair ROI connected component for the gold hairpin."""
    arr = np.asarray(image.convert("RGB"))
    hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)
    y, x = np.indices((1024, 1024))
    mask = (
        (hsv[:, :, 0] >= 12) & (hsv[:, :, 0] <= 42)
        & (hsv[:, :, 1] > 88) & (hsv[:, :, 2] > 115)
        & (y > 200) & (y < 425) & (x > 120) & (x < 870)
    )
    num, _, stats, centers = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    found = []
    for index in range(1, num):
        if stats[index, 4] >= 250:
            found.append((int(stats[index, 4]), centers[index]))
    if not found:
        return {"present": False, "pixels": 0, "center": None}
    area, center = max(found, key=lambda item: item[0])
    return {"present": True, "pixels": area,
            "center": [round(float(center[0]), 2), round(float(center[1]), 2)]}


def main():
    contract = json.loads((BASE/"metadata/p15-08-yaw055-generation-contract.json").read_text())
    registry = json.loads((PRIVATE/"p5-see-through/mv-candidate/parts.json").read_text())
    if contract["characterId"] != "p0_character_001" or registry["characterId"] != "p0_character_001":
        raise AssertionError("P0 unique character identity registry differs")
    orig45 = next(item for item in registry["wholeViews"] if item["yawDeg"] == 45)
    orig90 = next(item for item in registry["wholeViews"] if item["yawDeg"] == 90)
    if sha(PRIVATE/orig45["path"]) != orig45["sha256"]:
        raise AssertionError("Original yaw45 artwork SHA does not match")
    if sha(PRIVATE/orig90["path"]) != orig90["sha256"]:
        raise AssertionError("Original yaw90 artwork SHA does not match")
    input_meta = json.loads((PRIVATE/"p15-independent-candidates/yaw065-artmesh/ingest-qa.json").read_text())
    original65 = input_meta["referencePainting"]
    if sha(PRIVATE/original65["path"]) != original65["sha256"]:
        raise AssertionError("Registered yaw65 painting SHA does not match")
    images = {}
    details = {}
    for key, rel in INPUTS.items():
        file = PRIVATE/rel
        if not file.is_file():
            raise FileNotFoundError(file)
        with Image.open(file) as source:
            if source.size != (1024, 1024):
                raise AssertionError(f"Original art canvas wrong: {key}")
            images[key] = source.convert("RGBA").copy()
            details[key] = {
                "path": rel,
                "sha256": sha(file),
                "mode": source.mode,
                "canvas": list(source.size),
                "goldClip": gold_mark(source)
            }
    ref_gold = details["original45"]["goldClip"]
    if not ref_gold["present"] or ref_gold["center"][0] <= 600:
        raise AssertionError("P0 original physical-left hairpin reference unusable")
    if details["source65"]["goldClip"]["present"]:
        raise AssertionError("P15 registered yaw65 near profile unexpectedly shows hairpin")

    candidate_qa = {}
    for key, metadata in CANDIDATES.items():
        if details[key]["sha256"] != metadata["rgbSHA256"]:
            raise AssertionError(f"Qwen source image SHA changed: {key}")
        rgba = PRIVATE / metadata["rgbaPath"]
        alpha_qa_path = rgba.with_suffix(".qa.json")
        alpha_qa = json.loads(alpha_qa_path.read_text())
        if sha(rgba) != alpha_qa["outputPNG_SHA256"] or alpha_qa["sourceArtworkSHA256"] != metadata["rgbSHA256"]:
            raise AssertionError(f"RGBA edge and painting provenance mismatch: {key}")
        with Image.open(rgba) as image:
            if image.mode != "RGBA" or image.size != (1024, 1024):
                raise AssertionError(f"RGBA mask is invalid: {key}")
        marker = details[key]["goldClip"]
        wrong_handedness = marker["present"] and marker["center"][0] < 512
        candidate_qa[key] = {
            "model": "Qwen-Image-Edit-2511",
            "adapter": metadata["adapter"],
            "seed": metadata["seed"],
            "sourceReferenceRoles": metadata["references"],
            "inputImageSHA256": metadata["inputImageSHA256"],
            "painting": details[key],
            "mattePath": metadata["rgbaPath"],
            "matteSHA256": sha(rgba),
            "matteForegroundPixels": alpha_qa["alphaForegroundPixelsGt16"],
            "mattePartialAlphaPixels": alpha_qa["alphaPartialPixels"],
            "physicalHairclipCheck": "REWORK_REQUIRED" if wrong_handedness else "REVIEW_REQUIRED",
            "independentMidYawEyeCheck": "ONE_VISIBLE_EYE_MANUAL_REVIEW",
            "viewPoseAdmissibility": "REWORK_REQUIRED" if wrong_handedness else "MANUAL_REVIEW",
        }
    # The source role is P0 reference art only. New RGB/alpha bytes are private.
    canvas = Image.new("RGB", (5*300, 345), (242, 243, 246))
    draw = ImageDraw.Draw(canvas)
    for i, (label, _) in enumerate(INPUTS.items()):
        image = Image.new("RGBA", (1024, 1024), "white")
        src = images[label]
        if label.startswith("generated55"):
            # Display the registered transparent layer for accurate edge review.
            with Image.open(PRIVATE / CANDIDATES[label]["rgbaPath"]) as p:
                src = p.convert("RGBA")
        image.alpha_composite(src)
        canvas.paste(image.convert("RGB").resize((300, 300)), (i*300, 23))
        draw.text((i*300+6, 5), label, fill=(12, 20, 32))
    contact = PRIVATE/"p15-08-yaw055/yaw055-candidate-pose-contact.jpg"
    canvas.save(contact, quality=92)
    status = "P15_08_CANDIDATE_SOURCE_REGISTERED_POSE_REWORK"
    record = {
        "schema": "KOMA-P0-P15-08-55DEG-SOURCE-CANDIDATE-QA-V1",
        "characterId": "p0_character_001",
        "status": status,
        "originAngles": [45.,65.,90.],
        "targetAngle":55.,
        "registeredSourceViews": {
            "original45":details["original45"],
            "source65":details["source65"],
            "original90":details["original90"],
        },
        "candidateRecords":candidate_qa,
        "hairclipValidation": {
            "method":"HSV gold connected components within hair ROI y200–425",
            "original45ClipCenter":ref_gold["center"],
            "sideProfile65ClipVisible":False,
            "expectedTransition":"hairpin stays on physical-left or becomes occluded as head turns",
        },
        "artifact":{
            "path":str(contact.relative_to(PRIVATE)),
            "sha256":sha(contact),
            "bytes":contact.stat().st_size,
            "visibility":"private",
        },
        "sourceImageProduction":"Hugging Face connected Qwen-Image-Edit-2511 Multiple-Angles",
        "originalHeroSourceVerified":False,
        "semanticIndependent55LayersAccepted":0,
        "formalArtAcceptance":"PENDING_ANATOMICAL_VIEW_CORRESPONDENCE",
        "nextAction":"Calibrate actual pose yaw against P0 original 45/90; generate genuine 55-degree 2-eye 3/4 portrait with physical left hairpin provenance before 13 directly painted layers",
    }
    report=BASE/"evidence/p15-08-source-candidate-qa.json"
    report.write_text(json.dumps(record, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({"status":status,
                      "sourceSHA256":{k:v["sha256"] for k,v in details.items()},
                      "hairpinX":{k:v["goldClip"]["center"] for k,v in details.items()},
                      "mattePix":{k:v["matteForegroundPixels"] for k,v in candidate_qa.items()},
                      "contactSHA256":record["artifact"]["sha256"]},ensure_ascii=False))


if __name__=="__main__":
    main()

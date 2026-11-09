#!/usr/bin/env python3
"""Source-linked ArtMesh transition and stroke-density diagnostics for P0."""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

ANGLES = (65.0, 67.5, 72.5, 77.5)
METHODS = (
    ("P8", "p8-semantic-occlusion/selective-sequence/qa.json"),
    ("P14", "p14-authored-candidates/p14-vdd-smooth/qa.json"),
    ("coherent", "p15-source-coherent/qa.json"),
    ("bounded", "p15-flow-cap4/qa.json"),
)
PARTS = ("hair.back", "hair.side", "hair.front", "eye.near", "mouth", "nose")


def sha(file):
    h = hashlib.sha256()
    with Path(file).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def source_image(root, entry, key="sha256"):
    f = (root / entry["path"]).resolve()
    if not f.is_relative_to(root.resolve()):
        raise AssertionError("Source path outside private P0 root")
    if sha(f) != entry[key]:
        raise AssertionError("Original P0 source SHA mismatch")
    with Image.open(f) as image:
        assert image.mode == "RGBA" and image.size == (1024, 1024)
        return np.asarray(image).copy()


def alpha_gap(raw):
    mask = (raw[:, :, 3] >= 65).astype(np.uint8)
    head = mask[145:740, 170:850]
    closed = cv2.morphologyEx(head, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    return int((closed > head).sum())


def interior_detail(raw):
    alpha = (raw[:, :, 3] >= 230).astype(np.uint8)
    internal = cv2.erode(alpha, np.ones((7, 7), np.uint8), iterations=1) > 0
    denom = int(internal.sum())
    if not denom:
        return {"interiorPixels": 0, "edgePixels": 0, "edgeDensity": 0}
    gray = cv2.cvtColor(raw[:, :, :3], cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 55, 135)
    count = int(((edges > 0) & internal).sum())
    return {
        "interiorPixels": denom,
        "edgePixels": count,
        "edgeDensity": round(count / denom, 7),
    }


def run(root, output, preview):
    root = Path(root).resolve()
    result = {}
    for key, path in METHODS:
        qa = read(root / path)
        assert qa["characterId"] == "p0_character_001"
        entries = {float(f["angle"]): f for f in qa["frames"]}
        assert all(a in entries for a in ANGLES)
        result[key] = entries

    bounded = read(root / METHODS[-1][1])
    assert bounded["flowLimitPixelsPerDegree"] == 4
    assert bounded["method"] == "smooth-ink"

    p0 = read(root / "p5-see-through/mv-candidate/parts.json")
    p67 = read(root / "p14-authored-candidates/yaw067p5-artmesh/qa.json")
    p72 = read(root / "p14-authored-candidates/yaw072p5-artmesh/qa.json")
    original = {item["semanticId"]: item for item in p0["parts"] if item["yawDeg"] == 90}
    created = {
        "67.5": {part["semanticId"]: part for part in p67["parts"]},
        "72.5": {part["semanticId"]: part for part in p72["semanticLayerRecords"]},
    }
    stroke = {}
    for role in PARTS:
        a = source_image(root, original[role], "frameSha256")
        entry = {"original90": interior_detail(a)}
        for label in created:
            entry[label] = interior_detail(source_image(root, created[label][role]))
        stroke[role] = entry

    palette = (37, 51, 67, 255)
    panel_size, stride = 330, 360
    montage = Image.new("RGB", (panel_size * len(METHODS), stride * len(ANGLES)), palette[:3])
    painter = ImageDraw.Draw(montage)
    comparisons = []
    for row, angle in enumerate(ANGLES):
        metrics = {"yaw": angle, "methods": {}}
        for col, (method, _) in enumerate(METHODS):
            item = result[method][angle]
            data = source_image(root, item)
            metrics["methods"][method] = {
                "frameSHA256": item["sha256"],
                "alphaGapPixels": alpha_gap(data),
            }
            image = Image.fromarray(data, "RGBA")
            backdrop = Image.new("RGBA", image.size, palette)
            backdrop.alpha_composite(image)
            montage.paste(
                backdrop.convert("RGB").resize((panel_size, panel_size), Image.Resampling.LANCZOS),
                (col * panel_size, row * stride),
            )
            painter.text((col * panel_size + 9, row * stride + panel_size + 8),
                         method + " | " + str(angle), fill="white")
        comparisons.append(metrics)

    preview = Path(preview).resolve()
    preview.parent.mkdir(parents=True, exist_ok=True)
    montage.save(preview, quality=93)
    gap65 = next(e for e in comparisons if e["yaw"] == 65)["methods"]
    gap77 = next(e for e in comparisons if e["yaw"] == 77.5)["methods"]
    report = {
        "schema": "KOMA-P0-P15-STROKE-OCCLUSION-TRANSITION-QA-V1",
        "characterId": "p0_character_001",
        "originalAngles": [0, 45, 90],
        "generatedReferenceAngles": [67.5, 72.5],
        "angleSamples": list(ANGLES),
        "methods": [m for m, _ in METHODS],
        "source": "SHA-verified P0 ArtMesh and independently generated intermediate-source candidates",
        "frameComparison": comparisons,
        "semanticStrokeDensity": stroke,
        "preview": {
            "sourcePath": str(preview.relative_to(root)),
            "sha256": sha(preview),
            "private": True,
        },
        "diagnosis": {
            "boundedFlowImprovementPixelsAt77p5": (
                gap77["P14"]["alphaGapPixels"] - gap77["bounded"]["alphaGapPixels"]
            ),
            "boundedFlowImprovementPixelsAt65": (
                gap65["P14"]["alphaGapPixels"] - gap65["bounded"]["alphaGapPixels"]
            ),
            "sourceCoherentSameGapAt65And77p5": all(
                x["methods"]["P14"]["alphaGapPixels"] ==
                x["methods"]["coherent"]["alphaGapPixels"]
                for x in comparisons if x["yaw"] in (65, 77.5)
            ),
            "metricRole": "alpha-gap and inner-stroke proxies; source identity and anime line quality require direct review",
            "primaryDevelopmentPriority": "cross-view anatomical stroke correspondence and view-dependent masks",
        },
        "adoptedEngineeringBaseline": "P8_SEMANTIC_OCCLUSION_ARTMESH",
        "candidateArtisticAcceptance": "PENDING_ANATOMICAL_STROKE_REVIEW",
        "status": "P15_TRANSITION_SOURCE_DIAGNOSTIC_VERIFIED",
    }
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--preview", required=True)
    args = ap.parse_args()
    report = run(args.root, args.out, args.preview)
    print(json.dumps({
        "status": report["status"],
        "reviewAngles": report["angleSamples"],
        "diagnosis": report["diagnosis"],
    }, ensure_ascii=False))

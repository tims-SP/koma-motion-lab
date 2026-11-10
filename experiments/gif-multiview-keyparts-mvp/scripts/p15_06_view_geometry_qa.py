#!/usr/bin/env python3
"""Reproduce P0 holdout silhouette and canvas-alignment diagnostics."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = ROOT / "private-assets"
INPUTS = [
    ("original45", "p2-views/whole/yaw045.png"),
    ("P8_65", "p8-semantic-occlusion/selective-sequence/yaw65.png"),
    ("painted65", "p15-independent-candidates/yaw065-source-rgba.png"),
    ("P8_77p5", "p8-semantic-occlusion/selective-sequence/yaw77p5.png"),
    ("painted77p5", "p15-independent-candidates/yaw077p5-source-rgba.png"),
    ("original90", "p2-views/whole/yaw090.png"),
]
THRESHOLDS = {"silhouetteIoUMin": 0.9, "relativeAreaErrorMax": 0.08}
HEAD_CROP_Y = 710


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def score(render_mask: np.ndarray, source_mask: np.ndarray) -> dict:
    intersection = int(np.logical_and(render_mask, source_mask).sum())
    union = int(np.logical_or(render_mask, source_mask).sum())
    render_area = int(render_mask.sum())
    source_area = int(source_mask.sum())
    return {
        "intersectionPixels": intersection,
        "unionPixels": union,
        "renderAreaPixels": render_area,
        "sourceAreaPixels": source_area,
        "silhouetteIoU": round(intersection / max(union, 1), 6),
        "relativeAreaError": round(abs(render_area - source_area) / max(source_area, 1), 6),
    }


def main() -> None:
    images = {}
    manifest = {}
    for label, rel in INPUTS:
        source = PRIVATE / rel
        if not source.is_file():
            raise FileNotFoundError(source)
        image = Image.open(source).convert("RGBA")
        if image.size != (1024, 1024):
            raise ValueError(f"{label}: requires 1024x1024 RGBA source")
        images[label] = image
        alpha = np.asarray(image)[:, :, 3]
        manifest[label] = {
            "path": rel,
            "sha256": digest(source),
            "opaqueMaskPixels": int(np.count_nonzero(alpha >= 128)),
            "semiTransparentPixels": int(np.count_nonzero((alpha > 0) & (alpha < 255))),
        }

    samples = []
    for angle, ref, painted in [
        (65.0, "P8_65", "painted65"),
        (77.5, "P8_77p5", "painted77p5"),
    ]:
        ref_mask = np.asarray(images[ref])[:, :, 3] >= 128
        painted_mask = np.asarray(images[painted])[:, :, 3] >= 128
        full = score(ref_mask, painted_mask)
        head = score(ref_mask[:HEAD_CROP_Y], painted_mask[:HEAD_CROP_Y])
        passed = (
            full["silhouetteIoU"] >= THRESHOLDS["silhouetteIoUMin"]
            and full["relativeAreaError"] <= THRESHOLDS["relativeAreaErrorMax"]
        )
        samples.append({
            "yawDeg": angle,
            "renderer": ref,
            "independentCandidate": painted,
            "fullCanvas": full,
            "headCrop": head,
            "silhouetteGate": "PASS" if passed else "REWORK_REQUIRED",
        })

    contact = Image.new("RGB", (6 * 336, 450), "#f3f3f3")
    draw = ImageDraw.Draw(contact)
    for i, (label, _) in enumerate(INPUTS):
        image = Image.new("RGBA", (1024, 1024), "#ffffff")
        image.alpha_composite(images[label])
        tile = image.convert("RGB")
        tile.thumbnail((336, 425))
        contact.paste(tile, (i * 336, 24))
        draw.text((i * 336 + 6, 5), label, fill="#111111")
    image_path = PRIVATE / "p15-independent-candidates/p15-pose-comparison.jpg"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    contact.save(image_path, quality=92)

    result = {
        "schema": "KOMA-P0-P15-06-VIEW-GEOMETRY-QA-V1",
        "characterId": "p0_character_001",
        "baseline": "P8_SEMANTIC_OCCLUSION_ARTMESH",
        "comparisonRole": "independent-painting holdout and canvas-alignment diagnostic",
        "alphaMaskThreshold": 128,
        "headDiagnosticCropY": HEAD_CROP_Y,
        "thresholds": THRESHOLDS,
        "inputs": manifest,
        "samples": samples,
        "comparisonImage": {
            "path": str(image_path.relative_to(ROOT)),
            "sha256": digest(image_path),
            "bytes": image_path.stat().st_size,
            "visibility": "private",
        },
        "sourceIdentityHeroVerified": False,
        "visualAcceptance": "REWORK_REQUIRED" if any(
            sample["silhouetteGate"] != "PASS" for sample in samples
        ) else "STRUCTURAL_GATE_PASS_VISUAL_REVIEW_PENDING",
        "assessmentLimit": "Raw pixel masks include differences in view registration and painted silhouette; human anatomy/identity review is separate.",
    }
    path = ROOT / "evidence/p15-06-view-geometry-qa.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "status": result["visualAcceptance"],
        "samples": [{
            "angle": s["yawDeg"],
            "IoU": s["fullCanvas"]["silhouetteIoU"],
            "areaError": s["fullCanvas"]["relativeAreaError"],
            "headIoU": s["headCrop"]["silhouetteIoU"],
            "gate": s["silhouetteGate"],
        } for s in samples],
        "comparisonImageSHA256": result["comparisonImage"]["sha256"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Audit the P15-11 independently generated candidate source images.

An AI-generated source image is a *candidate*, not an approved P0 keyview.
The independent angle, anatomical, and identity gates remain explicit.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from p15_08_pose_qa import gold_mark

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "private-assets"
CANDIDATES = ASSETS / "p15-11-generation"
MANIFEST = ROOT / "metadata/p15-11-source-candidates.json"
OUT = ROOT / "evidence/p15-11-source-candidate-qa.json"


def sha(file: Path) -> str:
    digest = hashlib.sha256()
    with file.open("rb") as handle:
        for piece in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(piece)
    return digest.hexdigest()


def silhouette(image: Image.Image):
    rgb = np.asarray(image.convert("RGB")).astype(np.int16)
    delta = np.min(255 - rgb, axis=2)
    fg = delta > 23
    fg[:8] = False
    fg[-8:] = False
    fg[:, :8] = False
    fg[:, -8:] = False
    indices = np.argwhere(fg)
    bbox = [0, 0, 0, 0]
    if len(indices):
        bbox = [int(indices[:, 1].min()), int(indices[:, 0].min()),
                int(indices[:, 1].max() + 1), int(indices[:, 0].max() + 1)]
    return int(np.count_nonzero(fg)), bbox


def run():
    manifest = json.loads(MANIFEST.read_text())
    if manifest["characterId"] != "p0_character_001":
        raise AssertionError("P0 identity mismatch")
    refs = manifest["referenceImages"]
    for entry in refs:
        path = ASSETS / entry["path"]
        if sha(path) != entry["sha256"]:
            raise AssertionError("P0 generation reference changed")
    source_ref = Image.open(ASSETS / refs[0]["path"]).convert("RGB")
    original_clip = gold_mark(source_ref)
    if not original_clip["present"]:
        raise AssertionError("P0 hairclip identity witness missing")

    records = []
    board = Image.new("RGB", (3 * 330, 2 * 365), (246, 247, 249))
    draw = ImageDraw.Draw(board)
    collage_sources = [("P0 45° source", ASSETS / refs[0]["path"])]
    for item in manifest["candidates"]:
        if item["visualDisposition"] != "REWORK_REQUIRED":
            raise AssertionError("P15-11 candidate requires explicit visual disposition")
        path = CANDIDATES / item["file"]
        if sha(path) != item["sha256"]:
            raise AssertionError(f"Registered candidate checksum mismatch: {path.name}")
        with Image.open(path) as image:
            if image.size != (1024, 1024) or image.mode != "RGB":
                raise AssertionError(f"Candidate must be 1024x1024 RGB: {path.name}")
            gold = gold_mark(image)
            coverage, bbox = silhouette(image)
            if not 60000 <= coverage <= 850000:
                raise AssertionError(f"Candidate silhouette out of bounds: {path.name}")
        records.append({
            "requestedYaw": item["requestedYaw"],
            "file": str(path.relative_to(ASSETS)),
            "sha256": item["sha256"],
            "sourceBlobSHA": item["sourceBlobSHA"],
            "model": item["model"],
            "adapter": item["adapter"],
            "seed": item["seed"],
            "referenceAngles": item["referenceAngles"],
            "goldClipComponent": gold,
            "foregroundApproxPixels": coverage,
            "foregroundApproxBounds": bbox,
            "manualVisualObservations": item["visualObservations"],
            "poseAdmission": item["visualDisposition"],
            "canBeUsedAsRendererKeyframe": False,
        })
        collage_sources.append((item["file"].split(".")[0], path))
    collage_sources.append(("P15 65° registered", ASSETS / refs[1]["path"]))
    if len(collage_sources) != 6:
        raise AssertionError("P15-11 contact sheet requires four candidate views")
    for i, (label, path) in enumerate(collage_sources):
        with Image.open(path) as image:
            backdrop = Image.new("RGBA", image.size, "white")
            backdrop.alpha_composite(image.convert("RGBA"))
            face = backdrop.convert("RGB").resize((330, 330), Image.Resampling.LANCZOS)
        x, y = (i % 3) * 330, (i // 3) * 365
        board.paste(face, (x, y + 25))
        draw.text((x + 8, y + 6), label, fill=(17, 23, 31))
    contact = CANDIDATES / "p15-11-candidate-grid.jpg"
    board.save(contact, quality=91)
    result = {
        "schema": "KOMA-P15-11-SOURCE-CANDIDATE-QA-V1",
        "characterId": manifest["characterId"],
        "requestedAngles": [57.5, 60.0],
        "source45SHA256": refs[0]["sha256"],
        "source65SHA256": refs[1]["sha256"],
        "generatedCandidateCount": len(records),
        "sourceRecords": records,
        "candidateContactPath": str(contact.relative_to(ASSETS)),
        "candidateContactSHA256": sha(contact),
        "independentPaintingAccepted": 0,
        "semanticPaintedLayersAccepted": 0,
        "originalHeroSHA256Verified": False,
        "formalArtGate": "P15_11_IDENTITY_AND_POSE_REVIEW_REQUIRED",
        "next": "Create anatomically correct 57.5/60 source paintings and separately painted semantic ArtMesh/underpaint; evaluate on distinct heldout angles.",
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "status": result["formalArtGate"],
        "candidateCount": result["generatedCandidateCount"],
        "acceptedArtworks": result["independentPaintingAccepted"],
        "contactSHA256": result["candidateContactSHA256"]
    }, ensure_ascii=False))
    return result


if __name__ == "__main__":
    run()

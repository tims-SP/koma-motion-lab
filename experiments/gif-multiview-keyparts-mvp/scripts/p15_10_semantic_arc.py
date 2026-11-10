#!/usr/bin/env python3
"""Render a 55-65 degree P0 ArtMesh per-role occlusion correspondence study.

Both registered keyviews retain their original pixels at the endpoints.
Intermediate panels retain separate editable 1024 RGBA layers with
deterministic visibility schedules; art-quality approval remains independent.
"""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from p15_07_geometry_bridge import FLOW, N, field, warp, sha
from p15_09_anchor_pose import ASSETS, BASE, SOURCE
from p15_09_midarc import score
from p8_semantic_occlusion import output_frame_id
from p15_10_semantic_key55 import CHECK, OUTPUT, image_rgba

OUT = ASSETS / "p15-10-semantic-pose" / "arc"
SOURCE65 = ASSETS / "p15-independent-candidates/yaw065-source-rgba.png"
QA65 = ASSETS / "p15-independent-candidates/yaw065-artmesh/ingest-qa.json"
STEPS = [55., 57.5, 60., 62.5, 65.]


def smoothstep(v, start, end):
    p = np.clip((v - start) / (end - start), 0, 1)
    return float(p * p * (3 - 2 * p))


def frame_layers(records, source_path):
    out = {}
    for row in records:
        f = ASSETS / row[source_path]
        expected = row.get("sha256", row.get("sourceSHA256"))
        if sha(f) != expected:
            raise ValueError(f"ArtMesh source SHA mismatch: {row['semanticId']}")
        out[row["semanticId"]] = image_rgba(f)
    return out


def premult_to_rgba(array):
    arr = np.asarray(array, dtype=np.float32)
    a = np.clip(arr[:, :, 3:], 0, 1)
    rgb = np.where(a > 1e-5, arr[:, :, :3] / np.maximum(a, 1e-5), 0)
    return np.uint8(np.rint(np.concatenate([np.clip(rgb, 0, 1), a], axis=2) * 255))


def build():
    manifest55 = json.loads(CHECK.read_text())
    meta65 = json.loads(QA65.read_text())
    reference = image_rgba(ASSETS / "p15-09-anchor-pose/yaw055-p5-anchor-reference.png")
    target = image_rgba(SOURCE65)
    if manifest55["characterId"] != meta65["characterId"] or manifest55["characterId"] != "p0_character_001":
        raise ValueError("Source artwork character identity differs")
    if sha(SOURCE65) != meta65["referencePainting"]["sha256"]:
        raise ValueError("65-degree registered painting changed")
    roles55 = sorted(manifest55["semanticLayers"], key=lambda r: r["depthOrder"])
    roles65 = sorted(meta65["semanticLayers"], key=lambda r: r["depthOrder"])
    names = [row["semanticId"] for row in roles55]
    if names != [row["semanticId"] for row in roles65] or len(names) != 13:
        raise ValueError("Keyview ArtMesh role order changed")
    # 65-degree registered layers must reproduce their own independent
    # painting. This is a source check, not a claim of hidden underpainting.
    part65 = frame_layers(roles65, "path")
    sample65 = Image.new("RGBA", (N, N))
    for name in names:
        sample65.alpha_composite(Image.fromarray(part65[name], "RGBA"))
    whole65 = np.asarray(sample65)
    if not np.array_equal(whole65[:, :, 3], target[:, :, 3]):
        raise AssertionError("65-degree registered Alpha compositing differs")
    mask = target[:, :, 3] > 0
    if not np.array_equal(whole65[:, :, :3][mask], target[:, :, :3][mask]):
        raise AssertionError("65-degree visible painting color differs")
    part55 = frame_layers(roles55, "outputPath")
    flow55, flow65 = field(reference, target)
    yy, xx = np.meshgrid(np.arange(N, dtype=np.float32),
                         np.arange(N, dtype=np.float32), indexing="ij")
    OUT.mkdir(parents=True, exist_ok=True)
    records, frames = [], []
    for angle in STEPS:
        t = (angle - STEPS[0]) / (STEPS[-1] - STEPS[0])
        composite = Image.new("RGBA", (N, N))
        counts = {}
        partdir = OUT / output_frame_id(angle).replace(".png", "") / "parts"
        partdir.mkdir(parents=True, exist_ok=True)
        for role in names:
            a, b = part55[role], part65[role]
            if angle == 55:
                rgba = a.copy()
            elif angle == 65:
                rgba = b.copy()
            else:
                wa = warp(a, flow55, t, (xx, yy))
                wb = warp(b, flow65, 1 - t, (xx, yy))
                if role == "eye.far":
                    # P0 55 shows both eyes; P15 65 hides the far eye.
                    pixels = wa * (1 - smoothstep(angle, 57.5, 62.5))
                elif role == "hair.clip.cross_gold":
                    # Physical-side ornament goes behind the near hair.
                    pixels = wa * (1 - smoothstep(angle, 56, 63))
                elif not np.any(a[:, :, 3]) or not np.any(b[:, :, 3]):
                    w = smoothstep(angle, 55, 65)
                    pixels = (1 - w) * wa + w * wb
                else:
                    # Layer-local color transfer, not whole-portrait ownership.
                    w = smoothstep(t, .15, .85)
                    pixels = (1 - w) * wa + w * wb
                rgba = premult_to_rgba(pixels)
            f = partdir / (role + ".png")
            Image.fromarray(rgba, "RGBA").save(f)
            composite.alpha_composite(Image.fromarray(rgba, "RGBA"))
            counts[role] = int(np.count_nonzero(rgba[:, :, 3] > 127))
        if angle == 55:
            # Render exact registered P5 pose at the canonical key position.
            full = reference
        elif angle == 65:
            full = target
        else:
            full = np.asarray(composite)
        filename = OUT / output_frame_id(angle)
        Image.fromarray(full, "RGBA").save(filename)
        records.append({"yaw": angle, "path": str(filename.relative_to(ASSETS)),
                        "sha256": sha(filename), "parts": counts,
                        "partDirectory": str(partdir.relative_to(ASSETS)),
                        "wholeSource": "P5 55 geometric key" if angle == 55
                        else "registered 65 source" if angle == 65
                        else "ArtMesh role-local correspondence"})
        frames.append((angle, full))
    sheet = Image.new("RGB", (len(frames) * 280, 315), (244, 244, 244))
    pen = ImageDraw.Draw(sheet)
    for i, (angle, pic) in enumerate(frames):
        background = Image.new("RGBA", (N, N), "white")
        background.alpha_composite(Image.fromarray(pic, "RGBA"))
        sheet.paste(background.convert("RGB").resize((280, 280), Image.Resampling.LANCZOS),
                    (i * 280, 27))
        pen.text((i * 280 + 12, 8), str(angle) + " deg", fill=(20, 20, 30))
    contact = OUT / "p15-10-semantic-arc-contact.jpg"
    sheet.save(contact, quality=91)
    original = ASSETS / "p15-09-midarc"
    transition = []
    for i in range(1, len(frames)):
        aa, a = frames[i - 1]
        ab, b = frames[i]
        transition.append({"start": aa, "end": ab,
                           "semanticAlphaIoU": score(a, b),
                           "P15_09AlphaIoU": score(image_rgba(original / output_frame_id(aa)),
                                                  image_rgba(original / output_frame_id(ab)))})
    proof = {
        "schema": "KOMA-P15-10-ROLE-LOCAL-CORRESPONDENCE-V1",
        "characterId": "p0_character_001",
        "roleCount": len(names),
        "roles": names,
        "source55SHA256": manifest55["P5Pose55SHA256"],
        "source65SHA256": meta65["referencePainting"]["sha256"],
        "frames": records,
        "transition": transition,
        "contact": {"path": str(contact.relative_to(ASSETS)), "sha256": sha(contact)},
        "source55FarEyeVisible": records[0]["parts"]["eye.far"] > 0,
        "source65FarEyeHidden": records[-1]["parts"]["eye.far"] == 0,
        "source65HairclipHidden": records[-1]["parts"]["hair.clip.cross_gold"] == 0,
        "renderStatus": "ROLE_LOCAL_ARTMESH_FRAMES_REGISTERED",
        "artisticStatus": "INDEPENDENT_PAINTED_INBETWEENS_AND_HIDDEN_UNDERPAINT_PENDING",
        "sourceClaim": "55 derived key geometry; 65 independently generated source with semantic raster partitions"
    }
    output = BASE / "evidence" / "p15-10-semantic-arc-qa.json"
    output.write_text(json.dumps(proof, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": proof["renderStatus"], "frameCount": len(frames),
                      "roleCount": len(names), "transition": transition,
                      "farEyeCounts": [r["parts"]["eye.far"] for r in records],
                      "clipCounts": [r["parts"]["hair.clip.cross_gold"] for r in records]}))


if __name__ == "__main__":
    build()

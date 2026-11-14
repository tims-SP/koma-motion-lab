#!/usr/bin/env python3
"""P0 original-to-painted facial ArtMesh landmark and ink-stroke correspondence.

Reuses the P10 connected-stroke tracing / ambiguity-rejection implementation.
P5 source anchors are interpolated reference predictions, not measurements of
new model-painted intermediate views. Matches are source-backed candidates.
"""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw
from p9_color_region_correspondence import read as read_rgba, SOURCE_SIZE
from p10_stroke_identity import extract_strokes, match

CHARACTER = "p0_character_001"
VIEW_ANGLES = (45, 67.5, 72.5, 90)
VIEW_PAIRS = ((45, 67.5), (67.5, 72.5), (72.5, 90))
ROLES = ("face.skin", "eye.near", "nose", "mouth")
TRACK_LABELS = {
    "face.skin": ("face.chin", "face.jaw.near", "eye.near.iris", "nose", "mouth"),
    "eye.near": ("eye.near.iris",),
    "nose": ("nose",),
    "mouth": ("mouth",),
}
SOURCE_SIZE_PX = 1024


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for item in iter(lambda: handle.read(1 << 20), b""):
            h.update(item)
    return h.hexdigest()


def parse(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def verify_asset(root, item, key):
    file = (root / item["path"]).resolve()
    if not file.is_relative_to(root) or sha(file) != item[key]:
        raise ValueError("Source P0 semantic RGBA hash or root mismatch: " + str(file))
    with Image.open(file) as im:
        if im.mode != "RGBA" or im.size != (SOURCE_SIZE_PX, SOURCE_SIZE_PX):
            raise ValueError("Source semantic layer must be 1024px native RGBA")
    return file


def source_registry(root):
    original = parse(root / "p5-see-through/mv-candidate/parts.json")
    candidate67 = parse(root / "p14-authored-candidates/yaw067p5-artmesh/qa.json")
    candidate72 = parse(root / "p14-authored-candidates/yaw072p5-artmesh/qa.json")
    landmark = parse(root / "p5-see-through/mv-candidate/landmark-qa.json")
    palette = parse(root / "p9-region-correspondence/qa.json")
    if any(x["characterId"] != CHARACTER for x in
           (original, candidate67, candidate72, landmark, palette)):
        raise ValueError("P0 identity mismatch")
    original_path = root / "p5-see-through/mv-candidate/parts.json"
    if sha(original_path) != palette["sourceRegistrySHA256"]:
        raise ValueError("P9 source registry provenance mismatch")
    source = {}
    for item in original["parts"]:
        if item["yawDeg"] in (45, 90) and item["semanticId"] in ROLES:
            source[(item["yawDeg"], item["semanticId"])] = (
                verify_asset(root, item, "frameSha256"), item["frameSha256"])
    for angle, group in (
        (67.5, candidate67["parts"]),
        (72.5, candidate72["semanticLayerRecords"]),
    ):
        for item in group:
            if item["semanticId"] in ROLES:
                source[(angle, item["semanticId"])] = (
                    verify_asset(root, item, "sha256"), item["sha256"])
    if len(source) != len(ROLES) * len(VIEW_ANGLES):
        raise ValueError("P0 face source register incomplete")
    return source, landmark, palette


def alpha_centroid(image):
    weight = image[:, :, 3].astype(np.float64)
    total = float(weight.sum())
    if total <= 1:
        return None
    y, x = np.indices(weight.shape, dtype=np.float64)
    return np.array([(weight * x).sum() / total,
                     (weight * y).sum() / total], dtype=np.float64)


def source_anchor(landmarks, label, angle):
    samples = landmarks["landmarks"].get(label, [])
    known = {
        float(item["yaw"]): np.asarray(item["xy"], dtype=np.float64)
        for item in samples if item["yaw"] in (45, 90) and item["visible"]
    }
    if 45.0 not in known or 90.0 not in known:
        return None
    t = (float(angle) - 45) / 45
    return known[45.0] * (1 - t) + known[90.0] * t


def predicted_anchor_support(native, xy1024):
    """Distance in native pixels from P5 linear prediction to actual candidate alpha.

    This is an inclusion test only: the P5 interpolated point is never
    asserted to be an independently painted anatomical landmark.
    """
    if xy1024 is None:
        return None
    px, py = [float(v) for v in xy1024]
    rgba = native
    if rgba.ndim != 3 or rgba.shape[2] != 4:
        raise ValueError("Native RGBA required for anchor support")
    mask = (rgba[:, :, 3] >= 48).astype(np.uint8)
    u = int(np.clip(round(px * mask.shape[1] / SOURCE_SIZE_PX), 0, mask.shape[1] - 1))
    v = int(np.clip(round(py * mask.shape[0] / SOURCE_SIZE_PX), 0, mask.shape[0] - 1))
    inside = bool(mask[v, u])
    if inside:
        distance = 0.0
    elif not np.any(mask):
        distance = None
    else:
        # CV2 distanceTransform measures distance to zero pixels. Invert
        # the source mask so all nonzero alpha pixels become zero.
        near = cv2.distanceTransform(1 - mask, cv2.DIST_L2, 3)
        distance = float(near[v, u]) * (SOURCE_SIZE_PX / mask.shape[1])
    return {
        "candidateMaskContainsPrediction": inside,
        "distanceToCandidateAlphaPx1024": None if distance is None else round(distance, 3),
        "method": "P5_LINEAR_PREDICTION_WITH_RGBA_ALPHA_SUPPORT",
    }


def shift_from_measured_alpha(a, b):
    if a is None or b is None:
        return np.zeros(2, dtype=np.float64)
    return (b - a) * (SOURCE_SIZE / SOURCE_SIZE_PX)


def trace(image, role, angle, colors):
    # P10 extracts source-visible interior ink, excluding hard RGBA edges.
    # Angle tags retain one decimal to prevent different intermediate views
    # from ever sharing a semantic stroke ID.
    tag = int(round(float(angle) * 10))
    return extract_strokes(image, role, tag, colors)


def match_pair(source, target, shift, limit=42):
    """Use P10 bidirectional uniqueness/ambiguity rejection on candidate strokes."""
    if not source or not target:
        return []
    matches = match(source, target, np.asarray(shift, dtype=np.float64), limit=limit)
    # Enforce actual one-to-one and source/target IDs even if the matcher changes.
    seen_a, seen_b = set(), set()
    verified = []
    for record in matches:
        if record["sourceId"] in seen_a or record["targetId"] in seen_b:
            raise AssertionError("Duplicate stroke owner in P15 track")
        seen_a.add(record["sourceId"])
        seen_b.add(record["targetId"])
        verified.append(record)
    return verified


def preview(root, out, source, correspondences):
    width, height = 310, 325
    image = Image.new("RGB", (4 * width, 4 * height), (37, 49, 64))
    pen = ImageDraw.Draw(image)
    for row, role in enumerate(ROLES):
        for column, angle in enumerate(VIEW_ANGLES):
            file, _ = source[angle, role]
            with Image.open(file) as src:
                layer = src.convert("RGBA")
                backdrop = Image.new("RGBA", layer.size, (48, 60, 79, 255))
                backdrop.alpha_composite(layer)
                thumb = backdrop.convert("RGB").resize((width, width),
                                                        Image.Resampling.LANCZOS)
            image.paste(thumb, (column * width, row * height))
            pen.text((column * width + 6, row * height + width + 4),
                     role + " / " + str(angle), fill="white")
        # Draw accepted source-to-target stroke endpoint tracks on the same
        # semantic canvas panels, preserving explicit view/part ownership.
        for column, (a, b) in enumerate(VIEW_PAIRS):
            pair = correspondences[f"{a}-{b}/{role}"]
            for record in pair["accepted"]:
                ax = column * width + record["sourceXY"][0] * width / SOURCE_SIZE
                ay = row * height + record["sourceXY"][1] * width / SOURCE_SIZE
                bx = (column + 1) * width + record["targetXY"][0] * width / SOURCE_SIZE
                by = row * height + record["targetXY"][1] * width / SOURCE_SIZE
                pen.line((ax, ay, bx, by), fill=(88, 231, 177), width=1)
                for x, y in ((ax, ay), (bx, by)):
                    pen.ellipse((x - 2, y - 2, x + 2, y + 2),
                                fill=(255, 220, 156))
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out, quality=94)
    return sha(out)


def run(root, out, preview_file):
    root = Path(root).resolve()
    out = Path(out)
    source, landmarks, palette = source_registry(root)
    base = palette["pairs"]
    image_data, extracted, centers = {}, {}, {}
    for role in ROLES:
        pair = base.get(f"45-90/{role}")
        colors = np.asarray(pair["paletteLab"], dtype=np.float32) if pair else (
            np.asarray([[80, 128, 128]], dtype=np.float32))
        centers[role] = colors
        for angle in VIEW_ANGLES:
            file, _ = source[angle, role]
            image_data[angle, role] = read_rgba(file)
            extracted[angle, role] = trace(image_data[angle, role], role, angle, colors)

    report = {}
    for role in ROLES:
        for a, b in VIEW_PAIRS:
            name = f"{a}-{b}/{role}"
            A, B = image_data[a, role], image_data[b, role]
            center_a, center_b = alpha_centroid(A), alpha_centroid(B)
            shift = shift_from_measured_alpha(center_a, center_b)
            left, right = extracted[a, role], extracted[b, role]
            matched = match_pair(left, right, shift)
            sources = {
                "a": {"path": str(source[a, role][0].relative_to(root)),
                      "sha256": source[a, role][1]},
                "b": {"path": str(source[b, role][0].relative_to(root)),
                      "sha256": source[b, role][1]},
            }
            owners_a = {item["sourceId"] for item in matched}
            owners_b = {item["targetId"] for item in matched}
            predicted = {
                label: {
                    "a": [round(float(v), 3) for v in source_anchor(landmarks, label, a)],
                    "b": [round(float(v), 3) for v in source_anchor(landmarks, label, b)],
                    "type": "P5_LINEAR_PROJECTION_REFERENCE_ONLY",
                    "targetAlphaSupport": predicted_anchor_support(
                        B, source_anchor(landmarks, label, b)),
                }
                for label in TRACK_LABELS[role]
                if source_anchor(landmarks, label, a) is not None
                and source_anchor(landmarks, label, b) is not None
            }
            report[name] = {
                "role": role,
                "angles": [a, b],
                "source": sources,
                "alphaMeasuredCentroids443": {
                    "a": None if center_a is None else center_a.round(3).tolist(),
                    "b": None if center_b is None else center_b.round(3).tolist(),
                },
                "measuredCenterShift443": shift.round(3).tolist(),
                "physicalP5Predictions1024": predicted,
                "measuredCenterKind": "RGBA_ALPHA_CENTROID_NOT_ANATOMICAL_LANDMARK",
                "sourceStrokeCount": len(left),
                "targetStrokeCount": len(right),
                "accepted": matched,
                "unmatchedSourceCount": len(left) - len(owners_a),
                "unmatchedTargetCount": len(right) - len(owners_b),
                "sourceCoverage": round(len(matched) / max(1, len(left)), 4),
                "targetCoverage": round(len(matched) / max(1, len(right)), 4),
                "strokeStatus": "IDENTITY_CANDIDATES_REQUIRE_VISUAL_CONFIRMATION",
            }
    image_hash = preview(root, Path(preview_file), source, report)
    total = sum(len(q["accepted"]) for q in report.values())
    qa = {
        "schema": "KOMA-P0-P15-04-FACIAL-STROKE-ANCHOR-CORRESPONDENCE-V1",
        "characterId": CHARACTER,
        "originalKeyAngles": [45, 90],
        "intermediateCandidateAngles": [67.5, 72.5],
        "semanticRoles": list(ROLES),
        "sourceSize": [1024, 1024],
        "strokeWorkingCanvas": [SOURCE_SIZE, SOURCE_SIZE],
        "sourceMetadataSHA256": {
            "P5ArtMesh": sha(root / "p5-see-through/mv-candidate/parts.json"),
            "P5Landmarks": sha(root / "p5-see-through/mv-candidate/landmark-qa.json"),
            "P9Palette": sha(root / "p9-region-correspondence/qa.json"),
            "P10StrokeBaseline": sha(root / "p10-stroke-identity/qa.json"),
        },
        "method": "Original P10 RGBA interior stroke segmentation + palette-assisted connected components and one-to-one ambiguity rejection; view local alpha centroids; independent P5 linear physical anchor reference",
        "pairCount": len(report),
        "matchedStrokeCandidateCount": total,
        "pairs": report,
        "preview": {
            "privateRelativePath": str(Path(preview_file).resolve().relative_to(root)),
            "sha256": image_hash,
        },
        "artisticAcceptance": "PENDING_INDEPENDENT_STROKE_REVIEW",
        "status": "P15_04_SOURCE_BACKED_FACIAL_CORRESPONDENCE_REGISTERED",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps({
        "status": qa["status"],
        "pairs": qa["pairCount"],
        "matches": total,
        "roles": list(ROLES),
        "perPairMatches": {k: len(v["accepted"]) for k, v in report.items()},
    }, ensure_ascii=False))
    return qa


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--preview", required=True)
    a = p.parse_args()
    run(a.root, a.out, a.preview)

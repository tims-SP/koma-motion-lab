#!/usr/bin/env python3
"""Register independently illustrated 65°/77.5° P0 views as native ArtMesh candidates.

The model-created view is the only painted color source at each angle.
Original P0 90° ArtMesh layers provide a semantic ownership prior via DIS.
Every visible painted pixel belongs to one transparent semantic part, making
the composite exactly match the newly drawn reference. Assignment is reviewed
separately because perfect reconstruction does not establish correct anatomy.
"""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from flow_render import get_flow
from p14_semantic_reproject import assign_labels, coords_from_target

W = 1024
FLOW_W = 443
CHARACTER = "p0_character_001"
ANGLE_KEYS = {65.0: "yaw065", 77.5: "yaw077p5"}
SPECIAL_HIDDEN = {"ear.far", "eye.far", "hair.clip.cross_gold"}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rgba(path):
    with Image.open(path) as im:
        if im.mode != "RGBA" or im.size != (W, W):
            raise ValueError("P0 semantic source must be 1024 RGBA")
        return np.asarray(im).copy()


def candidate_ahoge(target):
    """Isolate the single upper scalp ahoge from independently painted alpha.

    Source P0 loop position is near the upper center; the same top-row prior
    handles both generated key poses without assuming fixed ahoge pixel IDs.
    """
    mask = (target[:, :, 3] > 5).astype(np.uint8)
    subset = np.zeros_like(mask)
    subset[:110, 300:750] = mask[:110, 300:750]
    count, labels, stats, _ = cv2.connectedComponentsWithStats(subset, 8)
    eligible = []
    for index in range(1, count):
        x, y, width, height, area = map(int, stats[index])
        if y <= 35 and area >= 350 and x >= 340 and 490 < x + width < 760:
            eligible.append((area, index))
    if not eligible:
        raise ValueError("P0 candidate single ahoge topological mask unavailable")
    chosen = max(eligible)[1]
    tip = (labels == chosen)
    # Recover a few lower root pixels only where they are contiguous with the
    # source loop; do not duplicate any painted pixels across part layers.
    dilated = cv2.dilate(tip.astype(np.uint8), np.ones((9, 9), np.uint8), iterations=2) > 0
    root = np.zeros_like(mask, dtype=bool)
    root[108:132, 450:675] = mask[108:132, 450:675].astype(bool)
    tip |= dilated & root
    if tip.sum() < 600:
        raise ValueError("P0 candidate ahoge pixel count below valid range")
    return tip


def candidate_ear(target, angle):
    """Keep only newly painted near-ear skin inside an angle-specific ROI."""
    ear_rois = {65.0: (548, 551, 37, 59), 77.5: (492, 548, 38, 66)}
    cx, cy, rx, ry = ear_rois[angle]
    yy, xx = np.indices(target.shape[:2])
    r, g, b = (target[:, :, i].astype(np.int16) for i in range(3))
    flesh = (r > 175) & (g > 100) & (g > b + 2) & (r > g + 10)
    ellipse = (((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1)
    return flesh & ellipse & (target[:, :, 3] > 16)


def register(root, angle, out):
    root = Path(root).resolve()
    out = Path(out).resolve()
    if float(angle) not in ANGLE_KEYS:
        raise ValueError("Only P15-06 independent 65 and 77.5 angles supported")
    out.mkdir(parents=True, exist_ok=True)
    key = ANGLE_KEYS[float(angle)]
    folder = root / "p15-independent-candidates"
    provenance = load(folder / (key + "-qwen2511-v2.provenance.json"))
    painted = folder / (key + "-qwen2511-v2.png")
    matte = folder / (key + "-source-rgba.png")
    matte_qa = load(matte.with_suffix(".qa.json"))
    original = load(root / "p5-see-through/mv-candidate/parts.json")
    original90 = next(x for x in original["wholeViews"] if x["yawDeg"] == 90)
    if original["characterId"] != CHARACTER or provenance["characterId"] != CHARACTER:
        raise AssertionError("Original P0 identity reference mismatch")
    if sha(painted) != provenance["sha256"]:
        raise AssertionError("Independently generated painted source hash changed")
    if sha(matte) != matte_qa["outputPNG_SHA256"] or sha(painted) != matte_qa["sourceArtworkSHA256"]:
        raise AssertionError("Native alpha-matting source chain mismatch")
    ref_file = root / original90["path"]
    if sha(ref_file) != original90["sha256"]:
        raise AssertionError("Original P0 90-degree reference image hash mismatch")

    base = rgba(ref_file)
    target = rgba(matte)
    part_list = sorted(
        (x for x in original["parts"] if x["yawDeg"] == 90),
        key=lambda x: x["depthOrder"],
    )
    ids = [p["semanticId"] for p in part_list]
    if len(part_list) != 13 or [x["depthOrder"] for x in part_list] != list(range(13)):
        raise AssertionError("P0 original source semantic depth contract changed")
    pairA = cv2.resize(base, (FLOW_W, FLOW_W), interpolation=cv2.INTER_AREA)
    pairB = cv2.resize(target, (FLOW_W, FLOW_W), interpolation=cv2.INTER_AREA)
    _, reverse = get_flow(pairA, pairB, mode="dis")
    map_x, map_y = coords_from_target(W, W, reverse)
    predictions = []
    for part in part_list:
        ref_part = root / part["path"]
        if sha(ref_part) != part["frameSha256"]:
            raise AssertionError("P0 original source part SHA changed: " + part["semanticId"])
        if part["semanticId"] in SPECIAL_HIDDEN or part["semanticId"] == "hair.ahoge":
            predictions.append(np.zeros((W, W), dtype=np.float32))
        else:
            alpha = rgba(ref_part)[:, :, 3].astype(np.float32) / 255
            predictions.append(cv2.remap(alpha, map_x, map_y, cv2.INTER_LINEAR,
                                         borderMode=cv2.BORDER_CONSTANT))
    labels, fallback = assign_labels(predictions, ids, target[:, :, 3], target[:, :, :3])
    ahoge = candidate_ahoge(target)
    ear = candidate_ear(target, float(angle))
    labels[ear] = ids.index("ear.near")
    labels[ahoge] = ids.index("hair.ahoge")
    fg = target[:, :, 3] > 0
    if np.any(fg & (labels < 0)):
        raise AssertionError("Some source-painted pixels have no semantic owner")
    if int(ahoge.sum()) < 500:
        raise AssertionError("P0 one-ahoge identity missing from painted source")
    canvas = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    records = []
    overlays = {}
    for i, part in enumerate(part_list):
        role = part["semanticId"]
        cutout = target.copy()
        cutout[(labels != i) | (~fg)] = 0
        if role in SPECIAL_HIDDEN:
            cutout[:, :, :] = 0
        file = out / "layers" / (role + ".png")
        file.parent.mkdir(parents=True, exist_ok=True)
        layer = Image.fromarray(cutout, "RGBA")
        layer.save(file)
        canvas.alpha_composite(layer)
        region_alpha = cutout[:, :, 3]
        count = int((region_alpha > 0).sum())
        ys, xs = np.where(region_alpha > 0)
        bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1] if len(xs) else None
        records.append({
            "semanticId": role, "depthOrder": part["depthOrder"],
            "originalP0View": 90, "originalP0LayerSHA256": part["frameSha256"],
            "path": str(file.relative_to(root)), "sha256": sha(file),
            "visiblePixels": count, "partialAlphaPixels": int(((region_alpha > 0) & (region_alpha < 255)).sum()),
            "bbox": bbox, "canvas": [W, W],
            "registeredFromArtwork": str(painted.relative_to(root)),
        })
        if role in ("face.skin", "eye.near", "nose", "mouth", "hair.front", "hair.side", "hair.back", "hair.ahoge"):
            overlays[role] = layer
    composite = out / (key + "-artmesh-composite.png")
    canvas.save(composite)
    a = np.asarray(canvas).astype(np.int16)
    t = target.astype(np.int16)
    delta_a = int(np.abs(a[:, :, 3] - t[:, :, 3]).max())
    delta_rgb = int(np.abs(a[:, :, :3][fg] - t[:, :, :3][fg]).max())
    if delta_a != 0 or delta_rgb != 0:
        raise AssertionError(f"Source pixel exactness failed: alpha={delta_a} RGB={delta_rgb}")
    panel = Image.new("RGB", (4 * 420, 460), (34, 47, 62))
    pen = ImageDraw.Draw(panel)
    def flat(pic):
        bg = Image.new("RGBA", (W, W), (45, 59, 75, 255))
        bg.alpha_composite(pic)
        return bg.convert("RGB")
    variants = [
        (Image.fromarray(base, "RGBA"), "Original P0 90°"),
        (Image.fromarray(target, "RGBA"), str(angle) + "° painted RGBA"),
        (canvas, str(angle) + "° / 13 ArtMesh"),
        (overlays["hair.front"], str(angle) + "° front hair ArtMesh"),
    ]
    for i, (pic, label) in enumerate(variants):
        panel.paste(flat(pic).resize((420, 420), Image.Resampling.LANCZOS), (i * 420, 0))
        pen.text((i * 420 + 9, 432), label, fill="white")
    sheet = out / (key + "-source-artmesh-contact.jpg")
    panel.save(sheet, quality=92)
    measures = {
        "schema": "KOMA-P0-P15-06-PAINTED-KEYVIEW-SEMANTIC-CANDIDATE-V1",
        "characterId": CHARACTER,
        "yaw": angle,
        "originalP0SourceAngles": [0, 45, 90],
        "independentPainting": {"path": str(painted.relative_to(root)), "sha256": sha(painted)},
        "paintingProvenanceSHA256": sha(folder / (key + "-qwen2511-v2.provenance.json")),
        "sourceInputYaw": provenance["sourceYaw"],
        "paintModel": provenance["model"],
        "paintAdapter": provenance["adapter"],
        "paintSeed": provenance["seed"],
        "sourceMatte": {"path": str(matte.relative_to(root)), "sha256": sha(matte)},
        "sourceMatteQASHA256": sha(matte.with_suffix(".qa.json")),
        "sourceSemanticOwnerYaw": 90,
        "source90SHA256": original90["sha256"],
        "semanticPartCount": len(records),
        "nativeRGBA": [W, W],
        "strokeFrameContext": [W, W],
        "sourceFlowGrid": [FLOW_W, FLOW_W],
        "pixelAssignment": "DIS_REGISTERED_P0_90_ARTMESH_WITH_COLORED_ANATOMY_ROI_AND_ONE_AHOGE",
        "nearestKnownSemanticOwnerPixels": fallback,
        "nearEarCandidateSkinPixels": int(ear.sum()),
        "singleAhogeCandidatePixels": int(ahoge.sum()),
        "foregroundPixels": int(fg.sum()),
        "semanticLayerRecords": records,
        "composite": {"path": str(composite.relative_to(root)), "sha256": sha(composite)},
        "contact": {"path": str(sheet.relative_to(root)), "sha256": sha(sheet)},
        "alphaRecompositionMaxDifference": delta_a,
        "rgbRecompositionMaxDifference": delta_rgb,
        "identityAnchorApproval": "PENDING_HERO_AND_ANATOMY_REVIEW",
        "angleArtworkApproval": "PENDING_INDEPENDENT_VISUAL_REVIEW",
        "semanticLayerApproval": "PENDING_BOUNDARY_AND_OCCLUSION_REVIEW",
        "status": "P15_06_PAINTED_KEYVIEW_SEMANTIC_CANDIDATE_REGISTERED",
    }
    (out / "qa.json").write_text(json.dumps(measures, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": measures["status"],
        "yaw": angle, "semanticParts": len(records),
        "visibleRolePixels": {r["semanticId"]: r["visiblePixels"] for r in records},
        "alphaDiff": delta_a, "rgbDiff": delta_rgb,
        "fallbackPixels": fallback,
    }, ensure_ascii=False))
    return measures


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--angle", type=float, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    register(args.root, args.angle, args.out)

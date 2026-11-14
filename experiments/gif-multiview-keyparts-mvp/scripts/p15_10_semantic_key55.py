#!/usr/bin/env python3
"""Register P0 55-degree ArtMesh semantic ownership from P5 controls.

This is a geometry-derived, editable diagnostic layer set. Independent
hand-painted 55-degree layers and hidden underpaint remain separate inputs.
"""
from __future__ import annotations
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from p15_09_anchor_pose import ASSETS, BASE, DEST, SOURCE, anchors, sha, source_checks, warp_image

OUTPUT = ASSETS / "p15-10-semantic-pose" / "yaw055"
CHECK = BASE / "evidence" / "p15-10-semantic-source-qa.json"


def image_rgba(file: Path) -> np.ndarray:
    with Image.open(file) as image:
        if image.size != (1024, 1024) or image.mode != "RGBA":
            raise ValueError(f"Expected native 1024 RGBA: {file}")
        return np.array(image)


def run():
    manifest, landmarks, whole = source_checks()
    roles = sorted((part for part in manifest["parts"] if part["yawDeg"] == 45),
                   key=lambda part: part["depthOrder"])
    if len(roles) != 13 or [p["depthOrder"] for p in roles] != list(range(13)):
        raise AssertionError("P0 45-degree semantic identity/depth registry changed")
    original = image_rgba(SOURCE)
    pose, flow = warp_image(original, anchors(landmarks))
    key55 = DEST / "yaw055-p5-anchor-reference.png"
    if not np.array_equal(pose, image_rgba(key55)):
        raise AssertionError("Pose differs from registered P15-09 geometry")
    # Assign the topmost original visible semantic owner to each target pixel.
    # The final layer colors are copied from one 55-degree geometric keyframe.
    # That ensures exact recomposition without claiming unpainted hidden details.
    yy, xx = np.meshgrid(np.arange(1024, dtype=np.float32),
                         np.arange(1024, dtype=np.float32), indexing="ij")
    ownership = np.full((1024, 1024), -1, dtype=np.int16)
    origin_composite = Image.new("RGBA", (1024, 1024))
    original_records = []
    for item in roles:
        src = ASSETS / item["path"]
        if sha(src) != item["frameSha256"]:
            raise AssertionError(f"Source part changed: {item['semanticId']}")
        layer = image_rgba(src)
        origin_composite.alpha_composite(Image.fromarray(layer, "RGBA"))
        ownership[cv2.remap(layer[:, :, 3], xx + flow[:, :, 0],
                            yy + flow[:, :, 1], cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_CONSTANT) > 2] = item["depthOrder"]
        original_records.append({"semanticId": item["semanticId"],
                                 "sourceSHA256": item["frameSha256"]})
    if not np.array_equal(np.asarray(origin_composite), original):
        raise AssertionError("Original P0 45-degree source layers differ from original image")
    # Preserve even RGB encoded below alpha=1: those bytes belong to the
    # same full-canvas source and are harmless after alpha compositing.
    fallback = (ownership < 0) & np.any(pose != 0, axis=2)
    ownership[fallback] = 0
    OUTPUT.mkdir(parents=True, exist_ok=True)
    layers, assembled = [], np.zeros_like(pose, dtype=np.uint16)
    for role in roles:
        color = np.zeros_like(pose)
        selected = ownership == role["depthOrder"]
        color[selected] = pose[selected]
        dest = OUTPUT / (role["semanticId"] + ".png")
        Image.fromarray(color, "RGBA").save(dest)
        assembled += color.astype(np.uint16)
        layers.append({"semanticId": role["semanticId"],
                       "depthOrder": role["depthOrder"],
                       "outputPath": str(dest.relative_to(ASSETS)),
                       "sha256": sha(dest),
                       "visiblePixels": int(np.count_nonzero(color[:, :, 3])),
                       "source45SHA256": role["frameSha256"],
                       "artRole": "P5 derived visible-raster ownership"})
    dst = assembled.astype(np.uint8)
    if not np.array_equal(dst, pose):
        raise AssertionError("P15-10 role ownership did not recompose exactly")
    report = {
        "schema": "KOMA-P15-10-GEOMETRY-OWNERSHIP-V1",
        "characterId": "p0_character_001",
        "angle": 55.0,
        "source45SHA256": whole["sha256"],
        "P5Pose55SHA256": sha(key55),
        "semanticLayerCount": len(layers),
        "semanticLayers": layers,
        "visibleUnownedFallbackPixels": int(np.count_nonzero(fallback)),
        "pixelExactComposite": True,
        "farEyePixels": next(x["visiblePixels"] for x in layers if x["semanticId"] == "eye.far"),
        "hairclipPixels": next(x["visiblePixels"] for x in layers if x["semanticId"] == "hair.clip.cross_gold"),
        "representation": "P5-anchored ownership labels with source texture",
        "sourceApproval": "INDEPENDENT_55_PAINTING_AND_HIDDEN_UNDERPAINT_REQUIRED",
    }
    CHECK.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("angle", "semanticLayerCount",
                      "visibleUnownedFallbackPixels", "pixelExactComposite",
                      "farEyePixels", "hairclipPixels")}))
    return report


if __name__ == "__main__":
    run()

#!/usr/bin/env python3
"""Verify eight Blender PMX structural reference renders and make a contact sheet.

All screenshots are derived images of an authorized third-party 3D model;
they are not independently hand-drawn layered artwork for the VDD engine.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

NAMES = [
    "yaw000_front", "yaw045_three_quarter", "yaw090_profile",
    "yaw135_back_three_quarter", "yaw180_back",
    "yaw225_back_three_quarter", "yaw270_profile",
    "yaw315_three_quarter"
]


def image_diagnostics(filename: Path, yaw: int) -> dict:
    blob = filename.read_bytes()
    with Image.open(filename) as handle:
        if handle.format != "PNG" or handle.mode != "RGBA":
            raise AssertionError(f"PNG_RGBA_REQUIRED: {filename.name}")
        im = handle.copy()
    if im.size != (768, 768):
        raise AssertionError(f"IMAGE_SIZE: {filename.name}: {im.size}")
    alpha = im.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        raise AssertionError(f"EMPTY_RENDER: {filename.name}")
    visible = sum(n for a, n in enumerate(alpha.histogram()) if a > 16)
    pixels = im.width * im.height
    coverage = visible / pixels
    if not (0.20 < coverage < 0.55):
        raise AssertionError(f"ALPHA_COVERAGE: {filename.name}: {coverage}")
    colors = im.crop((160, 55, 635, 545))
    orange_pixels = sum(1 for r, g, b, a in colors.getdata()
                        if a > 180 and r > 155 and r > g * 1.20 and g > b * 1.25)
    if orange_pixels < 1800:
        raise AssertionError(f"HAIR_COLOR_MISSING: {filename.name}: {orange_pixels}")
    return {
        "yawDeg": yaw, "filename": filename.name,
        "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(),
        "imageSize": [im.width, im.height], "alphaCoverage": round(coverage, 6),
        "alphaBounds": list(bbox), "orangeHairPixels": orange_pixels,
        "provenance": "third_party_pmx_reference_render",
        "independentPaintedArt": False
    }


def contact_sheet(root: Path, output: Path) -> str:
    panel_w, panel_h = 366, 424
    grid = Image.new("RGB", (4 * panel_w, 2 * panel_h), (18, 27, 42))
    draw = ImageDraw.Draw(grid)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font = ImageFont.truetype(font_path, 24) if Path(font_path).is_file() else ImageFont.load_default()
    for i, name in enumerate(NAMES):
        with Image.open(root / f"{name}.png") as source:
            crop = source.convert("RGBA").crop((120, 20, 648, 548))
        crop.thumbnail((330, 350), Image.Resampling.LANCZOS)
        layer = Image.new("RGBA", (330, 350), (240, 243, 248, 255))
        layer.alpha_composite(crop, ((330-crop.width)//2, (350-crop.height)//2))
        x, y = (i % 4)*panel_w+18, (i // 4)*panel_h+18
        grid.paste(layer.convert("RGB"), (x, y))
        draw.text((x+7, y+360), name, fill=(241, 244, 249), font=font)
    output.parent.mkdir(parents=True, exist_ok=True)
    grid.save(output, optimize=True)
    return hashlib.sha256(output.read_bytes()).hexdigest()


def run(input_dir: Path) -> dict:
    images = [image_diagnostics(input_dir / f"{name}.png", i*45) for i, name in enumerate(NAMES)]
    if len({d["sha256"] for d in images}) != len(images):
        raise AssertionError("DUPLICATE_VIEW_FRAMES")
    if images[2]["alphaCoverage"] >= images[0]["alphaCoverage"]:
        raise AssertionError("SIDE_SILHOUETTE_NOT_NARROWER")
    sheet_path = input_dir / "turnaround-contact-sheet.png"
    sheet_sha = contact_sheet(input_dir, sheet_path)
    report = {
        "schema": "R1999-SONETTO-3D-TURNAROUND-QA-V1",
        "status": "PASS_3D_REFERENCE_RENDER",
        "sourceType": "WTHN_Ross_Sonetto_PMX_render",
        "renderedViewAngles": [i*45 for i in range(len(images))],
        "renderedImageCount": len(images),
        "sourceModelRestricted": True,
        "releasePolicy": "rendered images with BLUEPOCH / Reverse:1999 and WTHN_Ross credit",
        "independent2DArtworkCount": 0,
        "viewKeySourceRole": "STRUCTURAL_REFERENCE_ONLY",
        "renderedImages": images,
        "contactSheet": {"filename": sheet_path.name, "sha256": sheet_sha,
                         "bytes": sheet_path.stat().st_size}
    }
    (input_dir / "turnaround-qa.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.input_dir.resolve())
    print(json.dumps({"status": report["status"],
                      "images": report["renderedImageCount"],
                      "sha256": report["contactSheet"]["sha256"]}))


if __name__ == "__main__":
    main()

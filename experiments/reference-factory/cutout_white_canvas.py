"""CORE-024 alternate cutout experiment (white-canvas baseline).

Experimental only: hard-alpha cutouts of the ORIGINAL source RGB.
Variant W250/W245: border-connected near-white removal (scipy.ndimage
binary_propagation seeded from the image border).
Variant XGEN: transfer of the existing imagegen alpha onto the original RGB.

No installs, no models, no API. Original RGB is preserved bit-for-bit.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "out/candidates/pilot-C-001.png")
GEN = os.path.join(ROOT, "out/core024/imagegen-cutout-C.png")
OUT = os.path.join(ROOT, "out/core024/white-canvas")
QA = os.path.join(OUT, "qa")

# Pinned input hashes. The run must fail immediately if either changed.
EXPECTED_C_SHA256 = "66d661022b811874afb68ac9a033e8cede5d591d005503e4d023702de5424169"
EXPECTED_GEN_SHA256 = "220ee4ff62baae15aa0fa14f9dfb967c74ad14028f902699df2562c1aa9e8f25"


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load_source():
    im = Image.open(SRC)
    rgb = np.array(im.convert("RGB"), dtype=np.uint8)
    return rgb


def border_connected_alpha(rgb: np.ndarray, threshold: int) -> np.ndarray:
    """Hard alpha: 0 only where near-white pixels connect to the image border."""
    near_white = np.all(rgb >= threshold, axis=2)
    h, w = near_white.shape
    seed = np.zeros_like(near_white)
    seed[0, :] = near_white[0, :]
    seed[h - 1, :] = near_white[h - 1, :]
    seed[:, 0] = near_white[:, 0]
    seed[:, w - 1] = near_white[:, w - 1]
    exterior = ndimage.binary_propagation(seed, mask=near_white)
    alpha = np.where(exterior, 0, 255).astype(np.uint8)
    return alpha


def alpha_stats(alpha: np.ndarray):
    """Split alpha into zero / partial / full(255) buckets.

    NOTE: the previous "opaque_px" name actually counted *non-zero* alpha
    (alpha > 0), which is not the same as alpha == 255. It is renamed
    "nonzero_px" here and the real buckets are reported separately.
    """
    total = alpha.size
    zero = int((alpha == 0).sum())
    full = int((alpha == 255).sum())
    partial = int(((alpha > 0) & (alpha < 255)).sum())
    nonzero = alpha > 0
    ys, xs = np.nonzero(nonzero)
    if len(ys) == 0:
        return {"zero_px": zero, "partial_px": partial, "full_px": full,
                "nonzero_px": 0, "transparent_px": total, "coverage": 0.0,
                "bbox_xywh": None, "edge_contact_px": 0}
    bbox = [int(xs.min()), int(ys.min()),
            int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)]
    edge = int(nonzero[0, :].sum() + nonzero[-1, :].sum()
               + nonzero[:, 0].sum() + nonzero[:, -1].sum())
    return {"zero_px": zero,
            "partial_px": partial,
            "full_px": full,
            "nonzero_px": int(len(ys)),
            "transparent_px": int(total - len(ys)),
            "coverage": round(float(len(ys)) / total, 6),
            "bbox_xywh": bbox,
            "edge_contact_px": edge}


def _png_complete(path: str) -> bool:
    """Chunk-level PNG integrity check (catches truncated writes)."""
    with open(path, "rb") as fh:
        d = fh.read()
    if len(d) < 8 or d[:8] != b"\x89PNG\r\n\x1a\n":
        return False
    i = 8
    while i + 8 <= len(d):
        ln = int.from_bytes(d[i:i + 4], "big")
        typ = d[i + 4:i + 8]
        if i + 12 + ln > len(d):
            return False
        if typ == b"IEND":
            return i + 12 + ln == len(d)
        i += 12 + ln
    return False


def save_rgba(rgb: np.ndarray, alpha: np.ndarray, path: str):
    out = np.dstack([rgb, alpha])
    Image.fromarray(out, "RGBA").save(path)
    if not _png_complete(path):
        raise RuntimeError("could not write a complete PNG: " + path)
    # verify RGB bit-for-bit round trip (including alpha==0 pixels)
    back = np.array(Image.open(path).convert("RGBA"), dtype=np.uint8)
    assert np.array_equal(back[:, :, :3], rgb), "RGB changed in " + path
    assert np.array_equal(back[:, :, 3], alpha), "alpha changed in " + path
    return {"path": os.path.relpath(path, ROOT), "sha256": sha256(path)}


def checker(w, h, cell=32):
    yy, xx = np.mgrid[0:h, 0:w]
    c = (((yy // cell) + (xx // cell)) % 2).astype(np.uint8) * 90 + 165
    return np.dstack([c, c, c]).astype(np.uint8)


def composite(rgb, alpha, bg):
    a = alpha[:, :, None].astype(np.float32) / 255.0
    return (rgb.astype(np.float32) * a + bg.astype(np.float32) * (1 - a)
            ).astype(np.uint8)


def crop_anchors(alpha):
    """Pick crop windows around geometry extremities of the opaque region."""
    opaque = alpha > 0
    ys, xs = np.nonzero(opaque)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    w, h = x1 - x0 + 1, y1 - y0 + 1
    s = max(64, int(0.16 * max(w, h)))
    anchors = {
        "top_center_fur": ((x0 + x1) // 2, max(0, y0 + s // 2)),
        "top_left_ear_tip": (x0 + s // 2, max(0, y0 + s // 2)),
        "top_right_ear_tip": (x1 - s // 2, max(0, y0 + s // 2)),
        "mid_right_hair": (x1 - s // 2, (y0 + y1) // 2),
        "bottom_center_neck": ((x0 + x1) // 2, min(y1 - s // 2, y1)),
    }
    out = {}
    for name, (cx, cy) in anchors.items():
        half = s // 2
        out[name] = (max(0, cx - half), max(0, cy - half),
                     min(rgb_w, cx + half), min(rgb_h, cy + half))
    return out


def make_qa(rgb, alpha, tag):
    h, w = alpha.shape
    bgs = {"black": np.zeros((h, w, 3), np.uint8),
           "white": np.full((h, w, 3), 255, np.uint8),
           "checker": checker(w, h)}
    for name, bg in bgs.items():
        Image.fromarray(composite(rgb, alpha, bg)).save(
            os.path.join(QA, f"{tag}_on_{name}.png"))
    # zoom crops (2x nearest) over the three backgrounds
    tiles = []
    for aname, (x0, y0, x1, y1) in crop_anchors(alpha).items():
        for bname in ("black", "checker"):
            patch = composite(rgb[y0:y1, x0:x1], alpha[y0:y1, x0:x1],
                              bgs[bname][y0:y1, x0:x1])
            p = Image.fromarray(patch).resize(
                (patch.shape[1] * 2, patch.shape[0] * 2), Image.NEAREST)
            tiles.append((f"{aname}|{bname}", p))
    cols = 5
    rows = (len(tiles) + cols - 1) // cols
    tw = max(t.width for _, t in tiles)
    th = max(t.height for _, t in tiles)
    sheet = Image.new("RGB", (cols * tw, rows * th), (30, 30, 30))
    for i, (_, t) in enumerate(tiles):
        sheet.paste(t, ((i % cols) * tw, (i // cols) * th))
    sheet.save(os.path.join(QA, f"{tag}_crop_sheet.png"))


def verify_pinned_inputs():
    """Fail fast if the pinned candidate / imagegen cutout changed."""
    problems = []
    for path, expected in ((SRC, EXPECTED_C_SHA256), (GEN, EXPECTED_GEN_SHA256)):
        if not os.path.exists(path):
            problems.append(f"missing input: {path}")
            continue
        actual = sha256(path)
        if actual != expected:
            problems.append(f"SHA256 MISMATCH {os.path.relpath(path, ROOT)}: {actual} != {expected}")
    if problems:
        for p in problems:
            print("FAIL:", p, file=sys.stderr)
        return False
    return True


def main():
    global rgb_w, rgb_h
    if not verify_pinned_inputs():
        return 2
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(QA, exist_ok=True)
    rgb = load_source()
    rgb_h, rgb_w = rgb.shape[:2]
    report = {"source": {"path": os.path.relpath(SRC, ROOT), "sha256": sha256(SRC),
                         "mode": "RGB", "size": [rgb_w, rgb_h]},
              "imagegen_cutout": {"path": os.path.relpath(GEN, ROOT),
                                  "sha256": sha256(GEN)},
              "variants": {}}

    for t in (250, 245):
        alpha = border_connected_alpha(rgb, t)
        tag = f"W{t}"
        p = os.path.join(OUT, f"white-canvas-{tag}.png")
        meta = save_rgba(rgb, alpha, p)
        meta.update({"threshold": t, "method": "border-connected near-white",
                     "alpha": alpha_stats(alpha)})
        make_qa(rgb, alpha, tag)
        report["variants"][tag] = meta

    gen = Image.open(GEN).convert("RGBA")
    if gen.size != (rgb_w, rgb_h):
        report["variants"]["XGEN"] = {"status": "SKIPPED_SIZE_MISMATCH",
                                      "gen_size": list(gen.size)}
    else:
        galpha = np.array(gen)[:, :, 3]
        p = os.path.join(OUT, "white-canvas-XGEN.png")
        meta = save_rgba(rgb, galpha, p)
        meta.update({"method": "imagegen alpha transferred to original RGB",
                     "alpha": alpha_stats(galpha)})
        make_qa(rgb, galpha, "XGEN")
        report["variants"]["XGEN"] = meta

    # comparison of alpha masks
    report["note"] = ("EXPERIMENTAL cutout only. Not semantic decomposition, not a rig, "
                      "not exact alpha ground truth, not an approved multi-view character.")
    with open(os.path.join(OUT, "report.json"), "w") as fh:
        json.dump(report, fh, indent=2)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""CORE-024 native source-layer export from the pinned tutorial-aka.psd.

Uses only the already installed psd-tools / Pillow / NumPy stack. No installs,
no model inference, no white-keying, no repainting.

Outputs (reference-factory/out/core024/native-v2/):
  layers/leaf-<i>-<name>.png   raw RGBA of every genuine native leaf (topil)
  composite-transparent.png     full-canvas native composite, force=True
  composite-cached.png         merged image stored in the PSD
  qa-backgrounds.png           black / checker / white composite QA sheet
  contact-sheet-layers.png     genuine leaf contact sheet
  native-export.json           machine report
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from psd_tools import PSDImage

HERE = Path(__file__).resolve().parent
ROOT = HERE  # experiments/reference-factory
OUT = ROOT / "out" / "core024" / "native-v2"
LAYERS = OUT / "layers"
LOCK = ROOT / "sources.lock.json"
PSD_NAME = "tutorial-aka.psd"
EXPECTED_LEAF_COUNT = 62


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def alpha_stats(arr):
    a = arr[..., 3]
    total = int(a.size)
    opaque = int((a == 255).sum())
    transparent = int((a == 0).sum())
    partial = total - opaque - transparent
    return {
        "min": int(a.min()), "max": int(a.max()),
        "opaque_px": opaque, "transparent_px": transparent, "partial_px": partial,
        "transparent_fraction": round(transparent / total, 6),
        "opaque_fraction": round(opaque / total, 6),
        "partial_fraction": round(partial / total, 6),
        "unique_values": int(np.unique(a).size),
    }


def walk(group, prefix=()):
    """Explicit recursion; layer.path is not assumed to exist."""
    for layer in group:
        path = prefix + (layer.name,)
        if layer.is_group():
            yield from walk(layer, path)
        else:
            yield path, layer


def safe(name):
    return "".join(c if (c.isalnum() or c in "-_") else "_" for c in name)


def checker(size, cell=32):
    w, h = size
    arr = np.zeros((h, w, 3), np.uint8)
    ys, xs = np.mgrid[0:h, 0:w]
    m = ((xs // cell + ys // cell) % 2).astype(bool)
    arr[m] = 190
    arr[~m] = 128
    return Image.fromarray(arr, "RGB")


def over(bg_rgb, rgba):
    """Composite RGBA over an RGB background colour."""
    a = rgba[..., 3:4].astype(np.float32) / 255.0
    rgb = rgba[..., :3].astype(np.float32)
    bg = np.asarray(bg_rgb, np.float32).reshape(1, 1, 3)
    return (rgb * a + bg * (1 - a)).round().astype(np.uint8)


def panel(rgba, bg, size, label, bg_image=None):
    """bg_image (RGB, already size-sized) replaces a flat colour background."""
    if bg_image is None:
        im = Image.fromarray(over(bg, rgba), "RGB")
    else:
        a = rgba[..., 3:4].astype(np.float32) / 255.0
        im = Image.fromarray(
            (rgba[..., :3].astype(np.float32) * a + bg_image.astype(np.float32) * (1 - a)).round().astype(np.uint8), "RGB")
    im.thumbnail(size, Image.LANCZOS)
    canvas = Image.new("RGB", (size[0], size[1] + 22), (20, 20, 20))
    canvas.paste(im, ((size[0] - im.width) // 2, (size[1] - im.height) // 2))
    ImageDraw.Draw(canvas).text((6, size[1] + 5), label, fill=(235, 235, 235))
    return canvas


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    LAYERS.mkdir(parents=True, exist_ok=True)

    # --- verify pinned source BEFORE using it ---
    lock = json.loads(LOCK.read_text())
    entry = next(s for s in lock["sources"] if s["file"] == PSD_NAME)
    psd_path = ROOT / "out" / "source" / PSD_NAME
    actual = sha256(psd_path)
    if actual != entry["sha256"]:
        raise SystemExit(f"SHA256 MISMATCH: {actual} != {entry['sha256']}")

    psd = PSDImage.open(psd_path)  # open before reading metadata
    canvas = (int(psd.width), int(psd.height))
    report = {
        "psd": {"file": str(psd_path.relative_to(ROOT)), "sha256": actual,
                "sha256_verified": True, "source_url": entry["url"], "license": entry["license"]},
        "canvas": list(canvas), "color_mode": str(psd.color_mode), "channels": int(psd.channels),
        "outputs_dir": str(OUT.relative_to(ROOT)),
        "leaves": [], "groups": [], "errors": [], "notes": [],
    }

    # --- native composite: force=True with alpha=0 background (source truth) ---
    native = psd.composite(force=True, alpha=0.0, color=(1.0, 1.0, 1.0)).convert("RGBA")
    n_arr = np.asarray(native)
    comp_path = OUT / "composite-transparent.png"
    native.save(comp_path)
    report["composite_transparent"] = {
        "file": str(comp_path.relative_to(ROOT)), "sha256": sha256(comp_path),
        "alpha": alpha_stats(n_arr),
    }

    # --- cached merged image stored inside the PSD (opaque reference) ---
    cached = psd.composite().convert("RGBA")
    c_arr = np.asarray(cached)
    cached_path = OUT / "composite-cached.png"
    cached.save(cached_path)
    report["composite_cached"] = {
        "file": str(cached_path.relative_to(ROOT)), "sha256": sha256(cached_path),
        "alpha": alpha_stats(c_arr),
    }

    # --- fidelity: white-composited native vs cached merged RGB, foreground MAE ---
    white_comp = over((255, 255, 255), n_arr)
    fg = n_arr[..., 3] > 0
    chan_diff = np.abs(white_comp.astype(np.int16) - c_arr[..., :3].astype(np.int16))
    # true single-channel max error: max over channels of |diff| for each pixel
    per_px_max = chan_diff.max(axis=2)
    # kept for reference only: sum of the three channel absolute differences
    rgb_sum = chan_diff.sum(axis=2)
    report["fidelity_white_vs_cached"] = {
        "definition": "white-composited native rendering vs cached merged PSD RGB, foreground pixels (native alpha > 0)",
        "mae_rgb_definition": "mean over pixels and over the 3 RGB channels of |native - cached|",
        "max_abs_definition": "max over pixels of max over the 3 RGB channels of |native - cached| (single-channel maximum error, 0..255)",
        "max_rgb_sum_abs_definition": "max over pixels of the SUM of the 3 channel absolute differences (reference only, not the headline error)",
        "foreground_px": int(fg.sum()),
        "mae_rgb": round(float(chan_diff[fg].mean()), 4),
        "mae_max_channel": round(float(per_px_max[fg].mean()), 4),
        "max_abs": int(per_px_max[fg].max()),
        "max_rgb_sum_abs": int(rgb_sum[fg].max()),
        "mae_all_px": round(float(chan_diff.mean()), 4),
    }

    # --- group structure (order / visibility evidence) ---
    def groups_of(group, prefix=()):
        for layer in group:
            p = prefix + (layer.name,)
            report["groups"].append({
                "path": "/".join(p), "is_group": layer.is_group(), "visible": bool(layer.visible),
                "opacity": float(layer.opacity), "blend_mode": str(layer.blend_mode),
            })
            if layer.is_group():
                groups_of(layer, p)
    groups_of(psd)

    # --- leaf export via topil() (pixel-preserving raw RGBA) ---
    order = 0
    thumbs = []
    for path, layer in walk(psd):
        order += 1
        name = layer.name
        rec = {
            "order": order, "name": name, "path": "/".join(path), "kind": str(layer.kind),
            "bounds": [int(layer.left), int(layer.top), int(layer.right), int(layer.bottom)],
            "width": int(layer.width), "height": int(layer.height),
            "visible": bool(layer.visible), "opacity": float(layer.opacity),
            "blend_mode": str(layer.blend_mode),
            "has_mask": layer.mask is not None,
            "mask_bbox": list(layer.mask.bbox) if layer.mask is not None else None,
            "clipping": bool(getattr(layer, "clipping", False)),
        }
        try:
            raw = layer.topil()
        except Exception as exc:  # noqa: BLE001
            rec["error"] = repr(exc)
            report["errors"].append({"path": rec["path"], "error": repr(exc)})
            report["leaves"].append(rec)
            continue
        if raw is None:
            rec["error"] = "topil() returned None"
            report["errors"].append({"path": rec["path"], "error": rec["error"]})
            report["leaves"].append(rec)
            continue
        rgba = raw.convert("RGBA")
        arr = np.asarray(rgba)
        fp = LAYERS / f"leaf-{order:02d}-{safe(name)}.png"
        rgba.save(fp)
        # pixel equality of exported PNG vs the topil RGBA buffer
        reread = np.asarray(Image.open(fp).convert("RGBA"))
        rec.update({
            "file": str(fp.relative_to(ROOT)), "sha256": sha256(fp),
            "size": [rgba.width, rgba.height],
            "alpha": alpha_stats(arr),
            "topil_pixel_equal": bool(np.array_equal(reread, arr)),
        })
        report["leaves"].append(rec)
        thumbs.append((rec, arr))

    # --- QA sheet: native composite over black / checker / white ---
    size = (520, 520)
    chk = np.asarray(checker(canvas, 32))
    panels = [
        panel(n_arr, (0, 0, 0), size, "native composite over black"),
        panel(n_arr, (0, 0, 0), size, "native composite over checker", bg_image=chk),
        panel(n_arr, (255, 255, 255), size, "native composite over white"),
    ]
    sheet = Image.new("RGB", (size[0] * 3, size[1] + 24), (20, 20, 20))
    for i, p in enumerate(panels):
        sheet.paste(p, (i * size[0], 0))
    qa_path = OUT / "qa-backgrounds.png"
    sheet.save(qa_path)
    report["qa_backgrounds"] = {"file": str(qa_path.relative_to(ROOT)), "sha256": sha256(qa_path)}

    # --- genuine-layer contact sheet (all leaves, checker thumbnails) ---
    cols, cell, pad, lab = 8, 150, 6, 26
    rows = (len(thumbs) + cols - 1) // cols
    cs = Image.new("RGB", (cols * (cell + pad) + pad, rows * (cell + pad + lab) + pad), (24, 24, 24))
    draw = ImageDraw.Draw(cs)
    font = ImageFont.load_default()
    for i, (rec, arr) in enumerate(thumbs):
        c, r = i % cols, i // cols
        x = pad + c * (cell + pad)
        y = pad + r * (cell + pad + lab)
        thumb = Image.fromarray(arr, "RGBA")
        thumb.thumbnail((cell, cell), Image.LANCZOS)
        tile = checker((cell, cell), 12)
        tile.paste(thumb, ((cell - thumb.width) // 2, (cell - thumb.height) // 2), thumb)
        cs.paste(tile, (x, y))
        draw.text((x, y + cell + 3), f"{rec['order']:02d} {rec['name']}"[:24], fill=(225, 225, 225), font=font)
    cs_path = OUT / "contact-sheet-layers.png"
    cs.save(cs_path)
    report["contact_sheet"] = {"file": str(cs_path.relative_to(ROOT)), "sha256": sha256(cs_path),
                               "tiles": len(thumbs), "cols": cols, "rows": rows}

    report["notes"].append(
        "Leaf PNGs are raw topil() RGBA buffers: they do NOT bake layer masks, blend modes, "
        "opacity or clipping, so masked/blended leaves are not appearance-equivalent standalone images."
    )
    report["notes"].append("No white-keying or thresholding was applied; alpha comes from the PSD itself.")
    report["notes"].append("Composite uses psd.composite(force=True, alpha=0.0, color=(1,1,1)): genuine source-layer rendering.")
    report["notes"].append(
        "The forced composite is a forced layer render: it is NOT verified full-front-view parity "
        "and NOT UV parity. Per-layer alpha / opacity / blend mode are preserved in this report; "
        "the leaf PNGs themselves do not bake masks, blend modes, opacity or clipping."
    )
    report["notes"].append(
        "Native alpha channel of the source PSD is preserved (no white-keying, no repainting). "
        "Forced compositing can spill shadows/halos outside the intended shape."
    )
    report["summary"] = {
        "leaf_count": len(report["leaves"]),
        "expected_leaf_count": EXPECTED_LEAF_COUNT,
        "leaf_errors": len(report["errors"]),
        "all_topil_pixel_equal": all(l.get("topil_pixel_equal") for l in report["leaves"] if "error" not in l),
        "mismatched_png_layers": [l.get("path") for l in report["leaves"]
                                  if "error" not in l and not l.get("topil_pixel_equal")],
    }

    (OUT / "native-export.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report["summary"], indent=2))
    print(json.dumps(report["fidelity_white_vs_cached"], indent=2))
    print(json.dumps(report["composite_transparent"]["alpha"], indent=2))
    print("out:", OUT)

    # --- hard acceptance gates: any failure => non-zero exit ---
    failures = []
    if report["summary"]["leaf_count"] != EXPECTED_LEAF_COUNT:
        failures.append(f"leaf count {report['summary']['leaf_count']} != {EXPECTED_LEAF_COUNT}")
    if report["errors"]:
        failures.append(f"{len(report['errors'])} leaf export errors")
    if report["summary"]["mismatched_png_layers"]:
        failures.append(f"PNG != SDK RGBA for: {report['summary']['mismatched_png_layers']}")
    if failures:
        for f in failures:
            print("FAIL:", f, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

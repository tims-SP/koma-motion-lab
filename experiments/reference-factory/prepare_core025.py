#!/usr/bin/env python3
"""CORE-025 M1: PSD -> GPU-reproducible NORMAL textures + CPU reference composite.

Pipeline
--------
1. Verify the pinned PSD (sources.lock.json + fixed SHA) and re-enumerate the 62
   leaf layers with the PSD SDK; cross-check against the CORE-024 export
   (names / order / bounds / blend mode) and against the CORE-024 layer PNGs
   (pixel-exact RGBA).  Any mismatch aborts with a non-zero exit code.
2. Write the fixed layer contract (config/core025-layer-contract.json).
3. For every layer, in bottom-to-top order, bake MULTIPLY layers into NORMAL
   textures (RGB = effective_source_rgb, quantised to uint8, alpha preserved)
   and composite the *quantised exported textures* so the CPU reference is
   reproducible from the exported PNGs alone.
4. Emit the transparent CPU composite plus white / black / checker QA renders,
   a labeled comparison sheet, and the 9-shadow before/after contact sheet.
5. Measure against the real SDK composite (psd.composite(force=True, alpha=0.0,
   color=(1,1,1))) and enforce the M1 numeric gate.

Numeric domain
---------------
All compositing math runs in float 0..1 on *straight* (non-premultiplied) RGB
plus alpha, in the sRGB value domain (no linearisation, no lighting).
Compositing is premultiplied internally:

    effective_source_rgb = Cs                                   (NORMAL)
                         = Cs * (1 - Ab + Ab * Cb)               (MULTIPLY)
    premult_out = As * effective_source_rgb + (1 - As) * Ab * Cb
    Ao          = As + Ab * (1 - As)
    Co          = premult_out / Ao            (Ao == 0 -> 0)

Source: W3C compositing-1 (alpha compositing) + Photoshop-style separable
multiply, matching psd_tools' own compositor arithmetic.

Outputs (only under out/core025/assembly/):
    source/layers/leaf-XX-<name>.png     clean/layers/leaf-XX-<name>.png
    source/source-cpu.png                clean/clean-cpu.png
    source/source-cpu-{white,black,checker}.png
    clean/clean-cpu-{white,black,checker}.png
    comparison-sheet.png  shadow-cleanup-sheet.png
    assembly.json  qa.json
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from psd_tools import PSDImage

HERE = Path(__file__).resolve().parent          # experiments/reference-factory
ROOT = HERE
OUT = HERE / "out" / "core025" / "assembly"
SRC_LAYERS = OUT / "source" / "layers"
CLEAN_LAYERS = OUT / "clean" / "layers"
CONFIG_DIR = HERE / "config"
CONTRACT_PATH = CONFIG_DIR / "core025-layer-contract.json"
LOCK = HERE / "sources.lock.json"
PSD_PATH = HERE / "out" / "source" / "tutorial-aka.psd"
CORE024_JSON = HERE / "out" / "core024" / "native-v2" / "native-export.json"
CORE024_LAYERS = HERE / "out" / "core024" / "native-v2" / "layers"

PSD_NAME = "tutorial-aka.psd"
FIXED_PSD_SHA = "979fa62702b25f8af25414637d9ba6c36cbc9eb03bfa0c454470c73bdf51e55e"
EXPECTED_LEAVES = 62
CANVAS = (1630, 1630)

# --- fixed semantic families (CORE-025 M1 contract) ---
FAMILY_RANGES = [
    (tuple(range(1, 3)), "ear"),
    (tuple(range(3, 11)), "rear_hair"),
    (tuple(range(11, 13)), "neck"),
    (tuple(range(13, 21)), "face_base"),
    ((21,), "nose"),
    (tuple(range(22, 24)), "mouth"),
    (tuple(range(24, 34)) + (58,), "left_eye"),
    (tuple(range(34, 44)) + (59,), "right_eye"),
    (tuple(range(44, 48)), "side_hair"),
    (tuple(range(48, 58)), "front_hair"),
    (tuple(range(60, 62)), "eyebrow"),
    ((62,), "leaf"),
]
# clean-only shadow alpha clipping: shadow layer order -> base layer order
SHADOW_TO_BASE = {6: 5, 12: 11, 14: 13, 15: 13, 16: 13, 17: 13,
                  18: 13, 19: 13, 20: 13}

# --- M1 numeric gate (MAE in 0..255 units) ---
GATE_MAE_RGB = 0.5
GATE_MAE_ALPHA = 0.5


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def safe(name: str) -> str:
    return "".join(c if (c.isalnum() or c in "-_") else "_" for c in name)


def semantic_family(order: int) -> str:
    for orders, fam in FAMILY_RANGES:
        if order in orders:
            return fam
    raise KeyError(f"no semantic family for layer order {order}")


def walk(group, prefix=()):
    for layer in group:
        path = prefix + (layer.name,)
        if layer.is_group():
            yield from walk(layer, path)
        else:
            yield path, layer


def checker(size, cell=32):
    w, h = size
    arr = np.zeros((h, w, 3), np.uint8)
    ys, xs = np.mgrid[0:h, 0:w]
    m = ((xs // cell + ys // cell) % 2).astype(bool)
    arr[m] = 190
    arr[~m] = 128
    return Image.fromarray(arr, "RGB")


# --------------------------------------------------------------------------
# blending core (unit-tested in tests/test_core025_blend.py)
# --------------------------------------------------------------------------
def bake_effective_source_rgb(src_rgb, backdrop_rgb, backdrop_alpha, mode):
    """Effective straight RGB of the source layer, 0..1.

    src_rgb/backdrop_rgb: (..., 3) float, straight (non-premultiplied) RGB.
    backdrop_alpha: (...,) float 0..1.
    """
    src_rgb = np.asarray(src_rgb, np.float32)
    backdrop_rgb = np.asarray(backdrop_rgb, np.float32)
    ab = np.asarray(backdrop_alpha, np.float32)[..., None]
    if str(mode).upper().endswith("MULTIPLY"):
        return src_rgb * (1.0 - ab + ab * backdrop_rgb)
    return src_rgb


def composite_over_premult(dst_rgb, dst_alpha, src_rgb, src_alpha, mode="NORMAL"):
    """Source-over composite, premultiplied result.  All inputs 0..1, straight RGB.

    Returns (premult_out, alpha_out) with shapes (...,3) and (...,).
    """
    dst_rgb = np.asarray(dst_rgb, np.float32)
    dst_alpha = np.asarray(dst_alpha, np.float32)
    src_rgb = np.asarray(src_rgb, np.float32)
    src_alpha = np.asarray(src_alpha, np.float32)

    ab = dst_alpha[..., None]
    cb = dst_rgb
    eff = bake_effective_source_rgb(src_rgb, cb, dst_alpha, mode)
    ao = src_alpha + dst_alpha * (1.0 - src_alpha)
    premult = src_alpha[..., None] * eff + (1.0 - src_alpha[..., None]) * ab * cb
    return premult.astype(np.float32), ao.astype(np.float32)


def composite_over(dst_rgb, dst_alpha, src_rgb, src_alpha, mode="NORMAL"):
    """Source-over composite of src over dst.  All inputs 0..1, straight RGB.

    Returns (out_rgb_straight, out_alpha) with shapes (...,3) and (...,).
    """
    premult, ao = composite_over_premult(dst_rgb, dst_alpha, src_rgb, src_alpha, mode)
    out_rgb = np.where(ao[..., None] > 0.0, premult / np.maximum(ao[..., None], 1e-8), 0.0)
    return out_rgb.astype(np.float32), ao.astype(np.float32)


def over_background(rgba_u8, bg_u8):
    """Composite straight RGBA (uint8) over a flat RGB background (uint8)."""
    a = rgba_u8[..., 3:4].astype(np.float32) / 255.0
    rgb = rgba_u8[..., :3].astype(np.float32)
    bg = np.asarray(bg_u8, np.float32).reshape(1, 1, 3)
    return np.clip(rgb * a + bg * (1.0 - a), 0, 255).round().astype(np.uint8)


def over_background_image(rgba_u8, bg_img):
    a = rgba_u8[..., 3:4].astype(np.float32) / 255.0
    rgb = rgba_u8[..., :3].astype(np.float32)
    bg = np.asarray(bg_img, np.float32)
    return np.clip(rgb * a + bg * (1.0 - a), 0, 255).round().astype(np.uint8)


# --------------------------------------------------------------------------
# step 1: verify inputs
# --------------------------------------------------------------------------
def verify_inputs():
    errs = []
    lock = json.loads(LOCK.read_text())
    entry = next(s for s in lock["sources"] if s["file"] == PSD_NAME)
    if entry["sha256"] != FIXED_PSD_SHA:
        errs.append(f"lock sha != fixed sha: {entry['sha256']}")
    actual = sha256(PSD_PATH)
    if actual != FIXED_PSD_SHA:
        errs.append(f"PSD sha mismatch: {actual} != {FIXED_PSD_SHA}")

    core = json.loads(CORE024_JSON.read_text())
    if core["psd"]["sha256"] != FIXED_PSD_SHA:
        errs.append("CORE-024 export references a different PSD sha")
    if list(core["canvas"]) != list(CANVAS):
        errs.append(f"CORE-024 canvas {core['canvas']} != {list(CANVAS)}")

    psd = PSDImage.open(PSD_PATH)
    if (int(psd.width), int(psd.height)) != CANVAS:
        errs.append(f"PSD canvas {(psd.width, psd.height)} != {list(CANVAS)}")

    leaves = list(walk(psd))
    if len(leaves) != EXPECTED_LEAVES:
        errs.append(f"leaf count {len(leaves)} != {EXPECTED_LEAVES}")

    core_leaves = core["leaves"]
    if len(core_leaves) != len(leaves):
        errs.append("CORE-024 leaf count differs from SDK enumeration")

    records = []
    for i, (path, layer) in enumerate(leaves):
        order = i + 1
        bounds = [int(layer.left), int(layer.top), int(layer.right), int(layer.bottom)]
        blend = str(layer.blend_mode)
        rec = {
            "order": order,
            "name": layer.name,
            "path": "/".join(path),
            "bounds": bounds,
            "width": int(layer.width),
            "height": int(layer.height),
            "blend_mode": blend,
            "opacity": float(layer.opacity),
            "has_mask": layer.mask is not None,
            "clipping": bool(getattr(layer, "clipping", False)),
            "visible": bool(layer.visible),
            "semantic_family": semantic_family(order),
        }
        # supported-source guard: never silently ignore an unsupported property
        if blend not in ("BlendMode.NORMAL", "BlendMode.MULTIPLY"):
            errs.append(f"layer {order} {layer.name}: unsupported blend mode {blend}")
        if float(layer.opacity) != 255.0:
            errs.append(f"layer {order} {layer.name}: opacity {layer.opacity} != 255")
        if rec["has_mask"]:
            errs.append(f"layer {order} {layer.name}: has mask")
        if rec["clipping"]:
            errs.append(f"layer {order} {layer.name}: has clipping")
        if not rec["visible"]:
            errs.append(f"layer {order} {layer.name}: not visible")
        if rec["width"] != bounds[2] - bounds[0] or rec["height"] != bounds[3] - bounds[1]:
            errs.append(f"layer {order} {layer.name}: size/bounds mismatch")

        raw = layer.topil()
        if raw is None:
            errs.append(f"layer {order} {layer.name}: topil() returned None")
            continue
        rgba = raw.convert("RGBA")
        arr = np.asarray(rgba)
        rec["rgba"] = arr

        if order <= len(core_leaves):
            c = core_leaves[order - 1]
            if c["name"] != rec["name"]:
                errs.append(f"layer {order}: name {rec['name']!r} != CORE-024 {c['name']!r}")
            if list(c["bounds"]) != bounds:
                errs.append(f"layer {order}: bounds {bounds} != CORE-024 {c['bounds']}")
            if c["blend_mode"] != blend:
                errs.append(f"layer {order}: blend {blend} != CORE-024 {c['blend_mode']}")
            png = CORE024_LAYERS / f"leaf-{order:02d}-{safe(rec['name'])}.png"
            if not png.exists():
                errs.append(f"layer {order}: CORE-024 PNG missing {png.name}")
            else:
                ref = np.asarray(Image.open(png).convert("RGBA"))
                if not np.array_equal(ref, arr):
                    errs.append(f"layer {order}: RGBA differs from CORE-024 PNG {png.name}")
                # provenance of the raw (unbaked) source texture actually compared above
                rec["raw_source_texture"] = {
                    "file": str(png.relative_to(ROOT)),
                    "sha256": sha256(png),
                    "pixel_compared_against_sdk_rgba": True,
                }
        records.append(rec)

    return psd, records, errs, actual


# --------------------------------------------------------------------------
# step 2: contract
# --------------------------------------------------------------------------
def write_contract(records, psd_sha):
    contract = {
        "schema": "koma-core025-layer-contract/1",
        "source": {
            "file": str(PSD_PATH.relative_to(ROOT)),
            "sha256": psd_sha,
            "sha256_fixed": FIXED_PSD_SHA,
            "license": "CC-BY-4.0",
        },
        "canvas": [CANVAS[0], CANVAS[1]],
        "pixel_convention": "source coordinates are pixel EDGE based; a pixel (i,j) covers [j, j+1) x [i, i+1) and its centre is at (j+0.5, i+0.5)",
        "default_order": "bottom-to-top (order 1 = bottom-most, order 62 = top-most)",
        "version_semantics": {
            "source": "DERIVED_REFERENCE: not a byte copy of the PSD. Every layer keeps its original alpha; the 51 NORMAL layers keep their original RGB bytes unchanged, the 11 MULTIPLY layers have their RGB changed (baked to NORMAL effective_source_rgb against the default lower-layer backdrop) and their alpha preserved",
            "clean": "same as source (also DERIVED_REFERENCE) except the 9 shadow layers listed in clean_shadow_alpha_clip have their alpha multiplied by the alpha of their base layer, aligned on the full canvas",
            "original_source": "the original PSD and the original CORE-024 layer PNGs remain the authoritative source of record; this contract describes derived textures only",
        },
        "authority": {
            "psd": "AUTHORITATIVE_SOURCE (original artwork)",
            "core024_layer_pngs": "AUTHORITATIVE_SOURCE (original per-layer PNGs, recorded per layer in raw_source_texture)",
            "source_version": "DERIVED_REFERENCE (multiply -> normal bake at the default pose)",
            "clean_version": "DERIVED_REFERENCE (shadow alpha repair on top of the source bake)",
        },
        "numeric_domain": "sRGB value domain 0..1, straight (non-premultiplied) RGB, no linearisation, no lighting",
        "blend_formula": {
            "effective_source_rgb": "Cs (NORMAL) | Cs * (1 - Ab + Ab * Cb) (MULTIPLY)",
            "premult_out": "As * effective_source_rgb + (1 - As) * Ab * Cb",
            "alpha_out": "As + Ab * (1 - As)",
            "reference": "W3C compositing-1, alpha compositing section",
        },
        "baked_blend_mode": "NORMAL",
        "semantic_family_rules": {
            "1-2": "ear", "3-10": "rear_hair", "11-12": "neck", "13-20": "face_base",
            "21": "nose", "22-23": "mouth", "24-33,58": "left_eye", "34-43,59": "right_eye",
            "44-47": "side_hair", "48-57": "front_hair", "60-61": "eyebrow", "62": "leaf",
        },
        "clean_shadow_alpha_clip": [
            {"shadow_order": k, "shadow_name": next(r["name"] for r in records if r["order"] == k),
             "base_order": v, "base_name": next(r["name"] for r in records if r["order"] == v),
             "rule": "alpha_shadow *= alpha_base, full-canvas aligned"}
            for k, v in sorted(SHADOW_TO_BASE.items())
        ],
        "eyebrow_note": "layers 60/61 (Eyebrow L/R) stay MULTIPLY-baked; they are NOT treated as spill shadows and are not alpha-clipped",
        "layers": [
            {
                "order": r["order"], "name": r["name"], "semantic_family": r["semantic_family"],
                "bounds": r["bounds"], "size": [r["width"], r["height"]],
                "source_blend_mode": r["blend_mode"], "baked_blend_mode": "NORMAL",
                "alpha_modified_in_clean": r["order"] in SHADOW_TO_BASE,
                "raw_source_texture": r.get("raw_source_texture"),
                "rgb_unchanged_vs_raw_source": not r["blend_mode"].endswith("MULTIPLY"),
            }
            for r in records
        ],
    }
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONTRACT_PATH.write_text(json.dumps(contract, indent=2))
    return contract


# --------------------------------------------------------------------------
# step 3+4: bake textures, accumulate, render
# --------------------------------------------------------------------------
def place(canvas_arr, arr, bounds):
    """Paste a bounds-sized array onto a full-canvas array."""
    l, t, r, b = bounds
    h, w = canvas_arr.shape[:2]
    out = np.zeros_like(canvas_arr)
    src = arr
    # clip to canvas
    cl, ct = max(l, 0), max(t, 0)
    cr, cb = min(r, w), min(b, h)
    if cl >= cr or ct >= cb:
        return out, (0, 0, 0, 0)
    out[ct:cb, cl:cr] = src[ct - t:cb - t, cl - l:cr - l]
    return out, (cl, ct, cr, cb)


def alpha_canvas(rec, canvas=CANVAS):
    a = np.zeros((canvas[1], canvas[0]), np.float32)
    l, t, r, b = rec["bounds"]
    a[t:b, l:r] = rec["rgba"][..., 3].astype(np.float32) / 255.0
    return a


def build_version(records, version, clean_map):
    """Bake + accumulate one version.  Returns (acc_rgb_straight, acc_alpha, textures)."""
    H, W = CANVAS[1], CANVAS[0]
    acc_premult = np.zeros((H, W, 3), np.float32)
    acc_alpha = np.zeros((H, W), np.float32)
    textures = {}

    for rec in records:
        order = rec["order"]
        bounds = rec["bounds"]
        rgba = rec["rgba"].astype(np.uint8)
        src_rgb = rgba[..., :3].astype(np.float32) / 255.0
        src_a_u8 = rgba[..., 3].copy()
        if version == "clean" and order in clean_map:
            src_a_u8 = clean_map[order]
        src_alpha = src_a_u8.astype(np.float32) / 255.0

        l, t, r, b = bounds
        reg = (slice(t, b), slice(l, r))
        Ab = acc_alpha[reg]
        Cb = np.where(Ab[..., None] > 0.0,
                      acc_premult[reg] / np.maximum(Ab[..., None], 1e-8), 0.0)

        is_multiply = rec["blend_mode"].endswith("MULTIPLY")
        eff = bake_effective_source_rgb(src_rgb, Cb, Ab, rec["blend_mode"])
        rgb_u8 = np.clip(np.round(eff * 255.0), 0, 255).astype(np.uint8)
        if not is_multiply:
            # NORMAL layers keep their original RGB bytes untouched
            rgb_u8 = rgba[..., :3].copy()

        tex = np.dstack([rgb_u8, src_a_u8])
        tex_path = (SRC_LAYERS if version == "source" else CLEAN_LAYERS) / \
            f"leaf-{order:02d}-{safe(rec['name'])}.png"
        Image.fromarray(tex, "RGBA").save(tex_path)

        # re-read the exported texture: the CPU reference must use the shipped PNG
        tex_back = np.asarray(Image.open(tex_path).convert("RGBA"))
        cs_q = tex_back[..., :3].astype(np.float32) / 255.0
        as_q = tex_back[..., 3].astype(np.float32) / 255.0

        premult_out, ao = composite_over_premult(Cb, Ab, cs_q, as_q, "NORMAL")
        acc_premult[reg] = premult_out
        acc_alpha[reg] = ao

        textures[order] = {
            "file": str(tex_path.relative_to(ROOT)),
            "sha256": sha256(tex_path),
            "size": [int(r - l), int(b - t)],
            "source_blend_mode": rec["blend_mode"],
            "baked_blend_mode": "NORMAL",
            "alpha_modified": bool(version == "clean" and order in clean_map),
        }

    straight = np.where(acc_alpha[..., None] > 0.0,
                        acc_premult / np.maximum(acc_alpha[..., None], 1e-8), 0.0)
    out_rgba = np.dstack([
        np.clip(np.round(straight * 255.0), 0, 255).astype(np.uint8),
        np.clip(np.round(acc_alpha * 255.0), 0, 255).astype(np.uint8)])
    return out_rgba, textures


def build_clean_alpha_maps(records):
    """clean version: shadow alpha *= base alpha (full-canvas aligned)."""
    maps = {}
    details = []
    alpha_by_order = {r["order"]: alpha_canvas(r) for r in records}
    for shadow_order, base_order in sorted(SHADOW_TO_BASE.items()):
        sh = alpha_by_order[shadow_order]
        base = alpha_by_order[base_order]
        new = np.clip(np.round(sh * base * 255.0), 0, 255).astype(np.uint8)
        rec = next(r for r in records if r["order"] == shadow_order)
        l, t, r, b = rec["bounds"]
        orig = rec["rgba"][..., 3]
        region_new = new[t:b, l:r]
        changed = int((region_new != orig).sum())
        alpha_sum_before = float(orig.astype(np.float64).sum() / 255.0)
        alpha_sum_after = float(region_new.astype(np.float64).sum() / 255.0)
        maps[shadow_order] = region_new
        details.append({
            "shadow_order": shadow_order,
            "shadow_name": rec["name"],
            "base_order": base_order,
            "base_name": next(x["name"] for x in records if x["order"] == base_order),
            "changed_px": changed,
            "layer_px": int(orig.size),
            "alpha_sum_before": round(alpha_sum_before, 4),
            "alpha_sum_after": round(alpha_sum_after, 4),
            "alpha_sum_delta": round(alpha_sum_after - alpha_sum_before, 4),
        })
    return maps, details


# --------------------------------------------------------------------------
# measurement
# --------------------------------------------------------------------------
def measure(ours_rgba, ref_rgba, bg):
    ours_bg = over_background(ours_rgba, bg)
    ref_bg = over_background(ref_rgba, bg)
    fg = (ours_rgba[..., 3] > 0) | (ref_rgba[..., 3] > 0)
    diff = np.abs(ours_bg.astype(np.int16) - ref_bg.astype(np.int16))
    if fg.any():
        d = diff[fg]
        mae = float(d.mean())
        max_px = diff.max(axis=2)
        max_abs = int(max_px[fg].max())
        over16 = float((max_px[fg] > 16).mean())
        alpha_mae = float(np.abs(ours_rgba[..., 3].astype(np.int16)[fg]
                                 - ref_rgba[..., 3].astype(np.int16)[fg]).mean())
    else:
        mae = 0.0
        max_abs = 0
        over16 = 0.0
        alpha_mae = 0.0
    return {
        "background": "white" if bg == (255, 255, 255) else "black",
        "foreground_px": int(fg.sum()),
        "mae_rgb_0_255": round(mae, 6),
        "mae_rgb_0_1": round(mae / 255.0, 8),
        "max_single_channel_error_0_255": max_abs,
        "pixels_over_16_fraction": round(over16, 8),
        "alpha_mae_0_255": round(alpha_mae, 6),
        "alpha_mae_0_1": round(alpha_mae / 255.0, 8),
    }


def panel(img, size, label):
    im = img.convert("RGB") if img.mode != "RGB" else img
    im = im.copy()
    im.thumbnail(size, Image.LANCZOS)
    canvas = Image.new("RGB", (size[0], size[1] + 22), (18, 18, 18))
    canvas.paste(im, ((size[0] - im.width) // 2, (size[1] - im.height) // 2))
    ImageDraw.Draw(canvas).text((6, size[1] + 6), label, fill=(235, 235, 235))
    return canvas


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    SRC_LAYERS.mkdir(parents=True, exist_ok=True)
    CLEAN_LAYERS.mkdir(parents=True, exist_ok=True)

    psd, records, errs, psd_sha = verify_inputs()
    if errs:
        for e in errs:
            print("FAIL:", e, file=sys.stderr)
        print(f"input verification failed with {len(errs)} error(s)", file=sys.stderr)
        return 2
    print(f"[1] inputs verified: {len(records)} leaves, canvas {CANVAS[0]}x{CANVAS[1]}, sha {psd_sha[:16]}...")

    contract = write_contract(records, psd_sha)
    print(f"[2] contract written: {CONTRACT_PATH.relative_to(ROOT)}")

    clean_maps, clean_details = build_clean_alpha_maps(records)

    # --- SDK reference (transparent truth) ---
    ref_img = psd.composite(force=True, alpha=0.0, color=(1.0, 1.0, 1.0)).convert("RGBA")
    ref_rgba = np.asarray(ref_img)

    results = {}
    versions = {}
    for version in ("source", "clean"):
        rgba, textures = build_version(records, version, clean_maps)
        versions[version] = (rgba, textures)
        prefix = "source" if version == "source" else "clean"
        cpu_path = OUT / version / f"{prefix}-cpu.png"
        Image.fromarray(rgba, "RGBA").save(cpu_path)
        white = over_background(rgba, (255, 255, 255))
        black = over_background(rgba, (0, 0, 0))
        chk = np.asarray(checker(CANVAS, 32))
        chk_img = over_background_image(rgba, chk)
        Image.fromarray(white, "RGB").save(OUT / version / f"{prefix}-cpu-white.png")
        Image.fromarray(black, "RGB").save(OUT / version / f"{prefix}-cpu-black.png")
        Image.fromarray(chk_img, "RGB").save(OUT / version / f"{prefix}-cpu-checker.png")

        m_white = measure(rgba, ref_rgba, (255, 255, 255))
        m_black = measure(rgba, ref_rgba, (0, 0, 0))
        results[version] = {
            "cpu_composite": {
                "file": str(cpu_path.relative_to(ROOT)),
                "sha256": sha256(cpu_path),
                "size": list(CANVAS),
            },
            "against_sdk_reference": {"white": m_white, "black": m_black},
        }
        print(f"[3] {version}: white MAE {m_white['mae_rgb_0_255']:.4f}  "
              f"black MAE {m_black['mae_rgb_0_255']:.4f}  "
              f"alpha MAE {m_white['alpha_mae_0_255']:.4f}")

    # --- comparison sheet ---
    ours = versions["source"][0]
    ref_white = over_background(ref_rgba, (255, 255, 255))
    our_white = over_background(ours, (255, 255, 255))
    amp = np.clip(np.abs(our_white.astype(np.int16) - ref_white.astype(np.int16)) * 8, 0, 255).astype(np.uint8)
    size = (520, 520)
    panels = [
        panel(Image.fromarray(ref_white, "RGB"), size, "SDK reference (psd.composite force) over white"),
        panel(Image.fromarray(our_white, "RGB"), size, "source-cpu (baked NORMAL textures) over white"),
        panel(Image.fromarray(amp, "RGB"), size, "abs diff x8 (ours - SDK)"),
        panel(Image.fromarray(over_background(ref_rgba, (0, 0, 0)), "RGB"), size, "SDK reference over black"),
        panel(Image.fromarray(over_background(ours, (0, 0, 0)), "RGB"), size, "source-cpu over black"),
        panel(Image.fromarray(over_background_image(ours, np.asarray(checker(CANVAS, 32))), "RGB"), size, "source-cpu transparent over checker"),
    ]
    sheet = Image.new("RGB", (size[0] * 3, (size[1] + 22) * 2), (18, 18, 18))
    for i, p in enumerate(panels):
        sheet.paste(p, ((i % 3) * size[0], (i // 3) * (size[1] + 22)))
    sheet_path = OUT / "comparison-sheet.png"
    sheet.save(sheet_path)

    # --- 9 shadow layers before/after contact sheet ---
    # 3 columns; each group is a full 2*cell wide before/after pair with its own
    # label band below, so groups never overlap and never get clipped.
    cols, cell, pad, lab = 3, 150, 10, 46
    group_w = 2 * cell          # source tile + clean tile side by side
    rows = (len(SHADOW_TO_BASE) + cols - 1) // cols
    sheet_w = pad + cols * (group_w + pad)
    sheet_h = pad + rows * (cell + lab + pad)
    cs = Image.new("RGB", (sheet_w, sheet_h), (24, 24, 24))
    draw = ImageDraw.Draw(cs)
    font = ImageFont.load_default()
    idx = 0
    for shadow_order in sorted(SHADOW_TO_BASE):
        rec = next(r for r in records if r["order"] == shadow_order)
        arr = rec["rgba"]
        c, r = idx % cols, idx // cols
        x = pad + c * (group_w + pad)
        y = pad + r * (cell + lab + pad)
        pair = Image.new("RGB", (group_w, cell), (24, 24, 24))
        for j, rgba in enumerate([arr, np.dstack([arr[..., :3], clean_maps[shadow_order]])]):
            tile = checker((cell, cell), 12)
            th = Image.fromarray(rgba, "RGBA")
            th.thumbnail((cell, cell), Image.LANCZOS)
            tile.paste(th, ((cell - th.width) // 2, (cell - th.height) // 2), th)
            pair.paste(tile, (j * cell, 0))
        # paste the image first, then draw the labels on top of the finished sheet
        cs.paste(pair, (x, y))
        draw.rectangle([x, y + cell, x + group_w - 1, y + cell + lab - 1], fill=(32, 32, 32))
        draw.text((x + 4, y + cell + 4), "source", fill=(200, 200, 200), font=font)
        draw.text((x + cell + 4, y + cell + 4), "clean", fill=(200, 200, 200), font=font)
        draw.text((x + 4, y + cell + 22), f"{shadow_order} {rec['name'][:24]}",
                  fill=(230, 230, 230), font=font)
        idx += 1
    shadow_path = OUT / "shadow-cleanup-sheet.png"
    cs.save(shadow_path)

    # --- gates ---
    src_w = results["source"]["against_sdk_reference"]["white"]
    src_b = results["source"]["against_sdk_reference"]["black"]
    failures = []
    if src_w["mae_rgb_0_255"] > GATE_MAE_RGB:
        failures.append(f"source white RGB MAE {src_w['mae_rgb_0_255']} > {GATE_MAE_RGB}")
    if src_b["mae_rgb_0_255"] > GATE_MAE_RGB:
        failures.append(f"source black RGB MAE {src_b['mae_rgb_0_255']} > {GATE_MAE_RGB}")
    if src_w["alpha_mae_0_255"] > GATE_MAE_ALPHA:
        failures.append(f"source alpha MAE {src_w['alpha_mae_0_255']} > {GATE_MAE_ALPHA}")
    gate = "PASS" if not failures else "FAIL"

    # --- assembly.json ---
    layer_meta = []
    for rec in records:
        o = rec["order"]
        layer_meta.append({
            "order": o,
            "name": rec["name"],
            "semantic_family": rec["semantic_family"],
            "bounds": rec["bounds"],
            "size": [rec["width"], rec["height"]],
            "source_blend_mode": rec["blend_mode"],
            "baked_blend_mode": "NORMAL",
            "source_texture": versions["source"][1][o],
            "clean_texture": versions["clean"][1][o],
            "raw_source_texture": rec.get("raw_source_texture"),
            "rgb_unchanged_vs_raw_source": not rec["blend_mode"].endswith("MULTIPLY"),
            "raw_source_is_original": True,
            "alpha_modified_in_clean": o in SHADOW_TO_BASE,
            "default_lower_layer_dependency": (
                "baked against the default (source) lower-layer backdrop; a GPU that "
                "composites this layer over a different backdrop will not reproduce the "
                "original MULTIPLY result exactly"
            ) if rec["blend_mode"].endswith("MULTIPLY") else None,
        })
    assembly = {
        "schema": "koma-core025-assembly/1",
        "source": {"file": str(PSD_PATH.relative_to(ROOT)), "sha256": psd_sha,
                   "license": "CC-BY-4.0"},
        "canvas": [CANVAS[0], CANVAS[1]],
        "pixel_convention": "pixel EDGE coordinates; pixel centre at i+0.5 / j+0.5",
        "numeric_domain": "sRGB value domain 0..1, straight RGB, no linearisation",
        "composite_formula": {
            "effective_source_rgb": "Cs | Cs * (1 - Ab + Ab * Cb)",
            "premult_out": "As * effective_source_rgb + (1 - As) * Ab * Cb",
            "alpha_out": "As + Ab * (1 - As)",
            "reference": "W3C compositing-1",
        },
        "authority": {
            "psd": "AUTHORITATIVE_SOURCE: the original PSD artwork",
            "core024_layer_pngs": "AUTHORITATIVE_SOURCE: the original per-layer PNGs, recorded per layer in raw_source_texture with file + sha256",
            "source": "DERIVED_REFERENCE: not a byte copy of the PSD. All 62 layers keep their original alpha; the 51 NORMAL layers keep their original RGB bytes unchanged; the 11 MULTIPLY layers have their RGB changed (baked to NORMAL effective_source_rgb against the default lower-layer backdrop) with alpha preserved",
            "clean": "DERIVED_REFERENCE: shadow-repaired variant on top of the source bake, alpha clipped to the base layer for the 9 shadow layers",
        },
        "rgb_provenance": {
            "normal_layers_with_original_rgb": sum(
                1 for r in records if not r["blend_mode"].endswith("MULTIPLY")),
            "multiply_layers_with_baked_rgb": sum(
                1 for r in records if r["blend_mode"].endswith("MULTIPLY")),
            "note": "the original PSD and the original CORE-024 layer PNGs remain the authoritative source of record; the source/clean textures above are derived from them",
        },
        "multiply_baking": {
            "count": sum(1 for r in records if r["blend_mode"].endswith("MULTIPLY")),
            "layers": [r["order"] for r in records if r["blend_mode"].endswith("MULTIPLY")],
            "note": "MULTIPLY layers are converted to NORMAL textures whose RGB is the "
                    "quantised effective_source_rgb against the default lower-layer "
                    "backdrop; alpha is preserved. The limitation is that the baked result "
                    "is only valid over that default backdrop.",
        },
        "clean_shadow_alpha_clip": clean_details,
        "layers": layer_meta,
        "comparisons": results,
        "outputs": {
            "comparison_sheet": {"file": str(sheet_path.relative_to(ROOT)), "sha256": sha256(sheet_path)},
            "shadow_cleanup_sheet": {"file": str(shadow_path.relative_to(ROOT)), "sha256": sha256(shadow_path)},
        },
    }
    (OUT / "assembly.json").write_text(json.dumps(assembly, indent=2))

    qa = {
        "schema": "koma-core025-qa/1",
        "inputs": {
            "psd": {"file": str(PSD_PATH.relative_to(ROOT)), "sha256": psd_sha,
                    "sha256_verified": True},
            "core024_export": {"file": str(CORE024_JSON.relative_to(ROOT)),
                                "sha256": sha256(CORE024_JSON)},
            "layer_count": len(records),
        },
        "outputs": {
            "source_cpu": results["source"]["cpu_composite"],
            "clean_cpu": results["clean"]["cpu_composite"],
            "assembly_json": {"file": "out/core025/assembly/assembly.json",
                              "sha256": sha256(OUT / "assembly.json")},
        },
        "measurements": results,
        "gate_thresholds": {
            "source_rgb_mae_0_255_max": GATE_MAE_RGB,
            "source_alpha_mae_0_255_max": GATE_MAE_ALPHA,
            "note": "thresholds are 0.5/255 expressed in 0..255 units; not relaxed",
        },
        "exit_conditions": {
            "source_composition_gate": gate,
            "failures": failures,
        },
        "clean_visual_gate": "NOT_REVIEWED",
        "clean_visual_gate_note": "the clean variant differs from the PSD on purpose; the "
                                  "supervisor reviews shadow-cleanup-sheet.png and decides",
    }
    (OUT / "qa.json").write_text(json.dumps(qa, indent=2))

    print(f"[4] source_composition_gate = {gate}")
    print(f"[5] out: {OUT}")
    if failures:
        for f in failures:
            print("FAIL:", f, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""CORE-023 Task A - deterministic offline candidate canonicalization (v2).

Pure deterministic image processing. Pillow performs ALL image IO, alpha
compositing and resampling (maintained ``Image.transform`` with
``Image.Resampling.BICUBIC``); this module never implements its own resampling
kernel. This tool does NOT redraw, re-imagine, inpaint, warp locally or crop
the subject. It fits the ENTIRE source canvas into one canonical 1024x1024
opaque white canvas with a uniform scale and letterboxing, then records full
evidence.

Coordinate contract (explicit): edge coordinates, pixel index i has its center
at i+0.5. The single affine source->canonical matrix and its exact inverse are
reported for every derivative; the inverse is handed to Pillow's AFFINE
transform verbatim (no extra half-pixel shift).

Authority: the identity derivative hash is taken from the COMMITTED evidence
``evidence/local-2026-10-30/source_freeze.json`` (``identity_sha256``). The
mutable runtime manifest ``out/identity/reference_manifest.json`` is only
cross-checked for consistency and can never override the committed hash.

Fail-closed: a missing input, a SHA256 mismatch, a blank candidate, an invalid
transform/config or an insufficient resulting margin aborts the run. Candidates
are never silently skipped.

Framing PASS is a framing statement only. Anatomy / identity / angle / style /
human-approval gates stay NOT_TESTED or MANUAL_REVIEW_REQUIRED, the benchmark
ranking stays NONE_ACCEPTED and the full A/B/C/D benchmark stays NOT_TESTED.
No APPROVED / GOLDEN state is ever written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
ALGORITHM_ID = "koma-deterministic-affine-canonicalization"
ALGORITHM_VERSION = "2.0.0"
REPORT_SCHEMA = "koma-canonicalization-report/2"

SUPPORTED_CONFIG_SCHEMA = "koma-canonicalization-config/2"
SUPPORTED_RESAMPLING = ("PILLOW_BICUBIC",)
SUPPORTED_FIT = ("uniform_scale_entire_source_canvas_letterbox "
                 "(inner box = canvas inset by min_margin_px + fit_inset_px)",)
SUPPORTED_TRANSFORM = ("single affine: uniform scale plus translation; "
                       "no rotation, no shear, no perspective")
SUPPORTED_COLOR_HANDLING = ("8-bit sRGB RGB; no ICC conversion; no gamma change; "
                            "no sharpening")
SUPPORTED_COORDINATE_DOMAIN = "edge_coordinates; pixel index i has its center at i+0.5"
SUPPORTED_CANVAS_ALPHA = "fully opaque; any source alpha is composited over opaque white"
SUPPORTED_CANVAS_MODE = ("RGB",)
SUPPORTED_DERIVATIVE_NAMING = "<source-stem>-canonical-v<config_version_major>.png"
CONFIG_KEYS = ("schema", "config_version", "stage", "intent", "canvas", "min_margin_px",
               "ink_threshold_rgb_min", "fit", "resampling", "color_handling",
               "coordinate_domain", "transform", "derivative_naming", "fit_inset_px")
CANVAS_KEYS = ("width", "height", "mode", "background_rgb", "alpha")


class CanonicalizationError(RuntimeError):
    """Raised for every fail-closed condition."""


# --------------------------------------------------------------------------- io
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _require_int(value, label: str, lo: int, hi: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CanonicalizationError(f"CONFIG_INVALID: {label} must be an integer")
    if not (lo <= value <= hi):
        raise CanonicalizationError(
            f"CONFIG_INVALID: {label} must be within [{lo}, {hi}], got {value}")
    return value


def load_config(path: Path) -> dict:
    """Load and fully validate the canonicalization config (fail closed)."""
    if not path.exists():
        raise CanonicalizationError(f"CONFIG_MISSING: {path}")
    try:
        cfg = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise CanonicalizationError(f"CONFIG_INVALID_JSON: {path}: {exc}") from exc
    if not isinstance(cfg, dict):
        raise CanonicalizationError(f"CONFIG_INVALID: top level must be an object in {path}")

    for key in CONFIG_KEYS:
        if key not in cfg:
            raise CanonicalizationError(f"CONFIG_INVALID: missing key '{key}' in {path}")
    unknown = sorted(set(cfg) - set(CONFIG_KEYS))
    if unknown:
        raise CanonicalizationError(
            f"CONFIG_INVALID: unsupported key(s) {unknown} in {path}")
    if cfg["schema"] != SUPPORTED_CONFIG_SCHEMA:
        raise CanonicalizationError(
            f"CONFIG_INVALID: unsupported schema '{cfg['schema']}' "
            f"(supported: {SUPPORTED_CONFIG_SCHEMA})")
    if not isinstance(cfg["config_version"], str) or \
            len(cfg["config_version"].split(".")) != 3:
        raise CanonicalizationError(
            f"CONFIG_INVALID: config_version must be a x.y.z string in {path}")

    canvas = cfg["canvas"]
    if not isinstance(canvas, dict):
        raise CanonicalizationError(f"CONFIG_INVALID: canvas must be an object in {path}")
    for key in CANVAS_KEYS:
        if key not in canvas:
            raise CanonicalizationError(f"CONFIG_INVALID: canvas.{key} missing in {path}")
    unknown = sorted(set(canvas) - set(CANVAS_KEYS))
    if unknown:
        raise CanonicalizationError(
            f"CONFIG_INVALID: unsupported canvas key(s) {unknown} in {path}")
    width = _require_int(canvas["width"], "canvas.width", 64, 8192)
    height = _require_int(canvas["height"], "canvas.height", 64, 8192)
    if canvas["mode"] not in SUPPORTED_CANVAS_MODE:
        raise CanonicalizationError(
            f"CONFIG_INVALID: unsupported canvas.mode '{canvas['mode']}' "
            f"(supported: {', '.join(SUPPORTED_CANVAS_MODE)})")
    if canvas["alpha"] != SUPPORTED_CANVAS_ALPHA:
        raise CanonicalizationError(
            f"CONFIG_INVALID: unsupported canvas.alpha setting in {path}")
    bg = canvas["background_rgb"]
    if not isinstance(bg, list) or len(bg) != 3:
        raise CanonicalizationError(f"CONFIG_INVALID: background_rgb must be RGB in {path}")
    for value in bg:
        _require_int(value, "canvas.background_rgb[*]", 0, 255)

    _require_int(cfg["min_margin_px"], "min_margin_px", 0, min(width, height) // 2)
    _require_int(cfg["ink_threshold_rgb_min"], "ink_threshold_rgb_min", 1, 255)
    _require_int(cfg.get("fit_inset_px", 0), "fit_inset_px", 0, min(width, height) // 2)
    if cfg["min_margin_px"] + cfg.get("fit_inset_px", 0) >= min(width, height) // 2:
        raise CanonicalizationError(
            f"CONFIG_INVALID: margin + inset does not fit inside {width}x{height} canvas")
    if cfg["resampling"] not in SUPPORTED_RESAMPLING:
        raise CanonicalizationError(
            f"CONFIG_INVALID: unsupported resampling '{cfg['resampling']}' "
            f"(supported: {', '.join(SUPPORTED_RESAMPLING)})")
    if cfg["fit"] not in SUPPORTED_FIT:
        raise CanonicalizationError(f"CONFIG_INVALID: unsupported fit setting in {path}")
    # Exact-equality contracts for these scalar settings. Substring membership
    # would wrongly accept "" or any partial prefix of the supported text.
    if cfg["transform"] != SUPPORTED_TRANSFORM:
        raise CanonicalizationError(f"CONFIG_INVALID: unsupported transform in {path}")
    if cfg["color_handling"] != SUPPORTED_COLOR_HANDLING:
        raise CanonicalizationError(f"CONFIG_INVALID: unsupported color setting in {path}")
    if cfg["coordinate_domain"] != SUPPORTED_COORDINATE_DOMAIN:
        raise CanonicalizationError(
            f"CONFIG_INVALID: unsupported coordinate_domain in {path}")
    if cfg["derivative_naming"] != SUPPORTED_DERIVATIVE_NAMING:
        raise CanonicalizationError(
            f"CONFIG_INVALID: unsupported derivative_naming in {path}")
    return cfg


# ------------------------------------------------------------------- geometry
def fit_transform(src_w: int, src_h: int, cfg: dict) -> dict:
    """Uniform-scale + letterbox fit of the ENTIRE source canvas.

    Matrices use the edge-coordinate domain required by the work order: pixel
    index i has its center at i+0.5. Tuple layout is (a, b, c, d, e, f) with

        x' = a*x + b*y + c
        y' = d*x + e*y + f
    """
    cw = int(cfg["canvas"]["width"])
    ch = int(cfg["canvas"]["height"])
    margin = int(cfg["min_margin_px"])
    inset = int(cfg.get("fit_inset_px", 0))
    if src_w <= 0 or src_h <= 0:
        raise CanonicalizationError(f"INVALID_SOURCE_SIZE: {src_w}x{src_h}")
    if margin + inset < 0:
        raise CanonicalizationError("INVALID_TRANSFORM: negative margin/inset")
    avail_w = cw - 2 * (margin + inset)
    avail_h = ch - 2 * (margin + inset)
    if avail_w <= 0 or avail_h <= 0:
        raise CanonicalizationError(
            f"INVALID_TRANSFORM: margin {margin} does not fit inside {cw}x{ch} canvas")
    scale = min(avail_w / src_w, avail_h / src_h)
    if scale <= 0:
        raise CanonicalizationError("INVALID_TRANSFORM: non-positive scale")
    off_x = (cw - src_w * scale) / 2.0
    off_y = (ch - src_h * scale) / 2.0
    fwd = {"a": scale, "b": 0.0, "c": off_x, "d": 0.0, "e": scale, "f": off_y}
    inv = {"a": 1.0 / scale, "b": 0.0, "c": -off_x / scale,
           "d": 0.0, "e": 1.0 / scale, "f": -off_y / scale}
    return {
        "model": "affine_uniform_scale_translation",
        "coordinate_domain": "edge_coordinates; pixel index i has its center at i+0.5",
        "matrix_layout": "(a,b,c,d,e,f): x' = a*x + b*y + c ; y' = d*x + e*y + f",
        "source_size": [src_w, src_h],
        "canonical_size": [cw, ch],
        "scale": scale,
        "fit_inset_px": inset,
        "offset_px": [off_x, off_y],
        "source_to_canonical": fwd,
        "canonical_to_source": inv,
        "resampling": cfg["resampling"],
        "fit": cfg["fit"],
    }


def matrix_tuple(matrix: dict) -> tuple:
    """(a, b, c, d, e, f) tuple of an affine matrix dict."""
    return (float(matrix["a"]), float(matrix["b"]), float(matrix["c"]),
            float(matrix["d"]), float(matrix["e"]), float(matrix["f"]))


def transform_with_matrix(src: Image.Image, out_size, matrix, fill=(255, 255, 255)) -> Image.Image:
    """Resample `src` into `out_size` through ONE affine using Pillow.

    The matrix is the canonical->source inverse in edge coordinates and is
    handed to Pillow's AFFINE transform verbatim: no extra half-pixel shift is
    applied, so the output footprint of a source pixel follows the edge-domain
    math exactly. Resampling is Pillow's maintained BICUBIC filter.
    """
    out = src.transform(tuple(int(v) for v in out_size), Image.Transform.AFFINE,
                        matrix_tuple(matrix), resample=Image.Resampling.BICUBIC,
                        fillcolor=tuple(int(v) for v in fill))
    return out.convert("RGB")


def apply_forward(src: Image.Image, transform: dict, cfg: dict) -> Image.Image:
    """Resample the source into the canonical canvas with ONE affine."""
    cw, ch = transform["canonical_size"]
    bg = tuple(int(v) for v in cfg["canvas"]["background_rgb"])
    return transform_with_matrix(src, (cw, ch), transform["canonical_to_source"], bg)


# --------------------------------------------------------------------- framing
def ink_margins(img: Image.Image, threshold: int) -> dict:
    arr = np.asarray(img.convert("RGB"))
    mask = arr.min(axis=2) < int(threshold)
    ys, xs = np.where(mask)
    if not len(xs):
        return {"blank": True, "margins_ltrb_px": None, "ink_bbox_px": None}
    return {
        "blank": False,
        "margins_ltrb_px": [int(xs.min()), int(ys.min()),
                            int(img.width - xs.max() - 1), int(img.height - ys.max() - 1)],
        "ink_bbox_px": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
    }


def framing_gate(img: Image.Image, cfg: dict) -> dict:
    """Framing only. Never an artistic judgement."""
    cw = int(cfg["canvas"]["width"])
    ch = int(cfg["canvas"]["height"])
    margin = int(cfg["min_margin_px"])
    info = ink_margins(img, int(cfg["ink_threshold_rgb_min"]))
    issues = []
    if img.size != (cw, ch):
        issues.append(f"CAMERA_CROP_ERROR: output canvas differs from {cw}x{ch} request")
    if info["blank"]:
        issues.append("BLANK_IMAGE: no diagnostic ink above threshold")
    elif min(info["margins_ltrb_px"]) < margin:
        issues.append(f"CAMERA_CROP_ERROR: ink threshold margin below {margin} px")
    return {"ink_threshold_rgb_min": int(cfg["ink_threshold_rgb_min"]),
            "min_margin_px": margin,
            "dimensions": [img.width, img.height],
            "margins_ltrb_px": info["margins_ltrb_px"],
            "issues": issues,
            "hard_gate": "FAIL" if issues else "PASS"}


# ------------------------------------------------------------------- pipeline
def load_rgb(path: Path) -> Image.Image:
    """Load ANY mode, composite its alpha over opaque white, return 8-bit RGB.

    Every source mode is routed through RGBA first (indexed-color PNGs carry
    their transparency in the palette/tRNS chunk, which only survives an RGBA
    conversion), then composited over opaque white.
    """
    with Image.open(path) as im:
        im.load()
        rgba = im.convert("RGBA")
        bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        return Image.alpha_composite(bg, rgba).convert("RGB")


def _same_file(a: Path, b: Path) -> bool:
    """True when both paths denote the same file (same path, symlink or hardlink)."""
    ra, rb = os.path.realpath(str(a)), os.path.realpath(str(b))
    if ra == rb:
        return True
    try:
        sa, sb = os.stat(str(a)), os.stat(str(b))
    except OSError:
        return False
    return (sa.st_dev, sa.st_ino) == (sb.st_dev, sb.st_ino)


def canonicalize_file(src_path: Path, out_path: Path, cfg: dict) -> dict:
    """Canonicalize one source. Rejects source/output aliases BEFORE writing."""
    src_path = Path(src_path)
    out_path = Path(out_path)
    if _same_file(src_path, out_path):
        raise CanonicalizationError(
            f"SOURCE_OUTPUT_ALIAS: refusing to write the canonical derivative over "
            f"its own source ({src_path})")
    src = load_rgb(src_path)
    transform = fit_transform(src.width, src.height, cfg)
    canonical = apply_forward(src, transform, cfg)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canonical.save(out_path, format="PNG", optimize=False)

    original = framing_gate(src, cfg)
    result = framing_gate(canonical, cfg)
    if result["hard_gate"] != "PASS":
        raise CanonicalizationError(
            f"MARGIN_OR_CANVAS_FAIL: canonical derivative {out_path.name} failed the "
            f"framing gate: {result['issues']}")
    return {"transform": transform, "original_framing": original,
            "derivative_framing": result}


def expected_hashes(input_dir: Path, evidence_dir: Path) -> dict:
    """Expected SHA256 values, read from COMMITTED evidence. Never invented.

    The identity hash authority is ``evidence/<set>/source_freeze.json``
    (``identity_sha256``). The mutable runtime manifest
    ``out/identity/reference_manifest.json`` is only consistency-checked: a
    forged runtime manifest can never bypass the committed hash.
    """
    freeze_path = evidence_dir / "source_freeze.json"
    cand_manifest = evidence_dir / "candidate-manifest.json"
    for p in (freeze_path, cand_manifest):
        if not p.exists():
            raise CanonicalizationError(f"EVIDENCE_MISSING: {p}")
    freeze = json.loads(freeze_path.read_text())
    if "identity_sha256" not in freeze or "identity_file" not in freeze:
        raise CanonicalizationError(f"EVIDENCE_INVALID: {freeze_path}")
    identity_sha = freeze["identity_sha256"]
    identity_rel = freeze["identity_file"]

    out = {"candidates": {}, "identity": {}, "identity_rel": identity_rel}
    for entry in json.loads(cand_manifest.read_text()).get("candidates", []):
        out["candidates"][entry["candidate_id"]] = entry["sha256"]
    out["identity"][Path(identity_rel).name] = identity_sha
    return out


def check_runtime_manifest(input_dir: Path, identity_sha: str) -> Path:
    """Consistency-check the mutable runtime manifest against the committed hash.

    Read-only and never authoritative: the committed
    ``evidence/<set>/source_freeze.json`` hash always wins.
    """
    runtime_manifest = input_dir / "identity" / "reference_manifest.json"
    if not runtime_manifest.exists():
        raise CanonicalizationError(f"EVIDENCE_MISSING: {runtime_manifest}")
    runtime = json.loads(runtime_manifest.read_text())
    runtime_sha = runtime.get("image_A_sha256")
    if runtime_sha != identity_sha:
        raise CanonicalizationError(
            f"RUNTIME_MANIFEST_INCONSISTENT: {runtime_manifest} records {runtime_sha} but "
            f"the committed source_freeze.json records {identity_sha}")
    return runtime_manifest


def run(input_dir: Path, output_dir: Path, config_path: Path, evidence_dir: Path) -> dict:
    cfg = load_config(config_path)
    exp = expected_hashes(input_dir, evidence_dir)
    version_tag = "v" + str(cfg["config_version"]).split(".")[0]

    identity_rel = exp["identity_rel"]
    jobs = [
        {"id": "source-A-aka-front", "arm": "SOURCE_IDENTITY",
         "rel": identity_rel,
         "authority": "SOURCE_TRUTH", "role": "DERIVED_REFERENCE",
         "expected_sha256": exp["identity"].get(Path(identity_rel).name)},
        {"id": "pilot-A-001", "arm": "A",
         "rel": "candidates/pilot-A-001.png",
         "authority": "GENERATED_CANDIDATE", "role": "GENERATED_CANDIDATE",
         "expected_sha256": exp["candidates"].get("pilot-A-001")},
        {"id": "pilot-C-001", "arm": "C",
         "rel": "candidates/pilot-C-001.png",
         "authority": "GENERATED_CANDIDATE", "role": "GENERATED_CANDIDATE",
         "expected_sha256": exp["candidates"].get("pilot-C-001")},
    ]

    canon_dir = output_dir / "canonical"
    canon_dir.mkdir(parents=True, exist_ok=True)

    items = []
    before_after = []
    for job in jobs:
        src_path = input_dir / job["rel"]
        if not src_path.exists():
            raise CanonicalizationError(f"INPUT_MISSING: {src_path}")
        if not job["expected_sha256"]:
            raise CanonicalizationError(f"EXPECTED_HASH_MISSING: {job['id']}")
        actual = sha256_file(src_path)
        if actual != job["expected_sha256"]:
            raise CanonicalizationError(
                f"HASH_MISMATCH: {job['id']} expected {job['expected_sha256']} got {actual}")
        if job["authority"] == "SOURCE_TRUTH":
            check_runtime_manifest(input_dir, job["expected_sha256"])
        stem = src_path.stem
        out_path = canon_dir / f"{stem}-canonical-{version_tag}.png"
        res = canonicalize_file(src_path, out_path, cfg)
        items.append({
            "id": job["id"],
            "arm": job["arm"],
            "source_file": job["rel"],
            "parent_sha256": actual,
            "expected_sha256": job["expected_sha256"],
            "hash_verified": True,
            "original_framing": res["original_framing"],
            "derivative": {
                "file": f"canonical/{out_path.name}",
                "sha256": sha256_file(out_path),
                "dimensions": res["derivative_framing"]["dimensions"],
                "margins_ltrb_px": res["derivative_framing"]["margins_ltrb_px"],
                "framing_gate": res["derivative_framing"]["hard_gate"],
                "issues": res["derivative_framing"]["issues"],
            },
            "transform": res["transform"],
            "status": "FRAME_PASS_ONLY",
            "artistic_gates": {
                "anatomy": "NOT_TESTED", "identity": "NOT_TESTED",
                "angle": "NOT_TESTED", "style": "NOT_TESTED",
                "human_approval": "MANUAL_REVIEW_REQUIRED"},
            "authority": job["authority"],
            "role": job["role"],
            "provenance": {
                "parent_state": job["authority"],
                "parent_sha256": actual,
                "derivative_kind": "DERIVED_REFERENCE" if job["authority"] == "SOURCE_TRUTH"
                else "GENERATED_CANDIDATE",
                "promotion": "NONE",
                "parent_manifest": str(evidence_dir / "source_freeze.json"),
            },
            "lifecycle": "REVIEWED",
            "golden": False,
            "approved": False,
        })
        before_after.append((src_path, out_path, job["id"], res["original_framing"]["hard_gate"]))

    report = {
        "schema": REPORT_SCHEMA,
        "stage": "CORE-023 Task A - deterministic candidate canonicalization (v2)",
        "generated_by": ALGORITHM_ID,
        "algorithm": {"id": ALGORITHM_ID, "version": ALGORITHM_VERSION,
                      "deterministic": True, "ai_redrawing": False,
                      "crop_or_warp_or_inpaint": False,
                      "resampler": "Pillow Image.transform AFFINE + BICUBIC"},
        "tool_versions": {
            "python": platform.python_version(),
            "pillow": Image.__version__,
            "numpy": np.__version__,
        },
        "config": {"path": str(config_path), "sha256": sha256_file(config_path),
                   "version": cfg["config_version"], "schema": cfg["schema"]},
        "inputs": {"input_dir": str(input_dir), "evidence_dir": str(evidence_dir),
                   "output_dir": str(output_dir)},
        "identity_hash_authority": {
            "committed_evidence": str(evidence_dir / "source_freeze.json"),
            "field": "identity_sha256",
            "runtime_manifest_role": "consistency_check_only",
        },
        "canvas": {"width": cfg["canvas"]["width"], "height": cfg["canvas"]["height"],
                   "background_rgb": cfg["canvas"]["background_rgb"],
                   "min_margin_px": cfg["min_margin_px"],
                   "resampling": cfg["resampling"],
                   "coordinate_domain": cfg["coordinate_domain"]},
        "items": items,
        "artistic_gates": {
            "anatomy": "NOT_TESTED", "identity": "NOT_TESTED", "angle": "NOT_TESTED",
            "style": "NOT_TESTED", "human_approval": "MANUAL_REVIEW_REQUIRED"},
        "frame_gate_summary": {i["id"]: i["derivative"]["framing_gate"] for i in items},
        "original_frame_gate_summary": {i["id"]: i["original_framing"]["hard_gate"] for i in items},
        "benchmark": {"ranking": "NONE_ACCEPTED", "full_ABCD_benchmark": "NOT_TESTED",
                      "production_status": "NOT_ACCEPTED",
                      "B": "NOT_TESTED", "D": "NOT_TESTED"},
        "approval_state": "NOT_APPROVED",
        "golden": False,
        "notes": [
            "Framing PASS is a framing statement only and is not an artistic approval.",
            "Original bytes are preserved; only new versioned derivatives are written.",
            "No earlier acceptance record is replaced by this report.",
            "The identity derivative is a DERIVED_REFERENCE over SOURCE_TRUTH; "
            "candidate art is never promoted.",
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    write_contact_sheet(before_after, output_dir / "contact_sheet.png")
    return report


def write_contact_sheet(pairs, path: Path, cell: int = 320) -> None:
    """Source / A / C before-and-after sheet."""
    cols, rows = 2, len(pairs)
    pad, label_h = 10, 26
    board = Image.new("RGB", (cols * (cell + pad) + pad, rows * (cell + pad + label_h) + pad),
                      (241, 242, 246))
    draw = ImageDraw.Draw(board)
    for row, (src_path, out_path, ident, orig_gate) in enumerate(pairs):
        y = pad + row * (cell + pad + label_h)
        for col, p in enumerate((src_path, out_path)):
            with Image.open(p) as im:
                im = im.convert("RGB")
                im.thumbnail((cell, cell))
                x = pad + col * (cell + pad) + (cell - im.width) // 2
                board.paste(im, (x, y + label_h))
        draw.text((pad, y), f"{ident} | BEFORE | original framing {orig_gate}", fill=(24, 31, 45))
        draw.text((pad + cell + pad, y), f"{ident} | AFTER | canonical framing PASS",
                  fill=(24, 31, 45))
    path.parent.mkdir(parents=True, exist_ok=True)
    board.save(path, format="PNG")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Deterministic candidate canonicalization")
    ap.add_argument("--input-dir", default=str(ROOT / "out"))
    ap.add_argument("--output-dir", default=str(ROOT / "out" / "core023"))
    ap.add_argument("--config", default=str(ROOT / "config" / "canonicalization-v2.json"))
    ap.add_argument("--evidence-dir", default=str(ROOT / "evidence" / "local-2026-10-30"))
    args = ap.parse_args(argv)
    try:
        report = run(Path(args.input_dir), Path(args.output_dir),
                     Path(args.config), Path(args.evidence_dir))
    except CanonicalizationError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}))
        return 1
    print(json.dumps({
        "status": "PASS",
        "frame_gate_summary": report["frame_gate_summary"],
        "original_frame_gate_summary": report["original_frame_gate_summary"],
        "ranking": report["benchmark"]["ranking"],
        "full_ABCD_benchmark": report["benchmark"]["full_ABCD_benchmark"],
        "artistic_gates": report["artistic_gates"],
        "report": str(Path(args.output_dir) / "report.json"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

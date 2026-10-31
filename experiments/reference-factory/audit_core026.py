#!/usr/bin/env python3
"""CORE-026 M1 subset A: source audit + PSD-layer <-> INX-node correspondence.

Scope (bounded):
  --audit         Hash pinned sources, CORE-025 scene/config/prepare/capture/QA/locks
                  and the 62 raw/source/clean PNGs; parse the COMPLETE Aka.inx
                  binary JSON section; verify Head:: Yaw-Pitch domain, axis grid
                  and binding count; export nodes/ancestors and relevant bindings;
                  build config/core026-part-correspondence.json from real decoded
                  texture evidence.
  --verify-source Re-hash the protected inputs, re-check the 62 orders and every
                  correspondence entry, and FAIL (non-zero exit) on tampering or on
                  a VERIFIED mapping that the real domain does not support.

This script NEVER claims overall M1 PASS: it only produces a source-domain verdict.
No GPU/native capture is performed or simulated here.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "core026"
CORRESPONDENCE = HERE / "config" / "core026-part-correspondence.json"

INX_SHA = "dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f"
PSD_SHA = "979fa62702b25f8af25414637d9ba6c36cbc9eb03bfa0c454470c73bdf51e55e"

HEAD_PARAM = "Head:: Yaw-Pitch"
HEAD_MIN = [-1.0, -1.0]
HEAD_MAX = [1.0, 1.0]
HEAD_DEFAULTS = [0.0, 0.0]
HEAD_AXIS_X = 9
HEAD_AXIS_Y = 3
HEAD_BINDINGS = 114
HEAD_AXIS_VALUES_X = [i / 8 for i in range(9)]
HEAD_AXIS_VALUES_Y = [0.0, 0.5, 1.0]
LAYER_PNG_COUNT = 186

# CORE-025 protected inputs (scene / config / prepare / capture / QA / locks)
CORE025_FILES = [
    "core025.html",
    "core025.js",
    "config/core025-render.json",
    "config/core025-layer-contract.json",
    "prepare_core025.py",
    "capture_core025.mjs",
    "capture_core025_video.mjs",
    "qa.py",
    "verify_core025_supervisor.py",
    "verify_core025_video.py",
    "package.json",
    "package-lock.json",
    "sources.lock.json",
    "out/core025/assembly/assembly.json",
    "out/core025/assembly/qa.json",
    "out/core025/render/manifest.json",
    "out/core025/render/supervisor-qa.json",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def jdump(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


# --------------------------------------------------------------------------- INX


def parse_inx(path: Path):
    """Parse the complete INX binary: JSON section + TEX_SECT textures."""
    data = path.read_bytes()
    if data[:8] != b"TRNSRTS\x00":
        raise ValueError("not an INX/TRNSRTS file")
    n = struct.unpack(">I", data[8:12])[0]
    if not (100 <= n <= len(data) - 12):
        raise ValueError("malformed INX JSON header length")
    raw_json = data[12:12 + n]
    model = json.loads(raw_json.decode("utf-8"))
    if 12 + n > len(data):
        raise ValueError("truncated INX JSON section")
    # trailing binary sections (textures)
    pos = 12 + n
    textures = []
    while pos + 8 <= len(data):
        tag = data[pos:pos + 8]
        if tag != b"TEX_SECT":
            break
        pos += 8
        count = struct.unpack(">I", data[pos:pos + 4])[0]
        pos += 4
        for _ in range(count):
            ln = struct.unpack(">I", data[pos:pos + 4])[0]
            pos += 4
            fmt = data[pos]
            pos += 1
            blob = data[pos:pos + ln]
            pos += ln
            textures.append({"format": fmt, "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest()})
        break
    return model, textures, {"json_bytes": n, "total_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def xy(seq):
    if not seq:
        return []
    if isinstance(seq[0], list):
        return seq
    return [seq[i:i + 2] for i in range(0, len(seq), 2)]


def index_nodes(model):
    """uuid -> node record with ancestor chain, mesh and texture info."""
    nodes = {}

    def visit(node, chain):
        rec = {
            "uuid": node.get("uuid"),
            "name": node.get("name"),
            "parent": chain[-1] if chain else None,
            "ancestors": list(chain),
            "has_mesh": isinstance(node.get("mesh"), dict),
            "textures": node.get("textures") or [],
            "origin": (node.get("mesh") or {}).get("origin"),
        }
        if rec["has_mesh"]:
            mesh = node["mesh"]
            verts = xy(mesh.get("verts") or [])
            uvs = xy(mesh.get("uvs") or [])
            faces = mesh.get("indices") or []
            rec["vertex_count"] = len(verts)
            rec["triangle_count"] = len(faces) // 3
            if verts:
                rec["vertex_bounds"] = [
                    float(min(v[0] for v in verts)), float(min(v[1] for v in verts)),
                    float(max(v[0] for v in verts)), float(max(v[1] for v in verts)),
                ]
            if uvs:
                rec["uv_bounds"] = [
                    float(min(u[0] for u in uvs)), float(min(u[1] for u in uvs)),
                    float(max(u[0] for u in uvs)), float(max(u[1] for u in uvs)),
                ]
        nodes[rec["uuid"]] = rec
        for child in node.get("children") or []:
            visit(child, chain + [rec["name"]])

    roots = model.get("nodes")
    if isinstance(roots, dict):
        # INX "nodes" is a SINGLE root node descriptor (uuid/name/children).
        # It is never a uuid -> node mapping, so never list(dict.values()).
        roots = [roots]
    if not isinstance(roots, list):
        roots = [roots] if roots else []
    for root in roots:
        if isinstance(root, dict):
            visit(root, [])
    return nodes


def decode_textures(path: Path):
    """Decode the embedded TGA textures of the INX into PIL images."""
    from PIL import Image

    data = path.read_bytes()
    n = struct.unpack(">I", data[8:12])[0]
    pos = 12 + n
    out = []
    if data[pos:pos + 8] != b"TEX_SECT":
        return out
    pos += 8
    count = struct.unpack(">I", data[pos:pos + 4])[0]
    pos += 4
    for idx in range(count):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        pos += 4
        fmt = data[pos]
        pos += 1
        blob = data[pos:pos + ln]
        pos += ln
        with Image.open(io.BytesIO(blob)) as im:
            rgba = im.convert("RGBA").copy()
        out.append({"id": idx, "format": fmt, "bytes": ln, "image": rgba,
                    "sha256": hashlib.sha256(blob).hexdigest(),
                    "size": list(rgba.size)})
    return out


# ------------------------------------------------------------------ raster match


def trim_alpha_bbox(arr):
    """Crop an RGBA array to the alpha>0 bounding box. Returns (crop, bbox)."""
    import numpy as np

    a = arr[..., 3]
    ys, xs = np.nonzero(a > 0)
    if ys.size == 0:
        return None, None
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    return arr[y0:y1, x0:x1, :], [x0, y0, x1 - x0, y1 - y0]


def premul_match(raw_rgba, native_rgba):
    """Bounded raster-identity check between a source layer and an INX texture.

    Rule (no flipping, no resampling, no opaque-only sub-crop):
      * both sides are cropped to their alpha>0 bounding boxes;
      * cropped dimensions must be EQUAL;
      * cropped alpha arrays must be EXACTLY equal;
      * on alpha>0 pixels, round(rawRGB * rawAlpha / 255) must equal the native
        RGB within max absolute difference <= 1.

    Returns None when the pair does not match, otherwise a metrics dict.
    """
    import numpy as np

    raw, raw_bb = trim_alpha_bbox(raw_rgba)
    native, native_bb = trim_alpha_bbox(native_rgba)
    if raw is None or native is None:
        return None
    if raw.shape[:2] != native.shape[:2]:
        return None
    if not np.array_equal(raw[..., 3], native[..., 3]):
        return None
    visible = raw[..., 3] > 0
    if not visible.any():
        return None
    premul = np.rint(raw[..., :3].astype(np.float64) * raw[..., 3:4].astype(np.float64) / 255.0)
    delta = np.abs(premul - native[..., :3].astype(np.float64))[visible]
    max_err = float(delta.max())
    if max_err > 1:
        return None
    return {
        "source_alpha_bbox": raw_bb,
        "native_alpha_bbox": native_bb,
        "alpha_max_error": 0,
        "premul_rgb_max_error": int(max_err),
        "premul_rgb_mae": float(delta.mean()),
    }


def texture_owners(nodes):
    """texture_id -> list of node records that ACTUALLY own that texture."""
    owners = {}
    for uuid, rec in nodes.items():
        for tid in rec.get("textures") or []:
            owners.setdefault(tid, []).append((uuid, rec))
    return owners


def build_correspondence(model, nodes, textures, assembly):
    """62-layer correspondence from real decoded pixels (premultiplied-alpha check)."""
    import numpy as np
    from PIL import Image

    tex_rgba = {}
    for t in textures:
        tex_rgba[t["id"]] = np.asarray(t["image"].convert("RGBA"))
    owners = texture_owners(nodes)

    entries = []
    for layer in assembly["layers"]:
        raw_rel = layer["raw_source_texture"]["file"]
        raw_path = HERE / raw_rel
        with Image.open(raw_path) as im:
            raw_rgba = np.asarray(im.convert("RGBA"))

        candidates = []
        for tid, native in sorted(tex_rgba.items()):
            m = premul_match(raw_rgba, native)
            if m is None:
                continue
            for uuid, rec in owners.get(tid, []):
                cand = {
                    "inx_uuid": uuid,
                    "inx_name": rec["name"],
                    "ancestors": rec["ancestors"],
                    "texture_id": tid,
                    "owns_texture_id": True,
                    "native_alpha_bbox": m["native_alpha_bbox"],
                    "alpha_max_error": m["alpha_max_error"],
                    "premul_rgb_max_error": m["premul_rgb_max_error"],
                    "premul_rgb_mae": m["premul_rgb_mae"],
                }
                candidates.append(cand)

        source_bb = trim_alpha_bbox(raw_rgba)[1]
        unique = len(candidates) == 1
        if unique:
            best = candidates[0]
            status = "VERIFIED"
            reason = ("unique raster-content identity: alpha-exact and premultiplied-RGB identical "
                      "(max diff <= 1) against the decoded INX texture owned by a single node")
            evidence = {
                "method": "alpha_trim_premultiplied_rgb_match",
                "detail": ("source layer trimmed to alpha>0 bbox; alpha arrays exactly equal to the "
                           "native texture; round(RGB*alpha/255) vs native RGB max abs diff <= 1; "
                           "no flip, no resampling, no name authority"),
                "decoded_texture_id": best["texture_id"],
                "decoded_texture_sha256": next(t["sha256"] for t in textures if t["id"] == best["texture_id"]),
                "alpha_max_error": best["alpha_max_error"],
                "premul_rgb_max_error": best["premul_rgb_max_error"],
                "premul_rgb_mae": best["premul_rgb_mae"],
                "candidate_count": len(candidates),
            }
        else:
            best = None
            status = "UNRESOLVED"
            if len(candidates) > 1:
                reason = ("raster content is duplicated across %d INX textures/nodes; the pixel check "
                          "cannot disambiguate them" % len(candidates))
            else:
                reason = "no INX texture satisfies the alpha-exact premultiplied-RGB identity check"
            evidence = {
                "method": "alpha_trim_premultiplied_rgb_match",
                "detail": ("no unique raster-content identity; %d exact candidate(s) retained "
                           "(duplicate rasters stay UNRESOLVED)" % len(candidates)),
                "candidate_count": len(candidates),
            }

        entries.append({
            "psd_order": layer["order"],
            "psd_name": layer["name"],
            "source_png": raw_rel,
            "source_png_sha256": layer["raw_source_texture"]["sha256"],
            "source_png_size": layer["raw_source_texture"].get("size"),
            "source_alpha_bbox": source_bb,
            "inx_uuid": best["inx_uuid"] if best else None,
            "inx_uuid_candidates": [c["inx_uuid"] for c in candidates],
            "candidates": candidates,
            "matching_evidence": evidence,
            "status": status,
            "reason": reason,
            "spatial_registration": "NOT_TESTED",
            "spatial_registration_note": ("raster-content identity only; geometric/UV registration "
                                          "is NOT evaluated and NOT claimed"),
        })
    entries.sort(key=lambda e: e["psd_order"])
    return entries


# ---------------------------------------------------------------------- commands


def do_audit():
    import numpy as np
    from PIL import Image

    OUT.mkdir(parents=True, exist_ok=True)
    report = {"schema": "koma-core026-source-audit/1",
              "scope": "M1_SUBSET_A_SOURCE_AUDIT_ONLY",
              "overall_m1_status": "NOT_EVALUATED",
              "note": "This audit covers source integrity and PSD<->INX correspondence only. "
                      "It is NOT an overall CORE-026 M1 PASS."}

    # --- pinned sources
    lock = json.loads((HERE / "sources.lock.json").read_text())
    lock_map = {s["file"]: s for s in lock["sources"]}
    sources = {}
    for fname, expected in (("tutorial-aka.psd", PSD_SHA), ("Aka.inx", INX_SHA)):
        p = HERE / "out" / "source" / fname
        actual = sha256(p)
        sources[fname] = {"file": str(p.relative_to(HERE)), "sha256": actual,
                          "matches_lock": actual == expected,
                          "lock_entry": lock_map.get(fname, {}).get("role")}
        if actual != expected:
            report["status"] = "FAIL_SOURCE_TAMPER"
            (OUT / "source-audit.json").write_text(jdump(report))
            print("FAIL: pinned source %s sha mismatch" % fname)
            return 2
    p = HERE / "out" / "source" / "reference.vrm"
    if p.is_file():
        sources["reference.vrm"] = {"file": str(p.relative_to(HERE)), "sha256": sha256(p),
                                    "matches_lock": sha256(p) == lock_map["reference.vrm"]["sha256"]}
    report["sources"] = sources

    # --- CORE-025 protected inputs
    core25 = {}
    for rel in CORE025_FILES:
        f = HERE / rel
        core25[rel] = {"sha256": sha256(f) if f.is_file() else None,
                       "present": f.is_file()}
    report["core025_protected_inputs"] = core25

    # --- assembly + 62 layer PNGs
    assembly = json.loads((HERE / "out" / "core025" / "assembly" / "assembly.json").read_text())
    layers = assembly["layers"]
    layer_files = []
    bad = []
    for lay in layers:
        for key in ("raw_source_texture", "source_texture", "clean_texture"):
            rec = lay[key]
            f = HERE / rec["file"]
            if not f.is_file():
                bad.append({"file": rec["file"], "problem": "missing"})
                continue
            actual = sha256(f)
            layer_files.append({"file": rec["file"], "role": key, "psd_order": lay["order"],
                                "sha256": actual, "recorded_sha256": rec["sha256"],
                                "matches": actual == rec["sha256"]})
            if actual != rec["sha256"]:
                bad.append({"file": rec["file"], "problem": "sha_mismatch"})
    report["layer_pngs"] = {"count": len(layer_files), "orders": len(layers),
                            "expected_pngs": len(layers) * 3, "problems": bad,
                            "png_count_ok": len(layer_files) == LAYER_PNG_COUNT}
    if bad or len(layers) != 62 or len(layer_files) != LAYER_PNG_COUNT:
        report["status"] = "FAIL_LAYER_INTEGRITY"
        (OUT / "source-audit.json").write_text(jdump(report))
        print("FAIL: layer PNG integrity problems: %s" % bad[:5])
        return 3

    # --- INX parse
    model, tex_meta, inx_info = parse_inx(HERE / "out" / "source" / "Aka.inx")
    nodes = index_nodes(model)
    params = model.get("param") or []
    if isinstance(params, dict):
        params = list(params.values())
    head = next((p for p in params if p.get("name") == HEAD_PARAM), None)
    if head is None:
        report["status"] = "FAIL_HEAD_PARAM_MISSING"
        (OUT / "source-audit.json").write_text(jdump(report))
        print("FAIL: Head:: Yaw-Pitch parameter missing")
        return 4
    axis = head.get("axis_points")
    axis_ok = (isinstance(axis, list) and len(axis) >= 1 and len(axis[0]) == HEAD_AXIS_X
               and len(axis) > 1 and len(axis[1]) == HEAD_AXIS_Y
               and [float(v) for v in axis[0]] == HEAD_AXIS_VALUES_X
               and [float(v) for v in axis[1]] == HEAD_AXIS_VALUES_Y)
    bindings = head.get("bindings") or []
    head_check = {
        "name": head.get("name"), "uuid": head.get("uuid"),
        "min": head.get("min"), "max": head.get("max"), "defaults": head.get("defaults"),
        "is_vec2": head.get("is_vec2"),
        "axis_points": axis,
        "axis_grid": "%dx%d" % (HEAD_AXIS_X, HEAD_AXIS_Y) if axis_ok else "unexpected",
        "binding_count": len(bindings),
        "min_ok": [float(x) for x in head.get("min", [])] == HEAD_MIN,
        "max_ok": [float(x) for x in head.get("max", [])] == HEAD_MAX,
        "defaults_ok": [float(x) for x in (head.get("defaults") or [])] == HEAD_DEFAULTS,
        "axis_ok": bool(axis_ok),
        "bindings_ok": len(bindings) == HEAD_BINDINGS,
    }
    report["inx"] = {"sha256": inx_info["sha256"], "json_bytes": inx_info["json_bytes"],
                     "total_bytes": inx_info["total_bytes"], "parameter_count": len(params),
                     "node_count": len(nodes), "texture_count": len(tex_meta),
                     "textures": tex_meta}
    report["head_yaw_pitch"] = head_check
    if not all([head_check["min_ok"], head_check["max_ok"], head_check["defaults_ok"],
                head_check["axis_ok"], head_check["bindings_ok"]]):
        report["status"] = "FAIL_HEAD_PARAMETER_DOMAIN"
        (OUT / "source-audit.json").write_text(jdump(report))
        print("FAIL: Head:: Yaw-Pitch domain mismatch: %s" % json.dumps(head_check)[:400])
        return 5

    # --- export nodes / ancestors / relevant bindings
    node_export = {}
    for uuid, rec in nodes.items():
        node_export[str(uuid)] = {"name": rec["name"], "ancestors": rec["ancestors"],
                                  "has_mesh": rec["has_mesh"], "vertex_count": rec.get("vertex_count"),
                                  "uv_bounds": rec.get("uv_bounds"),
                                  "vertex_bounds": rec.get("vertex_bounds"),
                                  "textures": rec["textures"]}
    (OUT / "inx-nodes.json").write_text(jdump({"schema": "koma-core026-inx-nodes/1",
                                                "node_count": len(nodes), "nodes": node_export}))

    binding_export = []
    for b in bindings:
        nid = b.get("node")
        rec = nodes.get(nid)
        binding_export.append({
            "node_uuid": nid,
            "node_name": rec["name"] if rec else None,
            "ancestors": rec["ancestors"] if rec else [],
            "param_name": b.get("param_name"),
            "values_shape": [len(b.get("values") or []), len((b.get("values") or [[]])[0]) if b.get("values") else 0],
            "isSet_shape": [len(b.get("isSet") or []), len((b.get("isSet") or [[]])[0]) if b.get("isSet") else 0],
            "value_sample": (b.get("values") or [[]])[0][:3] if b.get("values") else None,
        })
    (OUT / "inx-head-bindings.json").write_text(jdump({
        "schema": "koma-core026-inx-head-bindings/1",
        "param": HEAD_PARAM, "param_uuid": head.get("uuid"),
        "binding_count": len(bindings), "bindings": binding_export}))

    # --- correspondence
    textures = decode_textures(HERE / "out" / "source" / "Aka.inx")
    entries = build_correspondence(model, nodes, textures, assembly)
    doc = {
        "schema": "koma-core026-part-correspondence/1",
        "source": {"psd_sha256": PSD_SHA, "inx_sha256": INX_SHA,
                   "assembly": "out/core025/assembly/assembly.json",
                   "assembly_sha256": sha256(HERE / "out" / "core025" / "assembly" / "assembly.json")},
        "evidence_policy": ("VERIFIED requires a UNIQUE raster-content identity between the source "
                            "layer PNG and a decoded INX texture: both trimmed to their alpha>0 "
                            "bounding box, equal dimensions, EXACTLY equal alpha arrays, and "
                            "round(RGB*alpha/255) equal to the native RGB with max absolute "
                            "difference <= 1. The matched texture_id must actually be owned by the "
                            "mapped INX node. No flipping, no resampling, no opaque-only sub-crop, "
                            "and PSD/INX layer names are never authoritative (PSD L/R names are "
                            "opposite to INX naming). Duplicated rasters stay UNRESOLVED with every "
                            "exact candidate retained. This accepts raster identity only: "
                            "spatial_registration is NOT_TESTED."),
        "count": len(entries),
        "verified_count": sum(1 for e in entries if e["status"] == "VERIFIED"),
        "unresolved_count": sum(1 for e in entries if e["status"] == "UNRESOLVED"),
        "entries": entries,
    }
    CORRESPONDENCE.parent.mkdir(parents=True, exist_ok=True)
    CORRESPONDENCE.write_text(jdump(doc))
    report["correspondence"] = {"file": str(CORRESPONDENCE.relative_to(HERE)),
                                "sha256": sha256(CORRESPONDENCE),
                                "count": doc["count"], "verified": doc["verified_count"],
                                "unresolved": doc["unresolved_count"]}
    report["status"] = "SOURCE_AUDIT_OK"
    report["layer_pngs"]["files"] = layer_files
    (OUT / "source-audit.json").write_text(jdump(report))
    print("SOURCE_AUDIT_OK layers=%d verified=%d unresolved=%d" %
          (doc["count"], doc["verified_count"], doc["unresolved_count"]))
    print("report: %s" % (OUT / "source-audit.json"))
    return 0


def do_verify_source():
    import numpy as np
    from PIL import Image

    problems = []
    audit_path = OUT / "source-audit.json"
    if not audit_path.is_file():
        print("FAIL: no source audit found; run --audit first")
        return 10
    audit = json.loads(audit_path.read_text())

    # --- re-hash protected inputs (pinned sources, CORE-025 inputs, layer PNGs)
    for fname, rec in (audit.get("sources") or {}).items():
        if not rec.get("sha256"):
            continue
        p = HERE / rec["file"]
        if not p.is_file():
            problems.append("missing source %s" % fname)
            continue
        if sha256(p) != rec["sha256"]:
            problems.append("source tamper: %s" % fname)
    for rel, rec in (audit.get("core025_protected_inputs") or {}).items():
        p = HERE / rel
        if not p.is_file():
            problems.append("missing CORE-025 input %s" % rel)
        elif rec.get("sha256") and sha256(p) != rec["sha256"]:
            problems.append("CORE-025 tamper: %s" % rel)
    # the protected list must include the supervisor/video verifiers and npm manifests
    for rel in ("verify_core025_supervisor.py", "verify_core025_video.py",
                "package.json", "package-lock.json"):
        if rel not in (audit.get("core025_protected_inputs") or {}):
            problems.append("protected input list missing %s" % rel)
    layer_files = (audit.get("layer_pngs") or {}).get("files", [])
    for rec in layer_files:
        p = HERE / rec["file"]
        if not p.is_file():
            problems.append("missing layer PNG %s" % rec["file"])
        elif sha256(p) != rec["sha256"]:
            problems.append("layer PNG tamper: %s" % rec["file"])
    if len(layer_files) != LAYER_PNG_COUNT:
        problems.append("layer PNG count is %d, expected %d" % (len(layer_files), LAYER_PNG_COUNT))

    # --- assembly + 62 orders
    assembly = json.loads((HERE / "out" / "core025" / "assembly" / "assembly.json").read_text())
    layers = assembly["layers"]
    if len(layers) != 62:
        problems.append("assembly does not contain 62 orders")
    orders = [l["order"] for l in layers]
    if sorted(orders) != list(range(1, 63)):
        problems.append("assembly orders are not 1..62")
    # all 186 layer PNG hashes re-checked straight from the assembly record
    png_total = 0
    for lay in layers:
        for key in ("raw_source_texture", "source_texture", "clean_texture"):
            rec = lay[key]
            f = HERE / rec["file"]
            if not f.is_file():
                problems.append("missing layer PNG %s" % rec["file"])
                continue
            png_total += 1
            if sha256(f) != rec["sha256"]:
                problems.append("layer PNG sha mismatch %s" % rec["file"])
    if png_total != LAYER_PNG_COUNT:
        problems.append("re-hashed %d layer PNGs, expected %d" % (png_total, LAYER_PNG_COUNT))

    # --- reparse the CURRENT INX parameter / axes / bindings from the file
    model, _tex_meta, _inx_info = parse_inx(HERE / "out" / "source" / "Aka.inx")
    params = model.get("param") or []
    if isinstance(params, dict):
        params = list(params.values())
    head = next((x for x in params if x.get("name") == HEAD_PARAM), None)
    if head is None:
        problems.append("Head:: Yaw-Pitch parameter missing from current INX")
        head = {}
    axis = head.get("axis_points")
    if not (isinstance(axis, list) and len(axis) == 2
            and [float(v) for v in axis[0]] == HEAD_AXIS_VALUES_X
            and [float(v) for v in axis[1]] == HEAD_AXIS_VALUES_Y):
        problems.append("Head:: Yaw-Pitch axis points are not the exact %dx%d grid %s" %
                        (HEAD_AXIS_X, HEAD_AXIS_Y, [HEAD_AXIS_VALUES_X, HEAD_AXIS_VALUES_Y]))
    if [float(x) for x in (head.get("min") or [])] != HEAD_MIN:
        problems.append("Head:: Yaw-Pitch min mismatch")
    if [float(x) for x in (head.get("max") or [])] != HEAD_MAX:
        problems.append("Head:: Yaw-Pitch max mismatch")
    if [float(x) for x in (head.get("defaults") or [])] != HEAD_DEFAULTS:
        problems.append("Head:: Yaw-Pitch defaults mismatch")
    bindings = head.get("bindings") or []
    if len(bindings) != HEAD_BINDINGS:
        problems.append("Head:: Yaw-Pitch binding count is %d, expected %d" %
                        (len(bindings), HEAD_BINDINGS))

    nodes = index_nodes(model)
    owners = texture_owners(nodes)
    textures = decode_textures(HERE / "out" / "source" / "Aka.inx")
    tex_rgba = {t["id"]: np.asarray(t["image"].convert("RGBA")) for t in textures}

    # --- correspondence doc
    if not CORRESPONDENCE.is_file():
        problems.append("missing %s" % CORRESPONDENCE)
        doc = None
    else:
        doc = json.loads(CORRESPONDENCE.read_text())
        entries = doc.get("entries") or []
        if len(entries) != 62:
            problems.append("correspondence has %d entries, expected 62" % len(entries))
        seen_orders = [e.get("psd_order") for e in entries]
        if sorted(seen_orders) != list(range(1, 63)):
            problems.append("correspondence orders are not a 1..62 permutation")
        by_order = {l["order"]: l for l in layers}
        for e in entries:
            o = e.get("psd_order")
            lay = by_order.get(o)
            if lay is None:
                problems.append("entry %s: unknown psd_order" % o)
                continue
            if e.get("psd_name") != lay["name"]:
                problems.append("entry %s: name mismatch %r != %r" % (o, e.get("psd_name"), lay["name"]))
            raw = HERE / lay["raw_source_texture"]["file"]
            if not raw.is_file():
                problems.append("entry %s: missing raw PNG" % o)
                continue
            if sha256(raw) != lay["raw_source_texture"]["sha256"]:
                problems.append("entry %s: raw PNG sha mismatch" % o)
            elif e.get("source_png_sha256") != lay["raw_source_texture"]["sha256"]:
                problems.append("entry %s: recorded raw sha mismatch" % o)
            if e.get("status") not in ("VERIFIED", "UNRESOLVED"):
                problems.append("entry %s: invalid status %r" % (o, e.get("status")))
            if e.get("spatial_registration") != "NOT_TESTED":
                problems.append("entry %s: spatial_registration must be NOT_TESTED" % o)

            # independent re-derivation of the pixel correspondence
            with Image.open(raw) as im:
                raw_rgba = np.asarray(im.convert("RGBA"))
            real = []
            for tid, native in sorted(tex_rgba.items()):
                m = premul_match(raw_rgba, native)
                if m is None:
                    continue
                for uuid, rec in owners.get(tid, []):
                    real.append((uuid, tid, rec["name"], m))
            rec_cands = e.get("candidates") or []
            if len(rec_cands) != len(real):
                problems.append("entry %s: recorded %d candidates, independent check found %d" %
                                (o, len(rec_cands), len(real)))
            rec_pairs = sorted((c.get("inx_uuid"), c.get("texture_id")) for c in rec_cands)
            real_pairs = sorted((u, t) for (u, t, _n, _m) in real)
            if rec_pairs != real_pairs:
                problems.append("entry %s: candidate set does not match independent pixel check" % o)
            if e.get("status") == "VERIFIED":
                if len(real) != 1:
                    problems.append("entry %s: VERIFIED but %d independent candidates" % (o, len(real)))
                else:
                    uuid, tid, _n, _m = real[0]
                    if e.get("inx_uuid") != uuid:
                        problems.append("entry %s: VERIFIED uuid %r != independent %r" %
                                        (o, e.get("inx_uuid"), uuid))
                    ev = e.get("matching_evidence") or {}
                    if ev.get("decoded_texture_id") != tid:
                        problems.append("entry %s: VERIFIED texture id %r != independent %r" %
                                        (o, ev.get("decoded_texture_id"), tid))
                    if uuid not in owners.get(tid, []) and not any(
                            u == uuid for (u, t) in owners.get(tid, [])):
                        problems.append("entry %s: node %r does not own texture %r" % (o, uuid, tid))
            else:
                # UNRESOLVED must keep every exact candidate
                if len(real) > 1 and len(rec_cands) != len(real):
                    problems.append("entry %s: UNRESOLVED dropped exact candidates" % o)
                if e.get("inx_uuid") is not None:
                    problems.append("entry %s: UNRESOLVED entry must not claim a uuid" % o)

    result = {"schema": "koma-core026-verify-source/1",
              "scope": "SOURCE_ONLY",
              "overall_m1_status": "NOT_EVALUATED",
              "note": "Source-only pass. This is NOT an overall CORE-026 M1 PASS.",
              "problems": problems,
              "status": "FAIL" if problems else "SOURCE_ONLY_PASS"}
    (OUT / "verify-source.json").write_text(jdump(result))
    print(json.dumps({"status": result["status"], "problem_count": len(problems),
                      "problems": problems[:20]}, ensure_ascii=False))
    return 11 if problems else 0


def main():
    ap = argparse.ArgumentParser(description="CORE-026 M1 source audit / correspondence")
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--verify-source", action="store_true")
    a = ap.parse_args()
    if a.audit and a.verify_source:
        ap.error("choose one mode")
    if a.audit:
        return do_audit()
    if a.verify_source:
        return do_verify_source()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())

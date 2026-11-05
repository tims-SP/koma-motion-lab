#!/usr/bin/env python3
"""Verify independent P0 RGBA layers and GIF provenance; never infer image approval."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parents[1]
EXPECTED = "KOMA-P0-ARTMESH-MANIFEST-V1"


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def finite_xy(value):
    return (isinstance(value, (list, tuple)) and len(value) == 2
            and all(isinstance(c, (int, float)) and math.isfinite(c) for c in value))


def triangle_area(a, b, c):
    return abs((b[0] - a[0]) * (c[1] - a[1]) -
               (b[1] - a[1]) * (c[0] - a[0])) / 2


def layer_stats(path):
    with Image.open(path) as image:
        if image.format != "PNG":
            raise ValueError("PNG required")
        if image.mode != "RGBA":
            raise ValueError("native RGBA required")
        if image.size != (1024, 1024):
            raise ValueError("global canvas must be exactly 1024x1024")
        alpha = image.getchannel("A")
        histogram = alpha.histogram()
        occupied = sum(histogram[1:])
        soft = sum(histogram[1:255])
        bbox = alpha.getbbox()
        corners = [alpha.getpixel(p) for p in ((0, 0), (1023, 0), (0, 1023), (1023, 1023))]
        return {"width": 1024, "height": 1024, "opaquePixels": histogram[255],
                "softAlphaPixels": soft, "visiblePixels": occupied,
                "transparentCorners": all(v == 0 for v in corners),
                "bbox": list(bbox) if bbox else None}


def check_mesh(mesh):
    if not isinstance(mesh, dict):
        raise ValueError("ArtMesh metadata missing")
    names, points, triangles = (mesh.get(k) for k in ("vertexIds", "vertices", "triangles"))
    if not isinstance(names, list) or len(names) < 4 or len(names) != len(set(names)):
        raise ValueError("ArtMesh needs at least 4 unique vertex IDs")
    if not isinstance(points, list) or len(points) != len(names):
        raise ValueError("ArtMesh vertex correspondence invalid")
    if not all(finite_xy(p) and all(0 <= v <= 1024 for v in p) for p in points):
        raise ValueError("ArtMesh vertices outside global canvas")
    if not isinstance(triangles, list) or len(triangles) < 2:
        raise ValueError("ArtMesh needs at least two triangles")
    for tri in triangles:
        if (not isinstance(tri, list) or len(tri) != 3 or
            not all(isinstance(i, int) and 0 <= i < len(names) for i in tri) or
            len(set(tri)) != 3 or
            triangle_area(*(points[i] for i in tri)) < 0.1):
            raise ValueError("degenerate ArtMesh triangle")
    return {"vertices": len(names), "triangles": len(triangles),
            "topologySignature": json.dumps([names, triangles], separators=(",", ":"))}


def check_anchors(anchors):
    if not isinstance(anchors, list) or len(anchors) < 3:
        raise ValueError("three anatomical anchors required")
    names = [a.get("id") for a in anchors if isinstance(a, dict)]
    coords = [a.get("xy") for a in anchors if isinstance(a, dict)]
    if (len(names) != len(anchors) or not all(isinstance(n, str) and n for n in names)
        or len(set(names)) != len(names) or
        not all(finite_xy(p) and all(0 <= v <= 1024 for v in p) for p in coords)):
        raise ValueError("anatomical anchor format invalid")
    if max(triangle_area(coords[0], coords[i], coords[j])
           for i in range(1, len(coords)) for j in range(i + 1, len(coords))) < 0.1:
        raise ValueError("anatomical anchors are collinear")
    return sorted(names)


def part_key(angle, semantic):
    return str(angle) + "/" + semantic


def run(root, output, contract_path=HERE / "contract.json"):
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    root = Path(root).resolve()
    checks, failures, stats, hashes = [], [], {}, {}
    def record(name, ok, detail=""):
        checks.append({"name": name, "pass": bool(ok), "detail": str(detail)})
        if not ok:
            failures.append({"gate": name, "detail": str(detail)})

    hero = root / contract["identity"]["approvedHero"]
    hero_digest = sha256(hero) if hero.is_file() else None
    record("approved_hero_bytes", hero.is_file(), str(hero))
    record("approved_hero_sha256", hero_digest == contract["identity"]["expectedHeroSha256"],
           hero_digest or "source bytes unavailable")
    if hero.is_file():
        with Image.open(hero) as original:
            record("approved_hero_dimensions",
                   list(original.size) == contract["identity"]["expectedHeroSourceDimensions"],
                   original.size)
    gif_groups = [dict(name="whole", **contract["wholeGif"])] + contract["groups"]
    for group in gif_groups:
        name, target = group["name"], root / group["path"]
        found = target.is_file()
        record("gif_exists_" + name, found, str(target))
        if not found:
            continue
        hashes[group["path"]] = sha256(target)
        try:
            with Image.open(target) as im:
                record("gif_signature_" + name, im.format == "GIF", im.format)
                record("gif_count_" + name, getattr(im, "n_frames", 1) == group["frames"],
                       getattr(im, "n_frames", 1))
                record("gif_canvas_" + name, im.size == (1024, 1024), im.size)
                for index in range(getattr(im, "n_frames", 1)):
                    im.seek(index)
                    dispose = getattr(im, "disposal_method", None)
                    record(f"gif_disposal_{name}_{index}", dispose == 2, dispose)
                    frame = im.convert("RGBA")
                    corners = [frame.getpixel(pos)[3] for pos in
                               ((0, 0), (frame.width - 1, 0), (0, frame.height - 1),
                                (frame.width - 1, frame.height - 1))]
                    record(f"gif_alpha_{name}_{index}", all(a == 0 for a in corners), corners)
        except (OSError, ValueError) as exc:
            record("gif_decode_" + name, False, exc)

    manifest_path = root / "parts.json"
    if not manifest_path.is_file():
        record("manifest_exists", False, str(manifest_path))
        manifest = {}
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            manifest = {}
            record("manifest_decodes", False, exc)
    record("manifest_schema", manifest.get("schema") == EXPECTED, manifest.get("schema"))
    record("manifest_character", manifest.get("characterId") == contract["characterId"],
           manifest.get("characterId"))
    record("manifest_canvas", manifest.get("canvas") == [1024, 1024], manifest.get("canvas"))
    layers = manifest.get("parts", [])
    if not isinstance(layers, list):
        layers = []
        record("manifest_parts_array", False)
    registry = {}
    for i, layer in enumerate(layers):
        if not isinstance(layer, dict):
            record(f"record_{i}_is_object", False)
            continue
        angle, sid = layer.get("yawDeg"), layer.get("semanticId")
        key = part_key(angle, sid)
        record("slot_unique_" + key, key not in registry)
        registry[key] = layer
    for angle in contract["keyAngles"]:
        for sid in contract["semanticIds"]:
            key = part_key(angle, sid)
            record("primary_" + key, key in registry)
    for extra in contract["extraAnatomicalKeys"]:
        if extra["requiredForFullReconstruction"]:
            key = part_key(extra["yawDeg"], extra["semanticId"])
            record("anatomical_" + key, key in registry)
    role_set = set(contract["sourceRoles"])
    for key, layer in registry.items():
        sid, angle = layer.get("semanticId"), layer.get("yawDeg")
        if not isinstance(angle, int) or angle not in contract["keyAngles"]:
            record("angle_" + key, False)
            continue
        known_ids = set(contract["semanticIds"]) | {e["semanticId"] for e in contract["extraAnatomicalKeys"]}
        record("semantic_" + key, sid in known_ids)
        for field in contract["requiredPartFields"]:
            record("field_" + key + "_" + field, field in layer)
        visibility = layer.get("visibility")
        record("visibility_" + key, visibility in ("visible", "hidden"), visibility)
        if angle == 90 and sid == "hair.clip.cross_gold":
            record("side_clip_occlusion", visibility == "hidden")
        record("source_role_" + key, layer.get("sourceRole") in role_set, layer.get("sourceRole"))
        record("semantic_review_" + key, layer.get("semanticReviewed") is True)
        record("visual_review_" + key, layer.get("visualReviewed") is True)
        for field in ("sourceGifSha256", "frameSha256"):
            v = layer.get(field)
            record(field + "_" + key, isinstance(v, str) and len(v) == 64 and
                   all(c in "0123456789abcdef" for c in v or ""))
        sg = layer.get("sourceGif")
        if isinstance(sg, str) and sg in hashes:
            record("gif_hash_" + key, hashes[sg] == layer.get("sourceGifSha256"))
        else:
            record("gif_hash_" + key, False, sg)
        if not isinstance(layer.get("depthOrder"), (int, float)):
            record("depth_" + key, False)
        if not isinstance(layer.get("occludes"), list):
            record("occludes_" + key, False)
        try:
            check_anchors(layer.get("anchors"))
            record("anchors_" + key, True)
        except (ValueError, TypeError) as exc:
            record("anchors_" + key, False, exc)
        try:
            mesh_meta = check_mesh(layer.get("mesh"))
            record("mesh_" + key, True)
        except (ValueError, TypeError) as exc:
            record("mesh_" + key, False, exc)
            mesh_meta = None
        if visibility != "visible":
            continue
        relpath = layer.get("path")
        if (not isinstance(relpath, str) or Path(relpath).is_absolute()
            or ".." in Path(relpath).parts):
            record("path_" + key, False, relpath)
            continue
        png = (root / relpath).resolve()
        if not png.is_relative_to(root):
            record("path_" + key, False, relpath)
            continue
        record("png_exists_" + key, png.is_file(), relpath)
        if not png.is_file():
            continue
        digest = sha256(png)
        record("png_sha256_" + key, digest == layer.get("frameSha256"), digest)
        try:
            s = layer_stats(png)
            stats[key] = s
            record("png_nonempty_" + key, s["visiblePixels"] > 50, s["visiblePixels"])
            record("rgba_edge_" + key, s["softAlphaPixels"] >= 10,
                   s["softAlphaPixels"])
            record("transparent_corners_" + key, s["transparentCorners"])
            b = s["bbox"]
            record("margins_" + key, bool(b) and
                   b[0] > 0 and b[1] > 0 and b[2] < 1024 and b[3] < 1024, b)
            record("registered_bbox_" + key, b == layer.get("bbox"), b)
        except (ValueError, OSError) as exc:
            record("png_rgba_" + key, False, exc)
        if mesh_meta is not None:
            layer["_computedTopology"] = mesh_meta["topologySignature"]
    for sid in contract["semanticIds"]:
        topology = [registry.get(part_key(a, sid), {}).get("_computedTopology")
                    for a in contract["keyAngles"]]
        record("topology_" + sid, all(v is not None for v in topology)
               and len(set(topology)) == 1)
    report = {
        "schema": "KOMA-P0-GIF-INGESTION-QA-V1",
        "characterId": contract["characterId"],
        "sourceRoot": str(root),
        "status": "PASS_ENGINEERING_AND_VISUAL_GATES" if not failures else
                  ("BLOCKED_SOURCE_ASSETS" if not hero.is_file() or not layers else
                   "FAIL_ASSET_ACCEPTANCE"),
        "checked": len(checks), "passed": sum(c["pass"] for c in checks),
        "failed": len(failures), "failures": failures, "checks": checks,
        "sourceHashes": hashes, "layerStatistics": stats,
        "visualReviewPolicy": "manual assessment of original drawn frames and endpoint/holdout screenshots is mandatory"
    }
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="private directory containing approved originals and extracted layers")
    parser.add_argument("--output", required=True, help="persistent QA report JSON")
    parser.add_argument("--contract", type=Path, default=HERE / "contract.json")
    args = parser.parse_args()
    report = run(args.root, args.output, args.contract)
    print(json.dumps({key: report[key] for key in ("status", "checked", "passed", "failed")}))
    return 0 if report["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Production intake proof, using actual Reverse:1999 assets in a disposable runner.

Source bytes, extracted sprites, .riv files and rendered PNGs stay in
out/private-production (NEVER upload them from the public test repo).
Only sanitized machine-readable metadata/logs leave the runner.
"""
from __future__ import annotations
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "out" / "reverse1999-evidence"
PRIVATE = ROOT / "out" / "private-production"
INPUT = PRIVATE / "input"
EVIDENCE.mkdir(parents=True, exist_ok=True)
INPUT.mkdir(parents=True, exist_ok=True)
(EVIDENCE / "logs").mkdir(parents=True, exist_ok=True)

UPSTREAM = "myssal/Reverse-1999-CN-Asset"
REF = "45e75248ba3b25053fd32e63ab13c2f9f54dd9df"
SOURCE_L2D = "live2d/roles/300401_hongnujian"
SOURCE_SPINE = "roles/300401_hongnujian"
TARGET_REGION = "hnj_c_lian"  # unrotated actual face in Spine atlas


def download(path: str, limit: int = 12_000_000) -> Path:
    """Fetch a whitelisted small source file, no full 33GB checkout."""
    if not (path.startswith(SOURCE_L2D + "/") or path.startswith(SOURCE_SPINE + "/")):
        raise ValueError(f"non-whitelisted path: {path}")
    if ".." in Path(path).parts:
        raise ValueError("traversal")
    dest = INPUT / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = ("https://raw.githubusercontent.com/" + UPSTREAM + "/" + REF
           + "/" + urllib.parse.quote(path, safe="/"))
    req = urllib.request.Request(url, headers={"User-Agent": "koma-motion-lab/production-fixture"})
    with urllib.request.urlopen(req, timeout=45) as conn:
        chunks, size = [], 0
        while True:
            piece = conn.read(512 * 1024)
            if not piece:
                break
            size += len(piece)
            if size > limit:
                raise RuntimeError("over-size source file: " + path)
            chunks.append(piece)
    dest.write_bytes(b"".join(chunks))
    return dest


def signature(path: Path) -> dict:
    data = path.read_bytes()
    report = {
        "source_path": str(path.relative_to(INPUT)).replace("\\", "/"),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "git_lfs_pointer": data.startswith(b"version https://git-lfs.github.com/spec"),
    }
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        with Image.open(path) as image:
            report["image_dimensions"] = list(image.size)
            report["image_mode"] = image.mode
    if path.suffix == ".moc3":
        report["cubism_moc3_magic"] = data[:4] == b"MOC3"
    if path.suffix == ".skel":
        # Spine binary header is version-specific; don't assert parse support
        # based on a binary file's extension.
        report["nonempty_spine_binary"] = len(data) > 100
    return report


def atlas_regions(text: str) -> dict:
    regions = {}
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(" ") or not line.strip() or ":" in line or line.endswith(".png"):
            continue
        if line in ("filter", "scale"):
            continue
        for nextline in lines[i + 1:i + 6]:
            b = re.fullmatch(r"bounds:\s*(\d+),(\d+),(\d+),(\d+)", nextline.strip())
            if b:
                regions[line.strip()] = [int(x) for x in b.groups()]
                break
            if nextline and ":" not in nextline and nextline != line:
                break
    return regions


def run_cli(project: Path, name: str, *args: str) -> bool:
    cmd = ["rive", str(project), *args]
    result = subprocess.run(cmd, text=True, capture_output=True, timeout=45)
    (EVIDENCE / "logs" / (name + ".log")).write_text(
        result.stdout + "\n" + result.stderr + f"\nexit={result.returncode}\n")
    return result.returncode == 0


def real_image_rive_mesh(face: Path) -> dict:
    """An actual asset texture adapted into a new Rive Mesh, not a Spine rig import."""
    results = {}
    with Image.open(face) as image:
        w, h = image.size
    for angle in (0, 50, 100):
        project = PRIVATE / f"rive-face-{angle:03d}"
        subprocess.run(["rive", "create", str(project)], check=True, capture_output=True, text=True)
        (project / "face.png").write_bytes(face.read_bytes())
        xml = ET.parse(project / "scene.rml")
        root = xml.getroot()
        board = next(node for node in root.iter() if node.tag == "Artboard")
        board.set("width", "640")
        board.set("height", "360")
        board.set("name", "ImportedGameSprite")
        ET.SubElement(root, "ImageAsset", {"file": "face.png", "id": "0:60", "name": "GameSourceSprite"})
        container = ET.SubElement(board, "Node", {"x": "320", "y": "180", "name": "SpriteRig"})
        halfw, halfh = w / 2, h / 2
        rootbone = ET.SubElement(container, "RootBone", {
            "x": str(-halfw), "y": "0", "length": str(halfw), "rotation": "0",
            "id": "0:40", "name": "A"
        })
        ET.SubElement(rootbone, "Bone", {
            "length": str(halfw), "rotation": str(angle * 3.141592653589793 / 180),
            "id": "0:41", "name": "B",
        })
        image = ET.SubElement(container, "Image", {
            "assetId": "0:60", "id": "0:20", "name": "TextureFromSpineAtlas"
        })
        # Four triangles, six image mesh vertices. 1st tendon at x=-w/2,
        # 2nd at the center; weights 128+127 at transition to avoid >255.
        mesh = ET.SubElement(image, "Mesh", {
            "triangleIndexBytes": base64.b64encode(bytes([0,1,4,0,4,3,1,2,5,1,5,4])).decode(),
            "id": "0:21", "name": "GeneratedMesh",
        })
        vertices = [
            (-halfw, -halfh, 0, 0, 255, 1),
            (0, -halfh, .5, 0, 32640, 513),
            (halfw, -halfh, 1, 0, 255, 2),
            (-halfw, halfh, 0, 1, 255, 1),
            (0, halfh, .5, 1, 32640, 513),
            (halfw, halfh, 1, 1, 255, 2),
        ]
        for x, y, u, v, value, indices in vertices:
            vertex = ET.SubElement(mesh, "ContourMeshVertex", {
                "x": str(x), "y": str(y), "u": str(u), "v": str(v),
            })
            ET.SubElement(vertex, "Weight", {"values": str(value), "indices": str(indices)})
        skin = ET.SubElement(mesh, "Skin", {"name": "Skin"})
        ET.SubElement(skin, "Tendon", {
            "boneId": "0:40", "tx": str(-halfw), "ty": "0", "name": "A"
        })
        ET.SubElement(skin, "Tendon", {
            "boneId": "0:41", "tx": "0", "ty": "0", "name": "B"
        })
        xml.write(project / "scene.rml", encoding="unicode")
        rendered = PRIVATE / f"real-asset-{angle:03d}.png"
        result = {
            "verify": run_cli(project, f"rive-verify-{angle:03d}", "--verify"),
            "build": run_cli(project, f"rive-build-{angle:03d}", "--once"),
            "raster": run_cli(project, f"rive-render-{angle:03d}",
                              f"--screenshot={rendered}", "--viewport=640x360", "--advance=0s"),
        }
        result["rendered"] = rendered.exists()
        if result["rendered"]:
            with Image.open(rendered) as rendered_image:
                result["rgba_sha256"] = hashlib.sha256(rendered_image.convert("RGBA").tobytes()).hexdigest()
        results[str(angle)] = result
    return results


def main() -> int:
    report = {
        "experiment": "REVERSE1999-PROD-001",
        "upstream": UPSTREAM,
        "upstream_ref": REF,
        "asset_model": "300401_hongnujian",
        "source_license": "no repository root LICENSE found; upstream game copyright is not waived",
        "source_assets_in_public_artifacts": False,
        "files": [],
        "checks": {},
        "reuse": {},
    }

    def fetch(path: str) -> Path:
        result = download(path)
        report["files"].append(signature(result))
        return result

    try:
        # Spine and Cubism inventory, no bulk checkout.
        atlas = fetch(SOURCE_SPINE + "/300401_hongnujian.atlas")
        spine_png = fetch(SOURCE_SPINE + "/300401_hongnujian.png")
        for kind in ("room", "fight", "ui"):
            fetch(SOURCE_SPINE + f"/300401_hongnujian_{kind}.skel")
        model_file = fetch(SOURCE_L2D + "/300401_hongnujian.model3.json")
        moc3 = fetch(SOURCE_L2D + "/300401_hongnujian.moc3")
        model = json.loads(model_file.read_text())
        textures = [fetch(SOURCE_L2D + "/" + x) for x in model["FileReferences"]["Textures"]]
        motion_entries = [group[0]["File"] for group in model["FileReferences"]["Motions"].values() if group]
        # Live download of actual role's idle and existing gesture.
        for motion in ("motions/b_idle.motion3.json", "motions/b_hejiu.motion3.json"):
            if motion in motion_entries:
                file = fetch(SOURCE_L2D + "/" + motion)
                data = json.loads(file.read_text())
                report["reuse"][motion] = {
                    "meta": data.get("Meta", {}),
                    "curves": len(data.get("Curves", [])),
                }
        report["checks"]["live2d_model3_valid"] = model.get("Version") == 3
        report["checks"]["cubism_core_binary_present"] = moc3.read_bytes().startswith(b"MOC3")
        report["reuse"]["live2d_motion_groups"] = len(model["FileReferences"]["Motions"])
        report["reuse"]["live2d_motion_files"] = len(motion_entries)
        report["reuse"]["live2d_expression_entries"] = len(model["FileReferences"].get("Expressions", []))
        report["reuse"]["live2d_textures"] = len(textures)
        report["reuse"]["spine_skeleton_variants"] = 3

        regions = atlas_regions(atlas.read_text())
        report["reuse"]["spine_atlas_regions"] = len(regions)
        report["checks"]["spine_atlas_target_region_found"] = TARGET_REGION in regions
        report["checks"]["spine_binary_files_present"] = all(
            x["nonempty_spine_binary"] for x in report["files"] if x["source_path"].endswith(".skel"))
        if TARGET_REGION not in regions:
            raise RuntimeError("Target face region not found in Spine atlas")
        x, y, w, h = regions[TARGET_REGION]
        with Image.open(spine_png) as source:
            face = source.crop((x, y, x + w, y + h))
            if face.size != (w,h):
                raise RuntimeError("crop dimensions mismatch")
            if face.getbbox() is None:
                raise RuntimeError("atlas sprite empty")
            local_face = PRIVATE / "extracted-face.png"
            face.save(local_face)
        report["reuse"]["chosen_spine_region"] = TARGET_REGION
        report["reuse"]["chosen_region_size"] = [w, h]
        report["checks"]["spine_atlas_crop"] = True
        report["checks"]["binary_reuse_in_rive_native"] = False  # no importer / not tested

        # Real source texture -> new Rive Image+Mesh -> 3 angles, no Editor.
        report["rive_real_source_mesh"] = real_image_rive_mesh(local_face)
        poses = report["rive_real_source_mesh"]
        report["checks"]["rive_coded_mesh_renders"] = all(
            p["verify"] and p["build"] and p["raster"] and p["rendered"]
            for p in poses.values())
        report["checks"]["rive_pose_images_differ"] = len({
            p.get("rgba_sha256") for p in poses.values()}) == len(poses)

        # Do not export Rive scene files, source images, source skeletons,
        # textures or their derived screenshots from this public repo.
        report["limits"] = [
            "Spine .skel and Cubism .moc3 cannot be assumed to import into Rive automatically.",
            "Rive demo uses a cropped source texture, a *new* simple mesh, and generated weights.",
            "This is a production intake/adapter smoke test, not original Spine motion preservation.",
            "No full character performance, facial animation or native Cubism/Spine playback tested.",
            "Artwork redistribution rights not granted by presence in a public GitHub repository.",
        ]
        required = [
            "live2d_model3_valid", "cubism_core_binary_present",
            "spine_atlas_target_region_found", "spine_binary_files_present",
            "spine_atlas_crop", "rive_coded_mesh_renders", "rive_pose_images_differ",
        ]
        report["pass"] = all(report["checks"].get(x) for x in required)
    except Exception as exc:
        report["pass"] = False
        report["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        (EVIDENCE / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        lines = [
            "# Reverse:1999 production asset intake", "",
            f"Source: {UPSTREAM} at {REF}", "",
            f"**Status:** {'PASS' if report.get('pass') else 'FAIL'}", "",
            "## Checks", "",
        ]
        lines += [f"- {k}: {'PASS' if v else 'FAIL / NOT IMPLEMENTED'}"
                  for k,v in report["checks"].items()]
        if "reuse" in report:
            lines += ["", "## Reusable source metadata", ""]
            for k, v in report["reuse"].items():
                if not k.startswith("motions/"):
                    lines.append(f"- {k}: {v}")
        if report.get("error"):
            lines += ["", f"Error: {report['error']}"]
        lines += ["", "The original game images, .skel, .moc3 and derived artwork/screenshots",
                  "are NOT included in this public workflow artifact.",
                  "Successful Rive sprite-Mesh import does not imply original animation conversion."]
        (EVIDENCE / "summary.md").write_text("\n".join(lines) + "\n")
        print((EVIDENCE / "summary.md").read_text())
    return 0 if report.get("pass") else 1


if __name__ == "__main__":
    sys.exit(main())

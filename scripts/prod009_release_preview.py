#!/usr/bin/env python3
"""PROD-009: Rive-rendered previews from a real Spine rig.

Generated game imagery, project archives, and videos remain outside Git.
Release assets are published as a DRAFT by the workflow. Pose experiments
are procedural approximations and NOT original game animations or validated
Spine-runtime-equivalent renders.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw
import spine_multitrack_bake as multi
import spine_textured_rive as src

ROOT = src.ROOT
OUT = src.OUT
PRODUCT = ROOT / "prod009"
FRAMES = PRODUCT / "frames"
RELEASE = PRODUCT / "release"
FPS = int(os.getenv("PROD009_FPS", "24"))
VIEWPORT = os.getenv("PROD009_VIEWPORT", "960x540")
SOURCE_ACTIONS = ("idle_room", "walk", "sleep", "hit")
POSE_ORDER = ("neutral", "raise_hand", "wave", "bow", "lean_back", "squat", "sit", "prone")
POSES = {
    "neutral": {"rotate": {}, "root": (0, 0, 0)},
    "raise_hand": {"rotate": {"left_arm": 75, "right_arm": 15}, "root": (0, 0, 0)},
    "wave": {"rotate": {"left_arm": 85, "right_arm": 10}, "root": (0, 0, 0), "oscillate": True},
    "bow": {"rotate": {"torso": -30, "head": 10}, "root": (0, -12, -8)},
    "lean_back": {"rotate": {"torso": 28, "head": -12}, "root": (0, -8, 12)},
    "squat": {"rotate": {"left_thigh": 55, "right_thigh": -55, "left_shin": -65, "right_shin": 65},
              "root": (0, -68, 0)},
    "sit": {"rotate": {"left_thigh": 75, "right_thigh": -65, "left_shin": -72, "right_shin": 65},
            "root": (0, -88, -10)},
    "prone": {"rotate": {"torso": 10, "left_arm": 25, "right_arm": -15},
              "root": (42, -125, 78)},
}
MATCH = {
    "torso": ("sahngshen", "shangshen", "shenti"),
    "head": ("_tou", "head"),
    "left_arm": ("zuoshou1", "zuobi1", "left_arm"),
    "right_arm": ("youshou1", "youbi1", "right_arm"),
    "left_thigh": ("zuodatui", "left_thigh"),
    "right_thigh": ("youdatui", "right_thigh"),
    "left_shin": ("zuoxiaotui", "left_shin"),
    "right_shin": ("youxiaotui", "right_shin"),
}
REPORT = {
    "experiment": "PROD-009",
    "status": "NOT_STARTED",
    "asset": "myssal/Reverse-1999-CN-Asset 300401_hongnujian room.skel",
    "render_backend": "Rive CLI / source-weighted mesh bake",
    "source_spine_runtime_parity": "NOT_TESTED",
    "native_editable_rive_animations": False,
    "exported_riv": False,
    "poses_are_experiments_not_source_actions": True,
    "public_release": False,
    "storage": "draft GitHub Release; no media committed to Git",
    "clips": {},
}

def ease(a: float) -> float:
    a = max(0.0, min(1.0, a))
    return a * a * (3.0 - 2.0 * a)

def pose_amplitude(i: int, total: int) -> float:
    progress = i / max(1, total - 1)
    if progress < 0.3:
        return ease(progress / 0.3)
    if progress > 0.82:
        return ease((1.0 - progress) / 0.18)
    return 1.0

def bone_roles(bones):
    roles = {}
    for role, variants in MATCH.items():
        for token in variants:
            found = next((b["name"] for b in bones if token in b["name"].lower()), None)
            if found:
                roles[role] = found
                break
    root = next((b["name"] for b in bones if not b.get("parent")), None)
    if root is not None:
        roles["root"] = root
    return roles

def experimental_pose(bones, name: str, frame: int, count: int, roles):
    config = POSES[name]
    weight = pose_amplitude(frame, count)
    result = [dict(b) for b in bones]
    by_name = {bone["name"]: bone for bone in result}
    changed = []
    for role, rotation in config["rotate"].items():
        bone_name = roles.get(role)
        if bone_name is None:
            continue
        delta = rotation * weight
        if config.get("oscillate") and role == "left_arm":
            delta += math.sin(frame / FPS * math.tau * 1.6) * 16 * weight
        bone = by_name[bone_name]
        bone["rotation"] = float(bone.get("rotation", 0)) + delta
        changed.append(role)
    if "root" in roles:
        bone = by_name[roles["root"]]
        x, y, rotation = config["root"]
        bone["x"] = float(bone.get("x", 0)) + x * weight
        bone["y"] = float(bone.get("y", 0)) + y * weight
        bone["rotation"] = float(bone.get("rotation", 0)) + rotation * weight
    return result, changed

def render_frame(tree, project, bones, active, posed, path, label):
    world = src.world_transform(posed)
    moved = 0
    for slot, information in active.items():
        geometry = src.parse_attachment(information["attachment"], posed, world, information["bone"])
        if geometry is None or len(geometry["vertex"]) != len(information["vertices"]):
            raise RuntimeError("Mesh topology mismatch: " + slot)
        for vertex, (x, y, _) in zip(information["vertices"], geometry["vertex"]):
            vertex.set("x", f"{x:.8g}")
            vertex.set("y", f"{y:.8g}")
            moved += 1
    tree.write(project / "scene.rml", encoding="unicode")
    src.run(["rive", str(project), f"--screenshot={path}",
             f"--viewport={VIEWPORT}", "--advance=0s"])
    with Image.open(path) as raw:
        rgba = raw.convert("RGBA")
        canvas = Image.new("RGB", rgba.size, (30, 33, 43))
        canvas.paste(rgba, mask=rgba.getchannel("A"))
    drawer = ImageDraw.Draw(canvas)
    drawer.rectangle((12, 12, min(canvas.width - 12, 630), 58), fill=(9, 12, 19))
    drawer.text((22, 23), label, fill=(255, 255, 255))
    canvas.save(path, "PNG")
    return hashlib.sha256(canvas.tobytes()).hexdigest(), moved

def encode(dirpath, target, fps):
    pattern = str(dirpath / "%05d.png")
    src.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
             "-framerate", str(fps), "-i", pattern,
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
             "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(target)])
    if not target.exists() or target.stat().st_size < 5000:
        raise RuntimeError("Encoded movie missing or unexpectedly small: " + str(target))
    return target.stat().st_size

def contact_sheet(named_paths, destination):
    thumbs = []
    for name, image_path in named_paths:
        with Image.open(image_path) as img:
            thumb = img.convert("RGB")
            thumb.thumbnail((480, 270))
            tile = Image.new("RGB", (500, 310), (26, 29, 39))
            tile.paste(thumb, ((500 - thumb.width) // 2, 8))
            ImageDraw.Draw(tile).text((15, 283), name, fill="white")
            thumbs.append(tile)
    output = Image.new("RGB", (1000, ((len(thumbs) + 1) // 2) * 310), (26, 29, 39))
    for i, tile in enumerate(thumbs):
        output.paste(tile, ((i % 2) * 500, (i // 2) * 310))
    output.save(destination, optimize=True)
    return destination.stat().st_size

def process():
    if FPS < 4 or FPS > 60:
        raise ValueError("FPS must be between 4 and 60")
    PRODUCT.mkdir(parents=True, exist_ok=True)
    RELEASE.mkdir(parents=True, exist_ok=True)
    FRAMES.mkdir(parents=True, exist_ok=True)
    tree, project, bones, _, document, active = multi.setup_scene()
    REPORT["source_bones"] = len(bones)
    REPORT["converted_mesh_slots"] = len(active)
    REPORT["converted_vertices"] = sum(len(info["vertices"]) for info in active.values())
    REPORT["source_animations"] = sorted(document.get("animations", {}))
    REPORT["viewport"] = VIEWPORT
    REPORT["fps"] = FPS
    REPORT["bone_roles"] = bone_roles(bones)

    # Save and verify the ACTUAL authored Rive rig, not rive-create's blank
    # scene.rml template. setup_scene preserves pristine Skin and Tendon data
    # before stripping those elements for the frame-bake render path.
    native_rml = ROOT / "spine-native-rig-scaffold.rml"
    if not native_rml.is_file():
        raise RuntimeError("Native source rig was not captured before bake")
    shutil.copyfile(native_rml, project / "scene.rml")
    src.run(["rive", str(project), "--verify"])
    scaffold = RELEASE / "rive-native-rig-scaffold.zip"
    with zipfile.ZipFile(scaffold, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in project.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(project))
    REPORT["rive_rml_scaffold"] = scaffold.name
    REPORT["rive_rml_scaffold_bytes"] = scaffold.stat().st_size
    REPORT["rive_rml_scaffold_has_native_animation_tracks"] = False

    # Rendering route: static converted RML mesh vertices per independent frame.
    # Does not imply exported .riv or native editable motion tracks.
    per_action = FRAMES / "actions"
    per_action.mkdir(exist_ok=True)
    cursor = 0
    for action in SOURCE_ACTIONS:
        if action not in document["animations"]:
            REPORT["clips"][action] = {"status": "NOT_FOUND"}
            continue
        animation = document["animations"][action]
        total_duration = multi.clip_coverage(action, animation)["source_duration"]
        preview_duration = min(3.0, max(0.5, total_duration))
        frames = max(12, int(math.ceil(preview_duration * FPS)))
        hashes = []
        for frame in range(frames):
            t = min(total_duration, frame / FPS)
            posed = multi.pose_source_bones(bones, animation.get("bones", {}), t, set())
            image_path = per_action / f"{cursor:05d}.png"
            digest, _ = render_frame(tree, project, bones, active, posed, image_path,
                                     f"SOURCE | {action} | t={t:.2f}s")
            hashes.append(digest)
            cursor += 1
        REPORT["clips"][action] = {
            "status": "RENDERED",
            "frames": frames,
            "source_duration": total_duration,
            "preview_duration": preview_duration,
            "unique_frames": len(set(hashes)),
        }
    if cursor < 12:
        raise RuntimeError("No source action frames produced")
    REPORT["source_actions_video_bytes"] = encode(
        per_action, RELEASE / "01-source-actions-rive-baked.mp4", FPS)

    roles = REPORT["bone_roles"]
    per_pose = FRAMES / "poses"
    per_pose.mkdir(exist_ok=True)
    views = []
    cursor = 0
    frame_per_pose = FPS * 2
    for pose in POSE_ORDER:
        hashes, selected = [], set()
        middle_frame = None
        for frame in range(frame_per_pose):
            posed, used = experimental_pose(bones, pose, frame, frame_per_pose, roles)
            selected.update(used)
            image_path = per_pose / f"{cursor:05d}.png"
            digest, _ = render_frame(tree, project, bones, active, posed, image_path,
                                     f"EXPERIMENT | {pose} | NOT SOURCE ANIMATION")
            hashes.append(digest)
            if frame == frame_per_pose // 2:
                middle_frame = image_path
            cursor += 1
        views.append((pose, middle_frame))
        REPORT["clips"][pose] = {
            "status": "RENDERED_EXPERIMENTAL",
            "frames": frame_per_pose,
            "duration": frame_per_pose / FPS,
            "roles_modified": sorted(selected),
            "unique_frames": len(set(hashes)),
            "limitations": ["no IK, Path or source runtime equivalence",
                            "pose may require artwork redrawing or new viewing angle"],
        }
    REPORT["poses_video_bytes"] = encode(
        per_pose, RELEASE / "02-common-poses-rive-baked.mp4", FPS)
    REPORT["contact_sheet_bytes"] = contact_sheet(
        views, RELEASE / "03-common-poses-contact-sheet.png")
    REPORT["source_original_media_committed_to_git"] = False
    REPORT["all_release_files"] = sorted(p.name for p in RELEASE.iterdir() if p.is_file())
    REPORT["status"] = "PASS_EXPERIMENTAL_PREVIEW"

def finalize():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "prod009-result.json").write_text(
        json.dumps(REPORT, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# PROD-009 preview — acceptance release (research draft)",
        "",
        f"Result: **{REPORT['status']}**.",
        "",
        "All preview files, including game-derived video and texture-containing RML",
        "project archive, are attached ONLY to a DRAFT GitHub Release.",
        "",
        "Included preview clips are Rive CLI-rendered source-weighted mesh BAKES.",
        "The native Rig scaffold includes bone/mesh/skin structure but no",
        "converted native Rive animation timeline. Official .riv export was",
        "not attempted without a signed-in Rive publishing session.",
        "",
        "The eight common poses are automatic skeletal DEFORMATION EXPERIMENTS,",
        "not the game's poses, and are not claimed to be visually plausible.",
        "Spine original Runtime visual parity remains NOT_TESTED.",
        "",
        "Files: " + ", ".join(REPORT.get("all_release_files", [])),
        "",
        "No binary or media artifacts should be committed into Git history.",
    ]
    if REPORT.get("error"):
        lines += ["", "Error: " + str(REPORT["error"])]
    (OUT / "prod009-release-notes.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines), flush=True)

if __name__ == "__main__":
    try:
        process()
    except Exception as error:
        REPORT["status"] = "FAIL"
        REPORT["error"] = repr(error)
    finally:
        finalize()
    if REPORT["status"] != "PASS_EXPERIMENTAL_PREVIEW":
        sys.exit(1)

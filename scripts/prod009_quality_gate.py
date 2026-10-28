#!/usr/bin/env python3
"""Post-render audit of PROD-009 draft Release media.

This script inspects ACTUAL video frame pixels in the CI runner, as opposed to
trusting a frame count, file presence or a nominal render status.
No proprietary images or binaries are committed or printed into public logs.
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image

FPS = 24
ACTIONS = ("idle_room", "walk", "sleep", "hit")
POSES = ("neutral", "raise_hand", "wave", "bow", "lean_back", "squat", "sit", "prone")
EXPECTED = {
    "01-source-actions-rive-baked.mp4",
    "02-common-poses-rive-baked.mp4",
    "03-common-poses-contact-sheet.png",
    "04-prod009-metadata.json",
    "rive-native-rig-scaffold.zip",
}

def call(*argv):
    p = subprocess.run(argv, capture_output=True, text=True, check=True, timeout=90)
    return p.stdout

def probe(path: Path):
    data = json.loads(call("ffprobe", "-v", "error", "-select_streams", "v:0",
                           "-show_entries", "stream=width,height,avg_frame_rate,nb_frames",
                           "-show_entries", "format=duration", "-of", "json", str(path)))
    stream = data["streams"][0]
    return {
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "frame_rate": stream.get("avg_frame_rate"),
        "nb_frames": int(stream["nb_frames"]) if stream.get("nb_frames") else None,
        "duration": float(data["format"]["duration"]),
    }

def still_at(video: Path, frame_index: int):
    # Decode by index (not an approximate seek) to avoid mixing up neighboring poses.
    p = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(video),
         "-vf", "select=eq(n\\," + str(frame_index) + ")",
         "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
        capture_output=True, check=True, timeout=60)
    from io import BytesIO
    return Image.open(BytesIO(p.stdout)).convert("RGB")

def foreground_mask(image: Image.Image):
    arr = np.asarray(image, dtype=np.int16)
    # Generated clip canvas background is (30,33,43). Ignore the 70px title overlay.
    pixels = np.abs(arr - np.array([30, 33, 43], dtype=np.int16))
    mask = pixels.max(axis=2) > 38
    mask[:70, :] = False
    return mask

def visual_metrics(image: Image.Image):
    mask = foreground_mask(image)
    y, x = np.where(mask)
    area = int(mask.sum())
    denominator = (mask.shape[0]-70)*mask.shape[1]
    if area:
        bbox = [int(x.min()), int(y.min()), int(x.max()), int(y.max())]
        clip_edges = bool(x.min() <= 4 or
                          x.max() >= mask.shape[1]-5 or y.max() >= mask.shape[0]-5)
    else:
        bbox = None
        clip_edges = True
    return {"foreground_pixels": area, "foreground_fraction": round(area/denominator, 5),
            "bbox": bbox, "edge_touching": clip_edges}

def mask_iou(a, b):
    a = foreground_mask(a)
    b = foreground_mask(b)
    union = np.count_nonzero(a | b)
    return round(float(np.count_nonzero(a & b) / union), 5) if union else None

def main(folder: Path):
    findings, warnings, info = [], [], {}
    inventory = {p.name for p in folder.iterdir() if p.is_file()}
    missing = EXPECTED-inventory
    if missing: findings.append("MISSING_RELEASE_FILES: "+repr(sorted(missing)))
    if missing: return findings, warnings, info

    meta = json.loads((folder/"04-prod009-metadata.json").read_text("utf-8"))
    info["metadata_status"] = meta.get("status")
    info["source_bones"] = meta.get("source_bones")
    info["source_animations"] = meta.get("source_animations")
    info["converted_mesh_slots"] = meta.get("converted_mesh_slots")
    info["converted_vertices"] = meta.get("converted_vertices")
    info["bone_roles"] = meta.get("bone_roles")
    info["source_runtime_parity"] = meta.get("source_spine_runtime_parity")
    info["editable_native_rive_animations"] = meta.get("native_editable_rive_animations")

    if meta.get("source_bones") != 85:
        findings.append("BONE_COUNT_INCONSISTENT")
    if meta.get("converted_mesh_slots", 0) < 51:
        findings.append("SOURCE_MESH_COVERAGE_UNDER_BASELINE")
    if meta.get("native_editable_rive_animations") is False:
        findings.append("NATIVE_EDITABLE_ANIMATIONS_NOT_DELIVERED")
    if not meta.get("exported_riv"):
        findings.append("NO_EXPORTED_RIV")
    if meta.get("source_spine_runtime_parity") != "PASS":
        findings.append("SOURCE_SPINE_PARITY_NOT_ESTABLISHED")

    pose_roles = meta.get("bone_roles") or {}
    required_roles = {
        "raise_hand": ["left_arm"],
        "squat": ["left_thigh", "right_thigh", "left_shin", "right_shin"],
        "sit": ["left_thigh", "right_thigh", "left_shin", "right_shin"],
        "prone": ["torso"],
    }
    for pose, required in required_roles.items():
        declared = (meta.get("clips", {}).get(pose, {}) or {}).get("roles_modified") or []
        for role in required:
            if role not in declared:
                findings.append("UNCONTROLLED_JOINT:"+pose+":"+role)

    with zipfile.ZipFile(folder/"rive-native-rig-scaffold.zip") as archive:
        members=archive.namelist()
        info["rig_zip_entries"]=members[:15]
        rml=[n for n in members if n.endswith("scene.rml")]
        if not rml:
            findings.append("RIG_ARCHIVE_MISSING_RML")
        else:
            scene=ET.fromstring(archive.read(rml[0]))
            tag_counts={}
            for el in scene.iter():
                tag_counts[el.tag]=tag_counts.get(el.tag,0)+1
            info["rml_element_counts"]={x:tag_counts.get(x,0) for x in ("Bone","RootBone","Image","Mesh","Skin","Tendon","LinearAnimation","KeyFrame")}
            if not tag_counts.get("Mesh"): findings.append("RML_MISSING_MESH")
            if not tag_counts.get("Skin"): findings.append("RML_MISSING_SKIN")
            if not tag_counts.get("Bone") and not tag_counts.get("RootBone"): findings.append("RML_MISSING_BONES")
        if not any(n.lower().endswith(".png") for n in members):
            findings.append("RIG_ARCHIVE_MISSING_ATLAS")

    media = {
        "source": folder/"01-source-actions-rive-baked.mp4",
        "pose": folder/"02-common-poses-rive-baked.mp4",
    }
    for kind, path in media.items():
        d = probe(path)
        info[kind+"_video"] = d
        if (d["width"],d["height"]) != (960,540):
            findings.append("WRONG_VIDEO_RESOLUTION:"+kind)
        if not math.isclose(d["duration"],
                            (sum(int(meta["clips"][key]["frames"]) for key in ACTIONS) if kind=="source" else 8*48)/FPS,
                            abs_tol=.12):
            findings.append("VIDEO_DURATION_MISMATCH:"+kind)
        if d["nb_frames"] is not None:
            expected_frames=sum(int(meta["clips"][key]["frames"]) for key in ACTIONS) if kind=="source" else 8*48
            if d["nb_frames"] != expected_frames:
                findings.append("VIDEO_FRAME_COUNT_MISMATCH:"+kind)

    with Image.open(folder/"03-common-poses-contact-sheet.png") as contact:
        info["contact_sheet"]={"width":contact.width,"height":contact.height}
        if (contact.width, contact.height) != (1000,1240):
            findings.append("CONTACT_SHEET_UNEXPECTED_SIZE")

    # Sample exact frame positions: 3 shots per source action, 3 per pose.
    source_video=media["source"]
    cursor=0
    sample_report={}
    for action in ACTIONS:
        count=int(meta["clips"][action]["frames"])
        idxs=[cursor+max(0,int(count*ratio)) for ratio in (.15,.5,.80)]
        images=[still_at(source_video, ix) for ix in idxs]
        sample_report[action]={
            "sample_frame_indices":idxs,
            "sample_frames":[visual_metrics(im) for im in images],
            "first_middle_iou":mask_iou(images[0],images[1]),
        }
        cursor+=count

    pose_video=media["pose"]
    poses={}
    neutral_center=still_at(pose_video, 24)
    for index, pose in enumerate(POSES):
        idxs=[index*48+8,index*48+24,index*48+40]
        images=[still_at(pose_video, ix) for ix in idxs]
        poses[pose]={
            "sample_frame_indices":idxs,
            "sample_frames":[visual_metrics(im) for im in images],
            "pose_neutral_iou":mask_iou(neutral_center, images[1]),
            "motion_sample_iou":mask_iou(images[0], images[1]),
        }
        if pose != "neutral" and poses[pose]["pose_neutral_iou"] is not None and poses[pose]["pose_neutral_iou"] > .985:
            findings.append("POSE_INDISTINGUISHABLE_FROM_NEUTRAL:"+pose)

    info["action_samples"]=sample_report
    info["pose_samples"]=poses
    # Emit only heavily downsampled *shape diagnostics* (no texture/pixel blobs)
    # and numeric measurements to allow independent reviewer checks from CI logs.
    # This is NOT a substitute for viewing the full-resolution video.
    print("FRAME_SAMPLE_SUMMARY_BEGIN",flush=True)
    for label, dataset in (("action", sample_report), ("pose", poses)):
        for name, result in dataset.items():
            print(label, name,
                  "bbox_mid", result["sample_frames"][1]["bbox"],
                  "foreground_mid",result["sample_frames"][1]["foreground_fraction"],
                  "near_neutral_iou",result.get("pose_neutral_iou"),
                  "motion_iou",result.get("motion_sample_iou",result.get("first_middle_iou")),
                  flush=True)
    print("FRAME_SAMPLE_SUMMARY_END",flush=True)
    print("POSE_SILHOUETTES_COARSE_START",flush=True)
    for idx, pose in enumerate(POSES):
        middle=still_at(pose_video,idx*48+24)
        mask=foreground_mask(middle).astype(np.uint8)*255
        small=np.asarray(Image.fromarray(mask).resize((32,16),Image.Resampling.BOX))
        print("POSE",pose,flush=True)
        for row in small:
            print("".join("#" if cell>=45 else "." for cell in row),flush=True)
    print("POSE_SILHOUETTES_COARSE_END",flush=True)
    for name, result in {**sample_report,**poses}.items():
        sampled=result["sample_frames"]
        for frame in sampled:
            if frame["foreground_fraction"] < .02:
                findings.append("CHARACTER_MOSTLY_MISSING:"+name)
                break
            if frame["foreground_fraction"] > .80:
                findings.append("WHOLE_FRAME_FOREGROUND:"+name)
                break
            if frame["edge_touching"]:
                findings.append("CHARACTER_CROPPED_AT_VIEWPORT:"+name)
                break

    warnings.append("Top-edge cropping is not assessed: title overlay masks the top 70px of frames.")
    warnings.append("Automated pixel sampling cannot establish anatomical plausibility or visual quality.")
    warnings.append("PROD-009 pose generation lacks IK, contact and pose-specific re-art; visual review remains NOT_TESTED.")
    warnings.append("No direct comparison against authoritative Spine Runtime frames.")
    return sorted(set(findings)),sorted(set(warnings)),info

if __name__=="__main__":
    folder=Path(sys.argv[1])
    destination=Path(sys.argv[2])
    destination.mkdir(parents=True,exist_ok=True)
    try:
        findings,warnings,info=main(folder)
        result={"audit":"PROD-009-INDEPENDENT-AUDIT",
                "status":"FAIL_PRODUCTION_QUALITY" if findings else "BLOCKED_VISUAL_REVIEW",
                "production_gate":"FAIL",
                "anatomical_pose_validity":"NOT_TESTED",
                "frame_samples_per_clip":3,
                "findings":findings,"warnings":warnings,"measurements":info}
    except Exception as exc:
        result={"audit":"PROD-009-INDEPENDENT-AUDIT",
                "status":"AUDIT_ERROR","production_gate":"FAIL","error":repr(exc)}
    (destination/"05-prod009-independent-audit.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    lines=["# PROD-009 Independent Preview Audit", "",
           "**Status: "+result["status"]+"**", "",
           "This is a strict QA gate. Passing FFmpeg, file existence and file counts alone does not imply a usable character animation.",
           "", "## Blocking findings"]
    lines.extend("- "+item for item in result.get("findings",["Audit could not complete"]))
    lines += ["", "## Warnings"]
    lines.extend("- "+item for item in result.get("warnings",[]))
    lines += ["", "Full numerical frame sampling and per-pose results: 05-prod009-independent-audit.json."]
    (destination/"05-prod009-independent-audit.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines),flush=True)
    print("Audit report file:",destination/"05-prod009-independent-audit.json")

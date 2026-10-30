#!/usr/bin/env python3
"""Fail-closed CORE-014 artifact QA for generated view skin.

The real MP4 and user image binaries are local chat artifacts, not in GitHub;
this asserts metadata does NOT silently promote them to native INX bindings.
"""
from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path

def validate(meta:dict):
    assert meta["schema"] == "koma-core014-partwise-qa/1"
    assert meta["stage"] == "EXECUTED_LOCALLY_WITH_ACTUAL_USER_IMAGES"
    r=meta["result"];s=meta["source_native_model"]
    assert r["frames"]==97 and r["fps"]==24 and r["dimensions"]==[1080,588]
    assert r["final_mp4_decoded_frames"]==[0,12,24,36,48,60,72,84,96]
    assert len(r["video_sha256"])==64
    assert r["angle_45"].startswith("FAILED") and r["angle_135"].startswith("FAILED")
    assert r["native_inx_artmesh_uv_reused"] is False
    assert r["native_inx_animation_replayed"] is False
    assert r["shallow_z_surface"] is False
    assert r["acquired_true_new_45_art"] is False
    assert r["acquired_true_new_135_art"] is False
    assert r["anime_visual_quality"]=="FAIL"
    assert s["mesh_count"]==76 and s["total_vertices"]==3427 and s["total_triangles"]==5353
    assert s["source_uv_original_untouched"] is True
    assert s["registered_to_generated_45_or_135"] is False
    assert len(meta["next_required_parts"])>=5
    for k,v in meta["input"].items():
        assert len(v["sha256"])==64,(k,"missing SHA256")
    return {"checked":"metadata_only_no_binary_MP4_processed",
            "visual_result":"FAIL",
            "source_uv_registered":False,
            "missing_independent_45_135_art":True}
if __name__ == "__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--manifest",type=Path,required=True)
    args=a.parse_args()
    print("CORE014_NEGATIVE_GATES_PASS",json.dumps(validate(json.loads(args.manifest.read_text()))))

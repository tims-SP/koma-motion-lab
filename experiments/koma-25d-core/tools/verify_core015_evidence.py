#!/usr/bin/env python3
"""CORE015 metadata-policy verifier. NOT an actual remote 3D render test."""
from pathlib import Path
import argparse,json,math
a=argparse.ArgumentParser()
a.add_argument("--manifest",type=Path,required=True)
x=a.parse_args()
d=json.loads(x.manifest.read_text())
assert d["schema"]=="koma-core015-real-z-evidence/1"
assert d["stage"]=="REAL_LOCAL_3D_MESH_RENDER_NOT_ORIGINAL_INX"
assert sum(v["vertices"] for v in d["meshes"])==d["total_vertices"]==8750
assert sum(v["triangles"] for v in d["meshes"])==d["total_triangles"]==14753
assert len(d["meshes"])==5
assert d["actual_3d_positions"] and d["actual_zbuffer_depth_test"]
assert d["exported_glb_is_real_3d"]
assert d["original_inx_native_artmesh_uv_reused"] is False
assert d["original_inx_rig_parameters_replayed"] is False
assert d["generated_new_true_45_or_135_art"] is False
assert d["source_pose_physical_degrees_calibrated"] is False
assert d["production_accepted"] is False
v=d["video"]
assert v["frames"]==97 and v["fps"]==24
assert v["width"]==520 and v["height"]==560
assert v["actual_decoded_samples"]==[0,12,24,36,48,60,72,84,96]
assert v["quality"]=="FAILED_DIRECT_VISUAL_AUDIT"
assert v["execution"]=="LOCAL_SANDBOX_NOT_GITHUB_ACTIONS"
for k in ("debug","missing_overlay"):
    assert len(v[k]["sha256"])==64
for angle in ("yaw_45","yaw_135"):
    m=d["source_coverage_diagnostic"][angle]
    err=abs(m["unpainted_pixels"]/m["geometry_pixels"]-m["unpainted_fraction"])
    assert err<=.0001
print("CORE015_POLICY_PASS_METADATA_ONLY: genuine 3D local, INX UV and 45/135 art are missing, anime QA FAIL")

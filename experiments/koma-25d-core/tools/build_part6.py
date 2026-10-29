#!/usr/bin/env python3
"""CORE-006: adapt a real licensed 2D art rig into independent part-shells.

Retain original 2D source triangle indices, screen XY coordinates, alpha
texture and UV exactly. Only ADD local, partially closed head/arm side
proxies, explicitly marked UNPAINTED; bones and weights are reused verbatim.
No background pixels are "invented" as hidden anime art.
"""
from __future__ import annotations
import json,math,hashlib,argparse
from pathlib import Path

PARTS={"Head":0.55,"Chin":0.18,"RightArm":0.30,"LeftArm":0.30}
def digest(obj):
    return hashlib.sha256(json.dumps(obj,separators=(",",":"),sort_keys=True).encode()).hexdigest()

def run(folder:Path):
    p=folder/"character.json"
    model=json.loads(p.read_text(encoding="utf-8"))
    if model["source"]!="Godot Skeleton2D GBot MIT":raise ValueError("unexpected asset source")
    audit={}
    for mesh in model["meshes"]:
        name=mesh["name"]
        uv_before=digest(mesh["uv"])
        triangles_before=digest(mesh["indices"])
        weights_before=digest([mesh["skinIndex"],mesh["skinWeight"]])
        # Do not displace source artwork along Z: source front is a literal
        # frontal plane; it is rendered unchanged at zero yaw.
        for vertex in mesh["vertices"]:
            vertex[2]=0.
        if name in PARTS:
            shell=mesh["shell"]
            n=len(mesh["vertices"])
            zsize=PARTS[name]
            for i in range(n):
                shell["vertices"][i][:]=mesh["vertices"][i][:]
                shell["vertices"][i+n][:]=mesh["vertices"][i][:]
                shell["vertices"][i+n][2]=-zsize
            # Side UV is simply normalized from original mesh height and
            # shell depth. It's unregistered; the test canary is explicit.
            miny=min(v[1] for v in shell["vertices"])
            maxy=max(v[1] for v in shell["vertices"])
            h=max(maxy-miny,1e-5)
            shell["sideUv"]=[[min(1.,max(0.,-v[2]/zsize)),
                              min(1.,max(0.,(v[1]-miny)/h))]
                              for v in shell["vertices"]]
            mesh["partShellStatus"]="REAL_SOURCE_UV_FRONT_SYNTHETIC_SIDE_PROXY"
            mesh["partShellThickness"]=zsize
            mesh["sideSurfaceEnabled"]=True
        else:
            # Keep the original 2D art only; no thickened low-quality body
            # proxy should leak into the scene when the head turns.
            mesh["partShellStatus"]="SOURCE_ARTMESH_ONLY"
            mesh["sideSurfaceEnabled"]=False
        audit[name]={
            "uv_unchanged":uv_before==digest(mesh["uv"]),
            "indices_unchanged":triangles_before==digest(mesh["indices"]),
            "weights_unchanged":weights_before==digest([mesh["skinIndex"],mesh["skinWeight"]]),
            "shell_enabled":mesh["sideSurfaceEnabled"],
            "source_vertices":len(mesh["vertices"]),
            "front_z_exactly_zero":all(v[2]==0. for v in mesh["vertices"])
        }
        if not all(audit[name][k] for k in ("uv_unchanged","indices_unchanged","weights_unchanged","front_z_exactly_zero")):
            raise AssertionError("Original ArtMesh corrupted: "+name)
    model["schema"]="koma-25d-pilot/6"
    model["head_elbow_experiment"]={
        "implemented":"source_2d_uv_and_per-part_shallow_proxy",
        "source_2d_rig":"Godot GBot, MIT",
        "part_shells":PARTS,
        "source_front_texture":"gBot.png",
        "side_back_artwork":"MISSING_DIAGNOSTIC_CANARY",
        "head_and_arm_source_triangles_uv_weights":"PRESERVED",
        "animation_3d_parity":"NOT_ACCEPTED",
        "native_godot_appearance_parity":"NOT_TESTED",
        "joint_collision":"NOT_TESTED"
    }
    p.write_text(json.dumps(model,separators=(",",":")),encoding="utf-8")
    report={
       "status":"PART_ARTMESH_PAYLOAD_INTEGRITY_PASS",
       "source":"MIT Godot Skeleton2D GBot original data",
       "part_shells":list(PARTS),"art_uv_triangle_weight_checks":audit,
       "art_quality":"NOT_ACCEPTED","3d_skinning_accuracy":"NOT_TESTED",
       "native_2d_renderer_parity":"NOT_TESTED"
    }
    (folder/"part006.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("CORE006_PART_STRUCTURE",json.dumps(report))
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--asset-dir",type=Path,default=Path("viewer/public/asset"))
    a=ap.parse_args()
    run(a.asset_dir)

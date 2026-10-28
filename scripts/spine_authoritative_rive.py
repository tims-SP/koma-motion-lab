#!/usr/bin/env python3
"""Rive native Skin setup-rest audit against official Spine 4.2 geometry.

This probes the native Rive Bone/Mesh/Skin in Rive CLI. Unlike PROD-009
video baking, the test NEVER removes Skin for the main reference render.
All source art, RML and screenshots remain in ephemeral CI runner.
"""
from __future__ import annotations
import copy,json,math,os,shutil,sys
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
import spine_textured_rive as src

ROOT=src.ROOT
OUT=src.OUT
REPORT={"experiment":"PROD-010-native-rive-skin","status":"NOT_TESTED",
        "spine_runtime_reference":"4.2.120",
        "original_game_media_committed":False}
def compare_images(a,b):
    with Image.open(a) as A, Image.open(b) as B:
        pa=A.convert("RGBA");pb=B.convert("RGBA")
        if pa.size!=pb.size:raise RuntimeError("native/unskinned render sizes differ")
        d1=pa.tobytes();d2=pb.tobytes()
    corner1=d1[:4];corner2=d2[:4]
    both=union=changed=0
    delta=0
    for i in range(0,len(d1),4):
        vis1=d1[i:i+4]!=corner1
        vis2=d2[i:i+4]!=corner2
        if vis1 and vis2:both+=1
        if vis1 or vis2:
            union+=1
            diffs=[abs(d1[i+j]-d2[i+j]) for j in range(4)]
            delta+=sum(diffs)
            changed+=any(v>8 for v in diffs)
    return {"native_unskinned_mask_iou":both/max(1,union),
            "rgba_mean_abs_difference":delta/max(1,4*union),
            "changed_foreground_fraction":changed/max(1,union),
            "native_unskinned_union_pixels":union}

def main():
    official=json.loads((ROOT/"spine-official-world-vertices.json").read_text())
    shutil.rmtree(ROOT/"source-mesh-rive",ignore_errors=True)
    tree,project,bones,objects,doc,imported=src.construct()
    active=official["mesh"]
    mapped=0;old_sq=0;old_max=uv_max=0;coordinate_count=0
    for image in tree.getroot().iter("Image"):
        name=image.get("name","")
        if not name.startswith("src_"):continue
        slot=name[4:]
        ref=active.get(slot)
        if ref is None:raise RuntimeError("Active source slot missing official Spine geometry: "+slot)
        mesh=next((x for x in image if x.tag=="Mesh"),None)
        if mesh is None:raise RuntimeError("Missing Rive Mesh for "+slot)
        verts=mesh.findall("ContourMeshVertex")
        reference=ref["vertices"]
        uv=ref["uvs"]
        if len(verts)*2!=len(reference) or len(uv)!=len(reference):
            raise RuntimeError("UV/vertices length mismatch "+slot)
        for i,v in enumerate(verts):
            x=float(v.get("x"));y=float(v.get("y"))
            tx=float(reference[2*i]);ty=float(reference[2*i+1])
            errors=(x-tx,y-ty)
            old_sq+=sum(e*e for e in errors)
            old_max=max(old_max,*(abs(e) for e in errors))
            uv_max=max(uv_max,abs(float(v.get("u"))-uv[2*i]),
                       abs(float(v.get("v"))-uv[2*i+1]))
            v.set("x",f"{tx:.9g}")
            v.set("y",f"{ty:.9g}")
            coordinate_count+=2
        mapped+=1
    REPORT.update({"native_rive_bones":sum(1 for el in tree.getroot().iter()
                                           if el.tag in ("Bone","RootBone")),
        "native_rive_skins":sum(1 for _ in tree.getroot().iter("Skin")),
        "meshes_anchored_to_official_reference":mapped,
        "total_anchored_vertex_coordinates":coordinate_count,
        "previous_python_setup_geometry_rms_error":math.sqrt(old_sq/max(1,coordinate_count)),
        "previous_python_setup_geometry_max_error":old_max,
        "atlas_uv_max_error_vs_official":uv_max,
        "still_missing_source_constraints":["IK","Transform","Path","inherit scale/shear"]})
    if mapped!=len(active) or uv_max>1e-5:
        raise RuntimeError("Source UV or mesh coverage not even at official setup")
    tree.write(project/"scene.rml",encoding="unicode")
    src.run(["rive",str(project),"--verify"])
    native=ROOT/"native-referenced-setup.png"
    src.run(["rive",str(project),f"--screenshot={native}",
             "--viewport=640x360","--advance=0s"])
    unskinned_tree=copy.deepcopy(tree)
    root=unskinned_tree.getroot()
    for mesh in root.iter("Mesh"):
        for skin in list(mesh.findall("Skin")):mesh.remove(skin)
        for vertex in mesh.findall("ContourMeshVertex"):
            for weight in list(vertex.findall("Weight")):vertex.remove(weight)
    unskinned_tree.write(project/"scene.rml",encoding="unicode")
    unskinned=ROOT/"unskinned-referenced-setup.png"
    src.run(["rive",str(project),f"--screenshot={unskinned}",
             "--viewport=640x360","--advance=0s"])
    REPORT.update(compare_images(native,unskinned))
    REPORT["status"]=("PASS_NATIVE_SETUP" if
        REPORT["native_unskinned_mask_iou"]>=.99 and
        REPORT["changed_foreground_fraction"]<=.05
        else "FAIL_NATIVE_SKIN_SETUP")
    # Main project scene must remain native Skin, not the diagnostic no-skin copy.
    tree.write(project/"scene.rml",encoding="unicode")
def finish():
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"prod010-native-skin-check.json").write_text(
        json.dumps(REPORT,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(REPORT,ensure_ascii=False,indent=2),flush=True)
if __name__=="__main__":
    try:main()
    except Exception as error:
        REPORT["status"]="FAIL"
        REPORT["error"]=repr(error)
    finish()
    if REPORT["status"]!="PASS_NATIVE_SETUP":sys.exit(1)

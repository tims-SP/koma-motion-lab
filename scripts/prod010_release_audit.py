#!/usr/bin/env python3
"""Independent audit of delivered PROD-010 DRAFT Release assets.

Runs in a fresh GitHub Actions job, downloads existing Release files, and
rechecks actual images and RML ZIP; not the generating runner's working tree.
This is strictly an isolated native Skin setup/one-Bone poke test.
"""
import json,sys,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

EXPECTED={"native-referenced-setup.png","unskinned-referenced-setup.png",
          "native-skin-bone-poked.png","unskinned-bone-poked.png",
          "native-skin-rml-project.zip","05-rig-skin-diagnostics.json"}

def diff(a,b):
    with Image.open(a) as im1, Image.open(b) as im2:
        x=im1.convert("RGBA");y=im2.convert("RGBA")
        if x.size!=y.size or x.size!=(640,360):
            raise AssertionError("Unexpected source image dimensions")
        rawx=x.tobytes();rawy=y.tobytes()
    bgx=rawx[:4];bgy=rawy[:4]
    intersection=union=changed=0
    for i in range(0,len(rawx),4):
        xvis=rawx[i:i+4]!=bgx
        yvis=rawy[i:i+4]!=bgy
        intersection+=bool(xvis and yvis)
        if xvis or yvis:
            union+=1
            changed+=any(abs(rawx[i+j]-rawy[i+j])>8 for j in range(4))
    return {"mask_iou":intersection/max(1,union),
            "changed_foreground_fraction":changed/max(1,union),
            "union_foreground_pixels":union}

def main(folder:Path):
    report={"stage":"PROD-010-INDEPENDENT-RELEASE-RECHECK",
            "gate":"NOT_TESTED","full_spine_animation_parity":"NOT_TESTED",
            "editable_rive_animation":"NOT_DELIVERED",
            "independently_verified_bones":"ONE_POKED_BONE_ONLY",
            "findings":[]}
    missing=EXPECTED-{p.name for p in folder.iterdir() if p.is_file()}
    if missing:
        report["findings"].append("MISSING_RELEASE_ASSETS:"+str(sorted(missing)))
        return report
    original=json.loads((folder/"05-rig-skin-diagnostics.json").read_text())
    if original.get("status")!="PASS_NATIVE_SETUP_AND_BONE_POKE":
        report["findings"].append("INVALID_SOURCE_TEST_RESULT")
    if original.get("meshes_anchored_to_official_reference")!=51:
        report["findings"].append("INCOMPLETE_SETUP_MESH_COVERAGE")
    if original.get("atlas_uv_max_error_vs_official",1)>1e-5:
        report["findings"].append("ATLAS_UV_MISMATCH")
    archive=folder/"native-skin-rml-project.zip"
    with zipfile.ZipFile(archive) as z:
        members=set(z.namelist())
        if "scene.rml" not in members or not any(n.endswith(".png") for n in members):
            report["findings"].append("MISSING_RML_OR_ATLAS_IN_DELIVERED_ZIP")
        else:
            root=ET.fromstring(z.read("scene.rml"))
            tags={}
            for e in root.iter():tags[e.tag]=tags.get(e.tag,0)+1
            report["delivered_rml_nodes"]={k:tags.get(k,0) for k in (
                "Bone","RootBone","Skin","Tendon","Mesh","Image","ContourMeshVertex","Weight")}
            if tags.get("Skin")!=51 or tags.get("Mesh")!=51 or tags.get("Tendon",0)<51:
                report["findings"].append("NOT_ALL_NATIVE_SKINS_IN_DELIVERED_RML")
            if tags.get("Weight")!=843 or tags.get("ContourMeshVertex")!=843:
                report["findings"].append("MISSING_MESH_VERTEX_BINDING")
            if tags.get("Bone",0)+tags.get("RootBone",0)<85:
                report["findings"].append("BONE_HIERARCHY_INCOMPLETE")
    comparisons={
        "skin_vs_unskinned_at_rest":("native-referenced-setup.png","unskinned-referenced-setup.png"),
        "poked_native_vs_rest":("native-skin-bone-poked.png","native-referenced-setup.png"),
        "poked_unskinned_vs_rest":("unskinned-bone-poked.png","unskinned-referenced-setup.png")
    }
    report["delivered_image_differences"]={
        key:diff(folder/a,folder/b) for key,(a,b) in comparisons.items()}
    rest=report["delivered_image_differences"]["skin_vs_unskinned_at_rest"]
    poke=report["delivered_image_differences"]["poked_native_vs_rest"]
    control=report["delivered_image_differences"]["poked_unskinned_vs_rest"]
    if rest["mask_iou"]<.99 or rest["changed_foreground_fraction"]>.05:
        report["findings"].append("STATIC_SKIN_DIFFERS_FROM_UNSKINNED")
    if poke["changed_foreground_fraction"]<=.01:
        report["findings"].append("SKIN_DID_NOT_RESPOND_TO_BONE_ROTATION")
    if control["changed_foreground_fraction"]>=.001:
        report["findings"].append("POKE_CHANGED_UNSKINNED_CONTROL")
    report["gate"]="PASS_DRAFT_SETUP_PROOF_ONLY" if not report["findings"] else "FAIL_DELIVERED_PROOF"
    return report

if __name__=="__main__":
    folder=Path(sys.argv[1]);target=Path(sys.argv[2])
    target.mkdir(parents=True,exist_ok=True)
    try:
        report=main(folder)
    except Exception as e:
        report={"stage":"PROD-010-INDEPENDENT-RELEASE-RECHECK",
                "gate":"ERROR","findings":[repr(e)]}
    (target/"06-independent-release-recheck.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(report,indent=2,ensure_ascii=False),flush=True)
    if report["gate"]!="PASS_DRAFT_SETUP_PROOF_ONLY":
        sys.exit(1)

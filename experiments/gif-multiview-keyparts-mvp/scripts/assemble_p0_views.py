#!/usr/bin/env python3
"""Assemble P0 0/45/90 source-faithful independent RGBA ArtMeshes for HTML/VDD.

This composes the P1 front and P2 quarter/profile *candidate* manifests, retains
the original recovered asset versions, and validates 39 anatomical registrations
and mesh topology correspondence. Artistic interpolation acceptance is separate.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

ANGLES=(0,45,90)
SEMANTIC=("body.reference","hair.back","face.skin","ear.far","ear.near",
          "hair.side","eye.far","eye.near","nose","mouth","hair.front",
          "hair.ahoge","hair.clip.cross_gold")
ROOT=Path(__file__).resolve().parents[1]

def hashfile(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for z in iter(lambda:f.read(1024*1024),b""):
            h.update(z)
    return h.hexdigest()

def load(path):
    return json.loads(Path(path).read_text(encoding="utf8"))

def assemble(root):
    root=Path(root).resolve()
    front=load(root/"p1-front/parts.json")
    angles=load(root/"p2-views/parts.json")
    if front.get("characterId")!="p0_character_001" or angles.get("characterId")!="p0_character_001":
        raise ValueError("P0 identity not matched")
    registered=front["parts"]+angles["parts"]
    byslot={(p["yawDeg"],p["semanticId"]):p for p in registered}
    if len(registered)!=39 or len(byslot)!=39:
        raise ValueError("3×13 unique part slots required")
    checked=[]
    for y in ANGLES:
        for sid in SEMANTIC:
            key=(y,sid)
            if key not in byslot:raise ValueError("missing "+str(key))
            p=byslot[key]
            image_path=root/p["path"]
            if not image_path.is_file() or hashfile(image_path)!=p["frameSha256"]:
                raise ValueError("bad sha "+str(key))
            with Image.open(image_path) as im:
                if im.format!="PNG" or im.mode!="RGBA" or im.size!=(1024,1024):
                    raise ValueError("not global RGBA "+str(key))
            mesh=p["mesh"]
            if len(mesh["vertexIds"])!=49 or len(mesh["triangles"])!=72:
                raise ValueError("geometry missing "+str(key))
            checked.append(str(key))
    for sid in SEMANTIC:
        values=[byslot[(y,sid)]["mesh"] for y in ANGLES]
        if len({json.dumps(v["vertexIds"]) for v in values})!=1 or \
           len({json.dumps(v["triangles"]) for v in values})!=1:
            raise ValueError("mesh topology mismatch "+sid)
    expected_hidden={(45,"ear.far"),(90,"ear.far"),(90,"eye.far"),
                     (90,"hair.clip.cross_gold")}
    for key in expected_hidden:
        if byslot[key].get("visibility")!="hidden":
            raise ValueError("incorrect occlusion "+str(key))
    for key in ((0,"eye.near"),(0,"eye.far"),(45,"eye.near"),(45,"eye.far"),
                (45,"hair.clip.cross_gold"),(90,"eye.near")):
        if byslot[key].get("visibility")!="visible":
            raise ValueError("visible anatomy missing "+str(key))
    refs=[]
    for yaw in ANGLES:
        if yaw==0:
            file=root/"p1-front/diagnostics/front-reference.png"
        else:
            file=root/f"p2-views/whole/yaw{yaw:03d}.png"
        with Image.open(file) as im:
            if im.mode!="RGBA" or im.size!=(1024,1024):
                raise ValueError("bad source reference "+str(yaw))
        refs.append({"yawDeg":yaw,"path":str(file.relative_to(root)),
                     "sha256":hashfile(file)})
    previous_manifest=root/"parts.json"
    previous_qa=root/"qa.json"
    former=root/"candidate-v2"
    if previous_manifest.is_file():
        target=former/"archived-root-candidate-parts.json"
        if not target.is_file():target.write_bytes(previous_manifest.read_bytes())
    if previous_qa.is_file():
        target=former/"archived-root-candidate-qa.json"
        if not target.is_file():target.write_bytes(previous_qa.read_bytes())
    doc={"schema":"KOMA-P0-ARTMESH-MANIFEST-V1",
         "characterId":"p0_character_001","canvas":[1024,1024],
         "wholeViews":refs,"parts":registered,
         "headRois":{str(y):[0,0,1024,800] for y in ANGLES},
         "sourceStatus":"VERIFIED_GIF_DERIVED_SEMANTIC_ARTMESH_CANDIDATE",
         "sourcePixelReference":"independent_angle_original_drawn_GIF",
         "meshCorrespondenceStatus":"49_vertices_72_triangles_stable_ids",
         "sourceApprovedHeroSHAverified":False,
         "visualApproval":"PENDING_VIEW_DEPENDENT_DEFORMATION_ART",
         "authoredOccludedGeometrySource":"Recovered 15 + 9 independent part GIFs"}
    (root/"parts.json").write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    qa={"schema":"KOMA-P0-VDD-39ARTMESH-REGISTRY-QA-V1","characterId":"p0_character_001",
        "status":"REVIEW_CANDIDATE",
        "partRegistrations":len(checked),"viewAngles":list(ANGLES),
        "verifiedSourceFrames":len(refs),
        "geometry":"49_vertices_72_triangles_per_mesh",
        "sourceRole":"Genuine P0 recovered original GIF pixels + registered underpaint",
        "occlusion90Clip":"hidden",
        "SHA256AdmissionPassed":True,
        "independentPartArtReview":"PENDING",
        "intermediateViewVDDVisualReview":"PENDING",
        "originalApprovedHeroSHAverified":False}
    (root/"qa.json").write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    dest=root/"p2-views/assembled-view-registry-qa.json"
    dest.write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps(qa,ensure_ascii=False,indent=2))
    return qa

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True)
    args=p.parse_args()
    assemble(args.root)

#!/usr/bin/env python3
"""Register supplied view-specific art WITHOUT silently trusting its quality.

Input registration JSON schema:
{
 "schema": "koma-view-uv-registration/1",
 "meshes": {
   "<name>": {
     "sideUv": [[u,v], ...],  // length == shell vertex count
     "backUv": [[u,v], ...]   // length == shell vertex count
   }
 }
}

Each side/back PNG must be supplied separately. Correspondences are authored
or produced by an external registration algorithm; this tool validates shape,
hash and domain but DOES NOT solve the mapping or certify anime quality.
"""
from __future__ import annotations
import argparse, hashlib, json, math, shutil
from pathlib import Path
from PIL import Image

def check_uv(points, num, name):
    if not isinstance(points,list) or len(points)!=num:
        raise ValueError(f"{name}: {len(points) if isinstance(points,list) else 'non-list'} UVs, expected {num}")
    for idx, p in enumerate(points):
        if not isinstance(p,list) or len(p)!=2:
            raise ValueError(f"{name}[{idx}] not a float pair")
        if not all(isinstance(x,(int,float)) and math.isfinite(x) and 0<=x<=1 for x in p):
            raise ValueError(f"{name}[{idx}] has non-normalized or nonfinite UV")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(asset_dir, side, back, registration):
    asset_dir=Path(asset_dir).resolve()
    side=Path(side).resolve()
    back=Path(back).resolve()
    registration=Path(registration).resolve()
    model_path=asset_dir/"character.json"
    model=json.loads(model_path.read_text(encoding="utf-8"))
    reg=json.loads(registration.read_text(encoding="utf-8"))
    if reg.get("schema")!="koma-view-uv-registration/1":
        raise ValueError("Unknown view registration schema")
    mapping=reg.get("meshes")
    if not isinstance(mapping,dict):raise ValueError("Registration meshes object missing")
    actual={m["name"] for m in model["meshes"]}
    if actual!=set(mapping):raise ValueError(f"Mesh correspondence mismatch: {actual ^ set(mapping)}")
    for mesh in model["meshes"]:
        key=mesh["name"]
        n=len(mesh["shell"]["vertices"])
        for view in ("side","back"):
            field=view+"Uv"
            check_uv(mapping[key].get(field),n,key+"."+field)
            mesh["shell"][field]=mapping[key][field]
    for path in (side,back):
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            if im.format!="PNG" or im.width<16 or im.height<16:
                raise ValueError("Expected PNG image of at least 16x16")
    if side==back:raise ValueError("Side and back views must be supplied independently")
    if side.parent==asset_dir and side.name=="side.png":
        pass
    else:shutil.copyfile(side,asset_dir/"side.png")
    if back.parent==asset_dir and back.name=="back.png":
        pass
    else:shutil.copyfile(back,asset_dir/"back.png")
    views={
      "schema":"koma-multiview/1",
      "front":{"texture":"gBot.png","provenance":"ORIGINAL_SOURCE_ART","uv":"source_artmesh"},
      "side":{"texture":"side.png","provenance":"REGISTERED_UNREVIEWED","uv":"per_mesh_explicit_correspondences"},
      "back":{"texture":"back.png","provenance":"REGISTERED_UNREVIEWED","uv":"per_mesh_explicit_correspondences"},
      "production_accepted":False,
      "registry":{"source_model_sha256":sha(model_path),"side_sha256":sha(asset_dir/"side.png"),
                  "back_sha256":sha(asset_dir/"back.png"),"mapping_sha256":sha(registration)},
      "warnings":["Registered art has not been quality accepted",
                  "UV registration validation does not establish semantic art correspondence",
                  "Per-mesh side silhouette may still be geometrically wrong",
                  "No automatic hidden-surface synthesis occurs"]
    }
    model["view_registration"]="REGISTERED_UNREVIEWED"
    model["back_side_artwork"]="SUPPLIED_UNREVIEWED"
    model_path.write_text(json.dumps(model,separators=(",",":")),encoding="utf-8")
    (asset_dir/"appearance.json").write_text(json.dumps(views,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"REGISTERED_UNREVIEWED","mesh_count":len(model["meshes"]),
                      "side_sha256":views["registry"]["side_sha256"],"back_sha256":views["registry"]["back_sha256"]},indent=2))

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--asset-dir",required=True,type=Path)
    cli.add_argument("--side-image",required=True,type=Path)
    cli.add_argument("--back-image",required=True,type=Path)
    cli.add_argument("--registration",required=True,type=Path)
    args=cli.parse_args()
    run(args.asset_dir,args.side_image,args.back_image,args.registration)

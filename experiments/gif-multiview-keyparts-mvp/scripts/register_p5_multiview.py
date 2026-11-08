#!/usr/bin/env python3
"""Construct the P0 0/45 PSD-inferred + 90 original ArtMesh preview registry."""
import argparse,copy,hashlib,json
from pathlib import Path
from PIL import Image

def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()

def create(root,out):
 root=Path(root).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
 manifest=json.loads((root/"parts.json").read_text())
 original=manifest["parts"]
 assert manifest["characterId"]=="p0_character_001" and len(original)==39
 sources={
  0:root/"p4-see-through/front/integrated/integrated-parts.json",
  45:root/"p5-see-through/yaw045/integrated/parts.json"
 }
 maps={}
 for yaw,f in sources.items():
  doc=json.loads(f.read_text())
  assert doc["characterId"]=="p0_character_001" and len(doc["parts"])==13
  maps[yaw]={p["semanticId"]:p for p in doc["parts"]}
  assert len(maps[yaw])==13
 registered=[]
 for entry in original:
  yaw=entry["yawDeg"];sid=entry["semanticId"]
  item=copy.deepcopy(entry)
  if yaw in maps:
   donor=maps[yaw][sid]
   image_path=(sources[yaw].parent/donor["path"]).resolve()
   assert image_path.is_relative_to(root)
   assert donor["frameSha256"]==sha(image_path)
   with Image.open(image_path) as image:
    assert image.mode=="RGBA" and image.size==(1024,1024)
   assert entry["mesh"]["vertexIds"]==donor["mesh"]["vertexIds"]
   assert entry["mesh"]["triangles"]==donor["mesh"]["triangles"]
   assert entry["visibility"]==donor["visibility"]
   item.update({
    "path":str(image_path.relative_to(root)),
    "frameSha256":donor["frameSha256"],
    "modelInpaintSource":"See-through semantic PSD",
    "inferredTextureSHA256":donor.get("PSDSourceSHA256",
                         donor.get("modelPSDSHA256")),
    "provenance":"P0 recovered original visible pixels plus PSD inferred hidden pixels",
    "visualReviewed":False
   })
  if sha(root/item["path"])!=item["frameSha256"]:
   raise ValueError("Registered layer SHA mismatch "+str((yaw,sid)))
  registered.append(item)
 assert len({(p["yawDeg"],p["semanticId"]) for p in registered})==39
 manifest["parts"]=registered
 manifest.update({
  "sourceStatus":"P0_TWO_VIEW_PSD_INFILL_VISUAL_REVIEW",
  "PSDUnderpaintAngles":[0,45],
  "originalGIFAngles":[90],
  "sourceApprovedHeroSHAverified":False,
  "visualApproval":"PENDING_ANATOMICAL_CORRESPONDENCE"
 })
 f=out/"parts.json";f.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
 p0=json.loads((root/"p4-see-through/front/integrated/integration-qa.json").read_text())
 p45=json.loads((root/"p5-see-through/yaw045/integrated/qa.json").read_text())
 qa={
  "schema":"KOMA-P0-P5-TWO-PSD-VIEW-ARTMESH-QA-V1",
  "characterId":"p0_character_001",
  "status":"REVIEW_CANDIDATE",
  "registeredSemanticViews":39,
  "PSDViewAngles":[0,45],
  "originalP0ViewAngles":[90],
  "PSD0SHA256":p0["inferencePSDSHA256"],
  "PSD45SHA256":p45["sourcePSD"],
  "addedUnderpaintPixels":{"0":p0["inferredUnderpaintPixels"],
                          "45":p45["sumAddedInferredHiddenPixels"]},
  "keyViewRecompositionIoU":{"0":p0["metrics"]["originalStaticSilhouetteIoU"],
                              "45":p45["originalWholeSilhouetteIoU"],
                              "90":1},
  "approvedHeroMasterSHAverified":False,
  "visualAcceptance":"PENDING_CROSS_VIEW_TEXTURE_CORRESPONDENCE"
 }
 (out/"qa.json").write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps(qa,indent=2,ensure_ascii=False))
 return qa

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--root",required=True)
 p.add_argument("--out",required=True)
 a=p.parse_args()
 create(a.root,a.out)

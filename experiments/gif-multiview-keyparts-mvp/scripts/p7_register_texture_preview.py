#!/usr/bin/env python3
"""Register audited P0 real RGBA texture interpolation frames for HTML review."""
import hashlib,json,argparse
from pathlib import Path
from PIL import Image
import numpy as np

def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for blob in iter(lambda:f.read(1024*1024),b""):h.update(blob)
 return h.hexdigest()

def load(p):
 return json.loads(Path(p).read_text(encoding="utf8"))

def create(root):
 root=Path(root).resolve()
 dense=root/"p7-semantic-dense"
 older=root/"p5-see-through/mv-candidate"
 whole=load(older/"parts.json")
 assert whole["characterId"]=="p0_character_001"
 angles=[i*2.5 for i in range(37)]
 org={int(x["yawDeg"]):x for x in whole["wholeViews"]}
 sources=[
  {"id":"p6-mesh","name":"P6 · 物理锚点 ArtMesh","folder":older/"flow-mesh-sequence",
   "qa":"P6 physical-flow mesh, Canvas2D",
   "temporal":older/"flow-mesh-sequence/temporal-qa.json",
   "texture":older/"flow-mesh-browser/texture-qa.json"},
  {"id":"p7-dense","name":"P7 · 语义稠密光流","folder":dense/"full-sequence",
   "qa":"P7 original-source per-part RGBA dense flow with source selection",
   "temporal":dense/"full-sequence/temporal-qa.json",
   "texture":dense/"source-selection/texture-qa.json"},
  {"id":"p7-guided","name":"P7 · 部件流场与视角过渡","folder":dense/"guided-sequence",
   "qa":"P7 original-source per-part RGBA dense flow with guided transition",
   "temporal":dense/"guided-sequence/temporal-qa.json",
   "texture":dense/"guided-sequence/texture-qa.json"}
 ]
 result=[]
 for entry in sources:
  frames=[]
  for angle in angles:
   name="yaw"+(str(int(angle)) if angle.is_integer() else str(angle).replace(".","p"))+".png"
   filename=entry["folder"]/name
   with Image.open(filename) as image:
    if image.size!=(1024,1024) or image.mode!="RGBA":
     raise ValueError("Expected source-transformed RGBA PNG 1024 "+str(filename))
    if int(angle) in org and angle.is_integer() and angle in (0,45,90) and entry["id"]!="p6-mesh":
     with Image.open(root/org[int(angle)]["path"]) as original:
      if not np.array_equal(np.asarray(image),np.asarray(original.convert("RGBA"))):
       raise ValueError("Dense flow keyframe pixels not original P0")
   frames.append({"angle":angle,"path":str(filename.relative_to(root)),
                  "sha256":sha(filename),"bytes":filename.stat().st_size})
  if entry["id"]!="p6-mesh":
   qa={
    "schema":"KOMA-P0-P7-DENSE-SOURCE-RGBA-QA-V1",
    "characterId":"p0_character_001",
    "status":"SOURCE_DERIVED_RGBA_FRAMES_CAPTURED",
    "sourceKind":"OFFLINE_P0_SEMANTIC_FLOW_TEXTURE",
    "frameCount":37,"sourceMethod":entry["qa"],
    "outputs":[{"yaw":x["angle"],"path":str((root/x["path"]).resolve()),
                "sha256":x["sha256"],"bytes":x["bytes"]} for x in frames]
   }
   (entry["folder"]/"canvas-qa.json").write_text(
    json.dumps(qa,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
  temp=load(entry["temporal"]);texture=load(entry["texture"])
  assert temp["characterId"]==texture["characterId"]=="p0_character_001"
  result.append({
   "id":entry["id"],"name":entry["name"],
   "source":entry["qa"],"frames":frames,
   "temporalStatus":temp["status"],
   "temporalOutliers":len(temp["outliers"]),
   "maxAdjacentDifference":temp["maxAdjacentMeanRGBDelta"],
   "textureStatus":texture["status"],
   "textureRatios":{str(item["angle"]):item["edgeDensityRelativeToAdjacentMax"] for item in texture["holdouts"]},
   "visualAcceptance":"PENDING_ORIGINAL_ANATOMICAL_COMPARISON"})
 f=root/"p7-semantic-dense/viewer-manifest.json"
 manifest={
  "schema":"KOMA-P0-P7-REAL-RGBA-ANATOMY-REVIEW-V1",
  "characterId":"p0_character_001",
  "canvas":[1024,1024],
  "originalKeyAngles":[0,45,90],
  "sourcePSDViews":[0,45],
  "source90":"Original P0 profile RGBA",
  "angles":angles,
  "methods":result,
  "artisticAcceptance":"PENDING",
  "authoritativeOriginalFrames":[{"angle":x,"path":org[x]["path"],"sha256":org[x]["sha256"]} for x in (0,45,90)]
 }
 f.parent.mkdir(exist_ok=True,parents=True)
 f.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print(json.dumps({"schema":manifest["schema"],"sourceCount":len(result),
    "sourceRGBAs":sum(len(x["frames"]) for x in result),
    "manifestSHA256":sha(f),
    "quality":[{"id":x["id"],"temporal":x["temporalStatus"],
                 "texture":x["textureStatus"],"textureRatios":x["textureRatios"]}
               for x in result]},ensure_ascii=False,indent=2))
 return manifest

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--root",required=True)
 args=p.parse_args()
 create(args.root)

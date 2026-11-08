#!/usr/bin/env python3
"""Register source-authentic P0 comparison modes for P8 HTML acceptance."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image
import numpy as np

def get(path):return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
 return h.hexdigest()

def register(root):
 root=Path(root).resolve()
 p7=root/"p7-semantic-dense"
 p8=root/"p8-semantic-occlusion"
 prior=get(p7/"viewer-manifest.json")
 p8qa=get(p8/"selective-sequence/qa.json")
 p8texture=get(p8/"selective-sequence/texture-qa.json")
 p8temporal=get(p8/"selective-sequence/temporal-qa.json")
 if prior["characterId"]!="p0_character_001" or p8qa["characterId"]!="p0_character_001":
  raise ValueError("P0 identity differs")
 if len(p8qa["frames"])!=37 or p8qa["mode"]!="selective":
  raise ValueError("Full P8 source RGBAs required")
 src={int(x["angle"]):x for x in prior["authoritativeOriginalFrames"]}
 originals={}
 for yaw,record in src.items():
  source=root/record["path"]
  if sha(source)!=record["sha256"]:raise ValueError("Original P0 master view sha mismatch")
  with Image.open(source) as im:
   originals[yaw]=np.asarray(im.convert("RGBA"))
 filtered=[]
 for item in prior["methods"]:
  if item["id"] not in ("p6-mesh","p7-guided"):continue
  if len(item["frames"])!=37:raise ValueError("P7 source frame incomplete")
  filtered.append(item)
 assert [i["id"] for i in filtered]==["p6-mesh","p7-guided"]
 frames=[]
 for rec in p8qa["frames"]:
  f=root/rec["path"]
  if sha(f)!=rec["sha256"]:raise ValueError("P8 source image sha mismatch")
  with Image.open(f) as im:
   if im.mode!="RGBA" or im.size!=(1024,1024):
    raise ValueError("P8 source PNG must be RGBA 1024")
   if rec["angle"] in (0,45,90):
    if not np.array_equal(np.asarray(im),originals[int(rec["angle"])]):
     raise ValueError("Original P0 endpoint changed")
  frames.append({"angle":rec["angle"],"path":rec["path"],
                 "sha256":rec["sha256"],"bytes":f.stat().st_size})
 filtered.append({
  "id":"p8-selective",
  "name":"P8 · 物理锚点与视角遮挡",
  "source":"P0 part-specific flow, physical anchor RBF, occlusion-aware confidence",
  "frames":frames,
  "textureStatus":p8texture["status"],
  "textureRatios":{str(v["angle"]):v["edgeDensityRelativeToAdjacentMax"]
                   for v in p8texture["holdouts"]},
  "temporalStatus":p8temporal["status"],
  "temporalOutliers":len(p8temporal["outliers"]),
  "maxAdjacentDifference":p8temporal["maxAdjacentMeanRGBDelta"],
  "visualAcceptance":"PENDING_ARTISTIC_REVIEW"
 })
 out={
  "schema":"KOMA-P0-P8-SEMANTIC-OCCLUSION-VIEWER-V1",
  "characterId":"p0_character_001",
  "canvas":[1024,1024],
  "originalKeyAngles":[0,45,90],
  "sourcePSDViews":[0,45],
  "registeredArtMeshSlots":39,
  "source90":"original registered P0 RGBA",
  "angles":[i*2.5 for i in range(37)],
  "methods":filtered,
  "artisticAcceptance":"PENDING",
  "sourceProvenance":"P0 original author key views + 0°/45° inferred PSD parts",
  "authoritativeOriginalFrames":[src[i] for i in (0,45,90)],
  "semanticOcclusionWindows":p8qa["occlusionWindows"],
  "geometryConstraint":"physical source landmark correspondence"
 }
 manifest=p8/"viewer-manifest.json"
 manifest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"schema":out["schema"],"methods":[x["id"] for x in filtered],
      "sourceNativeRGBA":sum(len(x["frames"]) for x in filtered),
      "sourceP0Views":out["originalKeyAngles"],
      "p8Temporal":p8temporal["status"],
      "p8Texture":p8texture["status"],
      "SHA256":sha(manifest)},ensure_ascii=False,indent=2))
 return out

if __name__=="__main__":
 parser=argparse.ArgumentParser()
 parser.add_argument("--root",required=True)
 opts=parser.parse_args()
 register(opts.root)

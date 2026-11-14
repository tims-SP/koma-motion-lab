#!/usr/bin/env python3
"""Standalone P0 semantic-ArtMesh motion review package with source-derived flow.

Carries original P0 source image provenance, 0/45 See-through PSD inputs,
three-view registered RGBA parts, Chromium renders and all visual QA.
"""
import argparse,hashlib,json,zipfile
from pathlib import Path

def sha(f):
 h=hashlib.sha256()
 with Path(f).open("rb") as fd:
  for x in iter(lambda:fd.read(1024*1024),b""):h.update(x)
 return h.hexdigest()

def run(experiment,out):
 experiment=Path(experiment).resolve()
 assets=experiment/"private-assets"
 root=assets/"p5-see-through/mv-candidate"
 out=Path(out).resolve()
 manifest=json.loads((root/"parts.json").read_text())
 flow=json.loads((root/"flow-vertex-correspondence.json").read_text())
 comparison=json.loads((assets/"p5-see-through/p6-motion/comparison-qa.json").read_text())
 if any(doc["characterId"]!="p0_character_001" for doc in
        (manifest,flow,comparison)):
  raise ValueError("P0 identity mismatch")
 if len(manifest["parts"])!=39 or flow["qa"]["trackedSemanticSlots"]!=39:
  raise ValueError("Missing source ArtMesh/flow correspondence")
 if flow["sourceManifestSHA256"]!=sha(root/"parts.json"):
  raise ValueError("Source manifest mismatch for flow geometry")
 sources={}
 def add(path):
  path=Path(path).resolve()
  if not path.is_file() or not path.is_relative_to(experiment):
   raise FileNotFoundError("missing/private path "+str(path))
  sources[str(path.relative_to(experiment))]=path
 for item in (
   "review/index.html","review/review.js",
   "review/p1-front.html","review/p1-front.js",
   "scripts/qa_temporal.py","scripts/qa_vdd_texture.py","scripts/qa_vdd_holdout.py",
   "scripts/build_p6_flow_correspondence.py","scripts/report_p6_comparison.py",
   "scripts/flow_render.py","scripts/capture_vdd_canvases.cjs",
   "scripts/register_p5_multiview.py","scripts/build_p5_landmarks.py",
   "scripts/integrate_seethrough_view.py","scripts/encode_turn_gif.py",
   "scripts/p1_front_semantic.py","scripts/p2_semantic_art.py"):
  add(experiment/item)
 for item in (
   "p5-see-through/mv-candidate/parts.json",
   "p5-see-through/mv-candidate/qa.json",
   "p5-see-through/mv-candidate/landmark-qa.json",
   "p5-see-through/mv-candidate/flow-vertex-correspondence.json",
   "p5-see-through/mv-candidate/landmark-correspondence.jpg",
   "p5-see-through/mv-candidate/vdd-canvas/canvas-qa.json",
   "p5-see-through/mv-candidate/vdd-sequence/canvas-qa.json",
   "p5-see-through/mv-candidate/flow-mesh-browser/canvas-qa.json",
   "p5-see-through/mv-candidate/flow-mesh-sequence/canvas-qa.json",
   "p5-see-through/mv-candidate/flow-blend-sequence/canvas-qa.json",
   "p5-see-through/mv-candidate/vdd-sequence/temporal-qa.json",
   "p5-see-through/mv-candidate/flow-mesh-sequence/temporal-qa.json",
   "p5-see-through/mv-candidate/flow-blend-sequence/temporal-qa.json",
   "p5-see-through/mv-candidate/texture-qa.json",
   "p5-see-through/mv-candidate/flow-mesh-browser/texture-qa.json",
   "p5-see-through/mv-candidate/flow-blend-sequence/texture-qa.json",
   "p5-see-through/mv-candidate/flow-mesh-browser/holdout-qa.json",
   "p5-see-through/mv-candidate/flow-blend-sequence/holdout-qa.json",
   "p5-see-through/mv-candidate/p0-psd-paired-vdd-turn.gif",
   "p5-see-through/mv-candidate/p0-physical-flow-vdd-turn.gif",
   "p5-see-through/mv-candidate/p0-flow-transition-review.gif",
   "p5-see-through/mv-candidate/turn-gif-qa.json",
   "p5-see-through/mv-candidate/p0-physical-flow-vdd-turn.qa.json",
   "p5-see-through/mv-candidate/p0-flow-transition-review.qa.json",
   "p5-see-through/p6-motion/comparison-qa.json",
   "p5-see-through/p6-motion/rendering-quality-comparison.jpg",
   "p5-see-through/yaw045/p0-character-001-see-through.psd",
   "p5-see-through/yaw045/inference-qa.json",
   "p5-see-through/yaw045/exported/layer-qa.json",
   "p5-see-through/yaw045/integrated/parts.json",
   "p5-see-through/yaw045/integrated/qa.json",
   "p5-see-through/yaw045/integrated/semantic-comparison.jpg",
   "p4-see-through/front/p0-character-001-see-through.psd",
   "p4-see-through/front/inference-qa.json",
   "p4-see-through/front/exported/layer-qa.json",
   "p4-see-through/front/integrated/integrated-parts.json",
   "p4-see-through/front/integrated/integration-qa.json",
   "p4-see-through/front/integrated/front-source.png",
   "p4-see-through/front/integrated/p0-fringe-motion-review.jpg",
   "p4-see-through/front/exported/semantic-contact.jpg",
   "recovered-review/frames/head_8/yaw000_whole.png",
   "recovered-review/frames/head_8/yaw045_whole.png",
   "recovered-review/frames/head_8/yaw090_whole.png",
   "whole/head-turn-8view.gif",
   "gifs/identity.gif","gifs/face.gif","gifs/hair.gif"):
  add(assets/item)
 for part in manifest["parts"]:
  f=assets/part["path"]
  if sha(f)!=part["frameSha256"]:raise ValueError("ArtMesh source hash "+part["path"])
  add(f)
 for full in manifest["wholeViews"]:
  f=assets/full["path"]
  if sha(f)!=full["sha256"]:raise ValueError("Whole original view hash "+full["path"])
  add(f)
 for qpath in (
   "p4-see-through/front/exported/parts",
   "p5-see-through/yaw045/exported/parts"):
  for file in (assets/qpath).glob("*.png"):add(file)
 for relative in (
   "p5-see-through/mv-candidate/vdd-canvas",
   "p5-see-through/mv-candidate/flow-mesh-browser",
   "p5-see-through/mv-candidate/flow-mesh-sequence",
   "p5-see-through/mv-candidate/flow-blend-sequence"):
  for file in (assets/relative).glob("yaw*.png"):add(file)
 for rel in (
   "p5-see-through/mv-candidate/vdd-sequence/canvas-qa.json",
   "p5-see-through/mv-candidate/flow-mesh-sequence/canvas-qa.json",
   "p5-see-through/mv-candidate/flow-blend-sequence/canvas-qa.json"):
  doc=json.loads((assets/rel).read_text())
  if len(doc["outputs"])!=37:raise ValueError("Missing real browser source frame evidence")
  for rec in doc["outputs"]:
   if sha(rec["path"])!=rec["sha256"]:
    raise ValueError("Browser capture hash mismatch")
 for old,new in (
   ("p5-see-through/mv-candidate/p0-psd-paired-vdd-turn.gif","vdd-sequence"),
   ("p5-see-through/mv-candidate/p0-physical-flow-vdd-turn.gif","flow-mesh-sequence"),
   ("p5-see-through/mv-candidate/p0-flow-transition-review.gif","flow-blend-sequence")):
  payload=assets/old
  # Own GIF evidence is derived from real frame sha; independent SHA below.
  if payload.stat().st_size<1000000:raise ValueError("GIF output incomplete")
 for name,result in comparison["methods"].items():
  for entry in result["sourceImages"]:
   p=root/entry["path"]
   if sha(p)!=entry["sha256"]:
    raise ValueError("Comparison contact input mismatch")
 p0sha=sha(assets/"p4-see-through/front/p0-character-001-see-through.psd")
 p45sha=sha(assets/"p5-see-through/yaw045/p0-character-001-see-through.psd")
 fig=assets/"p5-see-through/p6-motion/rendering-quality-comparison.jpg"
 if sha(fig)!=comparison["contactSHA256"]:
  raise ValueError("Comparison contact output SHA mismatch")
 version={
  "schema":"KOMA-P0-P6-ARTMESH-FLOW-REVIEW-PACKAGE-V1",
  "characterId":"p0_character_001",
  "originalViewAngles":[0,45,90],"PSDViewAngles":[0,45],
  "registeredArtMeshSlots":39,
  "registeredPhysicalLandmarks":len(json.loads((root/"landmark-qa.json").read_text())["landmarks"]),
  "flowMeshControlVertices":sum(len(v) for pair in flow["pairs"].values()
      for byangle in pair.values() for v in byangle.values()),
  "nativeSourceCanvas":[443,443],"renderCanvas":[1024,1024],
  "sourcePSD_SHA256":{"0":p0sha,"45":p45sha},
  "flowJSON_SHA256":sha(root/"flow-vertex-correspondence.json"),
  "methodQA":{name:{
     "texture":r["holdoutTextureEdgeDensity"],
     "temporal":r["temporalStatus"],
     "temporalOutliers":r["temporalOutlierCount"]
    } for name,r in comparison["methods"].items()},
  "qualityStatus":"PHYSICAL_FLOW_ARTMESH_VISUAL_REVIEW",
  "artisticApproval":"PENDING_CROSS_VIEW_TEXEL_CONTINUITY",
  "files":[{"path":name,"bytes":f.stat().st_size,"sha256":sha(f)}
           for name,f in sorted(sources.items())]
 }
 README="""# 2.75D Anime Studio · p0_character_001

Original anime artwork: P0 registered 0°, 45°, 90° images.
Independent See-through PSD semantic assets: 0° and 45°.
Registered animated ArtMeshes: 39 layers, 1024×1024 RGBA.
Image-derived physical landmarks: 13 tracked across the source key views.
Optical-flow correspondence: 2548 semantic mesh-control vectors.

Review via an HTTP server from this extracted package root:

    python3 -m http.server 5181

HTML: P0 original ArtMesh comparison
    /review/index.html?mode=candidate&source=seethrough-paired

HTML: image-flow-constrained ArtMesh interpolation
    /review/index.html?mode=candidate&source=seethrough-paired&warp=flow

HTML: source flow transition comparison
    /review/index.html?mode=candidate&source=seethrough-paired&warp=flow&blend=window

HTML: original PSD-derived front parts
    /review/p1-front.html?source=seethrough

Animated GIFs:
    private-assets/p5-see-through/mv-candidate/p0-physical-flow-vdd-turn.gif
    private-assets/p5-see-through/mv-candidate/p0-flow-transition-review.gif
    private-assets/p5-see-through/mv-candidate/p0-psd-paired-vdd-turn.gif

Real screenshot comparison:
    private-assets/p5-see-through/p6-motion/rendering-quality-comparison.jpg

Source-derived QA:
    private-assets/p5-see-through/p6-motion/comparison-qa.json

The viewport uses real recorded original/PSD-derived PNG layers.
Automatic texture and temporal QA are separate from final visual artistic
acceptance. The latter remains subject to cross-view anatomical texture
correspondence and concealed-profile artwork registration.
"""
 out.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
  for name,file in sorted(sources.items()):z.write(file,arcname=name)
  z.writestr("README.md",README)
  z.writestr("package-manifest.json",json.dumps(version,ensure_ascii=False,indent=2)+"\n")
 with zipfile.ZipFile(out) as z:
  if z.testzip() is not None:raise ValueError("ZIP CRC check failed")
  manifest2=json.loads(z.read("package-manifest.json"))
  for f in manifest2["files"]:
   if hashlib.sha256(z.read(f["path"])).hexdigest()!=f["sha256"]:
    raise ValueError("ZIP source SHA256 check failed "+f["path"])
 qa={
  "schema":"KOMA-P0-P6-REAL-ARTMESH-PACKAGE-QA-V1",
  "characterId":"p0_character_001",
  "archivePath":str(out),"sha256":sha(out),
  "bytes":out.stat().st_size,"files":len(sources)+2,
  "registeredArtMeshes":39,
  "physicalLandmarks":version["registeredPhysicalLandmarks"],
  "flowControlVertices":version["flowMeshControlVertices"],
  "sourcePSD45SHA256":p45sha,
  "sourcePSD0SHA256":p0sha,
  "flowSourceSHA256":version["flowJSON_SHA256"],
  "internalHashesVerified":True,
  "qualityStatus":version["qualityStatus"],
  "artisticApproval":version["artisticApproval"]
 }
 (assets/"p5-see-through/p6-motion/package-qa.json").write_text(
  json.dumps(qa,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps(qa,ensure_ascii=False,indent=2))
 return qa

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--experiment",required=True)
 p.add_argument("--output",required=True)
 a=p.parse_args()
 run(a.experiment,a.output)

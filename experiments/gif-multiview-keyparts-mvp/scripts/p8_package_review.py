#!/usr/bin/env python3
"""Reproducible P0 semantic ArtMesh and anatomical occlusion HTML review archive."""
import argparse,hashlib,json,zipfile
from pathlib import Path

def sha(file):
 h=hashlib.sha256()
 with Path(file).open("rb") as fp:
  for block in iter(lambda:fp.read(1024*1024),b""):h.update(block)
 return h.hexdigest()

def load(file):
 return json.loads(Path(file).read_text(encoding="utf-8"))

def package(exp,out):
 exp=Path(exp).resolve()
 assets=exp/"private-assets"
 p8=assets/"p8-semantic-occlusion"
 p7=assets/"p7-semantic-dense"
 p5=assets/"p5-see-through/mv-candidate"
 manifest=load(p8/"viewer-manifest.json")
 browser=load(p8/"browser/browser-qa.json")
 parts=load(p5/"parts.json")
 qa=load(p8/"selective-sequence/qa.json")
 if any(x.get("characterId")!="p0_character_001" for x in (manifest,browser,parts,qa)):
  raise ValueError("P0 original reference identity mismatch")
 if len(parts["parts"])!=39 or len(manifest["methods"])!=3:
  raise ValueError("Missing registered P0 ArtMesh source")
 if sum(len(x["frames"]) for x in manifest["methods"])!=111:
  raise ValueError("P8 37-frame comparison sources incomplete")
 if browser["status"]!="PASS_REAL_BROWSER_TEXTURE_PREVIEW" or len(browser["screens"])!=6:
  raise ValueError("P8 actual HTML browser QA unavailable")
 files={}
 def add(path,expected=None):
  p=Path(path).resolve()
  if not p.is_file() or not p.is_relative_to(exp):
   raise FileNotFoundError("Review path unavailable: "+str(p))
  if expected and sha(p)!=expected:
   raise ValueError("SHA256 source mismatch "+str(p))
  files[str(p.relative_to(exp))]=p
 # Audited P0 live source and animated RGBA frames.
 for method in manifest["methods"]:
  for rec in method["frames"]:
   add(assets/rec["path"],rec["sha256"])
 for slot in parts["parts"]:
  add(assets/slot["path"],slot["frameSha256"])
 for original in parts["wholeViews"]:
  add(assets/original["path"],original["sha256"])
 for capture in browser["screens"]:
  add(capture["path"],capture["sha256"])
  for canvas in capture["canvases"]:
   add(canvas["path"],canvas["sha256"])
 # Text- and data-driven checks. The P0 original source and two genuine
 # inferred 0/45 PSDs are packed independently of archived preview GIF.
 privateInputs=(
  "p8-semantic-occlusion/viewer-manifest.json",
  "p8-semantic-occlusion/selective-sequence/qa.json",
  "p8-semantic-occlusion/selective-sequence/canvas-qa.json",
  "p8-semantic-occlusion/selective-sequence/texture-qa.json",
  "p8-semantic-occlusion/selective-sequence/temporal-qa.json",
  "p8-semantic-occlusion/selective-sequence/holdout-qa.json",
  "p8-semantic-occlusion/selective-sequence/semantic-occlusion-contact.jpg",
  "p8-semantic-occlusion/browser/browser-qa.json",
  "p8-semantic-occlusion/p0-semantic-occlusion-turn.gif",
  "p8-semantic-occlusion/p0-semantic-occlusion-turn.qa.json",
  "p8-semantic-occlusion/yaw090/inference-qa.json",
  "p7-semantic-dense/viewer-manifest.json",
  "p7-semantic-dense/guided-sequence/temporal-qa.json",
  "p7-semantic-dense/guided-sequence/texture-qa.json",
  "p7-semantic-dense/p0-semantic-guided-turn.gif",
  "p7-semantic-dense/p0-semantic-guided-turn.qa.json",
  "p5-see-through/mv-candidate/parts.json",
  "p5-see-through/mv-candidate/qa.json",
  "p5-see-through/mv-candidate/landmark-qa.json",
  "p5-see-through/mv-candidate/flow-vertex-correspondence.json",
  "p5-see-through/mv-candidate/flow-mesh-sequence/temporal-qa.json",
  "p5-see-through/mv-candidate/flow-mesh-browser/texture-qa.json",
  "p5-see-through/mv-candidate/p0-physical-flow-vdd-turn.gif",
  "p5-see-through/mv-candidate/p0-physical-flow-vdd-turn.qa.json",
  "p4-see-through/front/p0-character-001-see-through.psd",
  "p4-see-through/front/inference-qa.json",
  "p4-see-through/front/integrated/integration-qa.json",
  "p5-see-through/yaw045/p0-character-001-see-through.psd",
  "p5-see-through/yaw045/inference-qa.json",
  "p5-see-through/yaw045/integrated/qa.json")
 for name in privateInputs:add(assets/name)
 publicInputs=(
  "review/index.html","review/review.js",
  "review/p7-motion.html","review/p7-motion.js",
  "review/p8-motion.html","review/p8-motion.js",
  "scripts/capture_p7_motion.cjs","scripts/capture_p8_motion.cjs",
  "scripts/p7_semantic_dense_flow.py","scripts/p7_register_texture_preview.py",
  "scripts/p8_semantic_occlusion.py","scripts/p8_register_viewer.py",
  "scripts/p8_package_review.py",
  "scripts/qa_temporal.py","scripts/qa_vdd_texture.py",
  "scripts/qa_vdd_holdout.py","scripts/flow_render.py",
  "scripts/p1_front_semantic.py","scripts/encode_turn_gif.py",
  "tests/test_p7_semantic_texture.py","tests/test_p8_semantic_occlusion.py")
 for name in publicInputs:add(exp/name)
 gifs=[
  ("p8-semantic-occlusion/p0-semantic-occlusion-turn.gif",
   "p8-semantic-occlusion/p0-semantic-occlusion-turn.qa.json"),
  ("p7-semantic-dense/p0-semantic-guided-turn.gif",
   "p7-semantic-dense/p0-semantic-guided-turn.qa.json"),
  ("p5-see-through/mv-candidate/p0-physical-flow-vdd-turn.gif",
   "p5-see-through/mv-candidate/p0-physical-flow-vdd-turn.qa.json")
 ]
 for imagePath,qaPath in gifs:
  qaGif=load(assets/qaPath)
  if qaGif["sourceFrameCount"]!=37 or qaGif["GIFFrames"]!=72:
   raise ValueError("P0 motion GIF requires 37 real source frames")
  add(assets/imagePath,qaGif["GIFSHA256"])
 if sha(p8/"selective-sequence/semantic-occlusion-contact.jpg")!=qa["contactSHA256"]:
  raise ValueError("P8 source holdout contact SHA mismatch")
 for entry in browser["screens"]:
  if len(entry["canvases"])!=3:raise ValueError("Expected 3 real browser render alternatives")
 srcPSD={
  "0":sha(assets/"p4-see-through/front/p0-character-001-see-through.psd"),
  "45":sha(assets/"p5-see-through/yaw045/p0-character-001-see-through.psd")
 }
 manifestOut={
  "schema":"KOMA-P0-P8-SEMANTIC-OCCLUSION-ARTMESH-REVIEW-PACKAGE-V1",
  "characterId":"p0_character_001",
  "originalP0KeyAngles":[0,45,90],
  "independentlyInferredPSDViews":[0,45],
  "sourcePSDHashes":srcPSD,
  "registeredArtMeshViews":39,
  "semanticVisibilityRules":qa["occlusionWindows"],
  "sourceCanvas":[1024,1024],
  "registeredSourceRGBAFrames":111,
  "methodIDs":[x["id"] for x in manifest["methods"]],
  "nativeChromiumScreenshots":len(browser["screens"]),
  "nativeChromiumCanvases":sum(len(s["canvases"]) for s in browser["screens"]),
  "P8TemporalStatus":next(m["temporalStatus"] for m in manifest["methods"] if m["id"]=="p8-selective"),
  "P8TextureStatus":next(m["textureStatus"] for m in manifest["methods"] if m["id"]=="p8-selective"),
  "productionArtisticApproval":"PENDING_SOURCE_TEXTURE_CORRESPONDENCE",
  "files":[{"path":k,"bytes":f.stat().st_size,"sha256":sha(f)} for k,f in sorted(files.items())]
 }
 README="""# 2.75D Anime Studio · p0_character_001 / semantic occlusion

Authenticated project P0 source: front / 45° / profile 90°.
Native P0 ArtMeshes: 39 semantic view slots, normalized RGBA 1024x1024.
See-through PSD layering: genuine front and 45° input images.
Physical landmark and view-dependent occlusion schedules: see P8 QA JSON.
Three distinct preview modes: P6 optical flow ArtMesh, P7 guided dense
semantic flow, and P8 physical-anchor & semantic visibility motion.

From the extracted package root:

    python3 -m http.server 5181

Open the real browser interactive review:

    http://localhost:5181/review/p8-motion.html

The reviewer checks each PNG SHA-256 before use, offers 0°–90° motion
scrubbing by 2.5°, and compares source-consistent RGBA frames side-by-side.

Standalone 72-frame GIF:

    private-assets/p8-semantic-occlusion/p0-semantic-occlusion-turn.gif

Native original sources, full-resolution 37-frame PNG sequences, real
Chromium captured views, and the source-mesh/PSD verification evidence
are included. Temporal/edge metrics do not imply final artistic quality.
"""
 out=Path(out).resolve();out.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED,
                      compresslevel=2,allowZip64=True) as z:
  for path,file in sorted(files.items()):z.write(file,arcname=path)
  z.writestr("README.md",README)
  z.writestr("package-manifest.json",json.dumps(manifestOut,ensure_ascii=False,indent=2)+"\n")
 with zipfile.ZipFile(out) as z:
  if z.testzip() is not None:raise ValueError("ZIP CRC failed")
  stored=json.loads(z.read("package-manifest.json"))
  for rec in stored["files"]:
   if hashlib.sha256(z.read(rec["path"])).hexdigest()!=rec["sha256"]:
    raise ValueError("ZIP source SHA256 mismatch "+rec["path"])
 report={
  "schema":"KOMA-P0-P8-ORIGINAL-ASSET-REVIEW-QA-V1",
  "characterId":"p0_character_001",
  "archivePath":str(out),"sha256":sha(out),
  "bytes":out.stat().st_size,"entryCount":len(files)+2,
  "registeredArtMeshViews":39,"sourceRGBAFrames":111,
  "browserScreenshots":len(browser["screens"]),
  "browserCanvases":sum(len(x["canvases"]) for x in browser["screens"]),
  "internalHashesVerified":True,
  "P8TemporalGate":manifestOut["P8TemporalStatus"],
  "P8TextureGate":manifestOut["P8TextureStatus"],
  "artisticAcceptance":"PENDING"
 }
 (p8/"p8-package-qa.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps(report,indent=2,ensure_ascii=False))
 return report

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--experiment",required=True)
 p.add_argument("--output",required=True)
 args=p.parse_args()
 package(args.experiment,args.output)

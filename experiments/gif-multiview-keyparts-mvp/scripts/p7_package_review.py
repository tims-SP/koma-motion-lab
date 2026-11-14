#!/usr/bin/env python3
"""Private P0 semantic RGBA interpolation HTML and GIF reproducibility package.

Source art remains the previously approved P0 asset. Every registered image
is a genuine source-derived PNG, PSD or headless-browser validation screenshot.
"""
import argparse,hashlib,json,zipfile
from pathlib import Path

def sha(file):
 h=hashlib.sha256()
 with Path(file).open("rb") as inp:
  for chunk in iter(lambda:inp.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()

def read(file):
 return json.loads(Path(file).read_text(encoding="utf-8"))

def package(exp,out):
 exp=Path(exp).resolve();root=exp/"private-assets"
 p7=root/"p7-semantic-dense"
 p5=root/"p5-see-through/mv-candidate"
 manifest=read(p7/"viewer-manifest.json")
 browser=read(p7/"browser/browser-qa.json")
 registered=read(p5/"parts.json")
 if manifest["characterId"]!="p0_character_001" or browser["characterId"]!="p0_character_001":
  raise ValueError("Unexpected P0 asset identity")
 if len(manifest["methods"])!=3 or any(len(m["frames"])!=37 for m in manifest["methods"]):
  raise ValueError("Requires all three genuine 37-frame sequences")
 if browser["status"]!="PASS_REAL_BROWSER_TEXTURE_PREVIEW" or len(browser["screens"])!=6:
  raise ValueError("P7 browser QA incomplete")
 if len(registered["parts"])!=39:
  raise ValueError("ArtMesh semantic registry incomplete")
 if manifest["artisticAcceptance"]!="PENDING":
  raise ValueError("P0 artistic gate state differs")
 files={}
 def add(file,expected=None):
  f=Path(file).resolve()
  if not f.is_file() or not f.is_relative_to(exp):
   raise FileNotFoundError(f)
  actual=sha(f)
  if expected and actual!=expected:
   raise ValueError("P0 input digest mismatch "+str(f))
  files[str(f.relative_to(exp))]=f
 for method in manifest["methods"]:
  for frame in method["frames"]:
   add(root/frame["path"],frame["sha256"])
 for part in registered["parts"]:
  add(root/part["path"],part["frameSha256"])
 for frame in registered["wholeViews"]:
  add(root/frame["path"],frame["sha256"])
 for snap in browser["screens"]:
  add(snap["path"],snap["sha256"])
  for item in snap["canvases"]:
   add(item["path"],item["sha256"])
 for f in (
  "p7-semantic-dense/viewer-manifest.json",
  "p7-semantic-dense/full-sequence/qa.json",
  "p7-semantic-dense/full-sequence/canvas-qa.json",
  "p7-semantic-dense/full-sequence/temporal-qa.json",
  "p7-semantic-dense/source-selection/texture-qa.json",
  "p7-semantic-dense/source-selection/holdout-qa.json",
  "p7-semantic-dense/guided-sequence/qa.json",
  "p7-semantic-dense/guided-sequence/canvas-qa.json",
  "p7-semantic-dense/guided-sequence/texture-qa.json",
  "p7-semantic-dense/guided-sequence/temporal-qa.json",
  "p7-semantic-dense/guided-sequence/holdout-qa.json",
  "p7-semantic-dense/guided-sequence/texture-transition-contact.jpg",
  "p7-semantic-dense/full-sequence/semantic-dense-flow-contact.jpg",
  "p7-semantic-dense/guided-sequence/semantic-dense-flow-contact.jpg",
  "p7-semantic-dense/browser/browser-qa.json",
  "p7-semantic-dense/p0-semantic-dense-turn.gif",
  "p7-semantic-dense/p0-semantic-dense-turn.qa.json",
  "p7-semantic-dense/p0-semantic-guided-turn.gif",
  "p7-semantic-dense/p0-semantic-guided-turn.qa.json",
  "p5-see-through/mv-candidate/parts.json",
  "p5-see-through/mv-candidate/qa.json",
  "p5-see-through/mv-candidate/landmark-qa.json",
  "p5-see-through/mv-candidate/flow-vertex-correspondence.json",
  "p5-see-through/mv-candidate/flow-mesh-sequence/canvas-qa.json",
  "p5-see-through/mv-candidate/flow-mesh-sequence/temporal-qa.json",
  "p5-see-through/mv-candidate/flow-mesh-browser/texture-qa.json",
  "p5-see-through/mv-candidate/p0-physical-flow-vdd-turn.gif",
  "p5-see-through/mv-candidate/p0-physical-flow-vdd-turn.qa.json",
  "p5-see-through/p6-motion/comparison-qa.json",
  "p5-see-through/p6-motion/rendering-quality-comparison.jpg",
  "p5-see-through/yaw045/p0-character-001-see-through.psd",
  "p5-see-through/yaw045/inference-qa.json",
  "p5-see-through/yaw045/exported/layer-qa.json",
  "p5-see-through/yaw045/integrated/qa.json",
  "p4-see-through/front/p0-character-001-see-through.psd",
  "p4-see-through/front/exported/layer-qa.json",
  "p4-see-through/front/inference-qa.json",
  "p4-see-through/front/integrated/integration-qa.json",
  "p5-see-through/yaw090/inference-qa.json"
 ):
  add(root/f)
 for folder in (
  "p4-see-through/front/exported/parts",
  "p5-see-through/yaw045/exported/parts"):
  for f in sorted((root/folder).glob("*.png")):add(f)
 for f in (
  "review/index.html","review/review.js",
  "review/p1-front.html","review/p1-front.js",
  "review/p7-motion.html","review/p7-motion.js",
  "scripts/p7_semantic_dense_flow.py","scripts/p7_register_texture_preview.py",
  "scripts/capture_p7_motion.cjs","scripts/encode_turn_gif.py",
  "scripts/qa_temporal.py","scripts/qa_vdd_texture.py","scripts/qa_vdd_holdout.py",
  "scripts/flow_render.py","scripts/p1_front_semantic.py",
  "scripts/build_p5_landmarks.py","scripts/build_p6_flow_correspondence.py",
  "scripts/export_seethrough_psd.py","scripts/integrate_seethrough_view.py",
  "scripts/register_p5_multiview.py","tests/test_p7_semantic_texture.py"):
  add(exp/f)
 for label,name in (("guided","p0-semantic-guided-turn"),
                    ("dense","p0-semantic-dense-turn")):
  qa=read(p7/(name+".qa.json"))
  f=p7/(name+".gif")
  if qa["GIFSHA256"]!=sha(f) or qa["GIFFrames"]!=72 or qa["sourceFrameCount"]!=37:
   raise ValueError("P7 real source GIF "+label+" source integrity mismatch")
 originalPSDs={
   "0":sha(root/"p4-see-through/front/p0-character-001-see-through.psd"),
   "45":sha(root/"p5-see-through/yaw045/p0-character-001-see-through.psd")
 }
 manifestPkg={
  "schema":"KOMA-P0-P7-ANATOMICAL-RGBA-TEXTURE-REVIEW-V1",
  "characterId":"p0_character_001",
  "originalSourceViews":[0,45,90],
  "genuinePSDSemanticAngles":[0,45],
  "sourcePSDHashes":originalPSDs,
  "registeredSemanticArtMeshes":len(registered["parts"]),
  "interpolationVariants":len(manifest["methods"]),
  "sourcePNGCount":sum(len(method["frames"]) for method in manifest["methods"]),
  "sampleAngles":[0,22.5,45,67.5,72.5,90],
  "renderCanvas":[1024,1024],
  "sourceGIFFramesPerSequence":72,
  "browserScreenshotCount":len(browser["screens"]),
  "browserCanvasCaptures":sum(len(s["canvases"]) for s in browser["screens"]),
  "artisticAcceptance":"PENDING",
  "QAState":"PENDING_ANIME_ARTISTIC_APPROVAL",
  "files":[{"path":key,"bytes":file.stat().st_size,"sha256":sha(file)}
           for key,file in sorted(files.items())]
 }
 README="""# 2.75D Anime Studio P0 / 0–90° RGBA texture correspondence

Character: p0_character_001 (original registered P0 identity).
Reference views: 0, 45, 90 degrees; semantic PSD layers: 0 and 45 degrees.
Original semantic ArtMesh slots: 39; source resolution: 1024x1024 RGBA.

Serve the extracted package root locally:

    python3 -m http.server 5181

Interactive review:

    http://127.0.0.1:5181/review/p7-motion.html

Compare authentic P0 source-derived frames using the 0-90° slider,
with 2.5° increments and independent per-source SHA-256 checks.
This is an interactive *baked frame* review, not an equivalent
of live WebGL mesh deformation.

P6 live semantic ArtMesh viewer:

    http://127.0.0.1:5181/review/index.html?mode=candidate&source=seethrough-paired&warp=flow

P7 source-derived motion previews:
    private-assets/p7-semantic-dense/p0-semantic-guided-turn.gif
    private-assets/p7-semantic-dense/p0-semantic-dense-turn.gif

Native RGBA image sequences and their source integrity manifests are
under private-assets/p7-semantic-dense/ respectively.

Original P0 keyframe pixels, semantic part identities, true inferred PSD
sources, and image-source hashes are included and independently verified.
Temporal and edge-density diagnostics are separate from artistic acceptance.
Fine hair and facial texture still require improved cross-view correspondence.
"""
 out=Path(out).resolve();out.parent.mkdir(exist_ok=True,parents=True)
 with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED,
                      compresslevel=2,allowZip64=True) as zipout:
  for name,file in sorted(files.items()):
   zipout.write(file,arcname=name)
  zipout.writestr("README.md",README)
  zipout.writestr("package-manifest.json",json.dumps(manifestPkg,ensure_ascii=False,indent=2)+"\n")
 with zipfile.ZipFile(out) as z:
  if z.testzip() is not None:raise ValueError("ZIP CRC failed")
  registeredManifest=json.loads(z.read("package-manifest.json"))
  for source in registeredManifest["files"]:
   if hashlib.sha256(z.read(source["path"])).hexdigest()!=source["sha256"]:
    raise ValueError("P7 ZIP SHA-256 mismatch "+source["path"])
 qa={
  "schema":"KOMA-P0-P7-PACKAGE-QA-V1",
  "characterId":"p0_character_001",
  "archivePath":str(out),"sha256":sha(out),
  "bytes":out.stat().st_size,
  "entryCount":len(files)+2,
  "registeredSemanticArtMeshes":len(registered["parts"]),
  "registeredNativeRGBAFrames":manifestPkg["sourcePNGCount"],
  "browserScreenshotCount":manifestPkg["browserScreenshotCount"],
  "browserCanvasCaptures":manifestPkg["browserCanvasCaptures"],
  "internalHashesVerified":True,
  "temporalGate":next(m["temporalStatus"] for m in manifest["methods"] if m["id"]=="p7-guided"),
  "textureGate":next(m["textureStatus"] for m in manifest["methods"] if m["id"]=="p7-guided"),
  "artisticAcceptance":"PENDING"
 }
 (p7/"p7-package-qa.json").write_text(json.dumps(qa,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps(qa,ensure_ascii=False,indent=2))
 return qa

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--experiment",required=True)
 p.add_argument("--output",required=True)
 a=p.parse_args()
 package(a.experiment,a.output)

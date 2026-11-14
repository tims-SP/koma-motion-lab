#!/usr/bin/env python3
"""P13 source-verified P0 intermediate semantic art and interactive motion package."""
import argparse,hashlib,json,zipfile
from pathlib import Path

def sha(file):
 h=hashlib.sha256()
 with Path(file).open("rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
 return h.hexdigest()

def load(file):return json.loads(Path(file).read_text(encoding="utf8"))

def package(experiment,out):
 exp=Path(experiment).resolve();a=exp/"private-assets"
 p=a/"p13-source-priority"
 art=load(p/"p13-paint-contract.json")
 comparison=load(p/"comparison-qa.json")
 candidate=load(p/"source-feathered/qa.json")
 baseline=load(a/"p8-semantic-occlusion/selective-sequence/qa.json")
 browser=load(p/"browser/browser-qa.json")
 original=load(a/"p5-see-through/mv-candidate/parts.json")
 psd=load(a/"p11-profile-psd/yaw090/qa.json")
 gif=load(p/"p0-character-001-intermediate-turn.qa.json")
 if any(item["characterId"]!="p0_character_001" for item in
        (art,comparison,candidate,baseline,browser,original,psd,gif)):
  raise ValueError("Original P0 character identity differs")
 if (candidate["frameCount"],candidate["semanticLayerCount"])!=(37,26):
  raise ValueError("P13 original-source RGBA sequence/semantic slots incomplete")
 if browser["status"]!="PASS_REAL_ORIGINAL_P0_INTERMEDIATE_LAYER_REVIEW":
  raise ValueError("Actual Chromium source artwork verification missing")
 if len(browser["screens"])!=6 or browser["screenshotCount"]!=12:
  raise ValueError("Actual P0 source view/screenshots incomplete")
 if sha(exp/"metadata/p13-paint-contract.json")!=sha(p/"p13-paint-contract.json"):
  raise ValueError("GitHub P0 painting contract SHA differs from actual asset source")
 if len(art["intermediateViews"])!=2 or art["imageContract"]["componentCountPerView"]!=13:
  raise ValueError("ArtMesh source identities at both angles required")
 if sha(a/psd["psdPath"])!=psd["psdSHA256"]:
  raise ValueError("Editable canonical 90-degree P0 source PSD differs")
 if gif["GIFSHA256"]!=sha(p/"p0-character-001-intermediate-turn.gif"):
  raise ValueError("Source-derived P13 original motion GIF changed")
 files={}
 def add(path,expected=None):
  path=Path(path).resolve()
  if not path.is_file() or not path.is_relative_to(exp):
   raise FileNotFoundError("Source-authored P0 asset missing: "+str(path))
  s=sha(path)
  if expected and expected!=s:
   raise ValueError("Source P0 SHA mismatch: "+str(path))
  files[str(path.relative_to(exp))]=path
 # Authored keyframe original art and 39 independently cropped semantic sources.
 for rec in original["wholeViews"]:add(a/rec["path"],rec["sha256"])
 for rec in original["parts"]:add(a/rec["path"],rec["frameSha256"])
 # Three source-aligned actual layered PSD files.
 for rel in (
  "p4-see-through/front/p0-character-001-see-through.psd",
  "p5-see-through/yaw045/p0-character-001-see-through.psd"
 ):
  add(a/rel)
 add(a/psd["psdPath"],psd["psdSHA256"])
 # Baseline and source-derived 37-frame 1024x1024 sequences.
 for entry in baseline["frames"]:add(a/entry["path"],entry["sha256"])
 for entry in candidate["frames"]:add(a/entry["path"],entry["sha256"])
 # The exact 13 semantic transparent PNG slots for both intermediate angles.
 for view in art["intermediateViews"]:
  for part in view["parts"]:
   entry=part["sourceDerivedCandidate"]
   add(a/entry["path"],entry["sha256"])
 # True browser canvas comparisons.
 for capture in browser["screens"]:
  for item in capture["captures"].values():
   add(item["path"],item["sha256"])
 add(p/"p0-character-001-intermediate-turn.gif",gif["GIFSHA256"])
 add(a/comparison["originalSourceVisualContact"]["path"],
     comparison["originalSourceVisualContact"]["sha256"])
 for rel in (
  "p13-source-priority/p13-paint-contract.json",
  "p13-source-priority/comparison-qa.json",
  "p13-source-priority/source-feathered/qa.json",
  "p13-source-priority/source-feathered/canvas-qa.json",
  "p13-source-priority/source-feathered/texture-qa.json",
  "p13-source-priority/source-feathered/temporal-qa.json",
  "p13-source-priority/p0-character-001-intermediate-turn.qa.json",
  "p13-source-priority/browser/browser-qa.json",
  "p13-source-priority/source-feathered/p13-source-priority-contact.jpg",
  "p8-semantic-occlusion/selective-sequence/qa.json",
  "p8-semantic-occlusion/selective-sequence/texture-qa.json",
  "p8-semantic-occlusion/selective-sequence/temporal-qa.json",
  "p5-see-through/mv-candidate/parts.json",
  "p5-see-through/mv-candidate/landmark-qa.json",
  "p11-profile-psd/yaw090/qa.json",
  "p12-occlusion-gap/qa.json"
 ):add(a/rel)
 for mode in ("source-staggered","confidence-source"):
  add(a/f"p13-source-priority/{mode}/qa.json")
  add(a/f"p13-source-priority/{mode}/texture-qa.json")
  add(a/f"p13-source-priority/{mode}/temporal-qa.json")
  add(a/f"p13-source-priority/{mode}/p13-source-priority-contact.jpg")
 for rel in (
  "metadata/p13-paint-contract.json",
  "review/p13-intermediate.html",
  "review/p13-intermediate.js",
  "scripts/capture_p13_intermediate.cjs",
  "scripts/p13_source_priority.py",
  "scripts/p13_register_paint_contract.py",
  "scripts/p13_compare_intermediate.py",
  "scripts/p13_package_review.py",
  "tests/test_p13_intermediate_assets.py",
  "scripts/p8_semantic_occlusion.py",
  "scripts/p7_semantic_dense_flow.py",
  "scripts/flow_render.py",
  "scripts/p1_front_semantic.py",
  "scripts/encode_turn_gif.py",
  "scripts/qa_temporal.py",
  "scripts/qa_vdd_texture.py"
 ):add(exp/rel)
 manifest={
  "schema":"KOMA-P0-P13-INTERMEDIATE-SEMANTIC-ASSET-REVIEW-PACKAGE-V1",
  "characterId":"p0_character_001",
  "sourceOriginalKeyViews":[0,45,90],
  "sourcePSDViews":[0,45,90],
  "sourceSemanticViewSlots":39,
  "nativeCanvas":[1024,1024],
  "intermediateReviewAngles":[67.5,72.5],
  "intermediateSemanticComponentSlots":26,
  "sourceAuthoredArtStatus":"P0_ORIGINAL_0_45_90",
  "intermediateAssetStatus":"P0_SOURCE_DERIVED_RGBA_SEMANTIC_CANDIDATE",
  "independentNewArtRequired":comparison["independentPaintComponentsPending"],
  "sourceP0MotionFrames":37,
  "sourceDerivedMotionFrames":37,
  "motionGIFFrames":72,
  "browserSourceVerifiedScreenshots":12,
  "adoptedMotionReference":comparison["adoptedMotionBaseline"],
  "reviewHTML":"review/p13-intermediate.html",
  "semanticSourceContract":"private-assets/p13-source-priority/p13-paint-contract.json",
  "artisticApproval":"PENDING_INDEPENDENT_INTERMEDIATE_PAINTING_AND_VISUAL_QA",
  "files":[{"path":k,"bytes":v.stat().st_size,"sha256":sha(v)} for k,v in sorted(files.items())]
 }
 readme="""# P0 character · Intermediate Semantic Source Assets

This bundle contains the original P0 character's 0°, 45° and 90° authored
artwork, 39 corresponding source RGBA semantic parts and all three
previously verified PSD view assets.

The 67.5° and 72.5° intermediate views have thirteen individually
transparent 1024x1024 RGBA PNG semantic slots each. They are reconstructed
from original 45°/90° painted source materials by registered VDD, and
their semantic ID, source SHA-256, alpha, physical anchor references,
visibility and source-origin lineage are recorded in the contract.

Open the HTML review from the extracted package root:

    python3 -m http.server 5181

    http://127.0.0.1:5181/review/p13-intermediate.html

Compare P8's 37-frame source motion and the P13 source-derived candidate
frame-by-frame, then choose a semantic part and inspect both original
source layers alongside its 67.5° or 72.5° candidate PNG.

The 72-frame RGB GIF preview is:
    private-assets/p13-source-priority/p0-character-001-intermediate-turn.gif

Production artwork approval requires independent painting and visual
acceptance of the semantic intermediate parts listed in
    private-assets/p13-source-priority/p13-paint-contract.json

The adopted animation reference remains P8 with verified original keyviews.
"""
 out=Path(out).resolve();out.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED,
                      compresslevel=3,allowZip64=True) as z:
  for rel,file in sorted(files.items()):z.write(file,arcname=rel)
  z.writestr("README.md",readme)
  z.writestr("package-manifest.json",json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
 with zipfile.ZipFile(out) as z:
  if z.testzip() is not None:raise ValueError("P13 original source ZIP CRC failed")
  stored=json.loads(z.read("package-manifest.json"))
  for entry in stored["files"]:
   if hashlib.sha256(z.read(entry["path"])).hexdigest()!=entry["sha256"]:
    raise ValueError("Source SHA-256 failed in bundle: "+entry["path"])
 report={
  "schema":"KOMA-P0-P13-SOURCE-DERIVED-SEMANTIC-ART-QA-V1",
  "characterId":"p0_character_001",
  "archivePath":str(out),"sha256":sha(out),"bytes":out.stat().st_size,
  "entryCount":len(files)+2,
  "intermediateRGBAComponentSlots":26,
  "originalP0SemanticViewSlots":39,
  "sourceDerivedRGBAFrames":37,
  "motionGIFFrames":72,
  "actualChromiumScreenshots":12,
  "internalHashesVerified":True,
  "independentOriginalPaintingPending":comparison["independentPaintComponentsPending"],
  "visualArtApproval":"PENDING"
 }
 (p/"p13-package-qa.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps(report,indent=2,ensure_ascii=False))
 return report

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--experiment",required=True)
 p.add_argument("--output",required=True)
 x=p.parse_args()
 package(x.experiment,x.output)

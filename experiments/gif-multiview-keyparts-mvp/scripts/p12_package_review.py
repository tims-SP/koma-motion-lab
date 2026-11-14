#!/usr/bin/env python3
"""Distribute original P0 view-correspondence and occlusion atlas review bundle."""
import argparse,hashlib,json,zipfile
from pathlib import Path

def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
 return h.hexdigest()

def get(path):return json.loads(Path(path).read_text(encoding="utf8"))

def package(experiment,output):
 exp=Path(experiment).resolve();root=exp/"private-assets"
 cmp=get(root/"p12-comparison/comparison-qa.json")
 gap=get(root/"p12-occlusion-gap/qa.json")
 browser=get(root/"p12-comparison/browser/browser-qa.json")
 original=get(root/"p5-see-through/mv-candidate/parts.json")
 p11=get(root/"p11-profile-psd/yaw090/qa.json")
 if any(x["characterId"]!="p0_character_001" for x in (cmp,gap,browser,original,p11)):
  raise ValueError("Original P0 semantic character identity changed")
 if (cmp["semanticArtMeshSlots"],browser["screenshotCount"],gap["registeredPairCount"])!=(39,12,13):
  raise ValueError("P12 original source artwork verification incomplete")
 if len(cmp["methods"])!=5:
  raise ValueError("All five existing/P12 geometry variants required")
 if browser["status"]!="PASS_REAL_SOURCE_ARTMESH_P12_REVIEW":
  raise ValueError("True Chromium P0 source views needed")
 if sha(root/p11["psdPath"])!=p11["psdSHA256"]:
  raise ValueError("Original P0 editable 90 degree PSD changed")
 files={}
 def add(path,expected=None):
  path=Path(path).resolve()
  if not path.is_file() or not path.is_relative_to(exp):
   raise FileNotFoundError("Registered P0 source missing "+str(path))
  actual=sha(path)
  if expected and expected!=actual:
   raise ValueError("Source SHA mismatch "+str(path))
  files[str(path.relative_to(exp))]=path
 # Actual original 0/45/90 character viewpoints and their transparent semantic ArtMeshes.
 for view in original["wholeViews"]:add(root/view["path"],view["sha256"])
 for part in original["parts"]:add(root/part["path"],part["frameSha256"])
 # Real 37-frame VDD source baseline and its source authored endpoints.
 p8=get(root/"p8-semantic-occlusion/selective-sequence/qa.json")
 if p8["frameCount"]!=37:
  raise ValueError("Expected complete P8 original-derived 37 frame turn")
 for frame in p8["frames"]:add(root/frame["path"],frame["sha256"])
 # Five real original-source alternative texture/geometry checks at six angles.
 for method in cmp["methods"]:
  for frame in method["frames"]:add(root/frame["path"],frame["sha256"])
 # Original painted PNG/PSD view provenance.
 for psdpath in (
  "p4-see-through/front/p0-character-001-see-through.psd",
  "p5-see-through/yaw045/p0-character-001-see-through.psd"
 ):
  add(root/psdpath)
 add(root/p11["psdPath"],p11["psdSHA256"])
 # Registered 45->90 source coverage and occlusion difference atlases.
 for part in gap["parts"]:
  if part.get("sourceComparisonPath"):
   add(root/part["sourceComparisonPath"],part["sourceComparisonSHA256"])
 # True browser artifacts, screenshot captures remain original pixels.
 for scene in browser["screens"]:
  for capture in scene["screenshots"].values():
   add(capture["path"],capture["sha256"])
 # Both source derived original P0 preview GIF and geometry QA.
 gifQA=get(root/"p8-semantic-occlusion/p0-semantic-occlusion-turn.qa.json")
 add(root/"p8-semantic-occlusion/p0-semantic-occlusion-turn.gif",gifQA["GIFSHA256"])
 add(root/cmp["comparisonContactPath"],cmp["comparisonContactSHA256"])
 metadata=[
  "p12-comparison/comparison-qa.json",
  "p12-occlusion-gap/qa.json",
  "p12-comparison/browser/browser-qa.json",
  "p11-profile-psd/yaw090/qa.json",
  "p10-stroke-identity/qa.json",
  "p9-region-correspondence/qa.json",
  "p8-semantic-occlusion/selective-sequence/qa.json",
  "p8-semantic-occlusion/selective-sequence/texture-qa.json",
  "p8-semantic-occlusion/selective-sequence/temporal-qa.json",
  "p8-semantic-occlusion/p0-semantic-occlusion-turn.qa.json",
  "p5-see-through/mv-candidate/parts.json",
  "p5-see-through/mv-candidate/landmark-qa.json",
  "p4-see-through/front/inference-qa.json",
  "p5-see-through/yaw045/inference-qa.json"
 ]
 metadata+=sum(([f"p12-anatomical/{mode}-holdout/qa.json",
                  f"p12-anatomical/{mode}-holdout/texture-qa.json"]
                 for mode in ("anatomy","anatomy-strokes","stroke-wide","affine-face")),[])
 for file in metadata:add(root/file)
 public=[
  "review/p12-inspection.html","review/p12-inspection.js",
  "scripts/capture_p12_review.cjs",
  "scripts/p12_anatomical_vdd.py","scripts/p12_occlusion_audit.py",
  "scripts/p12_compare_variants.py","scripts/p12_package_review.py",
  "tests/test_p12_view_correspondence.py",
  "scripts/p8_semantic_occlusion.py","scripts/p7_semantic_dense_flow.py",
  "scripts/flow_render.py","scripts/p1_front_semantic.py"
 ]
 for file in public:add(exp/file)
 manifest={
  "schema":"KOMA-P0-P12-ANATOMICAL-VIEW-CORRESPONDENCE-REVIEW-BUNDLE-V1",
  "characterId":"p0_character_001",
  "sourceViews":[0,45,90],
  "independentPSDSourceViews":[0,45],
  "profileSourcePSDView":[90],
  "registeredSemanticArtMeshSlots":39,
  "registeredSourceViewGapParts":gap["registeredPairCount"],
  "registeredMotionMethods":len(cmp["methods"]),
  "registeredCandidateFrames":sum(len(m["frames"]) for m in cmp["methods"]),
  "registeredP8MotionFrames":37,
  "originalSourceLoopGIFFrames":gifQA["GIFFrames"],
  "realChromiumCaptures":browser["screenshotCount"],
  "HTML":"review/p12-inspection.html",
  "viewSourceGapQA":"private-assets/p12-occlusion-gap/qa.json",
  "originalAnimationBaseline":"P8_SEMANTIC_OCCLUSION",
  "artisticApproval":"PENDING_FINE_VIEW_TEXEL_AND_OCCLUSION_MAPPING",
  "files":[{"path":name,"bytes":path.stat().st_size,"sha256":sha(path)}
           for name,path in sorted(files.items())]
 }
 readme="""# 2.75D Anime Studio · P0 45°→90° Anatomy and Source Occlusion Review

Original approved P0 character p0_character_001. Includes the authentic
0°, 45° and 90° RGBA key artwork, 39 transparent semantic ArtMesh view
slots, the editable 90° 13-layer PSD assembled from the original source,
the existing inferred 0° and 45° PSDs, and the actual 37-frame P8
0–90° VDD sequence with a 72-frame GIF preview.

Four source-aligned local deformation hypotheses are available for
comparison with the P8 source-preserving renderer. Review their real
22.5°, 67.5° and 72.5° outputs with the source occlusion atlas.

From the extracted bundle root:

    python3 -m http.server 5181

Open in the browser:

    http://127.0.0.1:5181/review/p12-inspection.html

The HTML verifies SHA-256 of every source PNG/JPEG before display.
The first comparison panel shows actual rendered P8 and selected P12.
The lower panel visualizes original 45° and 90° semantic part images,
aligned alpha coverage gaps, and their correspondences.

Target-only alpha percentages can also arise from optical flow
misregistration. They are prioritization evidence for precise redraw
or alignment; they are not a measurement of proven anatomical hidden
surface size.

P8 remains the registered full-motion baseline. Original artwork in
the middle angles requires further semantic line and 3D anchor
correspondence for final animation-quality acceptance.
"""
 output=Path(output).resolve();output.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED,
                      compresslevel=3,allowZip64=True) as z:
  for name,path in sorted(files.items()):z.write(path,arcname=name)
  z.writestr("README.md",readme)
  z.writestr("package-manifest.json",json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
 with zipfile.ZipFile(output) as z:
  if z.testzip() is not None:raise ValueError("Original P0 archive CRC invalid")
  verify=json.loads(z.read("package-manifest.json"))
  for record in verify["files"]:
   if hashlib.sha256(z.read(record["path"])).hexdigest()!=record["sha256"]:
    raise ValueError("Original P0 archive content hash changed "+record["path"])
 report={
  "schema":"KOMA-P0-P12-ORIGINAL-VIEW-SOURCE-ARCHIVE-QA-V1",
  "characterId":"p0_character_001",
  "archivePath":str(output),"sha256":sha(output),"bytes":output.stat().st_size,
  "entryCount":len(files)+2,
  "sourceGaps":gap["registeredPairCount"],
  "sourceCandidateMethods":len(cmp["methods"]),
  "sourceBrowserScreenshots":browser["screenshotCount"],
  "P8OriginalMotionFrames":p8["frameCount"],
  "sourceP0SemanticSlots":39,
  "sourceP11ProfilePSDSHA256":p11["psdSHA256"],
  "internalHashesVerified":True,
  "artisticAcceptance":"PENDING"
 }
 qaPath=root/"p12-comparison/p12-package-qa.json"
 qaPath.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print(json.dumps(report,ensure_ascii=False,indent=2))
 return report

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--experiment",required=True)
 p.add_argument("--output",required=True)
 a=p.parse_args()
 package(a.experiment,a.output)

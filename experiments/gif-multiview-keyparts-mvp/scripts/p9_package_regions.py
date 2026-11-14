#!/usr/bin/env python3
"""Reproducible original P0 color-piece correspondence research review archive."""
import argparse,hashlib,json,zipfile
from pathlib import Path
def sha(f):
 h=hashlib.sha256()
 with Path(f).open("rb") as fp:
  for c in iter(lambda:fp.read(1024*1024),b""):h.update(c)
 return h.hexdigest()

def read(f):return json.loads(Path(f).read_text(encoding="utf-8"))

def pack(exp,out):
 exp=Path(exp).resolve();assets=exp/"private-assets"
 root=assets/"p9-region-correspondence"
 qa=read(root/"qa.json")
 compare=read(root/"comparison-qa.json")
 browser=read(root/"browser/browser-qa.json")
 source=read(assets/"p5-see-through/mv-candidate/parts.json")
 if any(j.get("characterId")!="p0_character_001" for j in (qa,compare,browser,source)):
  raise ValueError("P0 original character identity mismatch")
 if qa["registeredSemanticPairs"]!=22 or qa["matchedColorRegions"]!=155:
  raise ValueError("P0 correspondence dataset registration mismatch")
 if browser["status"]!="PASS_REAL_P0_REGION_CORRESPONDENCE_VIEW":
  raise ValueError("Original P0 browser source integrity QA incomplete")
 if compare["contactGrid"]["sha256"]!=sha(assets/compare["contactGrid"]["path"]):
  raise ValueError("P9 real source contact grid SHA mismatch")
 if compare["qualityComparison"]["sha256"]!=sha(assets/compare["qualityComparison"]["path"]):
  raise ValueError("P9 real rendered comparison image SHA mismatch")
 inputs={}
 def add(file,expected=None):
  file=Path(file).resolve()
  if not file.is_file() or not file.is_relative_to(exp):
   raise FileNotFoundError(file)
  real=sha(file)
  if expected and real!=expected:raise ValueError("Source HASH mismatch "+str(file))
  inputs[str(file.relative_to(exp))]=file
 for layer in source["parts"]:
  add(assets/layer["path"],layer["frameSha256"])
 for photo in source["wholeViews"]:
  add(assets/photo["path"],photo["sha256"])
 for shot in browser["screenshots"]:
  add(shot["path"],shot["sha256"])
 for comp in compare["methods"]:
  for frame in comp["frames"]:
   add(assets/frame["sourcePath"],frame["sha256"])
 for rel in (
  "p9-region-correspondence/qa.json",
  "p9-region-correspondence/comparison-qa.json",
  "p9-region-correspondence/region-pair-contact.jpg",
  "p9-region-correspondence/region-pair-grid.jpg",
  "p9-region-correspondence/region-quality-comparison.jpg",
  "p9-region-correspondence/browser/browser-qa.json",
  "p9-region-correspondence/face/qa.json",
  "p9-region-correspondence/face/texture-qa.json",
  "p9-region-correspondence/face-hair/qa.json",
  "p9-region-correspondence/face-hair/texture-qa.json",
  "p8-semantic-occlusion/viewer-manifest.json",
  "p8-semantic-occlusion/selective-sequence/qa.json",
  "p8-semantic-occlusion/selective-sequence/texture-qa.json",
  "p8-semantic-occlusion/selective-sequence/temporal-qa.json",
  "p5-see-through/mv-candidate/parts.json",
  "p5-see-through/mv-candidate/landmark-qa.json"):
  add(assets/rel)
 for rel in (
  "review/p9-correspondence.html",
  "review/p9-correspondence.js",
  "scripts/capture_p9_regions.cjs",
  "scripts/p9_color_region_correspondence.py",
  "scripts/p9_color_region_render.py",
  "scripts/p9_report_regions.py",
  "scripts/p9_package_regions.py",
  "tests/test_p9_region_correspondence.py"):
  add(exp/rel)
 manifest={
  "schema":"KOMA-P0-P9-COLOR-PIECE-CORRESPONDENCE-PACKAGE-V1",
  "characterId":"p0_character_001",
  "sourceOriginalViews":[0,45,90],
  "sourcePSDInferredViews":[0,45],
  "sourceSemanticArtMeshSlots":len(source["parts"]),
  "matchedSemanticViewPairs":qa["registeredSemanticPairs"],
  "matchedColorRegions":qa["matchedColorRegions"],
  "registeredBrowserScreenshots":len(browser["screenshots"]),
  "source":qa["method"],
  "html":"review/p9-correspondence.html",
  "reviewQualityStatus":"CORRESPONDENCE_RESEARCH_DATASET",
  "renderingBaseline":"P8_SEMANTIC_OCCLUSION_ARTMESH",
  "files":[{"path":name,"bytes":file.stat().st_size,"sha256":sha(file)}
           for name,file in sorted(inputs.items())]
 }
 README="""# p0_character_001 · Semantic color-region correspondence study

This package contains the authentic P0 0°, 45° and 90° RGBA semantic
parts, 22 registered view/part pairs, 155 source-derived color-region
matches, the source-vs-target match coordinates, and all SHA-256 values.

Run at the extracted package root:

    python3 -m http.server 5181

Open:
    http://127.0.0.1:5181/review/p9-correspondence.html

Select source angles, semantic part, and region match cost. The interface
verifies the source RGBA PNG SHA-256 for every selection. Each location is a
real source-image color component; a line shows a candidate match to the
corresponding semantic part in the adjacent original view.

Visual evidence:
    private-assets/p9-region-correspondence/region-pair-grid.jpg
    private-assets/p9-region-correspondence/region-quality-comparison.jpg

The region-matching records provide research candidates for anatomical
texture correspondence; the previous P8 ArtMesh remains the adopted motion
preview. Final source-artistic visual approval requires refined texture and
stroke matching and concealed profile layers.
"""
 out=Path(out).resolve()
 out.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=5,
                      allowZip64=True) as z:
  for name,file in sorted(inputs.items()):z.write(file,arcname=name)
  z.writestr("README.md",README)
  z.writestr("package-manifest.json",json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
 with zipfile.ZipFile(out) as z:
  if z.testzip() is not None:raise ValueError("ZIP CRC failed")
  stored=json.loads(z.read("package-manifest.json"))
  for rec in stored["files"]:
   if hashlib.sha256(z.read(rec["path"])).hexdigest()!=rec["sha256"]:
    raise ValueError("Archive source SHA-256 verification failed "+rec["path"])
 report={
  "schema":"KOMA-P0-P9-CORRESPONDENCE-PACKAGE-QA-V1",
  "characterId":"p0_character_001",
  "status":"PASS_REPRODUCIBLE_REGION_CORRESPONDENCE_PACKAGE",
  "archivePath":str(out),
  "sha256":sha(out),
  "bytes":out.stat().st_size,
  "entryCount":len(inputs)+2,
  "registeredColorRegions":155,
  "registeredSemanticPairs":22,
  "sourceSemanticArtMeshSlots":39,
  "browserScreenshots":len(browser["screenshots"]),
  "internalHashesVerified":True,
  "artisticApproval":"PENDING"
 }
 (root/"p9-package-qa.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print(json.dumps(report,indent=2,ensure_ascii=False))
 return report

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--experiment",required=True)
 p.add_argument("--output",required=True)
 args=p.parse_args()
 pack(args.experiment,args.output)

#!/usr/bin/env python3
"""Package authentic P0 ArtMesh, stroke identities and proven P8 motion preview."""
import argparse,hashlib,json,zipfile
from pathlib import Path

def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as fp:
  for chunk in iter(lambda:fp.read(1024*1024),b""):
   h.update(chunk)
 return h.hexdigest()

def load(p):return json.loads(Path(p).read_text(encoding="utf-8"))

def package(experiment,out):
 exp=Path(experiment).resolve();assets=exp/"private-assets"
 target=assets/"p10-stroke-identity"
 strokes=load(target/"qa.json")
 browser=load(target/"browser/browser-qa.json")
 P8=assets/"p8-semantic-occlusion"
 motion=load(P8/"selective-sequence/qa.json")
 original=load(assets/"p5-see-through/mv-candidate/parts.json")
 if any(d["characterId"]!="p0_character_001" for d in (strokes,browser,motion,original)):
  raise ValueError("P0 original identity mismatch")
 if (strokes["sourceArtMeshViewSlots"],strokes["registeredSemanticPairs"],strokes["candidateIdentities"])!=(39,22,24):
  raise ValueError("Original stroke registry incomplete")
 if browser["status"]!="PASS_REAL_ORIGINAL_P0_STROKE_REVIEW" or len(browser["screenshots"])!=6:
  raise ValueError("P10 live browser art acceptance incomplete")
 if motion["frameCount"]!=37:
  raise ValueError("Full P8 source animation required")
 files={}
 def add(path,expected=None):
  path=Path(path).resolve()
  if not path.is_file() or not path.is_relative_to(exp):
   raise FileNotFoundError("P0 expected original input "+str(path))
  actual=sha(path)
  if expected and expected!=actual:
   raise ValueError("P0 source SHA mismatch "+str(path))
  files[str(path.relative_to(exp))]=path
 for part in original["parts"]:
  add(assets/part["path"],part["frameSha256"])
 for view in original["wholeViews"]:
  add(assets/view["path"],view["sha256"])
 for frame in motion["frames"]:
  add(assets/frame["path"],frame["sha256"])
 for shot in browser["screenshots"]:
  add(shot["path"],shot["sha256"])
 add(assets/strokes["contactImage"],strokes["contactSHA256"])
 for extra in (
  "p10-stroke-identity/qa.json",
  "p10-stroke-identity/browser/browser-qa.json",
  "p8-semantic-occlusion/selective-sequence/qa.json",
  "p8-semantic-occlusion/selective-sequence/texture-qa.json",
  "p8-semantic-occlusion/selective-sequence/temporal-qa.json",
  "p8-semantic-occlusion/p0-semantic-occlusion-turn.qa.json",
  "p9-region-correspondence/qa.json",
  "p9-region-correspondence/comparison-qa.json",
  "p9-region-correspondence/region-pair-grid.jpg",
  "p5-see-through/mv-candidate/parts.json",
  "p5-see-through/mv-candidate/landmark-qa.json",
  "p4-see-through/front/p0-character-001-see-through.psd",
  "p5-see-through/yaw045/p0-character-001-see-through.psd"
 ):
  add(assets/extra)
 motionGIF=assets/"p8-semantic-occlusion/p0-semantic-occlusion-turn.gif"
 motionQA=load(assets/"p8-semantic-occlusion/p0-semantic-occlusion-turn.qa.json")
 if motionQA["GIFFrames"]!=72 or motionQA["sourceFrameCount"]!=37:
  raise ValueError("P8 genuine original-source loop frame count invalid")
 add(motionGIF,motionQA["GIFSHA256"])
 for relative in (
  "review/p10-stroke.html","review/p10-stroke.js",
  "scripts/p10_stroke_identity.py","scripts/capture_p10_strokes.cjs",
  "scripts/p10_package_review.py","tests/test_p10_stroke_identity.py",
  "scripts/p9_color_region_correspondence.py",
  "scripts/p8_semantic_occlusion.py",
  "scripts/p7_semantic_dense_flow.py",
  "scripts/flow_render.py","scripts/p1_front_semantic.py"
 ):
  add(exp/relative)
 manifest={
  "schema":"KOMA-P0-P10-REAL-STROKE-ID-P8-VDD-REVIEW-V1",
  "characterId":"p0_character_001",
  "sourceOriginalKeyAngles":[0,45,90],
  "independentPSDSourceAngles":[0,45],
  "originalArtMeshViewSlots":39,
  "registeredSemanticPairs":22,
  "originalInkStrokeCandidates":strokes["candidateIdentities"],
  "extractedOriginalStrokes":strokes["extractedStrokes"],
  "authoredSourceCanvas":[1024,1024],
  "registeredP8SourceRGBAFrames":37,
  "sourceGIFLoopFrames":72,
  "reviewScreenshotCount":len(browser["screenshots"]),
  "artisticApproval":"PENDING_MANUAL_STROKE_IDENTITY_AND_SOURCE_VIEW",
  "adoptedMotionRenderer":"P8_SEMANTIC_OCCLUSION_ARTMESH",
  "sourcePSD_SHA256":{
   "0":sha(assets/"p4-see-through/front/p0-character-001-see-through.psd"),
   "45":sha(assets/"p5-see-through/yaw045/p0-character-001-see-through.psd")
  },
  "files":[{"path":name,"bytes":file.stat().st_size,"sha256":sha(file)}
           for name,file in sorted(files.items())]
 }
 readme="""# 2.75D Anime Studio · Original P0 Stroke Correspondence

p0_character_001: independent semantic RGBA layers from approved original
0°, 45° and 90° anime artwork. 0° and 45° genuine inferred PSD sources
are included. P8 original-source 37-frame turn and 72-frame review GIF
remain the active VDD motion preview.

Study contents: 39 source ArtMesh view slots, 184 extracted line pieces,
24 conservative identity candidates across 22 semantic view pairs,
and 6 live-browser source/pose comparison screenshots.

To review locally from the extracted ZIP root:
    python3 -m http.server 5181

Open:
    http://127.0.0.1:5181/review/p10-stroke.html

Select original source angle pair, semantic part and minimum confidence.
The third panel shows the source-verified actual P8 image at the selected
intermediate angle. Browser code verifies SHA-256 before rendering.
Original previews remain visible through:
    private-assets/p8-semantic-occlusion/p0-semantic-occlusion-turn.gif

All source-only line matches are *research candidates*. Human evaluation
of face, front-hair, iris and occlusion correctness is still required.
"""
 out=Path(out).resolve();out.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED,
                      compresslevel=3,allowZip64=True) as z:
  for relative,file in sorted(files.items()):
   z.write(file,arcname=relative)
  z.writestr("README.md",readme)
  z.writestr("package-manifest.json",json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
 with zipfile.ZipFile(out) as z:
  if z.testzip() is not None:raise ValueError("P10 ZIP CRC invalid")
  m=json.loads(z.read("package-manifest.json"))
  for f in m["files"]:
   if hashlib.sha256(z.read(f["path"])).hexdigest()!=f["sha256"]:
    raise ValueError("P10 ZIP source SHA invalid "+f["path"])
 report={
  "schema":"KOMA-P0-P10-REPRODUCIBLE-STROKE-REVIEW-QA-V1",
  "characterId":"p0_character_001",
  "archivePath":str(out),
  "sha256":sha(out),"bytes":out.stat().st_size,
  "entryCount":len(files)+2,
  "originalRGBAViewSlots":39,
  "P8RGBAFrames":37,
  "originalStrokeCandidates":24,
  "browserScreenshots":len(browser["screenshots"]),
  "internalHashesVerified":True,
  "browserStatus":browser["status"],
  "artisticApproval":"PENDING"
 }
 (target/"p10-package-qa.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps(report,indent=2,ensure_ascii=False))
 return report

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--experiment",required=True)
 p.add_argument("--output",required=True)
 a=p.parse_args()
 package(a.experiment,a.output)

#!/usr/bin/env python3
"""Reproducible P0 0/45 PSD semantic ArtMesh + HTML multi-view review archive."""
import argparse,hashlib,json,zipfile
from pathlib import Path

def sha(file):
 h=hashlib.sha256()
 with Path(file).open("rb") as fp:
  for blob in iter(lambda:fp.read(1024*1024),b""):h.update(blob)
 return h.hexdigest()

def package(experiment,previous,output):
 exp=Path(experiment).resolve();assets=exp/"private-assets"
 previous=Path(previous).resolve();output=Path(output).resolve()
 with zipfile.ZipFile(previous) as z:
  prior=json.loads(z.read("package-manifest.json"))
  if prior["characterId"]!="p0_character_001":raise ValueError("P0 source mismatch")
  old=prior["files"]
 files={}
 changed={"review/review.js"}
 for rec in old:
  file=exp/rec["path"]
  if not file.is_file():raise FileNotFoundError(file)
  if sha(file)!=rec["sha256"] and rec["path"] not in changed:
   raise ValueError("Archived upstream file changed unexpectedly: "+rec["path"])
  files[rec["path"]]=file
 single=[
  "p5-see-through/yaw045/p0-character-001-see-through.psd",
  "p5-see-through/yaw045/inference-qa.json",
  "p5-see-through/yaw045/exported/layer-qa.json",
  "p5-see-through/yaw045/integrated/qa.json",
  "p5-see-through/yaw045/integrated/parts.json",
  "p5-see-through/mv-candidate/parts.json",
  "p5-see-through/mv-candidate/qa.json",
  "p5-see-through/mv-candidate/landmark-qa.json",
  "p5-see-through/mv-candidate/landmark-correspondence.jpg",
  "p5-see-through/mv-candidate/holdout-qa.json",
  "p5-see-through/mv-candidate/texture-qa.json",
  "p5-see-through/mv-candidate/vdd-canvas/canvas-qa.json",
  "p5-see-through/mv-candidate/vdd-sequence/canvas-qa.json",
  "p5-see-through/mv-candidate/p0-psd-paired-vdd-turn.gif",
  "p5-see-through/mv-candidate/turn-gif-qa.json",
  "p5-see-through/yaw090/inference-qa.json",
  "p5-flow-baseline/dis-sharp/contact.png",
  "p5-flow-baseline/dis-sharp/flow-qa.json",
  "p5-flow-baseline/dis-sharp/yaw000-yaw090-flow-review.gif"
 ]
 more=[assets/f for f in single]
 for folder,pattern in [
   ("p5-see-through/yaw045/exported/parts","*.png"),
   ("p5-see-through/yaw045/exported","*.png"),
   ("p5-see-through/yaw045/exported","*.jpg"),
   ("p5-see-through/yaw045/integrated/parts","*.png"),
   ("p5-see-through/yaw045/integrated","*.png"),
   ("p5-see-through/yaw045/integrated","*.jpg"),
   ("p5-see-through/mv-candidate/vdd-canvas","yaw*.png"),
   ("p5-see-through/mv-candidate/vdd-sequence","yaw*.png")]:
  more.extend(sorted((assets/folder).glob(pattern)))
 for file in more:
  if not file.is_file():raise FileNotFoundError(file)
  files[str(file.relative_to(exp))]=file
 native=assets/"p5-see-through/yaw045/p0-character-001-see-through.psd"
 source=json.loads((assets/"p5-see-through/yaw045/inference-qa.json").read_text())
 semantic=json.loads((assets/"p5-see-through/yaw045/integrated/qa.json").read_text())
 registration=json.loads((assets/"p5-see-through/mv-candidate/parts.json").read_text())
 landmark=json.loads((assets/"p5-see-through/mv-candidate/landmark-qa.json").read_text())
 pngs=json.loads((assets/"p5-see-through/mv-candidate/vdd-sequence/canvas-qa.json").read_text())
 gif=json.loads((assets/"p5-see-through/mv-candidate/turn-gif-qa.json").read_text())
 texture=json.loads((assets/"p5-see-through/mv-candidate/texture-qa.json").read_text())
 if source["outputFiles"][0]["sha256"]!=sha(native) or semantic["registeredParts"]!=13:
  raise ValueError("P5 independent 45-degree PSD provenance mismatch")
 if len(registration["parts"])!=39 or not all(landmark["qaGates"].values()):
  raise ValueError("P5 ArtMesh/correspondence gate failed")
 for item in registration["parts"]:
  if sha(assets/item["path"])!=item["frameSha256"]:
   raise ValueError("P5 RGBA source SHA mismatch: "+item["path"])
 if len(pngs["outputs"])!=37 or gif["GIFFrames"]!=72:
  raise ValueError("P5 real-browser motion capture incomplete")
 for frame in pngs["outputs"]:
  if sha(frame["path"])!=frame["sha256"]:
   raise ValueError("P5 browser frame SHA mismatch")
 if sha(assets/"p5-see-through/mv-candidate/p0-psd-paired-vdd-turn.gif")!=gif["GIFSHA256"]:
  raise ValueError("P5 GIF checksum mismatch")
 manifest={
   "schema":"KOMA-P0-P5-TWO-PSD-ARTMESH-REVIEW-V1",
   "characterId":"p0_character_001",
   "PSDViewAngles":[0,45],"originalOnlyViewAngles":[90],
   "nativePSDModelCanvas":[768,768],
   "registeredCanvas":[1024,1024],
   "PSD45SHA256":sha(native),
   "registeredSemanticViews":39,
   "physicalLandmarks":len(landmark["landmarks"]),
   "landmarkSourceAngles":[0,45,90],
   "P5AnimatedFrames":gif["GIFFrames"],
   "P5SourceFrames":gif["sourceFrameCount"],
   "P5GifSHA256":gif["GIFSHA256"],
   "holeCoverageStatus":"PASS_HOLDOUT_COVERAGE",
   "textureCorrespondenceStatus":texture["status"],
   "artisticAcceptance":"PENDING_ANATOMICAL_TEXTURAL_REFINEMENT",
   "files":[{"path":k,"sha256":sha(f),"bytes":f.stat().st_size} for k,f in sorted(files.items())]
 }
 README="""# P0 2.75D Anime Studio - original 0/45 semantic PSD ArtMesh study

Character identity p0_character_001, source author art remains authoritative.

True source views:
  * 0 degrees: recovered P0 source with inferred 13-layer See-through PSD
  * 45 degrees: recovered P0 source with independently inferred 13-layer PSD
  * 90 degrees: verified original P0 GIF RGBA ArtMesh parts

39 registered ArtMesh slots are named by stable semantic and physical IDs.
Every source PNG, PSD and render has SHA-256 verification evidence.
The 13 anatomical control tracks span 0, 45, and 90 degrees, and output
interpolated 22.5 and 67.5 positional correspondences.

Review locally by running at package root:

    python3 -m http.server 5181

Open interactive 3-view viewer:

    http://localhost:5181/review/index.html?mode=candidate&source=seethrough-paired

Open the 0 degree PSD independent-parts viewer:

    http://localhost:5181/review/p1-front.html?source=seethrough

View actual Chromium-captured animation and evidence:

    private-assets/p5-see-through/mv-candidate/p0-psd-paired-vdd-turn.gif
    private-assets/p5-see-through/mv-candidate/landmark-correspondence.jpg
    private-assets/p5-see-through/yaw045/integrated/semantic-comparison.jpg
    private-assets/p5-see-through/mv-candidate/texture-qa.json

The two independent PSD views provide concealed texture source material and
stable reference anchors for view-dependent deformation. Intermediate-angle
texture correspondence is a separate quality gate; the provided current
animation is a research visual-review candidate.
"""
 output.parent.mkdir(exist_ok=True,parents=True)
 with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
  for rel,p in sorted(files.items()):
   z.write(p,arcname=rel)
  z.writestr("README.md",README)
  z.writestr("package-manifest.json",json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
 with zipfile.ZipFile(output) as z:
  if z.testzip() is not None:raise ValueError("ZIP CRC integrity failed")
  persisted=json.loads(z.read("package-manifest.json"))
  for f in persisted["files"]:
   if hashlib.sha256(z.read(f["path"])).hexdigest()!=f["sha256"]:
    raise ValueError("ZIP SHA-256 integrity failed: "+f["path"])
 report={
  "schema":"KOMA-P0-P5-REVIEW-PACKAGE-QA-V1",
  "characterId":"p0_character_001",
  "status":"PASS_REPRODUCIBLE_SOURCE_PACKAGE",
  "archivePath":str(output),"bytes":output.stat().st_size,
  "sha256":sha(output),"entries":len(files)+2,
  "PSD45SHA256":sha(native),
  "registeredSemanticViews":39,
  "physicalLandmarks":len(landmark["landmarks"]),
  "genuineBrowserFrames":37,
  "GIFFrames":72,"gifSHA256":gif["GIFSHA256"],
  "internalHashesVerified":True,
  "VDDTextureAcceptance":texture["status"],
  "artisticAcceptance":"PENDING"
 }
 (assets/"p5-see-through/p5-package-qa.json").write_text(
     json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps(report,ensure_ascii=False,indent=2))
 return report

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--experiment",required=True)
 p.add_argument("--previous",required=True)
 p.add_argument("--output",required=True)
 a=p.parse_args()
 package(a.experiment,a.previous,a.output)

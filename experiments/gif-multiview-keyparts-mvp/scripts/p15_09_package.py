#!/usr/bin/env python3
"""Reproducible P15-09 offline HTML and registered P0 frame review archive."""
from __future__ import annotations
import hashlib,json,zipfile
from pathlib import Path

BASE=Path(__file__).resolve().parent.parent
ASSETS=BASE/"private-assets"
ZIP=ASSETS/"exports/p15-09-anchor-midarc-review.zip"
EVIDENCE=BASE/"evidence/p15-09-delivery.json"
ANGLES=[45.,47.5,50.,52.5,55.,57.5,60.,62.5,65.]


def sha(data):return hashlib.sha256(data).hexdigest()


def file_id(angle):
 return "yaw"+(str(int(angle)) if angle.is_integer() else str(angle).replace(".","p"))+".png"


def main():
 required={
 "review/p15-09-midarc.html","review/p15-09-midarc.js",
 "evidence/p15-09-anchor-pose-qa.json","evidence/p15-09-midarc-qa.json",
 "private-assets/p15-09-midarc/browser/qa.json",
 "private-assets/p15-09-anchor-pose/p15-09-pose-contact.jpg",
 "private-assets/p15-09-midarc/p15-09-midarc-contact.jpg",
 }
 for angle in ANGLES:
  name=file_id(angle)
  for folder in (
   "p8-semantic-occlusion/selective-sequence",
   "p15-07-wholekey-preview",
   "p15-09-midarc"):
   required.add("private-assets/"+folder+"/"+name)
 browser=json.loads((ASSETS/"p15-09-midarc/browser/qa.json").read_text())
 if browser["status"]!="HTML_SOURCE_AND_RENDERED_FRAMES_VERIFIED":
  raise RuntimeError("Browser QA required")
 for shot in browser["screenshots"]:
  required.add(shot["imagePath"])
 allfiles=[]
 for rel in sorted(required):
  f=BASE/rel
  if not f.is_file():raise FileNotFoundError(f)
  allfiles.append((rel,f,f.read_bytes()))
 manifest={
  "schema":"KOMA-P15-09-REVIEW-ARCHIVE-V1",
  "characterId":"p0_character_001",
  "htmlEntry":"review/p15-09-midarc.html",
  "renderedAngles":ANGLES,
  "renderedFrameSources":["P8","P15-07","P15-09"],
  "sourceLineage":"P0 45 original + P5 anchors + P15 65 painting",
  "artisticStatus":"POSE_REFERENCE_REQUIRES_VISUAL_REVIEW",
  "files":[{"path":name,"bytes":len(data),"sha256":sha(data)} for name,_,data in allfiles]
 }
 ZIP.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(ZIP,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=4) as arc:
  for name,f,data in allfiles:
   zi=zipfile.ZipInfo(name,(2026,11,10,0,0,0))
   zi.compress_type=zipfile.ZIP_DEFLATED
   zi.external_attr=(0o100644<<16)
   arc.writestr(zi,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=4)
  zi=zipfile.ZipInfo("manifest.json",(2026,11,10,0,0,0))
  zi.compress_type=zipfile.ZIP_DEFLATED
  arc.writestr(zi,json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
 with zipfile.ZipFile(ZIP) as arc:
  if arc.testzip() is not None:raise AssertionError("ZIP CRC differs")
  for item in manifest["files"]:
   if sha(arc.read(item["path"]))!=item["sha256"]:
    raise AssertionError("Archive data differs: "+item["path"])
 report={
  "schema":"KOMA-P15-09-PRIVATE-REVIEW-ASSET-V1",
  "characterId":"p0_character_001",
  "archivePath":str(ZIP.relative_to(BASE)),
  "sha256":sha(ZIP.read_bytes()),
  "bytes":ZIP.stat().st_size,
  "verifiedEntries":len(allfiles)+1,
  "htmlEntry":manifest["htmlEntry"],
  "renderedFrameCount":len(ANGLES)*3,
  "browserScreenshotCount":browser["captureCount"],
  "artisticStatus":"POSE_REFERENCE_REQUIRES_VISUAL_REVIEW"
 }
 EVIDENCE.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps(report,ensure_ascii=False))
if __name__=="__main__":main()

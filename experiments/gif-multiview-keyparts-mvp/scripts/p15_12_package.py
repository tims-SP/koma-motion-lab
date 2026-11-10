#!/usr/bin/env python3
"""Deterministic P15-12 offline camera-constraint and art review archive."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED

BASE=Path(__file__).resolve().parent.parent
PRIVATE=BASE/"private-assets"
ARCHIVE=PRIVATE/"exports/p15-12-camera-pose-review.zip"
PROOF=BASE/"evidence/p15-12-delivery.json"

def digest(b):return hashlib.sha256(b).hexdigest()

def main():
 proxy=json.loads((BASE/"evidence/p15-12-camera-proxy-qa.json").read_text())
 art=json.loads((BASE/"evidence/p15-12-guided-candidate-qa.json").read_text())
 browser=json.loads((PRIVATE/"p15-12-camera-proxy/browser/qa.json").read_text())
 if proxy["status"]!="NUMERIC_CAMERA_PROXY_VERIFIED" or browser["status"]!="INTERACTIVE_CAMERA_PROXY_HTML_VERIFIED":
  raise AssertionError("Camera and browser QA required")
 if art["generatedCount"]!=2 or art["independentlyPaintedKeyframesAdmitted"]!=0:
  raise AssertionError("Source art admission differs")
 paths={"review/p15-12-pose-calibration.html",
        "evidence/p15-12-camera-proxy-qa.json",
        "evidence/p15-12-guided-candidate-qa.json",
        "private-assets/p15-12-camera-proxy/browser/qa.json",
        "private-assets/"+art["contactPath"],
        "private-assets/p2-views/whole/yaw045.png",
        "private-assets/p15-independent-candidates/yaw065-source-rgba.png"}
 for frame in proxy["frames"]:
  if "guide" not in frame or frame["yaw"] not in [57.5,60]:continue
  paths.update("private-assets/"+frame["guide"][field+"Path"]
    for field in ("conditioning","annotated"))
  angle=str(frame["yaw"]).replace(".","p")
  paths.add("private-assets/p15-10-semantic-pose/arc/yaw"+angle+".png")
 for item in art["generated"]:paths.add("private-assets/"+item["sourcePath"])
 for shot in browser["captures"]:paths.add(shot["relativePath"])
 data=[]
 for rel in sorted(paths):
  f=BASE/rel
  if not f.is_file():raise FileNotFoundError(f)
  raw=f.read_bytes();data.append((rel,raw))
 manifest={
  "schema":"KOMA-P15-12-PROVENANCE-REVIEW-V1",
  "characterId":"p0_character_001",
  "entryHtml":"review/p15-12-pose-calibration.html",
  "angles":[57.5,60],"guideRole":"2.5D calibrated pose approximation",
  "acceptedIndependentPaintings":0,"candidateCount":2,
  "files":[{"path":name,"bytes":len(b),"sha256":digest(b)} for name,b in data]
 }
 data.append(("manifest.json",(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+"\n").encode()))
 ARCHIVE.parent.mkdir(parents=True,exist_ok=True)
 with ZipFile(ARCHIVE,"w",compression=ZIP_DEFLATED,compresslevel=4) as z:
  for rel,b in data:
   x=ZipInfo(rel,(2026,11,10,0,0,0));x.external_attr=0o100644<<16;x.compress_type=ZIP_DEFLATED
   z.writestr(x,b,compress_type=ZIP_DEFLATED,compresslevel=4)
 with ZipFile(ARCHIVE) as z:
  if z.testzip() is not None:raise AssertionError("ZIP CRC differs")
  for row in manifest["files"]:
   if digest(z.read(row["path"]))!=row["sha256"]:
    raise AssertionError("Archive member hash mismatch: "+row["path"])
 report={"schema":"KOMA-P15-12-REVIEW-ARTIFACT-V1",
  "characterId":"p0_character_001",
  "archivePath":str(ARCHIVE.relative_to(BASE)),
  "sha256":digest(ARCHIVE.read_bytes()),"bytes":ARCHIVE.stat().st_size,
  "entries":len(data),"htmlEntry":manifest["entryHtml"],
  "cameraAnchors":proxy["roleCount"],"targetAngles":[57.5,60],
  "generatedSourceCandidates":art["generatedCount"],
  "browserCaptures":browser["screenshotCount"],
  "visualAcceptance":"ANATOMICAL_PAINTING_REVIEW_REQUIRED"}
 PROOF.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps(report,ensure_ascii=False))
 return report
if __name__=="__main__":main()

#!/usr/bin/env python3
"""Build source-hashed P15-13 offline ArtMesh structural review archive."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from zipfile import ZIP_DEFLATED,ZipFile,ZipInfo
from p15_13_structural_condition import ROOT,PRIVATE,REPORT
from p15_13_local_alignment import QA

ARCHIVE=PRIVATE/"exports/p15-13-structural-portrait-review.zip"
DELIVERY=ROOT/"evidence/p15-13-delivery.json"

def checksum(content):return hashlib.sha256(content).hexdigest()

def main():
 structural=json.loads(REPORT.read_text())
 aligned=json.loads(QA.read_text())
 browser=json.loads((PRIVATE/"p15-13-structural/browser/qa.json").read_text())
 if structural["characterId"]!="p0_character_001" or aligned["characterId"]!=structural["characterId"]:
  raise AssertionError("Identity source differs")
 if browser["status"]!="STRUCTURAL_CHANNELS_HTML_VERIFIED" or browser["captureCount"]!=10:
  raise AssertionError("Chromium review evidence missing")
 if structural["approvedIndependentKeyPaintings"] or aligned["independentPaintingsApproved"]:
  raise AssertionError("Approved art gate differs")
 required={
  "review/p15-13-structure.html",
  "evidence/p15-13-structural-qa.json",
  "evidence/p15-13-local-alignment-qa.json",
  "private-assets/p15-13-structural/browser/qa.json",
 }
 for entry in structural["frames"]:
  required.add("private-assets/"+entry["sourcePaintingPath"])
  for role in entry["semanticLayers"].values():
   required.add("private-assets/"+role["path"])
  for p in entry["outputs"].values():
   required.add("private-assets/"+p["path"])
  filename="yaw"+(str(int(entry["angle"])) if float(entry["angle"]).is_integer()
                 else str(entry["angle"]).replace(".","p"))
  required.add("private-assets/p15-10-semantic-pose/arc/"+filename+".png")
 for entry in aligned["frames"]:
  required.add("private-assets/"+entry["output"]["path"])
 for c in browser["captures"]:required.add(c["relativePath"])
 items=[]
 for name in sorted(required):
  f=ROOT/name
  if not f.is_file():raise FileNotFoundError(f)
  items.append((name,f.read_bytes()))
 manifest={"schema":"KOMA-P15-13-STRUCTURAL-REVIEW-ARCHIVE-V1",
   "characterId":"p0_character_001",
   "html":"review/p15-13-structure.html",
   "angles":structural["angles"],
   "semanticRoles":structural["sourceRoleOrder"],
   "artAdmitted":0,
   "sourceRoles":"P15-10 ArtMesh masks and P15-12 generated RGB paintings",
   "diagnosticRole":"P5 eye retargeting/heatmap/edge/owner map",
   "files":[{"path":name,"sha256":checksum(data),"bytes":len(data)}
            for name,data in items]}
 items.append(("manifest.json",(json.dumps(manifest,indent=2,ensure_ascii=False,sort_keys=True)+"\n").encode()))
 ARCHIVE.parent.mkdir(parents=True,exist_ok=True)
 with ZipFile(ARCHIVE,"w",compression=ZIP_DEFLATED,compresslevel=4) as z:
  for path,data in items:
   info=ZipInfo(path,(2026,11,10,0,0,0))
   info.compress_type=ZIP_DEFLATED;info.external_attr=0o100644<<16
   z.writestr(info,data,compress_type=ZIP_DEFLATED,compresslevel=4)
 with ZipFile(ARCHIVE) as z:
  if z.testzip():raise AssertionError("Archive CRC differs")
  for r in manifest["files"]:
   if checksum(z.read(r["path"]))!=r["sha256"]:
    raise AssertionError("File hash differs: "+r["path"])
 report={"schema":"KOMA-P15-13-DELIVERY-V1","characterId":"p0_character_001",
   "archivePath":str(ARCHIVE.relative_to(ROOT)),
   "sha256":checksum(ARCHIVE.read_bytes()),"bytes":ARCHIVE.stat().st_size,
   "entries":len(items),"angles":structural["angles"],
   "semanticRoleCount":len(structural["sourceRoleOrder"]),
   "chromiumScreenshots":browser["captureCount"],
   "chromiumSourceImagesLoaded":browser["totalImageLoads"],
   "htmlEntry":"review/p15-13-structure.html",
   "artisticStatus":"INDEPENDENT_KEYART_AND_OCCLUDED_INK_PENDING"}
 DELIVERY.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps(report,ensure_ascii=False))
 return report

if __name__=="__main__":main()

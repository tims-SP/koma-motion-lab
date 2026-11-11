#!/usr/bin/env python3
"""P15-38 P0 original 45°–65° 13-role layered HTML review archive."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
from p15_32_mesh_vdd import R,P

ROOT=P/"exports/p15-38-original-p0-arc-review"
FILE=P/"exports/p15-38-p0-original-arc-review.zip"
DELIVERY=R/"evidence/p15-38-delivery.json"

def sha(data):return hashlib.sha256(data).hexdigest()

def run():
 source=json.loads((R/"evidence/p15-38-extended-artmesh-qa.json").read_text())
 visual=json.loads((R/"evidence/p15-38-visual-review-qa.json").read_text())
 browser=json.loads((R/"evidence/p15-38-browser-qa.json").read_text())
 if {source["characterId"],visual["characterId"],browser["characterId"]}!={"p0_character_001"}:
  raise AssertionError("P0 source identity mismatch")
 if len(source["angles"])!=13 or browser["viewportChecks"]!=78:
  raise AssertionError("Verified source frame or browser state missing")
 if source["fullIndependentArtAdmission"]!=0:
  raise AssertionError("Independent art gate not met")
 paths=[(str(f.relative_to(ROOT)),f.read_bytes())
        for f in sorted(ROOT.rglob("*")) if f.is_file()]
 for item in ("p15-38-extended-artmesh-qa.json","p15-38-visual-review-qa.json",
              "p15-38-browser-qa.json"):
  file=R/"evidence"/item
  paths.append(("evidence/"+item,file.read_bytes()))
 manifest={"schema":"KOMA-P15-38-P0-45_TO65-ORIGINAL-ARTMESH-REVIEW-V1",
  "characterId":"p0_character_001","indexHtml":"index.html",
  "angles":source["angles"],"semanticRoles":source["roleCount"],
  "registeredP0_45SHA256":source["sourceOriginal45"]["sourceP0SHA256"],
  "originalRoleKeyframes":[45.,55.,57.5,60.,65.],
  "newCrossviewInbetweens":[47.5,50.,52.5],
  "artisticAdmission":0,
  "files":[{"path":name,"bytes":len(data),"sha256":sha(data)} for name,data in paths]}
 paths.append(("manifest.json",(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+"\n").encode()))
 FILE.parent.mkdir(parents=True,exist_ok=True)
 with ZipFile(FILE,"w",ZIP_DEFLATED,compresslevel=5) as zipf:
  for name,data in paths:
   z=ZipInfo(name,(2026,11,11,0,0,0));z.compress_type=ZIP_DEFLATED
   z.external_attr=0o100644<<16
   zipf.writestr(z,data,compress_type=ZIP_DEFLATED,compresslevel=5)
 with ZipFile(FILE) as z:
  if z.testzip() is not None:raise AssertionError("ZIP CRC mismatch")
  for row in manifest["files"]:
   if sha(z.read(row["path"]))!=row["sha256"]:
    raise AssertionError("Archive member digest differs: "+row["path"])
 report={"schema":"KOMA-P15-38-DELIVERY-V1","characterId":"p0_character_001",
  "zipPath":str(FILE.relative_to(R)),"sha256":sha(FILE.read_bytes()),
  "bytes":FILE.stat().st_size,"entriesVerified":len(paths),
  "htmlEntry":"index.html","frames":len(source["frames"]),"roles":source["roleCount"],
  "sourceP0Original45SHA256":source["sourceOriginal45"]["sourceP0SHA256"],
  "realBrowserChecks":browser["viewportChecks"],
  "browserImageLoads":browser["imageLoads"],
  "browserScreenshots":browser["screenshotCount"],
  "formalArtApproval":False}
 DELIVERY.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps(report,ensure_ascii=False))
 return report
if __name__=="__main__":run()

#!/usr/bin/env python3
"""P15-37 offline painted ArtMesh review with reproducible provenance manifest."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
from p15_32_mesh_vdd import R,P

ROOT=P/"exports/p15-37-temporal-art-review"
ARCHIVE=P/"exports/p15-37-temporal-art-review.zip"
DELIVERY=R/"evidence/p15-37-delivery.json"

def sha(data):return hashlib.sha256(data).hexdigest()

def run():
 q=json.loads((R/"evidence/p15-37-temporal-artmesh-qa.json").read_text())
 v=json.loads((R/"evidence/p15-37-visual-review-qa.json").read_text())
 b=json.loads((R/"evidence/p15-37-browser-qa.json").read_text())
 if {x["characterId"] for x in (q,v,b)}!={"p0_character_001"}:
  raise AssertionError("Provenance identity mismatch")
 if len(q["frames"])!=9 or len(v["frames"])!=9 or b["viewportChecks"]!=54:
  raise AssertionError("Review source incomplete")
 if q["fullKeyViewsArtApproved"]!=0 or v["formalArtistApproval"]:
  raise AssertionError("Full painting admission must be independent")
 assets=[(str(f.relative_to(ROOT)),f.read_bytes()) for f in sorted(ROOT.rglob("*")) if f.is_file()]
 evidence=[
 "p15-37-temporal-artmesh-qa.json",
 "p15-37-visual-review-qa.json",
 "p15-37-browser-qa.json"
 ]
 for file in evidence:
  src=R/"evidence"/file
  assets.append(("evidence/"+file,src.read_bytes()))
 manifest={"schema":"KOMA-P15-37-TEMPORAL-PAINTED-ARTMESH-ARCHIVE-V1",
    "characterId":"p0_character_001","htmlEntry":"index.html",
    "sourceP0SHA256":q["sourceP0Original45SHA256"],
    "sourceP15_36SHA256":q["sourceP15_36SHA256"],
    "registeredPoses":q["angles"],"modelPaintedKeyAngles":q["modelPaintedKeysExact"],
    "semanticRoleCount":len(q["roles"]),"registeredPaintedRoles":q["paintedRoles"],
    "source45Role":"reference identity only; 55-65 frames generated separately",
    "visualArtAdmission":0,
    "files":[{"path":p,"sha256":sha(data),"bytes":len(data)} for p,data in assets]}
 assets.append(("manifest.json",(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+"\n").encode()))
 ARCHIVE.parent.mkdir(parents=True,exist_ok=True)
 with ZipFile(ARCHIVE,"w",ZIP_DEFLATED,compresslevel=5) as z:
  for file,data in assets:
   member=ZipInfo(file,(2026,11,11,0,0,0))
   member.external_attr=0o100644<<16
   member.compress_type=ZIP_DEFLATED
   z.writestr(member,data,compress_type=ZIP_DEFLATED,compresslevel=5)
 with ZipFile(ARCHIVE) as z:
  if z.testzip():raise AssertionError("ZIP CRC mismatch")
  for rec in manifest["files"]:
   if sha(z.read(rec["path"]))!=rec["sha256"]:
    raise AssertionError("ZIP entry digest mismatch "+rec["path"])
 report={"schema":"KOMA-P15-37-DELIVERY-V1","characterId":"p0_character_001",
  "zipPath":str(ARCHIVE.relative_to(R)),
  "sha256":sha(ARCHIVE.read_bytes()),
  "bytes":ARCHIVE.stat().st_size,"entriesVerified":len(assets),
  "htmlEntry":"index.html","frames":len(q["frames"]),
  "semanticRoles":len(q["roles"]),"paintKeys":q["modelPaintedKeysExact"],
  "browserChecks":b["viewportChecks"],"imageLoads":b["imageLoads"],
  "browserScreenshots":b["screenshotCount"],
  "formalArtistAdmission":0}
 DELIVERY.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps(report,ensure_ascii=False))
 return report

if __name__=="__main__":run()

#!/usr/bin/env python3
"""Deterministic complete P15-34 offline HTML and source-provenance ZIP."""
from __future__ import annotations
import hashlib,json,zipfile
from pathlib import Path
from p15_32_mesh_vdd import R,P
OUTPUT=P/"exports/p15-34-source-ink-mesh-review"
ARCHIVE=P/"exports/p15-34-ink-mesh-review.zip"
REPORT=R/"evidence/p15-34-delivery.json"
def sha(b):return hashlib.sha256(b).hexdigest()
def make():
 browser=json.loads((R/"evidence/p15-34-browser-qa.json").read_text())
 qa=json.loads((OUTPUT/"qa.json").read_text())
 geometry=json.loads((R/"evidence/p15-34-feature-mesh-qa.json").read_text())
 ink=json.loads((R/"evidence/p15-34-ink-landmarks-qa.json").read_text())
 if browser["viewportChecks"]!=18 or len(qa["frames"])!=9:
  raise ValueError("Real browser/pose QA incomplete")
 if ink["verifiedIndependentArtistLandmarks"] or geometry["formalArtisticAcceptance"]:
  raise AssertionError("Visual source cannot be silently promoted")
 entries=[(str(p.relative_to(OUTPUT)),p.read_bytes())
          for p in sorted(OUTPUT.rglob("*")) if p.is_file()]
 entries+= [
   ("evidence/p15-34-ink-landmarks-qa.json",(R/"evidence/p15-34-ink-landmarks-qa.json").read_bytes()),
   ("evidence/p15-34-feature-mesh-qa.json",(R/"evidence/p15-34-feature-mesh-qa.json").read_bytes()),
   ("evidence/p15-34-browser-qa.json",(R/"evidence/p15-34-browser-qa.json").read_bytes())]
 manifest={"schema":"KOMA-P15-34-ARTMESH-INK-REVIEW-V1",
   "characterId":"p0_character_001","index":"index.html",
   "keyframeCount":5,"meshMidpointCount":4,
   "sourceReference":"P0 45 original SHA + P15-31 source ArtMesh",
   "sourceProvenance":"P15-34 automatically sampled painted pixels",
   "artistApproval":False,"productionVddModified":False,
   "files":[{"path":path,"sha256":sha(data),"bytes":len(data)} for path,data in entries]}
 entries.append(("manifest.json",(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+"\n").encode()))
 ARCHIVE.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(ARCHIVE,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=5) as z:
  for name,data in entries:
   record=zipfile.ZipInfo(name,(2026,11,11,0,0,0))
   record.compress_type=zipfile.ZIP_DEFLATED
   record.external_attr=0o100644<<16
   z.writestr(record,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=5)
 with zipfile.ZipFile(ARCHIVE) as z:
  if z.testzip() is not None:raise AssertionError("ZIP CRC mismatch")
  for record in manifest["files"]:
   if sha(z.read(record["path"]))!=record["sha256"]:
    raise AssertionError("Content digest differs: "+record["path"])
 delivery={"schema":"KOMA-P15-34-DELIVERY-V1",
   "characterId":"p0_character_001","zipPath":str(ARCHIVE.relative_to(R)),
   "sha256":sha(ARCHIVE.read_bytes()),"bytes":ARCHIVE.stat().st_size,
   "entriesVerified":len(entries),"htmlEntry":"index.html",
   "reviewFrames":9,"chromiumScreenshots":browser["screenshotCount"],
   "imagesLoaded":browser["imageLoads"],"artisticallyApproved":False}
 REPORT.write_text(json.dumps(delivery,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps(delivery,ensure_ascii=False))
 return delivery
if __name__=="__main__":make()

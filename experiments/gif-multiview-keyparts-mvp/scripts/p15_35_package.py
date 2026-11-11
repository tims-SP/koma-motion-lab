#!/usr/bin/env python3
"""Source-hashed reproducible P15-35 HTML review of depth and hair attachment."""
from __future__ import annotations
import hashlib,json,zipfile
from pathlib import Path
from p15_32_mesh_vdd import R,P

SOURCE=P/"exports/p15-35-face-depth-hair-review"
ARCHIVE=P/"exports/p15-35-face-depth-hair-review.zip"
QA=R/"evidence/p15-35-delivery.json"

def sha(data):return hashlib.sha256(data).hexdigest()

def build():
 scene=json.loads((R/"evidence/p15-35-occlusion-mount-qa.json").read_text())
 browser=json.loads((R/"evidence/p15-35-browser-qa.json").read_text())
 visual=json.loads((SOURCE/"qa.json").read_text())
 if scene["characterId"]!=browser["characterId"] or browser["characterId"]!=visual["characterId"]:
  raise AssertionError("P0 identity witness changed")
 if len(scene["frames"])!=9 or browser["viewportChecks"]!=18 or browser["imageLoads"]!=198:
  raise AssertionError("Actual browser/scene evidence incomplete")
 if scene["formalArtisticAcceptance"] or visual["artisticallyAccepted"]:
  raise AssertionError("Artist gate must be independent")
 entries=[(str(p.relative_to(SOURCE)),p.read_bytes()) for p in sorted(SOURCE.rglob("*")) if p.is_file()]
 for name in ("p15-35-occlusion-mount-qa.json","p15-35-browser-qa.json"):
  entries.append(("evidence/"+name,(R/"evidence"/name).read_bytes()))
 manifest={"schema":"KOMA-P15-35-CAMERA-DEPTH-AND-CLIP-ATTACHMENT-ARCHIVE-V1",
  "characterId":"p0_character_001","entry":"index.html","frames":9,
  "source":"P15-34 generated view-dependent ArtMesh and P0 original role provenance",
  "eyeCompleteUnderpaintRetained":True,"physical3DCertified":False,
  "independentPaintingsAccepted":0,
  "files":[{"path":name,"sha256":sha(data),"bytes":len(data)} for name,data in entries]}
 entries.append(("manifest.json",(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+"\n").encode()))
 ARCHIVE.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(ARCHIVE,"w",zipfile.ZIP_DEFLATED,compresslevel=5) as archive:
  for name,data in entries:
   entry=zipfile.ZipInfo(name,(2026,11,11,0,0,0))
   entry.external_attr=0o100644<<16
   entry.compress_type=zipfile.ZIP_DEFLATED
   archive.writestr(entry,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=5)
 with zipfile.ZipFile(ARCHIVE) as zipf:
  if zipf.testzip() is not None:raise AssertionError("ZIP CRC mismatch")
  for x in manifest["files"]:
   if sha(zipf.read(x["path"]))!=x["sha256"]:
    raise AssertionError("ZIP provenance SHA mismatch: "+x["path"])
 report={"schema":"KOMA-P15-35-DELIVERY-V1",
  "characterId":"p0_character_001","zipPath":str(ARCHIVE.relative_to(R)),
  "sha256":sha(ARCHIVE.read_bytes()),"bytes":ARCHIVE.stat().st_size,
  "entriesVerified":len(entries),"htmlEntry":"index.html",
  "reviewFrames":9,"chromiumScreenshots":browser["screenshotCount"],
  "imagesLoaded":browser["imageLoads"],"physical3DVerified":False,
  "artisticallyApproved":False}
 QA.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps(report,ensure_ascii=False))
 return report

if __name__=="__main__":build()

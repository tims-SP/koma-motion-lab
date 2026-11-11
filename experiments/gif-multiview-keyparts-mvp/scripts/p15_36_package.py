#!/usr/bin/env python3
"""Package complete P15-36 13-role RGBA sets and interactive painting review."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from zipfile import ZipInfo,ZipFile,ZIP_DEFLATED
from p15_32_mesh_vdd import R,P,slug
from p15_35_depth_mount import ROLES
REVIEW=P/"exports/p15-36-original-keypart-review"
SOURCE=P/"p15-36-qwen-local-paint"
ARCHIVE=P/"exports/p15-36-original-keypart-review.zip"
QA=R/"evidence/p15-36-delivery.json"

def sha(data):return hashlib.sha256(data).hexdigest()

def run():
 source=json.loads((R/"evidence/p15-36-qwen-local-repair-qa.json").read_text())
 cel=json.loads((R/"evidence/p15-36-cel-keypart-qa.json").read_text())
 browser=json.loads((R/"evidence/p15-36-browser-qa.json").read_text())
 review=json.loads((REVIEW/"qa.json").read_text())
 if source["characterId"]!=cel["characterId"] or source["characterId"]!=browser["characterId"]:
  raise AssertionError("P0 source identity drift")
 if browser["viewportChecks"]!=12 or browser["imageLoads"]!=48 or len(review["frames"])!=2:
  raise AssertionError("Interactive review not completed")
 if source["fullKeyviewArtAccepted"] or cel["fullKeyviewArtistApproval"]:
  raise AssertionError("Art admissions must remain separate")
 entries=[(str(f.relative_to(REVIEW)),f.read_bytes())
          for f in sorted(REVIEW.rglob("*")) if f.is_file()]
 for frame in source["frames"]:
  angle=slug(frame["yaw"]);folder=SOURCE/angle
  for role in ROLES:
   f=folder/(role+".png")
   if not f.is_file():raise FileNotFoundError(f)
   entries.append((f"roles/{angle}/{role}.png",f.read_bytes()))
  for name in ("eye.far.original-underpaint.png","eye.far.hidden-original.png"):
   f=folder/name;entries.append((f"roles/{angle}/{name}",f.read_bytes()))
 for name in ("p15-36-qwen-local-repair-qa.json","p15-36-cel-keypart-qa.json",
              "p15-36-visual-review-qa.json","p15-36-browser-qa.json"):
  f=R/"evidence"/name
  entries.append(("evidence/"+name,f.read_bytes()))
 paths=[k for k,_ in entries]
 if len(paths)!=len(set(paths)):raise AssertionError("Duplicate path in review package")
 manifest={"schema":"KOMA-P15-36-ORIGINAL-PAINTED-KEYPART-REVIEW-V1",
  "characterId":"p0_character_001",
  "entryHtml":"index.html","keyframeAngles":source["angles"],
  "semanticRoles":ROLES,"roleCount":len(ROLES),
  "sourceOfNewPaint":"Qwen-Image-Edit-2511 local RGB plus original vector cel control",
  "newModelPaintedROIRoles":source["newModelPaintedROIRoles"],
  "acceptedCompleteKeyviews":0,"independentlyDrawnHiddenUnderpaintApproved":0,
  "sourceP0RGBAndEyeUnderpaintPreserved":True,
  "files":[{"path":name,"sha256":sha(data),"bytes":len(data)} for name,data in entries]}
 entries.append(("manifest.json",(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+"\n").encode()))
 ARCHIVE.parent.mkdir(parents=True,exist_ok=True)
 with ZipFile(ARCHIVE,"w",ZIP_DEFLATED,compresslevel=5) as z:
  for filename,data in entries:
   item=ZipInfo(filename,(2026,11,11,0,0,0))
   item.external_attr=0o100644<<16;item.compress_type=ZIP_DEFLATED
   z.writestr(item,data,compress_type=ZIP_DEFLATED,compresslevel=5)
 with ZipFile(ARCHIVE) as z:
  if z.testzip() is not None:raise AssertionError("ZIP CRC mismatch")
  for row in manifest["files"]:
   if sha(z.read(row["path"]))!=row["sha256"]:raise AssertionError("Artifact hash mismatch: "+row["path"])
 delivery={"schema":"KOMA-P15-36-DELIVERY-V1",
  "characterId":"p0_character_001","archivePath":str(ARCHIVE.relative_to(R)),
  "sha256":sha(ARCHIVE.read_bytes()),"bytes":ARCHIVE.stat().st_size,
  "entriesVerified":len(entries),"htmlEntry":"index.html",
  "angles":source["angles"],"semanticRoleCount":len(ROLES),
  "completeRoleSetFiles":len(ROLES)*len(source["angles"]),
  "newModelPaintedRolesPerAngle":len(source["newModelPaintedROIRoles"]),
  "chromiumScreenshots":browser["screenshotCount"],
  "chromiumImageLoads":browser["imageLoads"],
  "independentFullOriginalArtworkAccepted":False,
  "artisticReviewStatus":"P0_IDENTITY_AND_ANATOMICAL_KEYVIEW_REVIEW_REQUIRED"}
 QA.write_text(json.dumps(delivery,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps(delivery,ensure_ascii=False))
 return delivery
if __name__=="__main__":run()

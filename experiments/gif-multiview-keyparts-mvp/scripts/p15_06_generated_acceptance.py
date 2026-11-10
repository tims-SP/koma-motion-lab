#!/usr/bin/env python3
"""Verify independent 65/77.5 view art, 26 RGBA semantic layers and PSD underpaint.

This engineering gate validates source hashes and exact recomposition. Original
P0 Hero identity, anatomical angle precision, stroke placement and each part's
boundary require a separate artistic gate.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
PRIVATE=(ROOT/"private-assets").resolve()
ANGLES={65.0:"yaw065",77.5:"yaw077p5"}
REQUIRED_ROLES=(
 "body.reference","hair.back","face.skin","ear.far","ear.near",
 "hair.side","eye.far","eye.near","nose","mouth",
 "hair.front","hair.ahoge","hair.clip.cross_gold"
)

def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()


def read(path):
 return json.loads(Path(path).read_text(encoding="utf-8"))


def assert_source_path(path):
 p=(PRIVATE/path).resolve()
 if not p.is_relative_to(PRIVATE) or not p.is_file():
  raise AssertionError("P0 private source path absent or outside root")
 return p


def check_sha(path,expected):
 if sha(path)!=expected:
  raise AssertionError("Source identity SHA mismatch "+str(path))
 return path


def composite(records):
 out=Image.new("RGBA",(1024,1024),(0,0,0,0))
 for record in sorted(records,key=lambda x:x["depthOrder"]):
  path=check_sha(assert_source_path(record["path"]),record["sha256"])
  with Image.open(path) as img:
   if img.mode!="RGBA" or img.size!=(1024,1024):
    raise AssertionError("Source semantic part must be true native 1024 RGBA")
   out.alpha_composite(img)
 return out


def source_comparison(x,y):
 aa=np.asarray(x.convert("RGBA"),dtype=np.int16)
 bb=np.asarray(y.convert("RGBA"),dtype=np.int16)
 valid=aa[:,:,3]>0
 return {
   "maxAlphaDifference":int(np.abs(aa[:,:,3]-bb[:,:,3]).max()),
   "maxRGBDifferenceOnSource":int(np.abs(aa[:,:,:3][valid]-bb[:,:,:3][valid]).max()),
 }


def run():
 contract=read(ROOT/"metadata/p15-holdout-generation-contract.json")
 original=read(PRIVATE/"p5-see-through/mv-candidate/parts.json")
 gate=read(ROOT/"evidence/p15-06-source-readiness.json")
 if any(o["characterId"]!="p0_character_001" for o in (contract,original,gate)):
  raise AssertionError("Original P0 character ID mismatch")
 if contract["assetsPerView"]!=list(REQUIRED_ROLES):
  raise AssertionError("P0 semantic asset contract changed")
 sources={x["yawDeg"]:x for x in original["wholeViews"]}
 for yaw in (0,45,90):
  item=sources[yaw]
  check_sha(assert_source_path(item["path"]),item["sha256"])
 artifacts=[]
 for angle,key in ANGLES.items():
  folder=PRIVATE/"p15-independent-candidates"
  qa_path=folder/(key+"-artmesh/qa.json")
  qa=read(qa_path)
  art=read(folder/(key+"-qwen2511-v2.provenance.json"))
  matte=read(folder/(key+"-source-rgba.qa.json"))
  ingested=read(folder/(key+"-artmesh/ingest-qa.json"))
  if qa["characterId"]!="p0_character_001" or qa["yaw"]!=angle:
   raise AssertionError("New independent key pose identity/yaw mismatch")
  source=check_sha(assert_source_path(qa["independentPainting"]["path"]),
                   qa["independentPainting"]["sha256"])
  if art["sha256"]!=qa["independentPainting"]["sha256"]:
   raise AssertionError("Generator provenance mismatch")
  if qa["sourceInputYaw"]!=art["sourceYaw"] or qa["paintSeed"]!=art["seed"]:
   raise AssertionError("Generator seed/source reference mismatch")
  check_sha(assert_source_path(qa["sourceMatte"]["path"]),qa["sourceMatte"]["sha256"])
  if matte["outputPNG_SHA256"]!=qa["sourceMatte"]["sha256"]:
   raise AssertionError("Anime RGBA matte hash mismatch")
  rows=qa["semanticLayerRecords"]
  if len(rows)!=13 or [r["semanticId"] for r in rows]!=list(REQUIRED_ROLES) and set(r["semanticId"] for r in rows)!=set(REQUIRED_ROLES):
   raise AssertionError("Native P0 semantic parts incomplete")
  if sorted(x["depthOrder"] for x in rows)!=list(range(13)):
   raise AssertionError("P0 original view depth order not registered")
  img=composite(rows)
  with Image.open(assert_source_path(qa["sourceMatte"]["path"])) as ref:
   ref_rgba=ref.copy()
  gap=source_comparison(ref_rgba,img)
  if any(gap.values()):
   raise AssertionError("New semantic split changed source painting: "+str(gap))
  if ingested["status"]!="P15_06_INDEPENDENT_PARTS_READY_FOR_ART_REVIEW" or ingested["partCount"]!=13:
   raise AssertionError("P15 formal ArtMesh import is incomplete")
  if ingested["referencePainting"]["sha256"]!=qa["sourceMatte"]["sha256"]:
   raise AssertionError("Registered painting provenance changed")
  essential=("hair.back","face.skin","eye.near","nose","mouth","hair.front","hair.ahoge","ear.near")
  if any(next(p for p in rows if p["semanticId"]==role)["visiblePixels"]==0 for role in essential):
   raise AssertionError("Expected visible original anatomical component absent")
  photo=check_sha(assert_source_path(qa["contact"]["path"]),qa["contact"]["sha256"])
  artifacts.append({
   "angle":angle,
   "sourceView":art["sourceYaw"],
   "sourceViewSHA256":sources[art["sourceYaw"]]["sha256"],
   "model":qa["paintModel"],"adapter":qa["paintAdapter"],"seed":qa["paintSeed"],
   "originalPainting":{"path":qa["independentPainting"]["path"],"sha256":qa["independentPainting"]["sha256"]},
   "transparentPainting":qa["sourceMatte"],
   "semanticLayerCount":len(rows),
   "visibleRoleCount":sum(p["visiblePixels"]>0 for p in rows),
   "singleAhogePixelCount":qa["singleAhogeCandidatePixels"],
   "nearEarPixelCount":qa["nearEarCandidateSkinPixels"],
   "renderRecomposition":gap,
   "sourceQA_SHA256":sha(qa_path),
   "formalIngestionSHA256":sha(folder/(key+"-artmesh/ingest-qa.json")),
   "sourceVisualContact":{"path":qa["contact"]["path"],"sha256":sha(photo)},
   "semanticBoundaryStatus":"PENDING_VISUAL_PART_OWNERSHIP_REVIEW"
  })
 under=read(PRIVATE/"p15-independent-candidates/yaw077p5-inpainted/qa.json")
 if under["yaw"]!=77.5 or under["visiblePixelExactAlphaMax"]!=0 or under["visiblePixelExactRGBMax"]!=0:
  raise AssertionError("See-through underpainting changed original source-visible pixels")
 if under["totalHiddenPaintedPixels"]<=0:
  raise AssertionError("Expected underlying inpainted hair/skin pixels absent")
 psd=PRIVATE/"p15-independent-candidates/seethrough/yaw077p5-layers.psd"
 check_sha(psd,under["seeThroughPSD_SHA256"])
 for entry in under["nativeLayers"]:
  check_sha(assert_source_path(entry["path"]),entry["sha256"])
 rebuilt=composite(under["nativeLayers"])
 with Image.open(assert_source_path(artifacts[1]["transparentPainting"]["path"])) as original_77:
  gap=source_comparison(original_77,rebuilt)
 if any(gap.values()):
  raise AssertionError("Inpainted semantic layers visibly changed P0 candidate art")
 browser_file=PRIVATE/"p15-independent-candidates/browser/qa.json"
 browser=read(browser_file)
 if browser["characterId"]!="p0_character_001" or browser["status"]!="PASS_SOURCE_HASHED_GENERATED_KEYVIEW_BROWSER_REVIEW":
  raise AssertionError("P15-06 actual Chromium review incomplete")
 if browser["screenshotCount"]!=8 or browser["sourceImagesHashVerified"]!=32:
  raise AssertionError("P15-06 Chromium source hash coverage incomplete")
 if browser["javascriptErrors"] or browser["failedRequests"]:
  raise AssertionError("Chromium browser errors present")
 for sample in browser["samples"]:
  photo=(ROOT/sample["path"]).resolve()
  if not photo.is_relative_to(PRIVATE) or sha(photo)!=sample["sha256"]:
   raise AssertionError("Real browser capture original source hash mismatch")
 browser_summary={
    "source":"Chromium Playwright",
    "reviewScreenshots":browser["screenshotCount"],
    "sourceImagesHashVerified":browser["sourceImagesHashVerified"],
    "sourceQA_SHA256":sha(browser_file),
    "javascriptErrors":len(browser["javascriptErrors"]),
    "failedRequests":len(browser["failedRequests"]),
    "status":browser["status"],
 }
 stage={
  "schema":"KOMA-P0-P15-06-GENERATED-KEYVIEWS-ARTMESH-ENGINEERING-V1",
  "characterId":"p0_character_001",
  "originalKeyviewSHA256Verified":[0,45,90],
  "generatedIndependentCandidateViews":artifacts,
  "candidateViewCount":len(artifacts),
  "registeredSemanticRGBA":sum(v["semanticLayerCount"] for v in artifacts),
  "sourceExactRecompositions":len(artifacts),
  "sourceRGBAResolution":[1024,1024],
  "seeThroughBackHairAndSkin":{
    "sourceSpace":"afredzhou/see-through-demo",
    "sourceResolution":[768,768],
    "targetAngle":77.5,
    "PSD_SHA256":under["seeThroughPSD_SHA256"],
    "hiddenInpaintedPixels":under["totalHiddenPaintedPixels"],
    "hiddenSourceRoles":under["hiddenSourceRoles"],
    "resultRGBAExactRecomposition":gap,
    "sourceQA_SHA256":sha(PRIVATE/"p15-independent-candidates/yaw077p5-inpainted/qa.json")
  },
  "browserReview":browser_summary,
  "referenceHeroSHA256Verified":gate["approvedHeroDirectSourceSHA256Verified"],
  "candidateStatus":"P15_06_INDEPENDENT_ART_AND_SEMANTIC_ENGINEERING_VERIFIED",
  "artisticQualityStatus":"PENDING_FIVE_SENSE_AND_STRAND_VISUAL_ACCEPTANCE",
  "formalArtAcceptance":0,
  "renderBaseline":"P8_SEMANTIC_OCCLUSION_ARTMESH"
 }
 dest=ROOT/"evidence/p15-06-generated-keyviews-qa.json"
 dest.write_text(json.dumps(stage,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({
  "status":stage["candidateStatus"],"views":stage["candidateViewCount"],
  "nativeRGBA":stage["registeredSemanticRGBA"],
  "sourceExactFrames":stage["sourceExactRecompositions"],
  "underpaintPixels":stage["seeThroughBackHairAndSkin"]["hiddenInpaintedPixels"],
  "browserScreenshots":stage["browserReview"]["reviewScreenshots"],
  "heroSHA256Verified":stage["referenceHeroSHA256Verified"],
  "artAccepted":stage["formalArtAcceptance"]
 },ensure_ascii=False))
 return stage


if __name__=="__main__":
 run()

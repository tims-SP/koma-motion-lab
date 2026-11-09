#!/usr/bin/env python3
"""P15-06 independent 65/77.5 view-generation provenance preflight.

The approved original Hero hash is a hard identity gate; SHA-verified P0
0/45/90 source views are valid geometric references for planning independent
intermediate paintings. P14 ArtMesh frames are diagnostic references only.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

CHARACTER="p0_character_001"
HOLDOUTS=(65.0,77.5)
SOURCE_ANGLES=(0,45,90)
ROLES=(
 "body.reference","hair.back","face.skin","ear.far","ear.near",
 "hair.side","eye.far","eye.near","nose","mouth",
 "hair.front","hair.ahoge","hair.clip.cross_gold"
)


def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as stream:
  for piece in iter(lambda:stream.read(1<<20),b""):
   h.update(piece)
 return h.hexdigest()


def load(path):
 return json.loads(Path(path).read_text(encoding="utf8"))


def run(root,design,out,contract_file):
 root=Path(root).resolve();design=Path(design).resolve()
 original=load(root/"p5-see-through/mv-candidate/parts.json")
 identity=load(design/"identity_spec.json")
 p15=load(root.parent/"evidence/p15-05-acceptance.json")
 if original["characterId"]!=CHARACTER or identity["character_id"]!=CHARACTER or p15["characterId"]!=CHARACTER:
  raise ValueError("P0 character identity contract mismatch")
 source=identity["source"]
 hero=design/source["working_hero_file"]
 expected=source["working_hero_sha256"]
 candidates=[]
 for file in (hero,design/"hero_master.png",root/"recovered-review/sources/generated-master.png"):
  observed=None;dims=None
  if file.is_file():
   observed=sha(file)
   with Image.open(file) as img:
    dims=list(img.size)+[img.mode]
  candidates.append({"assetRole":"HERO" if file==hero else "REFERENCE_CANDIDATE",
     "path":str(file),"exists":file.is_file(),
     "sha256":observed,"matchesApprovedHeroSHA256":bool(observed==expected),
     "geometry":dims})
 canonical=[item for item in candidates if item["sha256"]==expected]
 keys=[]
 for entry in original["wholeViews"]:
  angle=entry["yawDeg"]
  if angle not in SOURCE_ANGLES:continue
  file=(root/entry["path"]).resolve()
  if not file.is_relative_to(root) or sha(file)!=entry["sha256"]:
   raise AssertionError("Registered P0 original view changed")
  with Image.open(file) as img:
   geometry=list(img.size)+[img.mode]
  keys.append({"yaw":angle,"sourceRole":"ORIGINAL_P0_VIEW",
    "path":entry["path"],"sha256":entry["sha256"],"geometry":geometry})
 if [e["yaw"] for e in sorted(keys,key=lambda e:e["yaw"])]!=list(SOURCE_ANGLES):
  raise AssertionError("Original 0/45/90 P0 input source coverage incomplete")
 landmarks=root/"p5-see-through/mv-candidate/landmark-qa.json"
 if not landmarks.is_file():raise ValueError("Original physical anchor registry unavailable")
 p14_67=load(root/"p14-authored-candidates/yaw067p5-artmesh/qa.json")
 p14_72=load(root/"p14-authored-candidates/yaw072p5-artmesh/qa.json")
 sourceCandidates=[
  {"yaw":67.5,"sha256":p14_67["composite"]["sha256"],
   "path":p14_67["composite"]["path"],"sourceRole":"GENERATED_PAINTED_REFERENCE"},
  {"yaw":72.5,"sha256":p14_72["composite"]["sha256"],
   "path":p14_72["composite"]["path"],"sourceRole":"GENERATED_PAINTED_REFERENCE"}
 ]
 for entry in sourceCandidates:
  f=root/entry["path"]
  if sha(f)!=entry["sha256"]:raise ValueError("Painted reference source hash mismatch")
 contract={
  "schema":"KOMA-P0-P15-06-INDEPENDENT-HOLDOUT-ARTWORK-CONTRACT-V1",
  "characterId":CHARACTER,
  "sourceOriginalViews":keys,
  "sourceGeneratedArtReferences":sourceCandidates,
  "physicalAnchorSourceSHA256":sha(landmarks),
  "originalHeroExpectedSHA256":expected,
  "originalHeroDimensions":[source["working_hero_dimensions_px"]["width"],
                            source["working_hero_dimensions_px"]["height"]],
  "originalHeroSourceAvailable":bool(canonical),
  "holdingYawAngles":list(HOLDOUTS),
  "assetsPerView":list(ROLES),
  "assetsPerViewCount":len(ROLES),
  "canvas":[1024,1024],
  "renderRequirements":{
    "sourceRole":"INDEPENDENT_AUTHORED_2D_KEYFRAME",
    "referenceMode":"approved original character identity with registered source key poses",
    "style":"Japanese TV anime, consistent thin-line ink and restrained cel shading",
    "alpha":"RGBA8 antialiased transparent native PNG",
    "partIsolation":"one semantic part per native full-canvas PNG",
    "headYawConvention":"0 front, 90 camera at character right, consistent orthographic bust",
    "viewSemantics":"65 and 77.5 target yaw are independently drawn anatomical references, not reused VDD output",
    "visibility":"view-dependent near/far eye, ear and golden hair clip occlusion",
    "strandCorrespondence":"original hair bangs, back hair and one ahoge must be recognizable across angle",
    "filenames":"parts/yaw065/<semantic-id>.png and parts/yaw077p5/<semantic-id>.png"
  },
  "comparison":{
    "renderEngine":"P8_SEMANTIC_OCCLUSION_ARTMESH",
    "testAngles":[65.0,77.5],
    "targetSilhouetteIoU":0.90,
    "maxRelativeSilhouetteAreaError":0.08,
    "manualCriteria":"face, near eye, ear, hair strand, nose and mouth exact visual identity; no ghosting"
  },
  "admission":{
    "sourceIdentityGate":"P0_HERO_SHA256_VERIFIED",
    "sourceArtworkGate":"INDEPENDENT_PAINTED_SEMANTIC_PARTS_AND_SHA256",
    "visualAcceptanceGate":"INDEPENDENT_ART_AND_VDD_COMPARISON"
  }
 }
 out=Path(out);contract_file=Path(contract_file)
 out.parent.mkdir(parents=True,exist_ok=True)
 contract_file.parent.mkdir(parents=True,exist_ok=True)
 contract_file.write_text(json.dumps(contract,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 qa={
  "schema":"KOMA-P0-P15-06-HOLDOUT-SOURCE-PREFLIGHT-V1",
  "characterId":CHARACTER,
  "originalKeyViewCount":len(keys),
  "originalKeyViewHashesVerified":True,
  "originalP5AnchorsSHA256":sha(landmarks),
  "approvedIdentityExpectedSHA256":expected,
  "approvedHeroDirectSourceSHA256Verified":bool(canonical),
  "approvedHeroCandidateInventory":candidates,
  "registeredInputAngles":[x["yaw"] for x in keys],
  "generatedPaintedReferenceAngles":[67.5,72.5],
  "requestedIndependentHoldoutAngles":list(HOLDOUTS),
  "plannedIndependentSemanticAssets":len(HOLDOUTS)*len(ROLES),
  "independentlyPaintedHoldoutAssetsAccepted":0,
  "readiness":"INPUT_KEYFRAMES_VERIFIED_IDENTITY_SOURCE_RECONCILIATION_REQUIRED" if not canonical else "INPUT_IDENTITY_SOURCE_READY",
  "contractPath":str(contract_file),
  "contractSHA256":sha(contract_file),
  "sourceArtworkAcceptance":"PENDING_INDEPENDENT_HOLDOUT_ART",
  "baselineRenderer":"P8_SEMANTIC_OCCLUSION_ARTMESH"
 }
 out.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print(json.dumps({"sourceViews":qa["originalKeyViewCount"],
  "heroVerified":qa["approvedHeroDirectSourceSHA256Verified"],
  "independentViews":qa["requestedIndependentHoldoutAngles"],
  "semanticAssetsRequired":qa["plannedIndependentSemanticAssets"],
  "readiness":qa["readiness"]},ensure_ascii=False))
 return qa


if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--root",required=True)
 p.add_argument("--design",required=True)
 p.add_argument("--out",required=True)
 p.add_argument("--contract",required=True)
 a=p.parse_args()
 run(a.root,a.design,a.out,a.contract)

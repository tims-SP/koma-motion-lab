#!/usr/bin/env python3
"""P13 P0 semantic RGBA asset contract and source-authored redraw requirements.

The independently painted original views remain 0,45,90. Intermediate
source-derived previews are registered separately from authored art and
receive both layer recomposition and visibility checks.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image
import p8_semantic_occlusion as p8

ANGLE_SET=(67.5,72.5)
ROLES=(
 "body.reference","hair.back","face.skin","ear.far","ear.near",
 "hair.side","eye.far","eye.near","nose","mouth",
 "hair.front","hair.ahoge","hair.clip.cross_gold"
)
DRAWING_RULES={
 "body.reference":"Only torso, jacket, collar, bow and clothing gold trim. Preserve original ribbon knot and tailored lines; do not include face or hair.",
 "hair.back":"Back hair mass and rear nape layers; match 90° flowing bob silhouette and the 45° source color design, excluding frontal bangs and single ahoge.",
 "face.skin":"Skin/jaw/cheek only. Correct continuous 67.5/72.5 oblique jaw, nose bridge occlusion boundary and under-eye contour without embedded eyes, mouth or ears.",
 "ear.far":"Registered far ear: fully occluded in this angle range. Native transparent layer and stable physical ID.",
 "ear.near":"Only the visible near ear, aligned to its 45°/90° ear anatomical anchors; match side-facing cartilage and hair overlap.",
 "hair.side":"Side locks framing the ear and cheek, with continuous single hair-strand contours and no frontal bang or rear mass duplicates.",
 "eye.far":"Far eye is progressively occluded by nose bridge/hair; only visible source-backed portion belongs here, decreasing toward 90°.",
 "eye.near":"One near eye only, including iris, lids, lashes and highlights. Match original purple-pink iris identity and a natural side-facing ellipse.",
 "nose":"One oblique side-profile nose with correct contour and bridge, no full-face duplicate or unrelated facial skin.",
 "mouth":"Single mouth and lip stroke at side-facing perspective, preserving the approved subtle expression.",
 "hair.front":"Only frontal fringe and its visible single-strand edges, preserving the original short asymmetrical bangs and correct near-eye occlusion.",
 "hair.ahoge":"One original single hair antenna sprout, based on 45/90 root anchor and original pink-purple strand shape.",
 "hair.clip.cross_gold":"Original gold crossed hair clip. Progressive visibility is linked to its occlusion by 67.5° and hidden by 72.5°."
}
NEEDS_INDEPENDENT_ART=[
 "eye.near","face.skin","hair.front","ear.near","nose",
 "mouth","hair.back","body.reference","hair.side"
]

def sha(file):
 h=hashlib.sha256()
 with Path(file).open("rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()

def load(file):return json.loads(Path(file).read_text(encoding="utf8"))

def alpha_stats(img):
 a=np.asarray(img.getchannel("A"))
 visible=np.argwhere(a>0)
 if len(visible):
  top,left=visible.min(axis=0);bottom,right=visible.max(axis=0)
  bbox=[int(left),int(top),int(right+1),int(bottom+1)]
 else:bbox=None
 return {"opaqueOrTranslucentPixelCount":int((a>0).sum()),
         "partialAlphaPixelCount":int(((a>0)&(a<255)).sum()),
         "boundingBox":bbox,"maxAlpha":int(a.max())}

def anchors_for_angle(land,angle):
 t=(angle-45)/45
 anchors=[]
 for sid,pts in land["landmarks"].items():
  a=next((x for x in pts if x["yaw"]==45),None)
  b=next((x for x in pts if x["yaw"]==90),None)
  if not a or not b or not (a["visible"] and b["visible"]):
   continue
  P=np.asarray(a["xy"],float);Q=np.asarray(b["xy"],float)
  anchors.append({"name":sid,
     "45":a["xy"],"90":b["xy"],
     "referenceXY":[round(float(x),2) for x in P*(1-t)+Q*t],
     "coordRole":"LINEAR_REFERENCE_NOT_MEASURED_INTERMEDIATE_ART"})
 return anchors

def run(root,out,method="source-feathered"):
 root=Path(root).resolve();out=Path(out).resolve();out.mkdir(exist_ok=True,parents=True)
 original=load(root/"p5-see-through/mv-candidate/parts.json")
 landmarks=load(root/"p5-see-through/mv-candidate/landmark-qa.json")
 p12=load(root/"p12-occlusion-gap/qa.json")
 p11=load(root/"p11-profile-psd/yaw090/qa.json")
 p13root=root/"p13-source-priority"/method
 rendered=load(p13root/"qa.json")
 assert original["characterId"]==landmarks["characterId"]==p12["characterId"]==p11["characterId"]==rendered["characterId"]=="p0_character_001"
 assert rendered["frameCount"]==37 and rendered["semanticLayerCount"]==26
 assert rendered["expectedSemanticSlotsPerIntermediateAngle"]==13
 assert sha(root/p11["psdPath"])==p11["psdSHA256"]
 reference={x["yawDeg"]:x for x in original["wholeViews"]}
 source={(x["yawDeg"],x["semanticId"]):x for x in original["parts"]}
 assert len(source)==39 and len(set(x["semanticId"] for x in original["parts"]))==13
 for a in (45,90):
  assert sha(root/reference[a]["path"])==reference[a]["sha256"]
 for rec in original["parts"]:
  if rec["yawDeg"] in (45,90):
   assert sha(root/rec["path"])==rec["frameSha256"]
 gap={x["role"]:x for x in p12["parts"]}
 rendered_layers={(x["angle"],x["semanticId"]):x for x in rendered["semanticLayers"]}
 angles=[]
 for angle in ANGLE_SET:
  semantic=[]
  frame=next(x for x in rendered["frames"] if x["angle"]==angle)
  filepath=root/frame["path"]
  assert sha(filepath)==frame["sha256"]
  image=Image.new("RGBA",(1024,1024),(0,0,0,0))
  for role in ROLES:
   a=source[45,role];b=source[90,role]
   ref=rendered_layers.get((angle,role))
   if ref is None:raise ValueError("Missing P0 source-derived semantic role "+role)
   filename=root/ref["path"]
   if sha(filename)!=ref["sha256"]:
    raise ValueError("Derived P13 layer SHA-256 mismatch "+role)
   with Image.open(filename) as png:
    if png.mode!="RGBA" or png.size!=(1024,1024):
     raise ValueError("Native 1024x1024 RGBA required "+role)
    layer=png.copy()
   stat=alpha_stats(layer)
   image.alpha_composite(layer)
   if a["visibility"]=="hidden" and b["visibility"]=="hidden":
    if stat["maxAlpha"]!=0:raise ValueError("Occluded semantic role must have zero alpha "+role)
   if role in ("eye.far","hair.clip.cross_gold") and angle>=72.5:
    if stat["maxAlpha"]!=0:
     if role=="hair.clip.cross_gold":
      raise ValueError("90-degree gold hair clip is fully hidden by 72.5°")
   opacity=(
    p8.schedule_visibility(role,45,90,angle) if a["visibility"]=="visible" and b["visibility"]=="hidden"
    else 1.0 if a["visibility"]=="visible" and b["visibility"]=="visible"
    else 0.0 if a["visibility"]=="hidden" and b["visibility"]=="hidden"
    else 1-p8.schedule_visibility(role,45,90,angle))
   row={
    "semanticId":role,
    "assetId":f"p0_character_001/yaw{str(angle).replace('.','p')}/{role}",
    "viewAngle":angle,
    "globalCanvas":[1024,1024],
    "imageEncoding":"PNG RGBA8",
    "sourceAlpha":"ANTIALIASED",
    "semanticDepthOrder":a["depthOrder"],
    "alphaVisibility":stat,
    "referenceVisibility45":a["visibility"],
    "referenceVisibility90":b["visibility"],
    "estimatedVisibilityWeight":round(float(opacity),5),
    "source45":{"path":a["path"],"sha256":a["frameSha256"]},
    "source90":{"path":b["path"],"sha256":b["frameSha256"]},
    "sourceRegistrationGapFraction":gap[role]["targetOnlyFraction"],
    "sourceGapInterpretation":"P0 90-degree mapped-alpha coverage relative to 45-degree source",
    "sourceDerivedCandidate":{"path":ref["path"],"sha256":ref["sha256"]},
    "contentRequirement":DRAWING_RULES[role],
    "artisticSourceStatus":"INDEPENDENT_AUTHORING_REQUIRED" if role in NEEDS_INDEPENDENT_ART else "CANONICAL_SOURCE_VERIFICATION_REQUIRED",
    "sourceArtworkAcceptance":"PENDING"
   }
   semantic.append(row)
  if list(x["semanticId"] for x in semantic)!=list(ROLES):
   raise ValueError("The same P0 13 semantic identities must preserve depth order")
  with Image.open(filepath) as originalFrame:
   merged=np.asarray(image)
   expected=np.asarray(originalFrame.convert("RGBA"))
  diff=np.abs(merged.astype(np.int16)-expected.astype(np.int16))
  if diff.max()>0:
   raise ValueError("Native P13 13-layer RGBA reconstruction not byte pixel exact at "+str(angle))
  angles.append({
   "viewAngle":angle,
   "generatedAssetType":"SOURCE_DERIVED_REGISTERED_INTERMEDIATE_PREVIEW",
   "registeredArtMeshSemanticSlots":13,
   "sourceDerivedFrame":{"path":frame["path"],"sha256":frame["sha256"]},
   "reconstructionPixelExact":True,
   "predictedReferenceAnchors":anchors_for_angle(landmarks,angle),
   "parts":semantic
  })
 contract={
  "schema":"KOMA-P0-P13-INTERMEDIATE-ANGLE-PAINT-CONTRACT-V1",
  "characterId":"p0_character_001",
  "sourceApprovedCharacterViews":[0,45,90],
  "sourceMotherPortraitIdentity":"p0_character_001",
  "reference45":{"path":reference[45]["path"],"sha256":reference[45]["sha256"]},
  "reference90":{"path":reference[90]["path"],"sha256":reference[90]["sha256"]},
  "sourceP11Editable90PSD_SHA256":p11["psdSHA256"],
  "sourceP12GapQA_SHA256":sha(root/"p12-occlusion-gap/qa.json"),
  "candidateP13Engine":method,
  "imageContract":{
   "canvas":[1024,1024],
   "alpha":"native 8-bit RGBA transparency, 256 transparency levels",
   "oneFrameOneSemanticComponent":True,
   "camera":"P0 frozen orthographic bust framing, yaw to visual right",
   "characterReference":"same P0 short pink-purple bob, single ahoge, crossed gold clip, purple-pink eyes, navy school jacket, burgundy ribbon",
   "viewList":[67.5,72.5],
   "componentIDs":list(ROLES),
   "componentCountPerView":13,
   "componentDepthOrderPreserved":True,
   "sourcePaintingApproval":"PENDING_GENERATIVE_OR_MANUAL_AUTHORING"
  },
  "intermediateViews":angles,
  "authoringPriority":NEEDS_INDEPENDENT_ART,
  "requiredQualityGates":{
   "identity":"match approved source P0 0/45/90",
   "visibility":"far eye and cross gold clip progressively occluded, single near eye",
   "partOwnership":"no duplicate eye, ear, front fringe, ahoge or gold clip in other semantic parts",
   "sourceTextures":"new artist-approved pixels within each component with 8-bit antialiased edge",
   "rendering":"P8 baseline 37-frame movement with P13 painted key view slots",
   "acceptance":"visual review at 22.5/67.5/72.5 and structured per-component QA"
  },
  "status":"SOURCE_DERIVED_LAYER_REGISTRY_AND_ART_AUTHORING_CONTRACT_READY"
 }
 target=out/"p13-paint-contract.json"
 target.write_text(json.dumps(contract,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print(json.dumps({"status":contract["status"],
   "angles":len(angles),"semanticSlots":sum(len(x["parts"]) for x in angles),
   "pixelExactComposites":sum(x["reconstructionPixelExact"] for x in angles),
   "independentAuthoringPriority":len(NEEDS_INDEPENDENT_ART),
   "SHA256":sha(target)},ensure_ascii=False,indent=2))
 return contract

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--root",required=True)
 p.add_argument("--out",required=True)
 p.add_argument("--method",default="source-feathered")
 x=p.parse_args()
 run(x.root,x.out,x.method)

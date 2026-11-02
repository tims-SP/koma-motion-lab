#!/usr/bin/env python3
"""Validate independently authored RGBA component assets at 45°/90°.

The validator checks file integrity, transparent borders, semantic coverage,
camera registration, independent source traceability and landmark validity.
Pixel-perfect anatomical quality still requires visual sign-off.
"""
import argparse, hashlib, json, math, pathlib, re, sys
from PIL import Image

EXPECTED_SCHEMA="R1999-INDEPENDENT-VIEW-LAYERS-V1"
ALLOWED_ROLES={"independent_art","synthetic_fixture","runtime_sample"}
HEX=re.compile(r"^[0-9a-f]{64}$")

def validate(manifest,root):
 errors=[]
 if manifest.get("schema")!=EXPECTED_SCHEMA:errors.append("SCHEMA")
 required=manifest.get("requiredAngles",[])
 parts=manifest.get("requiredParts",[])
 if sorted(required)!=[45,90]:errors.append("VIEW_RANGE")
 if len(set(parts))!=len(parts) or len(parts)<8:errors.append("REQUIRED_PARTS")
 if manifest.get("coordinates",{}).get("canvas")!=[640,640]:errors.append("CANVAS")
 assets=manifest.get("assets",[])
 pairs=set(); seen={}; truths=set(); evidence=[]
 for idx,a in enumerate(assets):
  angle=a.get("yawDeg");part=a.get("semanticId");role=a.get("role")
  tag=f"{idx}:{angle}:{part}"
  if angle not in (45,90) or part not in parts:errors.append("IDENTITY_"+tag)
  if (angle,part) in pairs:errors.append("DUPLICATE_"+tag)
  pairs.add((angle,part))
  if role not in ALLOWED_ROLES:errors.append("ROLE_"+tag)
  rel=a.get("path","")
  loc=pathlib.Path(rel)
  if not rel or loc.is_absolute() or ".." in loc.parts or loc.suffix.lower()!=".png":
   errors.append("UNSAFE_PATH_"+tag);continue
  p=root/loc
  if not p.is_file():errors.append("MISSING_PNG_"+tag);continue
  blob=p.read_bytes();digest=hashlib.sha256(blob).hexdigest()
  if not HEX.fullmatch(a.get("sha256","")) or digest!=a["sha256"]:
   errors.append("HASH_"+tag)
  if role=="independent_art":
   if not a.get("creator") or not a.get("sourceId") or not a.get("licenseReview"):
    errors.append("PROVENANCE_"+tag)
   if a.get("cameraCalibrated") is not True: errors.append("CAMERA_CALIBRATION_"+tag)
   truths.add((angle,part))
  if digest in seen and seen[digest]!=angle:errors.append("CROSS_VIEW_REUSE_"+tag)
  seen[digest]=angle
  try:
   im=Image.open(p)
   if im.format!="PNG" or im.mode!="RGBA":errors.append("RGBA_"+tag)
   if im.size!=(640,640):errors.append("SIZE_"+tag)
   rgba=im.convert("RGBA")
   alpha=rgba.getchannel("A")
   bbox=alpha.getbbox()
   if bbox is None:errors.append("EMPTY_ALPHA_"+tag)
   else:
    if bbox[0]==0 or bbox[1]==0 or bbox[2]==640 or bbox[3]==640:
     errors.append("BORDER_TOUCH_"+tag)
   # check source canvas actually has transparency, not an opaque report or composite
   area=sum(v>0 for v in alpha.getdata())
   if area>640*640*0.85:errors.append("LAYER_TOO_LARGE_"+tag)
   landmarks=a.get("landmarks",{})
   if not isinstance(landmarks,dict) or len(landmarks)<3:errors.append("LANDMARK_COUNT_"+tag)
   else:
    unique=set()
    for key,point in landmarks.items():
     if not isinstance(point,list) or len(point)!=2 or not all(isinstance(x,(float,int)) and math.isfinite(x) and 0<=x<=640 for x in point):
      errors.append("LANDMARK_"+tag);break
     unique.add(tuple(point))
    if len(unique)<3:errors.append("LANDMARK_DEGENERACY_"+tag)
    # non-collinear triangle required for affine mesh
    points=list(unique)
    if len(points)>=3:
     x0,y0=points[0]
     if not any(abs((x-x0)*(v-y0)-(y-y0)*(u-x0))>=1 for x,y in points for u,v in points):
      errors.append("LANDMARK_COLLINEAR_"+tag)
   evidence.append({"yawDeg":angle,"semanticId":part,"role":role,"sha256":digest,"pixels":area,"bbox":bbox})
  except Exception as e:errors.append("DECODE_"+tag+":"+type(e).__name__)
 missing=[{"yawDeg":angle,"semanticId":p} for angle in required for p in parts if (angle,p) not in truths]
 result={"schema":"R1999-VIEW-ASSET-VALIDATION-V1","checkedAssets":len(assets),
         "verifiedFiles":len(evidence),"geometryValidated":not errors,"errors":errors,
         "missingIndependent":missing,"coverage":len(truths),
         "requiredCoverage":len(required)*len(parts),"readyForInterpolation":not errors and not missing,
         "evidence":evidence}
 return result

def main():
 p=argparse.ArgumentParser();p.add_argument("--manifest",type=pathlib.Path,required=True)
 p.add_argument("--root",type=pathlib.Path,required=True);p.add_argument("--output",type=pathlib.Path)
 p.add_argument("--strict",action="store_true")
 a=p.parse_args()
 output=validate(json.loads(a.manifest.read_text()),a.root.resolve())
 output["status"]="READY" if output["readyForInterpolation"] else ("INVALID" if output["errors"] else "AWAITING_AUTHORED_ART")
 if a.output:
  a.output.parent.mkdir(parents=True,exist_ok=True)
  a.output.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({k:output[k] for k in ["status","checkedAssets","verifiedFiles","coverage","requiredCoverage","errors","missingIndependent"]},ensure_ascii=False))
 if output["errors"] or a.strict and not output["readyForInterpolation"]:sys.exit(1)

if __name__=="__main__":main()

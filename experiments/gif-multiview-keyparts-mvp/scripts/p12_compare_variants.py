#!/usr/bin/env python3
"""Reproducible original P0 texture trials + 45°→90° source gap assessment."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw

MODES=("anatomy","anatomy-strokes","stroke-wide","affine-face")
KEYS=(0,22.5,45,67.5,72.5,90)
PRIORITY=("ear.near","mouth","nose","body.reference","hair.back","hair.front")

def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()

def load(path):return json.loads(Path(path).read_text(encoding="utf8"))

def run(root,out):
 root=Path(root).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
 gap=load(root/"p12-occlusion-gap/qa.json")
 registry=load(root/"p5-see-through/mv-candidate/parts.json")
 p11=load(root/"p11-profile-psd/yaw090/qa.json")
 p10=load(root/"p10-stroke-identity/qa.json")
 p8=load(root/"p8-semantic-occlusion/selective-sequence/qa.json")
 p8edges=load(root/"p8-semantic-occlusion/selective-sequence/texture-qa.json")
 if any(x["characterId"]!="p0_character_001" for x in (gap,registry,p11,p10,p8)):
  raise ValueError("P0 original character source mismatch")
 if sha(root/p11["psdPath"])!=p11["psdSHA256"]:
  raise ValueError("90 degree original editable PSD SHA differs")
 if gap["originalRegistrySHA256"]!=sha(root/"p5-see-through/mv-candidate/parts.json"):
  raise ValueError("P0 semantic ArtMesh source changed")
 def frame(mode,angle):
  filename="yaw"+(str(int(angle)) if angle==int(angle) else str(angle).replace(".","p"))+".png"
  name=(f"p12-anatomical/{mode}-holdout/{filename}"
        if mode!="p8-selective" else f"p8-semantic-occlusion/selective-sequence/{filename}")
  path=root/name
  if not path.is_file():raise FileNotFoundError(path)
  with Image.open(path) as im:
   if im.mode!="RGBA" or im.size!=(1024,1024):raise ValueError("True P0 source RGBA required")
  return {"angle":angle,"path":name,"sha256":sha(path),"bytes":path.stat().st_size}
 edges=lambda x:{str(z["angle"]):z["edgeDensityRelativeToAdjacentMax"] for z in x["holdouts"]}
 methods=[]
 for mode in ("p8-selective",)+MODES:
  if mode=="p8-selective":
   frames=[next(({"angle":r["angle"],"path":r["path"],"sha256":r["sha256"],
                  "bytes":(root/r["path"]).stat().st_size}
           for r in p8["frames"] if r["angle"]==k),None) for k in KEYS]
   texture=p8edges
   title="P8 · semantic ArtMesh render"
   meta={"sourceOriginalAuthoredViews":[0,45,90],"sourceMotionFrames":37}
  else:
   qa=load(root/f"p12-anatomical/{mode}-holdout/qa.json")
   if qa["sourceProfilePSD_SHA256"]!=p11["psdSHA256"]:
    raise ValueError("P12 original side PSD source changed")
   frames=[frame(mode,k) for k in KEYS]
   texture=load(root/f"p12-anatomical/{mode}-holdout/texture-qa.json")
   title="P12 · "+mode
   meta={"strokeAnchorsUsed":sum(qa["localStrokeCandidatesUsed"].values()),
         "sourceOriginalAuthoredViews":[0,45,90]}
  if any(f is None for f in frames):raise ValueError("Missing original P0 holdout frame "+mode)
  methods.append({"id":mode,"label":title,"frames":frames,"textureStatus":texture["status"],
                  "textureRatios":edges(texture),"source":meta})
 # Build legible 2x5 true RGBA side-by-side comparison contact.
 W=320;H=344
 contact=Image.new("RGB",(5*W,2*H),(31,42,58))
 draw=ImageDraw.Draw(contact)
 for i,method in enumerate(methods):
  for j,yaw in enumerate((22.5,67.5)):
   rec=next(x for x in method["frames"] if x["angle"]==yaw)
   with Image.open(root/rec["path"]) as pic:
    img=Image.new("RGBA",(1024,1024),(48,64,84,255))
    img.alpha_composite(pic.convert("RGBA"))
   contact.paste(img.convert("RGB").resize((W,W),Image.Resampling.LANCZOS),
                 (i*W,j*H))
   draw.text((i*W+8,j*H+323),method["id"]+" @ "+str(yaw)+"°",fill="white")
 file=out/"p12-motion-candidate-contact.jpg"
 contact.save(file,quality=94)
 priority=[]
 for role in PRIORITY:
  part=next(x for x in gap["parts"] if x["role"]==role)
  assert part["targetOnlyFraction"]>0.15
  priority.append({
   "semanticId":role,
   "targetOnlyFraction":part["targetOnlyFraction"],
   "targetOnlyNativePixels":part["targetOnlyPixels"],
   "registrationMethod":part["registrationMethod"],
   "source45SHA256":part["source45SHA256"],
   "source90SHA256":part["target90SHA256"],
   "visualAtlasPath":part["sourceComparisonPath"],
   "visualAtlasSHA256":part["sourceComparisonSHA256"],
   "interpretation":"POTENTIAL_ARTWORK_OR_GEOMETRY_CORRESPONDENCE_GAP"
  })
 qa={
  "schema":"KOMA-P0-P12-ANATOMY-STROKE-SEMANTIC-GAP-COMPARISON-V1",
  "characterId":"p0_character_001",
  "nativeP0Canvas":[1024,1024],
  "P0OriginalViews":[0,45,90],
  "PSDViews":[0,45,90],
  "P11RealProfilePSD_SHA256":p11["psdSHA256"],
  "semanticArtMeshSlots":39,
  "P10HighConfidenceStrokeIdentities":p10["candidateIdentities"],
  "methods":methods,
  "P8MotionTemporalStatus":load(root/"p8-semantic-occlusion/selective-sequence/temporal-qa.json")["status"],
  "P12FullMotionAdoption":"P8_SEMANTIC_OCCLUSION_REMAINS_REFERENCE",
  "P12ModifiedRenderingFullMotionStatus":"CANDIDATE_HOLDOUT_ONLY",
  "P12TextureAdoption":"PENDING_ARTISTIC_AND_CONTINUITY_REVIEW",
  "targetViewGapRatioBasis":"P0 original target alpha not covered by aligned 45 degree original source alpha, may include geometrical misregistration",
  "sourceGapAtlasSHA256":sha(root/"p12-occlusion-gap/qa.json"),
  "sourceGapPriority":priority,
  "comparisonContactPath":str(file.relative_to(root)),
  "comparisonContactSHA256":sha(file),
  "status":"P12_SOURCE_GAP_AND_GEOMETRY_VARIANT_REVIEW"
 }
 (out/"comparison-qa.json").write_text(json.dumps(qa,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({
  "status":qa["status"],"candidates":len(MODES),
  "sourceGapPriority":[(i["semanticId"],i["targetOnlyFraction"]) for i in priority],
  "edgeRatios":{m["id"]:m["textureRatios"] for m in methods},
  "sourceMotionBaseline":qa["P12FullMotionAdoption"],
  "contactSHA256":qa["comparisonContactSHA256"]
 },ensure_ascii=False,indent=2))
 return qa

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--root",required=True)
 p.add_argument("--out",required=True)
 a=p.parse_args()
 run(a.root,a.out)

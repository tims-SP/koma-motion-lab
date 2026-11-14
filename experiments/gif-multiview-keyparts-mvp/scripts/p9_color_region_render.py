#!/usr/bin/env python3
"""Region-guided P0 original ArtMesh interpolation experiment.

Adds observed matching color-piece centers as conservative local controls to
P8 physical landmarks. A region has an identity only within its semantic
part; no matched region is allowed to jump between source P0 ArtMeshes.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import p8_semantic_occlusion as p8

HUMAN_FACE={"face.skin","eye.near","eye.far","nose","mouth","ear.near","ear.far"}
HAIR={"hair.front","hair.side","hair.back"}

def sha(file):
 h=hashlib.sha256()
 with Path(file).open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()

def run(root,out,mode,angles,max_cost=47):
 root=Path(root).resolve()
 qaPath=root/"p9-region-correspondence/qa.json"
 data=json.loads(qaPath.read_text())
 if data["characterId"]!="p0_character_001" or data["registeredSemanticPairs"]!=22:
  raise ValueError("Approved P0 regional source correspondence unavailable")
 if data["sourceRegistrySHA256"]!=sha(root/"p5-see-through/mv-candidate/parts.json"):
  raise ValueError("P0 source art changed after region registration")
 original=p8.tracked
 wanted=HUMAN_FACE if mode=="face" else HUMAN_FACE|HAIR
 if mode=="face-hair":
  p8.FACE_CONTROLS.update(HAIR)
 provenance={}
 def corrected(track,role,a,b):
  controls=original(track,role,a,b)
  if role not in wanted:return controls
  item=data["pairs"].get(f"{a}-{b}/{role}")
  if not item:return controls
  used=0
  for number,region in enumerate(item["pairs"]):
   # Restrict to central, sufficiently large color-piece matches. The
   # original anatomy tracks retain the deciding physical identity.
   if region["cost"]>max_cost or min(region["originArea"],region["destinationArea"])<250:
    continue
   A=np.asarray(region["originXY"],dtype=np.float32)
   B=np.asarray(region["destinationXY"],dtype=np.float32)
   controls.append((f"region.{role}.{number}",A,B))
   used+=1
  provenance[f"{a}-{b}/{role}"]={"physicalAndRegionControls":len(controls),
                                "acceptedRegionControls":used}
  return controls
 p8.tracked=corrected
 output=p8.render(root,out,angles,mode="selective")
 output["schema"]="KOMA-P0-P9-REGION-AUGMENTED-ARTMESH-RENDER-V1"
 output["sourceRegionQA_SHA256"]=sha(qaPath)
 output["regionGuidedMode"]=mode
 output["maxMatchCost"]=max_cost
 output["supplementalControls"]=provenance
 f=Path(out)/"qa.json"
 f.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"status":"P9_REGION_GUIDED_P0_RENDER",
                   "controlsAdded":sum(x["acceptedRegionControls"] for x in provenance.values()),
                   "mode":mode,"samples":len(angles),
                   "sourceRegionQA_SHA256":output["sourceRegionQA_SHA256"]},indent=2))
 return output

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--root",required=True)
 p.add_argument("--out",required=True)
 p.add_argument("--mode",choices=["face","face-hair"],default="face")
 p.add_argument("--max-match-cost",type=float,default=47)
 p.add_argument("--angles",default="0,22.5,45,67.5,90")
 a=p.parse_args()
 run(a.root,a.out,a.mode,[float(x) for x in a.angles.split(",")],a.max_match_cost)

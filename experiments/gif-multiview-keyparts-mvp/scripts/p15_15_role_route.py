#!/usr/bin/env python3
"""P15-15: reversible PSD role routing, NOT artistic acceptance."""
import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent.parent
P=R/"private-assets"
QA=R/"evidence/p15-14-existing-psd-mapping-qa.json"
OUT=P/"p15-15-psd-role-routing"
E=R/"evidence/p15-15-role-routing-qa.json"
ROLES=json.loads((R/"evidence/p15-10-semantic-arc-qa.json").read_text())["roles"]
GROUP={"neck":"body.reference","topwear":"body.reference","handwear":"body.reference","back hair":"hair.back","face":"face.skin","nose":"nose","mouth":"mouth","front hair":"hair.front","headwear":"hair.clip.cross_gold"}
SPLIT={"ears":("ear.far","ear.near"),"eyewhite":("eye.far","eye.near"),"irides":("eye.far","eye.near"),"eyelash":("eye.far","eye.near"),"eyebrow":("eye.far","eye.near")}
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def image(p):
 return np.asarray(Image.open(p).convert("RGBA")).copy()
def save(p,a):
 p.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(a,"RGBA").save(p)
def split_point(layers,key):
 # Separation is a deterministic heuristic on source-layer visible X distribution.
 a=next((image(P/x["path"]) for x in layers if x["name"]==key),None)
 if a is None:return None
 ys,xs=np.where(a[:,:,3]>16)
 if not len(xs):return None
 h=np.bincount(xs,minlength=a.shape[1])
 # Find two separated large regions; require both populations to be substantial.
 best=None
 for x in range(int(xs.min())+12,int(xs.max())-12):
  left=h[:x].sum();right=h[x:].sum()
  if min(left,right)<max(100,int(len(xs)*.12)):continue
  valley=h[max(0,x-6):min(len(h),x+7)].sum()
  score=valley/(min(left,right)+1)
  if best is None or score<best[0]:best=(score,x)
 return best[1] if best else None
def route(src):
 name=src["angle"];d=OUT/name;d.mkdir(parents=True,exist_ok=True)
 layers=src["nativeLayerEntries"]
 iris_cut=split_point(layers,"irides")
 ear_cut=split_point(layers,"ears")
 accum={r:[] for r in ROLES};provenance=[];missing=[];reversible=True
 for e in layers:
  if "path" not in e:continue
  a=image(P/e["path"])
  if e["name"] in GROUP:
   role=GROUP[e["name"]];pieces=[(role,a,"GROUPED_ROLE_UNVERIFIED")]
  elif e["name"] in SPLIT:
   cut=ear_cut if e["name"]=="ears" else iris_cut
   if cut is None:
    role="ear.near" if e["name"]=="ears" else "eye.near"
    pieces=[(role,a,"UNRESOLVED_SINGLE_SIDE")]
   else:
    left=a.copy();right=a.copy()
    left[:,cut:]=0;right[:,:cut]=0
    assert np.array_equal(np.maximum(left,right),a)
    far,near=SPLIT[e["name"]]
    pieces=[(far,left,"HEURISTIC_X_SPLIT"),(near,right,"HEURISTIC_X_SPLIT")]
  else:
   missing.append(e["name"]);continue
  for role,part,status in pieces:
   accum[role].append((e["index"],part,e["name"],status))
   dest=d/f"native-{e['index']:02d}-{role.replace('.','_')}.png"
   save(dest,part)
   provenance.append({"nativeLayer":e["name"],"index":e["index"],"role":role,
     "splitStatus":status,"visiblePixels":int(np.count_nonzero(part[:,:,3]>16)),
     "file":str(dest.relative_to(P)),"sha256":sha(dest)})
 results=[]
 for role in ROLES:
  parts=accum[role]
  # Combined preview: layer over from bottom to top, not an original painted layer.
  color=np.zeros((768,768,4),dtype=np.float32)
  for index,a,_,_ in sorted(parts,key=lambda t:t[0],reverse=True):
   source=a.astype(np.float32)/255.
   sa=source[:,:,3:4];da=color[:,:,3:4]
   oa=sa+da*(1-sa)
   rgb=np.divide(source[:,:,:3]*sa+color[:,:,:3]*da*(1-sa),
                 np.maximum(oa,1e-10),out=np.zeros_like(source[:,:,:3]))
   color=np.concatenate([rgb,oa],axis=2)
  res=np.uint8(np.rint(color*255).clip(0,255))
  path=d/(role+".png");save(path,res)
  results.append({"role":role,"sourceLayerCount":len(parts),"derived":True,
   "missingIndependentArt":len(parts)==0 or role in ("hair.side","hair.ahoge"),
   "path":str(path.relative_to(P)),"sha256":sha(path),
   "visiblePixels":int(np.count_nonzero(res[:,:,3]>16))})
 return {"yaw":name,"irisXBoundary":iris_cut,"earXBoundary":ear_cut,
   "mappingMethod":"REVERSIBLE_HEURISTIC_NO_ART_APPROVAL","nativeComponents":provenance,
   "roles":results,"unroutedNativeLayers":missing,
   "missingOrNonIndependentRoles":[r["role"] for r in results if r["missingIndependentArt"]],
   "acceptedIndependentArtMeshLayers":0}
def main():
 original=json.loads(QA.read_text())
 result=[route(src) for src in original["sources"]]
 report={"schema":"KOMA-P15-15-PSD-ROLE-ROUTING-V1",
  "characterId":"p0_character_001","sourceSHA256":sha(QA),
  "roleCount":len(ROLES),"angles":[r["yaw"] for r in result],
  "views":result,"artisticAcceptance":False,"validUnderpaintAccepted":False,
  "acceptedIndependentArtMeshLayers":0,
  "status":"REVERSIBLE_ROLE_ROUTING_ONLY_NEEDS_ART_REVIEW"}
 E.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"status":report["status"],"roleFiles":sum(len(x["roles"]) for x in result),
 "candidateParts":sum(len(x["nativeComponents"]) for x in result),
 "missingPerView":{x["yaw"]:x["missingOrNonIndependentRoles"] for x in result}},ensure_ascii=False))
if __name__=="__main__":main()

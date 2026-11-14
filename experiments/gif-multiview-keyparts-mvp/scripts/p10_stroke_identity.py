#!/usr/bin/env python3
"""P10 P0 semantic ink-stroke identity candidates from real source RGBA.

Uses OpenCV connected line contours, P9 shared-Lab color regions, and P5
physical landmark predictions to register only high-confidence candidates.
Stroke matches are labeled candidate identities until artistic verification.
"""
import argparse,hashlib,json,math
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
from p8_semantic_occlusion import tracked
from p9_color_region_correspondence import SOURCE_SIZE,VIEW_PAIRS,read as read_rgba

ROLE_SET=("face.skin","eye.near","eye.far","nose","mouth","ear.near",
          "hair.front","hair.side","hair.back","hair.ahoge",
          "hair.clip.cross_gold","body.reference")
MIN_AREA=9
MAX_STROKES=120
STROKE_CONFIDENCE=0.43
MARGIN_DISTANCE=6.0

def sha(file):
 h=hashlib.sha256()
 with Path(file).open("rb") as f:
  for part in iter(lambda:f.read(1024*1024),b""):h.update(part)
 return h.hexdigest()

def loaded(path):
 return json.loads(Path(path).read_text(encoding="utf-8"))

def srgb_luma(rgb):
 f=rgb.astype(np.float32)
 return (0.2126*f[:,:,0]+0.7152*f[:,:,1]+0.0722*f[:,:,2])

def extract_strokes(image,role,yaw,centers):
 a=image[:,:,3]
 opaque=a>=165
 # Ignore canvas-cut opacity boundaries so they cannot become false ink.
 visible=cv2.distanceTransform(opaque.astype(np.uint8),cv2.DIST_L2,3)
 rgb=image[:,:,:3]
 grey=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
 detected=cv2.Canny(grey,36,95,L2gradient=True)
 # Also include dark drawn interior linework, while keeping alpha borders separate.
 local=cv2.GaussianBlur(grey,(0,0),3)
 ink=((grey<125)&((local.astype(np.float32)-grey.astype(np.float32))>11))
 mask=(((detected>0)|(ink))&(visible>2.0)).astype(np.uint8)
 # Reconnect adjacent anti-aliased stroke pixels, not whole hair patches.
 mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((2,2),np.uint8))
 count,labels,stats,cents=cv2.connectedComponentsWithStats(mask,8)
 picked=[]
 for n in range(1,count):
  x,y,w,h,area=map(int,stats[n])
  if area<MIN_AREA or max(w,h)<4:continue
  if area>0.18*int(np.sum(opaque)):continue
  pts=np.argwhere(labels[y:y+h,x:x+w]==n).astype(np.float32)
  pts[:,0]+=y;pts[:,1]+=x
  centroid=np.array([float(cents[n,0]),float(cents[n,1])],dtype=float)
  if len(pts)>2:
   xy=pts[:,::-1].copy()
   covariance=np.cov(xy,rowvar=False)
   eigvals,eigvecs=np.linalg.eigh(covariance)
   direction=eigvecs[:,np.argmax(eigvals)]
   theta=float(np.arctan2(direction[1],direction[0])%np.pi)
   length=float(np.sqrt(max(eigvals))*3.4)
  else:theta=0;length=0
  cx,cy=int(round(centroid[0])),int(round(centroid[1]))
  pixel=image[max(0,min(SOURCE_SIZE-1,cy)),max(0,min(SOURCE_SIZE-1,cx)),:3]
  lab=cv2.cvtColor(np.array([[pixel]],dtype=np.uint8),cv2.COLOR_RGB2LAB)[0,0].astype(float)
  dist=((centers-lab[None,:])**2).sum(axis=1)
  color=int(np.argmin(dist))
  sid=f"{role}.yaw{yaw:03d}.stroke.{len(picked):03d}"
  picked.append({
   "id":sid,
   "xy":[round(float(v),2) for v in centroid],
   "bbox":[x,y,w,h],
   "area":area,
   "orientation":round(float(theta),5),
   "extent":round(length,2),
   "palette":color
  })
 picked.sort(key=lambda d:(-d["area"],d["xy"][1],d["xy"][0]))
 picked=picked[:MAX_STROKES]
 for i,item in enumerate(picked):
  item["id"]=f"{role}.yaw{yaw:03d}.stroke.{i:03d}"
 return picked

def predict(source,destination,shift):
 # Candidate displacement uses established P0 anatomical motion and
 # per-stroke normalized semantic-local positions as a weak secondary cue.
 o=np.array(source["xy"],dtype=float)
 physical=o+shift
 return physical

def cost(strokeA,strokeB,shift,agreeColor=True):
 pa=predict(strokeA,strokeB,shift)
 pb=np.array(strokeB["xy"])
 residue=float(np.linalg.norm(pb-pa))
 ratio=max(strokeA["area"],strokeB["area"])/max(1,min(strokeA["area"],strokeB["area"]))
 orientation=abs(strokeA["orientation"]-strokeB["orientation"])
 orientation=min(orientation,np.pi-orientation)
 extent=max(strokeA["extent"],strokeB["extent"])/max(1,min(strokeA["extent"],strokeB["extent"]))
 mismatch=0 if (strokeA["palette"]==strokeB["palette"] or not agreeColor) else 14
 value=residue+11*abs(math.log(ratio))+10*orientation+5*abs(math.log(extent))+mismatch
 return value,residue,ratio,orientation

def match(partsA,partsB,shift,limit=64):
 proposals=[]
 for ia,s in enumerate(partsA):
  for ib,t in enumerate(partsB):
   total,res,area,orient=cost(s,t,shift)
   if res>90 or area>5 or orient>1.25 or total>limit:continue
   proposals.append((total,ia,ib,res,area,orient))
 proposals.sort()
 chosen=[];usedA=set();usedB=set()
 for total,ia,ib,res,ratio,orient in proposals:
  if ia in usedA or ib in usedB:continue
  othersA=sorted(q[0] for q in proposals if q[1]==ia and q[2]!=ib)
  othersB=sorted(q[0] for q in proposals if q[2]==ib and q[1]!=ia)
  marginA=(othersA[0]-total) if othersA else 100
  marginB=(othersB[0]-total) if othersB else 100
  margin=min(marginA,marginB)
  confidence=float(np.exp(-total/75)*min(1,max(0,margin)/22))
  if confidence<STROKE_CONFIDENCE or margin<MARGIN_DISTANCE:continue
  s,t=partsA[ia],partsB[ib]
  chosen.append({
   "sourceId":s["id"],"targetId":t["id"],
   "sourceXY":s["xy"],"targetXY":t["xy"],
   "sourceArea":s["area"],"targetArea":t["area"],
   "cost":round(float(total),2),"physicalResidual":round(float(res),2),
   "ambiguityMargin":round(float(margin),2),
   "confidence":round(confidence,4),
   "sourcePalette":s["palette"],"targetPalette":t["palette"],
   "occlusion":"COMMON_VISIBLE_CANDIDATE"
  })
  usedA.add(ia);usedB.add(ib)
 return chosen

def visualize(root,out,source,paired,registry,overview):
 W=560;H=610
 chart=Image.new("RGB",(2*W,4*H),(33,46,64))
 d=ImageDraw.Draw(chart)
 examples=[(0,45,"hair.front"),(45,90,"hair.front"),
           (0,45,"eye.near"),(45,90,"face.skin")]
 for k,(a,b,role) in enumerate(examples):
  row=k*H
  for col,yaw in enumerate((a,b)):
   ref=source[yaw,role]
   face=Image.new("RGBA",(ref.shape[1],ref.shape[0]),(52,68,87,255))
   face.alpha_composite(Image.fromarray(ref,"RGBA"))
   thumb=face.convert("RGB").resize((W,W),Image.Resampling.LANCZOS)
   chart.paste(thumb,(col*W,row))
   d.text((col*W+10,row+W+10),f"{role} · yaw {yaw}",fill="white")
  record=paired.get(f"{a}-{b}/{role}")
  if record:
   for i,match in enumerate(record["accepted"][:24]):
    x1=match["sourceXY"][0]*W/SOURCE_SIZE;y1=row+match["sourceXY"][1]*W/SOURCE_SIZE
    x2=W+match["targetXY"][0]*W/SOURCE_SIZE;y2=row+match["targetXY"][1]*W/SOURCE_SIZE
    d.line((x1,y1,x2,y2),fill="#42e6bd",width=1)
    d.ellipse((x1-3,y1-3,x1+3,y1+3),fill="#ffdda5")
    d.ellipse((x2-3,y2-3,x2+3,y2+3),fill="#ffdda5")
 file=out/"stroke-identity-contact.jpg"
 chart.save(file,quality=93)
 return file

def run(root,out,conf=STROKE_CONFIDENCE):
 global STROKE_CONFIDENCE
 STROKE_CONFIDENCE=conf
 root=Path(root).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
 orig=loaded(root/"p5-see-through/mv-candidate/parts.json")
 land=loaded(root/"p5-see-through/mv-candidate/landmark-qa.json")
 regions=loaded(root/"p9-region-correspondence/qa.json")
 assert orig["characterId"]==land["characterId"]==regions["characterId"]=="p0_character_001"
 assert regions["sourceRegistrySHA256"]==sha(root/"p5-see-through/mv-candidate/parts.json")
 slots={(p["yawDeg"],p["semanticId"]):p for p in orig["parts"]}
 rgba={}
 outlines={}
 for (yaw,role),part in slots.items():
  file=root/part["path"]
  if sha(file)!=part["frameSha256"]:raise ValueError("P0 source changed "+str(file))
  rgba[yaw,role]=read_rgba(file)
  if part["visibility"]!="visible":continue
  pal=None
  for aa,bb in VIEW_PAIRS:
   if yaw in (aa,bb):
    record=regions["pairs"].get(f"{aa}-{bb}/{role}")
    if record:
     pal=np.array(record["paletteLab"],dtype=np.float32)
     break
  if pal is None:pal=np.array([[80,128,128]],dtype=np.float32)
  outlines[yaw,role]=extract_strokes(rgba[yaw,role],role,yaw,pal)
 pairs={};candidateCount=0;strokeCount=sum(len(v) for v in outlines.values())
 for a,b in VIEW_PAIRS:
  for role in ROLE_SET:
   entryA,entryB=slots[(a,role)],slots[(b,role)]
   if entryA["visibility"]!="visible" or entryB["visibility"]!="visible":
    continue
   src,dst=outlines.get((a,role),[]),outlines.get((b,role),[])
   anchors=tracked(land,role,a,b)
   if anchors:
    shift=np.median(np.array([end-start for _,start,end in anchors],dtype=float),axis=0)
   else:
    shift=np.zeros(2)
   accepted=match(src,dst,shift)
   candidateCount+=len(accepted)
   mappedSrc={i["sourceId"] for i in accepted}
   mappedDst={i["targetId"] for i in accepted}
   occluded=[x["id"] for x in src if x["id"] not in mappedSrc]
   appearing=[x["id"] for x in dst if x["id"] not in mappedDst]
   pairs[f"{a}-{b}/{role}"]={
    "semanticId":role,
    "angles":[a,b],
    "sourceSHA256":[entryA["frameSha256"],entryB["frameSha256"]],
    "physicalShift":shift.round(3).tolist(),
    "sourceStrokeCount":len(src),
    "targetStrokeCount":len(dst),
    "accepted":accepted,
    "occludedCandidates":occluded,
    "appearingCandidates":appearing,
    "matchCoverageSource":round(len(accepted)/max(1,len(src)),4),
    "matchCoverageTarget":round(len(accepted)/max(1,len(dst)),4),
    "acceptanceStatus":"RESEARCH_STROKE_IDENTITY_CANDIDATES"
   }
 chart=visualize(root,out,rgba,pairs,orig,{})
 print("P10 stroke components",strokeCount,"high-confidence",candidateCount)
 qa={
  "schema":"KOMA-P0-P10-INK_STROKE-IDENTITY-CANDIDATES-V1",
  "characterId":"p0_character_001",
  "sourceP0KeyViews":[0,45,90],
  "genuinePSDViews":[0,45],
  "sourceArtMeshViewSlots":len(slots),
  "nativeCanvas":[SOURCE_SIZE,SOURCE_SIZE],
  "registeredSemanticPairs":len(pairs),
  "extractedStrokes":strokeCount,
  "candidateIdentities":candidateCount,
  "minConfidence":conf,
  "method":"RGBA interior Canny and luminance ink extraction; connected components; P0 physical-motion guided bidirectional ambiguity exclusion",
  "sourceRegistrySHA256":sha(root/"p5-see-through/mv-candidate/parts.json"),
  "physicalLandmarksSHA256":sha(root/"p5-see-through/mv-candidate/landmark-qa.json"),
  "regionQA_SHA256":sha(root/"p9-region-correspondence/qa.json"),
  "sources":{f"{yaw}/{role}":{
   "path":orig_item["path"],"sha256":orig_item["frameSha256"],
   "visibility":orig_item["visibility"],
   "strokes":outlines.get((yaw,role),[])
   } for (yaw,role),orig_item in slots.items()},
  "pairs":pairs,
  "contactImage":str(chart.relative_to(root)),
  "contactSHA256":sha(chart),
  "status":"CANDIDATE_STROKE_IDENTITIES_REGISTERED",
  "visualApproval":"PENDING_MANUAL_IDENTITY_AND_VIEW_MOTION_INSPECTION"
 }
 (out/"qa.json").write_text(json.dumps(qa,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"registeredSemanticPairs":len(pairs),
  "extractedStrokes":strokeCount,"candidateIdentities":candidateCount,
  "sourceRGBA":len(slots),"status":qa["status"],
  "contactSHA256":qa["contactSHA256"]},ensure_ascii=False,indent=2))
 return qa

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--root",required=True)
 p.add_argument("--out",required=True)
 p.add_argument("--min-confidence",type=float,default=STROKE_CONFIDENCE)
 a=p.parse_args()
 run(a.root,a.out,a.min_confidence)

#!/usr/bin/env python3
"""Original P0 color-piece correspondences for layered anime inbetweening.

AnimeInterp (CVPR 2021) uses segment-guided matching to handle low texture.
This is a lightweight deterministic color-piece study using already
registered P0 PSD-derived RGBA layers and physical anchor tracks.

The output is a measured matching and provenance registry, not approval
that a particular matched region is artistically correct.
"""
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np
import cv2
from PIL import Image,ImageDraw,ImageFont
from p8_semantic_occlusion import tracked

SOURCE_SIZE=443
VIEW_PAIRS=((0,45),(45,90))
ROLES=("face.skin","eye.near","eye.far","nose","mouth","ear.near",
       "hair.front","hair.side","hair.back","hair.ahoge",
       "hair.clip.cross_gold","body.reference")
MIN_PART_AREA=140
MIN_REGION_AREA=90
CLUSTER_COUNT=5
CV2_CRITERIA=(cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER,16,0.5)

def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""):
   h.update(chunk)
 return h.hexdigest()

def read(path):
 with Image.open(path) as im:
  if im.mode!="RGBA" or im.size!=(1024,1024):
   raise ValueError("Source texture must be 1024 RGBA: "+str(path))
  image=np.array(im)
 return cv2.resize(image,(SOURCE_SIZE,SOURCE_SIZE),interpolation=cv2.INTER_AREA)

def color_cluster(src,dst,seed=42):
 masks=[i[:,:,3]>=170 for i in (src,dst)]
 lab=[cv2.cvtColor(img[:,:,:3],cv2.COLOR_RGB2LAB) for img in (src,dst)]
 selected=[]
 rng=np.random.default_rng(seed)
 for image,mask in zip(lab,masks):
  candidates=image[mask]
  if len(candidates)<MIN_PART_AREA:return None
  count=min(len(candidates),12000)
  samples=candidates[rng.choice(len(candidates),size=count,replace=False)].astype(np.float32)
  selected.append(samples)
 data=np.concatenate(selected)
 k=min(CLUSTER_COUNT,len(np.unique(data.astype(np.uint8),axis=0)))
 if k<=0:return None
 cv2.setRNGSeed(seed)
 _,_,centers=cv2.kmeans(data,k,None,CV2_CRITERIA,3,cv2.KMEANS_PP_CENTERS)
 mapped=[]
 for image,mask in zip(lab,masks):
  pixels=image.reshape(-1,3).astype(np.float32)
  near=np.full(pixels.shape[0],255,dtype=np.uint8)
  valid=np.flatnonzero(mask.reshape(-1))
  for chunk in np.array_split(valid,max(1,math.ceil(len(valid)/45000))):
   if not len(chunk):continue
   delta=pixels[chunk,None,:]-centers[None,:,:]
   dist=(delta*delta).sum(axis=2)
   near[chunk]=np.argmin(dist,axis=1).astype(np.uint8)
  mapped.append(near.reshape((SOURCE_SIZE,SOURCE_SIZE)))
 return mapped,centers

def regions(labels,alpha):
 output=[]
 cluster_values=[int(v) for v in np.unique(labels) if v!=255]
 for index in cluster_values:
  region=((labels==index)&(alpha>=170)).astype(np.uint8)
  region=cv2.morphologyEx(region,cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
  num,cc,stats,centers=cv2.connectedComponentsWithStats(region,8)
  for n in range(1,num):
   area=int(stats[n,cv2.CC_STAT_AREA])
   if area<MIN_REGION_AREA:continue
   center=[round(float(x),2) for x in centers[n]]
   rect=[int(x) for x in stats[n,:4]]
   output.append({"cluster":index,"area":area,
                  "center":center,"bbox":rect})
 output.sort(key=lambda x:x["area"],reverse=True)
 return output[:42]

def expected_translation(track,semantic,a,b):
 anchors=tracked(track,semantic,a,b)
 if anchors:
  moves=np.array([dst-src for _,src,dst in anchors],dtype=np.float64)
  return np.median(moves,axis=0)
 return np.array([0,0],dtype=np.float64)

def greedy_match(source,target,delta):
 candidates=[]
 for ia,s in enumerate(source):
  for ib,t in enumerate(target):
   if s["cluster"]!=t["cluster"]:continue
   locA=np.array(s["center"])
   locB=np.array(t["center"])
   displacement=locB-locA
   residue=np.linalg.norm(displacement-delta)
   areaRatio=max(s["area"],t["area"])/max(1,min(s["area"],t["area"]))
   cost=residue+16*abs(math.log(areaRatio))
   if residue<=115 and areaRatio<=6.0:
    candidates.append((round(float(cost),3),ia,ib,float(residue)))
 candidates.sort(key=lambda x:(x[0],x[1],x[2]))
 pairs=[];seenA=set();seenB=set()
 for cost,ia,ib,res in candidates:
  if ia in seenA or ib in seenB or cost>145:continue
  a=source[ia];b=target[ib]
  pairs.append({
   "colorRegion":a["cluster"],
   "originArea":a["area"],"destinationArea":b["area"],
   "originXY":a["center"],"destinationXY":b["center"],
   "residualFromPhysicalAnchor":round(res,2),
   "cost":cost
  })
  seenA.add(ia);seenB.add(ib)
 return pairs

def contact(root,records,out,images):
 names=("face.skin","hair.front","eye.near","hair.side")
 W=360;H=390
 sheet=Image.new("RGB",(2*len(names)*len(VIEW_PAIRS)*W,H),(26,38,54))
 draw=ImageDraw.Draw(sheet)
 for j,(a,b) in enumerate(VIEW_PAIRS):
  for k,sid in enumerate(names):
   i=2*len(names)*j+2*k
   # Render input crop and matched segments directly from author P0 RGBA.
   record=records.get(f"{a}-{b}/{sid}")
   if record is None:continue
   for offset,yaw in enumerate((a,b)):
    source=images[yaw,sid]
    matte=Image.new("RGBA",(SOURCE_SIZE,SOURCE_SIZE),(52,67,87,255))
    matte.alpha_composite(Image.fromarray(source,"RGBA"))
    frame=matte.convert("RGB").resize((W,W),Image.Resampling.LANCZOS)
    pos=(i+offset)*W
    sheet.paste(frame,(pos,0))
    draw.text((pos+8,365),f"{sid} {yaw}°",fill="#ffffff")
   left=2*len(names)*j+2*k
   for v in record["pairs"][:12]:
    ax,ay=v["originXY"];bx,by=v["destinationXY"]
    x1=left*W+ax*W/SOURCE_SIZE
    y1=ay*W/SOURCE_SIZE
    x2=(left+1)*W+bx*W/SOURCE_SIZE
    y2=by*W/SOURCE_SIZE
    color="#5af5d0"
    draw.ellipse((x1-3,y1-3,x1+3,y1+3),fill=color)
    draw.ellipse((x2-3,y2-3,x2+3,y2+3),fill=color)
    # Connecting lines may cross panel borders; this is analytical only.
    draw.line((x1,y1,x2,y2),fill=color,width=1)
 file=out/"region-pair-contact.jpg"
 sheet.save(file,quality=92)
 return file

def run(root,out):
 root=Path(root).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
 registry=json.loads((root/"p5-see-through/mv-candidate/parts.json").read_text())
 track=json.loads((root/"p5-see-through/mv-candidate/landmark-qa.json").read_text())
 assert registry["characterId"]==track["characterId"]=="p0_character_001"
 slots={(p["yawDeg"],p["semanticId"]):p for p in registry["parts"]}
 assert len(slots)==39
 images={}
 for y in (0,45,90):
  for sid in ROLES:
   part=slots[y,sid]
   file=root/part["path"]
   if sha(file)!=part["frameSha256"]:
    raise ValueError("Original P0 physical source sha mismatch")
   images[y,sid]=read(file)
 records={};pairCount=0;acceptedArea=0
 for a,b in VIEW_PAIRS:
  for sid in ROLES:
   A=slots[a,sid];B=slots[b,sid]
   if A["visibility"]!="visible" or B["visibility"]!="visible":continue
   first,second=images[a,sid],images[b,sid]
   clustered=color_cluster(first,second,seed=42)
   if clustered is None:continue
   label,centers=clustered
   regionsA=regions(label[0],first[:,:,3])
   regionsB=regions(label[1],second[:,:,3])
   shift=expected_translation(track,sid,a,b)
   pairs=greedy_match(regionsA,regionsB,shift)
   matched=sum(min(p["originArea"],p["destinationArea"]) for p in pairs)
   cap=max(1,min(int(np.sum(first[:,:,3]>=170)),int(np.sum(second[:,:,3]>=170))))
   coverage=min(1,matched/cap)
   record={
    "part":sid,"sourceAngles":[a,b],
    "referenceSourceSHA256":[A["frameSha256"],B["frameSha256"]],
    "paletteLab":[[round(float(x),2) for x in color] for color in centers],
    "physicalAnchorTranslation":shift.round(2).tolist(),
    "sourceRegions":len(regionsA),"destinationRegions":len(regionsB),
    "matchedRegions":len(pairs),
    "matchedMinAreaPixels":matched,
    "sourceAreaCoverageFraction":round(float(coverage),4),
    "pairs":pairs
   }
   records[f"{a}-{b}/{sid}"]=record
   pairCount+=len(pairs);acceptedArea+=matched
 image=contact(root,records,out,images)
 qa={
  "schema":"KOMA-P0-P9-REGION_GUIDED-CORRESPONDENCE-V1",
  "characterId":"p0_character_001",
  "sourceOriginalKeyViews":[0,45,90],
  "sourcePSDViews":[0,45],
  "canvas":[1024,1024],"workingCanvas":[SOURCE_SIZE,SOURCE_SIZE],
  "sourceRegistrySHA256":sha(root/"p5-see-through/mv-candidate/parts.json"),
  "physicalLandmarksSHA256":sha(root/"p5-see-through/mv-candidate/landmark-qa.json"),
  "method":"shared-Lab color clustering; connected color pieces; source-physical-guided region matching",
  "registeredSemanticPairs":len(records),"matchedColorRegions":pairCount,
  "matchedAreaPixels":acceptedArea,
  "pairs":records,
  "contactImage":str(image.relative_to(root)),
  "contactSHA256":sha(image),
  "status":"REGION_CORRESPONDENCE_RESEARCH_DATASET",
  "animatedArtisticAcceptance":"PENDING_VERIFIED_TEXEL_MAPPING"
 }
 (out/"qa.json").write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print(json.dumps({
  "status":qa["status"],"registeredSemanticPairs":len(records),
  "matchedColorRegions":pairCount,
  "matchedAreaPixels":acceptedArea,
  "contactSHA256":qa["contactSHA256"],
  "perPart":[{"role":k,"pairs":v["matchedRegions"],
              "coverage":v["sourceAreaCoverageFraction"]}
             for k,v in records.items()]
 },indent=2,ensure_ascii=False))
 return qa

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--root",required=True)
 p.add_argument("--out",required=True)
 a=p.parse_args()
 run(a.root,a.out)

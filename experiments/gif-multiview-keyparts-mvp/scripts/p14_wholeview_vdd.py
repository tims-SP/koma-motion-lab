#!/usr/bin/env python3
"""P14 full-original-key-art view-dependent 1024 RGBA correspondence candidate.

Whole-canvas bidirectional DIS is an independent comparison to the
painted P0 ArtMesh-specific VDD: the complete artist image keeps
inter-layer ownership at intermediate views, while source alpha
coverage determines visible surfaces. Preserves all approved P0 keys.
"""
import argparse,hashlib,json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from flow_render import get_flow
from p7_semantic_dense_flow import native_to_rgba
from p8_semantic_occlusion import output_frame_id
from p14_keyview_vdd import register

PAIRS=((45,67.5),(67.5,72.5),(72.5,90))
W=1024;GRID=443

def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()

def candidate(a,b,fa,fb,t,mode,grid):
 raw=[]
 for img,flow,w in ((a,fa,t),(b,fb,1-t)):
  f=img.astype(np.float32)/255
  f[:,:,:3]*=f[:,:,3:4]
  dx=cv2.resize(flow[:,:,0],(W,W))*W/GRID
  dy=cv2.resize(flow[:,:,1],(W,W))*W/GRID
  xx,yy=grid
  raw.append(cv2.remap(f,xx-w*dx,yy-w*dy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT))
 aa,bb=raw
 if mode=="source-weighted":
  mix=aa*(1-t)+bb*t
  mix[:,:,3]=np.maximum(mix[:,:,3],np.maximum(aa[:,:,3],bb[:,:,3])*.88)
  # Restore premultiplied color for union-alpha fallback from source
  # with more coverage, retaining original painted source texels.
  which=aa[:,:,3]>bb[:,:,3]
  src=np.where(which[:,:,None],aa,bb)
  sparse=(mix[:,:,3]-(aa[:,:,3]*(1-t)+bb[:,:,3]*t))>0.03
  norm=np.maximum(src[:,:,3:4],1e-5)
  rgb=src[:,:,:3]/norm*mix[:,:,3:4]
  mix[:,:,:3][sparse]=rgb[sparse]
 elif mode=="source-owner":
  mix=aa.copy() if t<.5 else bb.copy()
  alt=bb if t<.5 else aa
  low=mix[:,:,3]<.01
  mix[low]=alt[low]
 else:raise ValueError("Unknown painted source comparison mode "+mode)
 return native_to_rgba(mix)

def run(root,out,angles,mode):
 root=Path(root).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
 keys,parts,roles,sources,p8=register(root)
 textures={}
 for yaw in (45,67.5,72.5,90):
  with Image.open(keys[yaw][0]) as img:
   textures[yaw]=np.asarray(img.convert("RGBA")).copy()
 motion={x["angle"]:x for x in p8["frames"]}
 flow={}
 for a,b in PAIRS:
  xa=cv2.resize(textures[a],(GRID,GRID),interpolation=cv2.INTER_AREA)
  xb=cv2.resize(textures[b],(GRID,GRID),interpolation=cv2.INTER_AREA)
  flow[a,b]=get_flow(xa,xb,"dis")
 xx,yy=np.meshgrid(np.arange(W,dtype=np.float32),np.arange(W,dtype=np.float32))
 frames=[]
 for angle in angles:
  angle=float(angle)
  if angle in keys:
   with Image.open(keys[angle][0]) as src:frame=src.convert("RGBA").copy()
   source=sources[angle]
  elif angle<45:
   x=motion.get(angle)
   if x is None or sha(root/x["path"])!=x["sha256"]:
    raise ValueError("P8 original source view mismatch "+str(angle))
   with Image.open(root/x["path"]) as src:frame=src.convert("RGBA").copy()
   source="P8_ORIGINAL_SOURCE_VIEW"
  else:
   a,b=next((p for p in PAIRS if p[0]<angle<p[1]),(None,None))
   if a is None:raise ValueError("No registered original P0 candidate bracket")
   t=(angle-a)/(b-a)
   raw=candidate(textures[a],textures[b],*flow[a,b],t,mode,(xx,yy))
   frame=Image.fromarray(raw,"RGBA")
   source="PAINTED_P0_WHOLEVIEW_OCCLUSION_CORRESPONDENCE"
  f=out/output_frame_id(angle);frame.save(f)
  frames.append({"angle":angle,"path":str(f.relative_to(root)),
                 "sha256":sha(f),"bytes":f.stat().st_size,"sourceType":source})
 contact=Image.new("RGB",(6*280,310),(29,42,55))
 draw=ImageDraw.Draw(contact)
 for k,y in enumerate((0,22.5,45,67.5,72.5,90)):
  f=out/output_frame_id(y)
  with Image.open(f) as im:
   panel=Image.new("RGBA",(1024,1024),(45,61,78,255))
   panel.alpha_composite(im.convert("RGBA"))
  contact.paste(panel.convert("RGB").resize((280,280),Image.Resampling.LANCZOS),(k*280,0))
  draw.text((k*280+8,287),str(y)+"° · "+mode,fill="white")
 pic=out/"p14-p0-painted-source-contact.jpg"
 contact.save(pic,quality=94)
 qa={
  "schema":"KOMA-P0-P14-PAINTED-ORIGINAL-KEYFRAME-WHOLE-VDD-V1",
  "characterId":"p0_character_001",
  "originalP0Angles":[0,45,90],
  "paintedIntermediateKeyAngles":[67.5,72.5],
  "paintedArtMeshSemanticParts":13,
  "sourceKeys":{str(y):{"path":str(f.relative_to(root)),"sha256":sha(f)}
   for y,(f,s) in keys.items()},
  "registeredSourceSemanticViewSlots":39,
  "warpAlgorithm":"original source painted RGBA 1024 with DIS 443 bidirectional and alpha coverage",
  "flowCanvas":[443,443],
  "nativeCanvas":[1024,1024],
  "sourceOwnerMethod":mode,
  "frames":frames,"frameCount":len(frames),
  "contactPath":str(pic.relative_to(root)),"contactSHA256":sha(pic),
  "artisticApproval":"PENDING_ARTISTIC_P0_VIEW_CONTINUITY_INSPECTION",
  "status":"P14_PAINTED_ORIGINAL_VIEW_CORRESPONDENCE_CANDIDATE"
 }
 (out/"qa.json").write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({"status":qa["status"],"method":mode,"frames":len(frames),
                   "contactSHA256":qa["contactSHA256"]},indent=2))
 return qa

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--root",required=True)
 p.add_argument("--out",required=True)
 p.add_argument("--mode",choices=["source-weighted","source-owner"],default="source-weighted")
 p.add_argument("--angles",default=",".join(str(i*2.5) for i in range(37)))
 x=p.parse_args()
 run(x.root,x.out,[float(y) for y in x.angles.split(",")],x.mode)

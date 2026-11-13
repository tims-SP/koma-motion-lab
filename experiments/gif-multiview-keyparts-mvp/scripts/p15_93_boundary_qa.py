#!/usr/bin/env python3
"""Quantify continuity at independent keyframe boundaries for multi-view optical flow."""
import sys,hashlib,json,statistics
from pathlib import Path
import numpy as np
import cv2
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/"scripts"))
from flow_render import get_flow,morph,warp_float
P=R/"private-assets/exports/p15-92-angle-keyart"
D=R/"private-assets/exports/p15-93-flow-ablation"
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
small={}
for a in (45,60,75,90):
 name=f"yaw{a:03d}-{'reference' if a in (45,90) else 'registered'}.png"
 small[a]=np.asarray(Image.open(P/name).convert("RGBA").resize((512,512),Image.Resampling.LANCZOS)).copy()
y,x=np.indices((512,512),dtype=np.float32)
grid=np.stack((x,y),axis=2)
def fwd(a,flow,t):
 src=a.astype(np.float32)/255
 pre=np.concatenate([src[:,:,:3]*src[:,:,3:4],src[:,:,3:4]],axis=2)
 out=warp_float(pre,flow,t,grid)
 alpha=np.clip(out[:,:,3:4],0,1)
 rgb=np.divide(out[:,:,:3],np.maximum(alpha,1e-5))
 return (np.concatenate([np.clip(rgb,0,1),alpha],axis=2)*255).astype('uint8')
def bg(a):
 pix=a.astype('float32')
 alpha=pix[:,:,3:4]/255
 return pix[:,:,:3]*alpha+(1-alpha)*255
roi=(slice(155,355),slice(240,475))
out={"schema":"KOMA-P15-93-BOUNDARY_CONTINUITY_V1","segments":{},"roiHalfResolution":[240,155,475,355],"status":"RESEARCH_DIAGNOSTIC"}
rows=[]
for a,b in ((45,60),(60,75),(75,90)):
 flows=get_flow(small[a],small[b],"dis")
 samp=np.linspace(0,1,7)
 per={}
 for mode in ("blend","forward"):
  frames=[]
  for t in samp:
   if t<=0:pix=small[a]
   elif t>=1:pix=small[b]
   elif mode=="blend":pix=morph(small[a],small[b],*flows,t,grid)
   else:pix=fwd(small[a],flows[0],t)
   frames.append(pix)
  errs=[]
  for j in range(1,len(frames)):
   A=bg(frames[j-1])[roi];B=bg(frames[j])[roi]
   errs.append(float(np.abs(A-B).mean()))
  mid=statistics.median(errs[:5])
  per[mode]={"adjacentMAE":[round(v,3) for v in errs],
             "boundaryStepMAE":round(errs[-1],3),"internalMedianMAE":round(mid,3),
             "boundaryToInternalRatio":round(errs[-1]/max(mid,.00001),3),
             "maxStepMAE":round(max(errs),3)}
  for j in (4,5,6):
   tile=Image.fromarray(frames[j],"RGBA")
   white=Image.new("RGBA",tile.size,"white");white.alpha_composite(tile)
   thumb=white.convert("RGB").resize((310,310),Image.Resampling.LANCZOS)
   rows.append((a,b,mode,j,thumb))
 out["segments"][f"{a}-{b}"]=per
contact=Image.new("RGB",(310*3,330*6),"white")
draw=ImageDraw.Draw(contact)
for row in range(6):
 for col in range(3):
  a,b,mode,j,img=rows[row*3+col]
  x=col*310;y=row*330
  contact.paste(img,(x,y+20))
  draw.text((x+6,y+4),f"yaw {a+(b-a)*j/6:g} ({a}-{b}) {mode}",fill="black")
contact.save(D/"boundary-contact.jpg",quality=91)
out["contact"]="private-assets/exports/p15-93-flow-ablation/boundary-contact.jpg"
(R/"evidence/p15-93-boundary-qa.json").write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps({k:{m:{x:v for x,v in q.items() if x!="adjacentMAE"} for m,q in val.items()} for k,val in out["segments"].items()},indent=2))

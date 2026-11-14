#!/usr/bin/env python3
"""Compare source-preserving optical-flow warps against blended interpolation for P0 keyviews."""
from pathlib import Path
import sys,json,hashlib
import cv2
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/"scripts"))
from flow_render import get_flow,morph,warp_float
P=R/"private-assets/exports/p15-92-angle-keyart"
D=R/"private-assets/exports/p15-93-flow-ablation"
D.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source={a:np.asarray(Image.open(P / f"yaw{a:03d}-{'reference' if a in (45,90) else 'registered'}.png").convert("RGBA")) for a in (45,60,75,90)}
dim=512
small={a:np.asarray(Image.fromarray(source[a],"RGBA").resize((dim,dim),Image.Resampling.LANCZOS)).copy() for a in source}
yy,xx=np.indices((dim,dim),dtype=np.float32)
grid=np.stack((xx,yy),axis=2)
def single(a,flow,t):
 af=a.astype(np.float32)/255
 pre=np.concatenate([af[:,:,:3]*af[:,:,3:4],af[:,:,3:4]],axis=2)
 pa=warp_float(pre,flow,t,grid)
 al=np.clip(pa[:,:,3:4],0,1)
 rgb=np.divide(np.clip(pa[:,:,:3],0,1),np.maximum(al,1e-5))
 return np.concatenate([np.clip(rgb,0,1),al],axis=2).clip(0,1).astype(np.float32)*255
rows=[]
qa={"schema":"KOMA-P15-93-SOURCE_PRESERVING_FLOW_ABLATION_V1","angles":[52.5,67.5,82.5],
"methods":["blend","forward","backward"],"frames":{},"formalArtMeshAccepted":False,
"visualGate":"PENDING_VISUAL_SELECTION"}
for a,b in ((45,60),(60,75),(75,90)):
 mid=(a+b)/2
 ab,ba=get_flow(small[a],small[b],"dis")
 frames={
 "blend":morph(small[a],small[b],ab,ba,0.5,grid),
 "forward":single(small[a],ab,0.5).astype(np.uint8),
 "backward":single(small[b],ba,0.5).astype(np.uint8),
 }
 qa["frames"][str(mid)]={}
 for tag,ar in frames.items():
  out=Image.fromarray(ar,"RGBA").resize((1024,1024),Image.Resampling.LANCZOS)
  path=D/f"yaw{str(mid).replace('.','p')}-{tag}.png";out.save(path)
  qa["frames"][str(mid)][tag]={"path":str(path.relative_to(R)),"sha256":sha(path)}
  bg=Image.new("RGBA",out.size,"white");bg.alpha_composite(out)
  thumb=bg.convert("RGB").resize((410,410),Image.Resampling.LANCZOS)
  rows.append((mid,tag,thumb))
contact=Image.new("RGB",(410*3,444*3),"white")
d=ImageDraw.Draw(contact)
for n,(ang,tag,thumb) in enumerate(rows):
 i=n%3;j=n//3
 contact.paste(thumb,(i*410,j*444+24))
 d.text((i*410+8,j*444+6),f"yaw {ang:g} : {tag}",fill="black")
contact.save(D/"comparison.jpg",quality=92)
qa["contact"]="private-assets/exports/p15-93-flow-ablation/comparison.jpg"
(R/"evidence/p15-93-flow-ablation-qa.json").write_text(json.dumps(qa,indent=2)+"\n")
print(json.dumps({"angles":qa["angles"],"methods":qa["methods"],"frames":sum(len(x) for x in qa["frames"].values()),"contact":qa["contact"]},indent=2))

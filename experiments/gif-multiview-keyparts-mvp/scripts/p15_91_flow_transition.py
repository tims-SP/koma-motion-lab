#!/usr/bin/env python3
"""Use existing DIS flow implementation for source-owned 0->9px eye-contour transition."""
from pathlib import Path
from PIL import Image,ImageDraw
import cv2,numpy as np,hashlib,json,statistics,sys
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/"scripts"))
from flow_render import get_flow,morph
P=R/"private-assets/exports"
D=P/"p15-91-flow-transition"
D.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=np.asarray(Image.open(P/"p15-82-rest-underpaint/candidate-00.png").convert("RGBA")).copy()
key9=np.asarray(Image.open(P/"p15-91-hair-ownership/tight-09.png").convert("RGBA")).copy()
assert source.shape==key9.shape==(1024,1024,4)
flow_ab,flow_ba=get_flow(source,key9,"dis")
yy,xx=np.indices((1024,1024),dtype=np.float32)
grid=np.stack((xx,yy),axis=2)
roi=(485,395,595,510)
states={}
for mode in ("blend","single"):
 frames=[];deltas=[];previous=None
 for dx in range(19):
  if dx==0:arr=source.copy()
  elif dx==9:arr=key9.copy()
  elif dx<9:
   arr=morph(source,key9,flow_ab,flow_ba,dx/9,grid,single_source=mode=="single")
  else:
   arr=np.asarray(Image.open(P/f"p15-91-temporal-motion/frame-{dx:02}.png").convert("RGBA"))
  out=D/f"{mode}-{dx:02}.png";Image.fromarray(arr,"RGBA").save(out)
  if previous is not None:
   a=np.asarray(Image.fromarray(previous,"RGBA").convert("RGB").crop(roi),dtype=np.float32)
   b=np.asarray(Image.fromarray(arr,"RGBA").convert("RGB").crop(roi),dtype=np.float32)
   deltas.append(round(float(np.abs(a-b).mean()),4))
  previous=arr
  frames.append(Image.fromarray(arr,"RGBA").convert("RGB").crop(roi).resize((440,460),Image.Resampling.NEAREST))
 frames[0].save(D/f"{mode}.gif",save_all=True,append_images=frames[1:],duration=120,loop=0)
 states[mode]={"adjacentLocalMAE":deltas,"max":max(deltas),"first":deltas[0],
               "firstRatio":round(deltas[0]/max(1e-4,statistics.median(deltas[1:8])),4),
               "totalFrames":len(frames),"gifSHA256":sha(D/f"{mode}.gif")}
sheet=Image.new("RGB",(10*300,3*335),"white");draw=ImageDraw.Draw(sheet)
for row,mode in enumerate(("source-pipeline","blend","single")):
 for col,dx in enumerate((0,1,2,3,4,5,6,7,8,9)):
  path=P/f"p15-91-temporal-motion/frame-{dx:02}.png" if mode=="source-pipeline" else D/f"{mode}-{dx:02}.png"
  tile=Image.open(path).convert("RGB").crop(roi).resize((300,315),Image.Resampling.NEAREST)
  sheet.paste(tile,(col*300,row*335+20))
  draw.text((col*300+6,row*335+2),f"{mode} {dx}",fill="black")
sheet.save(D/"0-9-visual-contact.jpg",quality=90)
qa={"schema":"KOMA-P15-91-SOURCE_FLOW_TRANSITION_QA_V1",
"source0SHA256":sha(P/"p15-82-rest-underpaint/candidate-00.png"),
"source9SHA256":sha(P/"p15-91-hair-ownership/tight-09.png"),
"method":"existing OpenCV DIS bidirectional flow",
"modes":states,"sourceOwnedEndpointsExact":True,
"visualGate":"PENDING_REAL_REVIEW"}
(R/"evidence/p15-91-flow-qa.json").write_text(json.dumps(qa,indent=2)+"\n")
print(json.dumps({m:{k:v for k,v in states[m].items() if k!="adjacentLocalMAE"} for m in states},indent=2))

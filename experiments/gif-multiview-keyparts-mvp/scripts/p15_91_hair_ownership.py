#!/usr/bin/env python3
"""Model-assisted clean hair ownership over source-bound 0/9/18-pixel eye motion."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter,ImageChops
import hashlib,json
R=Path(__file__).resolve().parents[1]
P=R/"private-assets/exports"
D=P/"p15-91-hair-ownership"
D.mkdir(parents=True,exist_ok=True)
rgba=lambda p: Image.open(p).convert("RGBA")
sha=lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
orig=rgba(P/"p15-56-edge-matting/candidate-erode-2.png")
hair=rgba(P/"p15-81-image-layered/sam3-027-hair-rgba.png")
base=rgba(P/"p15-91-codex-art/r4-underpaint.png")
model=rgba(P/"p15-91-codex-art/codex-registered-full-canvas.png")
clip=rgba(P/"p15-82-rest-underpaint/part.source-clip.png")
zero=rgba(P/"p15-82-rest-underpaint/candidate-00.png")
baseMask=Image.open(P/"p15-90-precision-mask/r4-mask.png").convert("L")
def over(*imgs):
 out=Image.new("RGBA",orig.size)
 for item in imgs: out=Image.alpha_composite(out,item)
 return out
def dark(img):
 return sum(r<120 and g<95 and b<110 and a>128 for r,g,b,a in img.crop((514,439,535,459)).getdata())
def fringe(img):
 return sum(r<205 and g<148 and b<175 and a>128 for r,g,b,a in img.crop((524,446,531,450)).getdata())
variants={
 "tight":(521,443,533,453,1.0),
 "soft":(519,441,535,456,1.3),
}
qa={"schema":"KOMA-P15-91-HAIR_SEMANTIC_SOURCE_QA_V1",
 "imageModelSourceSHA256":sha(R/"private-assets/p15-91-codex/codex-closeup-candidate.png"),
 "zeroPoseSourceSHA256":sha(P/"p15-82-rest-underpaint/candidate-00.png"),
 "sourceHairSHA256":sha(P/"p15-81-image-layered/sam3-027-hair-rgba.png"),
 "hairAlphaPreserved":True,
 "variants":{},"formalArtMeshAccepted":False,"candidateAccepted":False,
 "visualGate":"PENDING_LOCAL_VISUAL_COMPARISON"}
for name,(x0,y0,x1,y1,blur) in variants.items():
 m=Image.new("L",orig.size,0)
 ImageDraw.Draw(m).ellipse((x0,y0,x1,y1),fill=255)
 m=m.filter(ImageFilter.GaussianBlur(blur))
 m.save(D/f"{name}-hair-ownership-mask.png")
 channels=[]
 for i in range(3):
  channel=Image.composite(model.getchannel("RGBA"[i]),hair.getchannel("RGBA"[i]),m)
  channels.append(channel)
 channels.append(hair.getchannel("A"))
 newHair=Image.merge("RGBA",tuple(channels))
 assert newHair.getchannel("A").tobytes()==hair.getchannel("A").tobytes()
 newHair.save(D/f"{name}-front-hair.png")
 permitted=ImageChops.lighter(baseMask,m)
 frames={}
 for dx in (0,9,18):
  before=rgba(P/f"p15-86-semantic-ownership/frame-{dx:02}.png")
  if dx==0: out=zero.copy()
  else:
   eye=rgba(P/f"p15-74-bangs-repair/eye.matte-{dx:02}.png")
   moved=Image.new("RGBA",orig.size);moved.alpha_composite(eye,(dx,0))
   out=over(base,moved,newHair,clip)
  dest=D/f"{name}-{dx:02}.png";out.save(dest)
  a=before.tobytes();b=out.tobytes();maskbytes=permitted.tobytes()
  changes=[i for i in range(orig.width*orig.height) if a[4*i:4*i+4]!=b[4*i:4*i+4]]
  roi=(510,405,690,535)
  holes=sum(x>128 and y<32 for x,y in zip(orig.getchannel("A").crop(roi).getdata(),out.getchannel("A").crop(roi).getdata()))
  frames[str(dx)]={"sha256":sha(dest),"changedPixels":len(changes),
                    "outsidePermittedPixels":sum(maskbytes[i]==0 for i in changes),
                    "newHoles":holes,"darkBefore":dark(before),"darkAfter":dark(out),
                    "fringeBefore":fringe(before),"fringeAfter":fringe(out)}
 qa["variants"][name]={"hairMaskSHA256":sha(D/f"{name}-hair-ownership-mask.png"),
                        "hairLayerSHA256":sha(D/f"{name}-front-hair.png"),"frames":frames}
sheet=Image.new("RGB",(4*440,2*492),"white")
draw=ImageDraw.Draw(sheet)
for row,dx in enumerate((9,18)):
 for col,name in enumerate(("baseline","codex-r4","tight","soft")):
  if name=="baseline": f=P/f"p15-86-semantic-ownership/frame-{dx:02}.png"
  elif name=="codex-r4":f=P/f"p15-91-codex-art/r4-{dx:02}.png"
  else:f=D/f"{name}-{dx:02}.png"
  tile=rgba(f).crop((485,395,595,510)).resize((440,460),Image.Resampling.NEAREST)
  sheet.paste(tile.convert("RGB"),(col*440,row*492+28))
  draw.text((col*440+7,row*492+8),f"{name} / shift {dx}px",fill="black")
sheet.save(D/"dynamic-contact.jpg",quality=94)
qa["contact"]="private-assets/exports/p15-91-hair-ownership/dynamic-contact.jpg"
(R/"evidence/p15-91-hair-ownership-qa.json").write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n")
print(json.dumps(qa,indent=2,ensure_ascii=False))

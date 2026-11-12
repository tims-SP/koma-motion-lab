#!/usr/bin/env python3
"""Evaluate tightly constrained model transfer for the hidden hair contour."""
from PIL import Image,ImageDraw,ImageFilter,ImageChops
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
P=R/"private-assets/exports"
D=P/"p15-90-precision-mask"
D.mkdir(parents=True,exist_ok=True)
im=lambda p:Image.open(p).convert("RGBA")
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
model=im(P/"p15-90-qwen-masked/returned-model-1024.png")
authmask=Image.open(P/"p15-90-qwen-masked/local-mask-1024.png").convert("L")
under=im(P/"p15-86-semantic-ownership/corrected-hidden-face.png")
hair=im(P/"p15-81-image-layered/sam3-027-hair-rgba.png")
clip=im(P/"p15-82-rest-underpaint/part.source-clip.png")
rest=im(P/"p15-82-rest-underpaint/candidate-00.png")
def over(*layers):
 out=Image.new("RGBA",(1024,1024))
 for x in layers:out=Image.alpha_composite(out,x)
 return out
def dark(image):
 return sum(r<120 and g<95 and b<110 and a>128 for r,g,b,a in image.crop((514,439,535,459)).getdata())
variants={"r4":(525,444,535,454,1.0),"r6":(523,442,537,456,1.4),"r8":(521,440,539,458,1.8)}
qa={"schema":"KOMA-P15-90-PRECISION_MASK_QA_V1","modelSHA256":sha(P/"p15-90-qwen-masked/returned-model-1024.png"),"variants":{},"sourceOwnedRestPose":True,"formalArtMeshAccepted":False,"candidateAccepted":False,"visualGate":"PENDING_IMAGE_REVIEW"}
for label,(x0,y0,x1,y1,blur) in variants.items():
 mask=Image.new("L",(1024,1024),0)
 ImageDraw.Draw(mask).ellipse((x0,y0,x1,y1),fill=255)
 mask=ImageChops.multiply(mask.filter(ImageFilter.GaussianBlur(blur)),authmask)
 mask.save(D/f"{label}-mask.png")
 patched=Image.composite(model,under,mask)
 patched.save(D/f"{label}-underpaint.png")
 frames={}
 for dx in (0,9,18):
  baseline=im(P/f"p15-86-semantic-ownership/frame-{dx:02}.png")
  if dx==0:out=rest.copy()
  else:
   eye=im(P/f"p15-74-bangs-repair/eye.matte-{dx:02}.png")
   moved=Image.new("RGBA",(1024,1024));moved.alpha_composite(eye,(dx,0))
   out=over(patched,moved,hair,clip)
  dest=D/f"{label}-{dx:02}.png";out.save(dest)
  a=baseline.tobytes();b=out.tobytes();mm=mask.tobytes()
  changed=[i for i in range(1024*1024) if a[4*i:4*i+4]!=b[4*i:4*i+4]]
  frames[str(dx)]={"sha256":sha(dest),"changedPixels":len(changed),
        "outsideMask":sum(mm[i]==0 for i in changed),
        "darkBefore":dark(baseline),"darkAfter":dark(out)}
 qa["variants"][label]={"maskSHA256":sha(D/f"{label}-mask.png"),
      "maskBBox":mask.getbbox(),"activePixels":sum(x>0 for x in mask.getdata()),"frames":frames}
sheet=Image.new("RGB",(440*4,492*2),"white");draw=ImageDraw.Draw(sheet)
for i,label in enumerate(("baseline","r4","r6","r8")):
 for row,dx in enumerate((9,18)):
  path=P/f"p15-86-semantic-ownership/frame-{dx:02}.png" if label=="baseline" else D/f"{label}-{dx:02}.png"
  tile=im(path).crop((485,395,595,510)).resize((440,460),Image.Resampling.NEAREST)
  sheet.paste(tile.convert("RGB"),(440*i,492*row+28))
  draw.text((440*i+8,492*row+8),f"{label} / shift {dx}px",fill="black")
sheet.save(D/"precision-contact.jpg",quality=94)
qa["review"]=str((D/"precision-contact.jpg").relative_to(R))
(R/"evidence/p15-90-precision-mask-qa.json").write_text(json.dumps(qa,indent=2)+"\n")
print(json.dumps(qa,indent=2))

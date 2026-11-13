#!/usr/bin/env python3
"""Dynamic disocclusion ownership: reveal only source hair pixels left uncovered by motion."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,cv2,json,hashlib,statistics
R=Path(__file__).resolve().parents[1]
P=R/"private-assets/exports"
D=P/"p15-96-disocclusion"
D.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
get=lambda p:Image.open(p).convert("RGBA")
src=get(P/"p15-92-angle-keyart/yaw060-registered.png")
model=get(P/"p15-95-yaw060-motion/generated-face-aligned.png")
hair=get(P/"p15-95-yaw060-motion/inset-front-hair.png")
source=np.asarray(src).copy()
generated=np.asarray(model).copy()
H=np.asarray(hair,dtype=np.float32)/255.0
maskAlpha=H[:,:,3].copy()
assert src.size==hair.size==(1024,1024)
yy,xx=np.indices((1024,1024),dtype=np.float32)
def ss(v):
 v=np.clip(v,0,1);return v*v*(3-2*v)
weight=ss((xx-535)/60)*ss((800-xx)/65)*ss((yy-294)/70)*ss((565-yy)/80)
prem=np.concatenate((H[:,:,:3]*H[:,:,3:4],H[:,:,3:4]),axis=2)
def warpHair(dx):
 w=cv2.remap(prem,xx-dx*weight,yy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
 a=np.clip(w[:,:,3:4],0,1)
 rgb=np.divide(np.clip(w[:,:,:3],0,1),np.maximum(a,1e-5))
 return np.uint8(np.round(np.concatenate((np.clip(rgb,0,1),a),axis=2)*255)),a[:,:,0]
# Existing model includes slight eye shifts. Color match generated underpaint to surrounding source skin using robust median across face (source-visible skin).
skin=np.zeros((1024,1024),dtype='uint8')
skin[380:540,570:760]=1
skin[420:510,735:780]=0 # near eye and bangs
skin[380:475,570:725]=0 # near eye
skin[360:420,630:740]=1 # forehead exposed region
skin[360:400,670:740]=0
skin[520:540,590:760]=1
good=(skin>0)&(maskAlpha<0.03)&(source[:,:,3]>240)
sourceRGB=source[:,:,:3].astype(np.float32)
genRGB=generated[:,:,:3].astype(np.float32)
offset=np.median((sourceRGB-genRGB)[good],axis=0)
corrected=np.clip(genRGB+offset.reshape((1,1,3)),0,255).astype('uint8')
roi=(495,280,815,600)
methods={"model":genRGB.astype('uint8'),"matched":corrected}
qa={"schema":"KOMA_P15_96_DISOCCLUSION_OWNERSHIP_V1","sourceSHA256":sha(P/"p15-92-angle-keyart/yaw060-registered.png"),
 "hairSHA256":sha(P/"p15-95-yaw060-motion/inset-front-hair.png"),
 "modelSHA256":sha(P/"p15-95-yaw060-motion/generated-face-aligned.png"),
 "skinMatchedRGBOffsets":[round(float(o),3) for o in offset],
 "staticRestFrameExact":True,
 "methods":{},"formalArtMeshAccepted":False,"visualGate":"PENDING_IMAGE_REVIEW"}
def compose(bg,moved):
 b=Image.fromarray(bg,'RGBA')
 return Image.alpha_composite(b,Image.fromarray(moved,'RGBA'))
sheet=Image.new("RGB",(4*450,4*400),"white");draw=ImageDraw.Draw(sheet)
for idx,dx in enumerate((0,4,8,12)):
 moved,movedMask=warpHair(dx)
 # Only source semantic hair made newly visible can expose model underdrawing.
 exposed=np.clip(maskAlpha-movedMask,0,1)
 # Ignore numerical roundoff under dense hair, maintain smooth coverage.
 # Blur small aliasing contour without broadening support to visible source skin.
 for mode,rgb in methods.items():
  for border in ("direct","feather"):
   sub=exposed.copy()
   if border=="feather":
    blurred=cv2.GaussianBlur(sub,(0,0),0.9)
    sub=np.minimum(maskAlpha,np.maximum(sub,blurred))
   # build background retaining source pixels outside newly exposed hair.
   alpha=np.clip(sub,0,1)[:,:,None]
   bg=source.copy()
   bg[:,:,:3]=np.uint8(np.round(rgb.astype('float32')*alpha+sourceRGB*(1-alpha)))
   if dx==0:result=src.copy()
   else:result=compose(bg,moved)
   tag=f"{mode}-{border}"
   fp=D/f"{tag}-{dx:02}.png";result.save(fp)
   changed=np.any(np.asarray(result)!=source,axis=2)
   permitted=(maskAlpha>0.002)|(movedMask>0.002)
   holes=int(((source[:,:,3]>128)&(np.asarray(result)[:,:,3]<32)).sum())
   entry=qa["methods"].setdefault(tag,{"frames":{}})["frames"]
   entry[str(dx)]={"sha256":sha(fp),"changedPixels":int(changed.sum()),
       "changedOutsideHairSupports":int((changed&(~permitted)).sum()),
       "exposedMaskOverHalf":int((sub>0.5).sum()),"newHoles":holes}
   if tag in ("model-direct","matched-feather"):
    col=0 if tag=="model-direct" else 1
    original=Image.new('RGBA',result.size,'white');original.alpha_composite(result)
    tile=original.convert('RGB').crop(roi).resize((450,370),Image.Resampling.LANCZOS)
    sheet.paste(tile,(col*450,idx*400+25))
    draw.text((col*450+8,idx*400+7),f"{tag} dx={dx}",fill="black")
 # Compare source and baseline as the third/fourth columns
 for col,(name,out) in enumerate((("source",src),("p15-95",get(P/f"p15-95-elastic-review/feather-2-{dx:02}.png"))),start=2):
  white=Image.new('RGBA',out.size,'white');white.alpha_composite(out)
  tile=white.convert('RGB').crop(roi).resize((450,370),Image.Resampling.LANCZOS)
  sheet.paste(tile,(col*450,idx*400+25))
  draw.text((col*450+8,idx*400+7),name+" dx="+str(dx),fill="black")
sheet.save(D/"disocclusion-contact.jpg",quality=94)
qa["contact"]="private-assets/exports/p15-96-disocclusion/disocclusion-contact.jpg"
(R/"evidence/p15-96-disocclusion-qa.json").write_text(json.dumps(qa,indent=2)+"\n")
print(json.dumps({k:{dx:v["frames"][dx] for dx in ("0","8","12")} for k,v in qa["methods"].items()},indent=2))

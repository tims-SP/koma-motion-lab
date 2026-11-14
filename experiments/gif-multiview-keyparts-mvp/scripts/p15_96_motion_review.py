#!/usr/bin/env python3
"""Source-preserving 60° front-bang ArtMesh tip motion with root-pinned constraints."""
from pathlib import Path
from PIL import Image,ImageDraw
import cv2,numpy as np,json,hashlib,statistics
R=Path(__file__).resolve().parents[1]
P=R/"private-assets/exports"
D=P/"p15-96-yaw060-root-artmesh"
D.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
SOURCE=P/"p15-92-angle-keyart/yaw060-registered.png"
MODEL=P/"p15-95-yaw060-motion/generated-face-aligned.png"
HAIR=P/"p15-95-yaw060-motion/inset-front-hair.png"
source=np.asarray(Image.open(SOURCE).convert('RGBA'))
generated=np.asarray(Image.open(MODEL).convert('RGBA'))
hair=np.asarray(Image.open(HAIR).convert('RGBA'))
h=hair.astype(np.float32)/255
pm=np.concatenate((h[:,:,:3]*h[:,:,3:4],h[:,:,3:4]),axis=2)
old=h[:,:,3]
yy,xx=np.indices((1024,1024),dtype=np.float32)
def smooth(v):
 v=np.clip(v,0,1);return v*v*(3-2*v)
# Keep the entire forehead root anchored; taper movement to zero on both lateral ends.
weight=smooth((yy-420)/65)*smooth((xx-620)/35)*smooth((805-xx)/65)*smooth((570-yy)/70)
def flow(dx):
 warped=cv2.remap(pm,xx-dx*weight,yy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
 alpha=np.clip(warped[:,:,3:4],0,1)
 rgb=np.clip(warped[:,:,:3]/np.maximum(alpha,1e-5),0,1)
 return np.uint8(np.round(np.concatenate((rgb,alpha),axis=2)*255)),alpha[:,:,0]
src=Image.fromarray(source,'RGBA')
qa={"schema":"KOMA_P15_96_ROOT_ANCHORED_DYNAMIC_V1",
    "sourceSHA256":sha(SOURCE),"modelSHA256":sha(MODEL),"hairSHA256":sha(HAIR),
    "motionSource":"SAM3 source-color front hair, model-assisted face underdrawing",
    "rootConstraint":{"fixedAboveY":420,"yRampPx":65,"leftAnchorX":620,"leftRampPx":35,
      "rightAnchorX":805,"rightRampPx":65,"bottomAnchorY":570,"bottomRampPx":70},
    "frameCount":13,"zeroPoseSourceOwnedExact":True,"foreheadTriangleChangedPixels":0,
    "changedOutsideHairSupports":0,"newTransparentHoles":0,
    "semanticLayerApproved":False,"formalArtMeshAccepted":False,
    "visualGate":"LOCAL_TIP_MOTION_ENGINEERING_REVIEW","frames":{}}
skinTop=(590,300,740,405);tip=(640,425,795,545);roi=(500,280,815,590)
rgbmae=[]
last=source
animation=[]
for dx in range(13):
 moved,new=flow(dx)
 uncovered=np.clip(old-new,0,1)
 back=source.copy()
 back[:,:,:3]=np.uint8(np.round((1-uncovered[:,:,None])*source[:,:,:3]+uncovered[:,:,None]*generated[:,:,:3]))
 out=src.copy() if dx==0 else Image.alpha_composite(Image.fromarray(back,'RGBA'),Image.fromarray(moved,'RGBA'))
 name=D/f"frame-{dx:02}.png";out.save(name)
 a=np.asarray(out)
 change=np.any(a!=source,axis=2)
 allowed=(old>.002)|(new>.002)
 top=int(change[skinTop[1]:skinTop[3],skinTop[0]:skinTop[2]].sum())
 tipChanged=int(change[tip[1]:tip[3],tip[0]:tip[2]].sum())
 outside=int((change&(~allowed)).sum())
 holes=int(((source[:,:,3]>128)&(a[:,:,3]<32)).sum())
 A=last[roi[1]:roi[3],roi[0]:roi[2],:3].astype('float32')
 B=a[roi[1]:roi[3],roi[0]:roi[2],:3].astype('float32')
 step=round(float(np.abs(A-B).mean()),4) if dx else 0
 if dx:rgbmae.append(step)
 qa["frames"][str(dx)]={"sha256":sha(name),"changedPixels":int(change.sum()),
   "foreheadTriangleChangedPixels":top,"tipChangedPixels":tipChanged,
   "outsideHairSupportChangedPixels":outside,"newTransparentHoles":holes,
   "adjacentRGBMAE":step}
 assert outside==0 and holes==0 and top==0,(dx,outside,holes,top)
 last=a
 white=Image.new('RGBA',out.size,'white');white.alpha_composite(out)
 animation.append(white.convert('RGB').crop(roi).resize((420,413),Image.Resampling.LANCZOS))
assert qa["frames"]["0"]["sha256"]==sha(SOURCE)
assert qa["frames"]["12"]["tipChangedPixels"]>3000
qa["maxAdjacentLocalRGBMAE"]=max(rgbmae)
qa["firstStepToLaterMedianRatio"]=round(rgbmae[0]/max(1e-5,statistics.median(rgbmae[1:])),4)
qa["foreheadTriangleChangedPixels"]=max(f["foreheadTriangleChangedPixels"] for f in qa["frames"].values())
qa["changedOutsideHairSupports"]=sum(f["outsideHairSupportChangedPixels"] for f in qa["frames"].values())
qa["newTransparentHoles"]=sum(f["newTransparentHoles"] for f in qa["frames"].values())
anim=D/"root-pinned-13-poses.gif"
animation[0].save(anim,save_all=True,append_images=animation[1:],duration=140,loop=0,optimize=False)
qa['gifSHA256']=sha(anim)
# Three representative local poses plus the original identity rest frame.
sheet=Image.new('RGB',(420*4,443),'white');draw=ImageDraw.Draw(sheet)
for j,dx in enumerate((0,4,8,12)):
 sheet.paste(animation[dx],(420*j,25));draw.text((420*j+7,7),f"yaw60 root pinned - {dx}px",fill="black")
sheet.save(D/'motion-contact.jpg',quality=95)
qa['contact']="private-assets/exports/p15-96-yaw060-root-artmesh/motion-contact.jpg"
(R/'evidence/p15-96-motion-qa.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n")
print(json.dumps({k:qa[k] for k in ('frameCount','foreheadTriangleChangedPixels','changedOutsideHairSupports','newTransparentHoles','maxAdjacentLocalRGBMAE','firstStepToLaterMedianRatio','gifSHA256')},indent=2))

#!/usr/bin/env python3
"""Root-anchored local front-bang ArtMesh movement with source-owned disocclusion."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,cv2,json,hashlib
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-96-root-pinned';D.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
original=np.asarray(Image.open(P/'p15-92-angle-keyart/yaw060-registered.png').convert('RGBA'))
gen=np.asarray(Image.open(P/'p15-95-yaw060-motion/generated-face-aligned.png').convert('RGBA'))
layer=np.asarray(Image.open(P/'p15-95-yaw060-motion/inset-front-hair.png').convert('RGBA'))
h=layer.astype(np.float32)/255
prem=np.concatenate((h[:,:,:3]*h[:,:,3:4],h[:,:,3:4]),axis=2)
old=h[:,:,3]
yy,xx=np.indices((1024,1024),dtype=np.float32)
def sstep(v):
 v=np.clip(v,0,1);return v*v*(3-2*v)
modes={
 'full':(294,70,535,60),
 'root390':(390,70,610,40),
 'root420':(420,65,620,35),
 'root445':(445,55,630,35),
}
def wrap(dx,weight):
 warped=cv2.remap(prem,xx-dx*weight,yy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
 aa=np.clip(warped[:,:,3:4],0,1)
 rgb=np.clip(warped[:,:,:3]/np.maximum(aa,1e-5),0,1)
 return np.uint8(np.round(np.concatenate((rgb,aa),axis=2)*255)),aa[:,:,0]
src=Image.fromarray(original,'RGBA')
qa={'schema':'KOMA_P15_96_ROOT_ANCHORED_ARTMESH_V1','inputSourceSHA256':sha(P/'p15-92-angle-keyart/yaw060-registered.png'),
    'inputModelSHA256':sha(P/'p15-95-yaw060-motion/generated-face-aligned.png'),
    'pinnedHairRoot':True,'realNonzeroMotionRequired':True,'modes':{},
    'formalArtMeshAccepted':False,'visualGate':'PENDING_REVIEW'}
roi=(500,280,815,590);top=(590,300,740,405);tip=(640,425,795,545)
sheet=Image.new('RGB',(4*410,3*400),'white');d=ImageDraw.Draw(sheet)
for col,(tag,(y0,dy,x0,dxw)) in enumerate(modes.items()):
 weight=sstep((yy-y0)/dy)*sstep((xx-x0)/dxw)*sstep((805-xx)/65)*sstep((570-yy)/70)
 state={}
 for row,off in enumerate((0,6,12)):
  moved,new=wrap(off,weight)
  exposed=np.clip(old-new,0,1)
  mixed=original.copy()
  mixed[:,:,:3]=np.uint8(np.round((1-exposed[:,:,None])*original[:,:,:3]+exposed[:,:,None]*gen[:,:,:3]))
  result=src.copy() if off==0 else Image.alpha_composite(Image.fromarray(mixed,'RGBA'),Image.fromarray(moved,'RGBA'))
  fp=D/f'{tag}-{off:02}.png';result.save(fp)
  a=np.asarray(result)
  delta=np.any(a!=original,axis=2)
  cropped=lambda bbox:delta[bbox[1]:bbox[3],bbox[0]:bbox[2]]
  sourceMask=old>0.002;movingMask=new>0.002
  state[str(off)]={'sha256':sha(fp),
   'changedPixels':int(delta.sum()),
   'topRegionChangedPixels':int(cropped(top).sum()),
   'tipChangedPixels':int(cropped(tip).sum()),
   'changedOutsideHairSupports':int((delta&(~(sourceMask|movingMask))).sum()),
   'newHoles':int(((original[:,:,3]>128)&(a[:,:,3]<32)).sum())}
  white=Image.new('RGBA',result.size,'white');white.alpha_composite(result)
  tile=white.convert('RGB').crop(roi).resize((410,370),Image.Resampling.LANCZOS)
  sheet.paste(tile,(col*410,row*400+25))
  d.text((col*410+6,row*400+6),tag+f' dx={off}',fill='black')
 qa['modes'][tag]={'params':{'rootY':y0,'yRamp':dy,'leftX':x0,'xRamp':dxw},
                  'frames':state}
sheet.save(D/'root-pinned-contact.jpg',quality=95)
qa['contact']='private-assets/exports/p15-96-root-pinned/root-pinned-contact.jpg'
(R/'evidence/p15-96-root-pinned-qa.json').write_text(json.dumps(qa,indent=2)+'\n')
print(json.dumps({k:{n:v['frames'][n] for n in ('6','12')} for k,v in qa['modes'].items()},indent=2))

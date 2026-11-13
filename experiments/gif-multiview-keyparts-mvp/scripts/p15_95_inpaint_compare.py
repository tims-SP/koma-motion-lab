#!/usr/bin/env python3
"""Compare source-context inpainting with generated face painting for front-hair deformation."""
from pathlib import Path
from PIL import Image,ImageDraw
import cv2,numpy as np,json,hashlib
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports';D=P/'p15-95-inpaint-compare'
D.mkdir(parents=True,exist_ok=True)
src=Image.open(P/'p15-92-angle-keyart/yaw060-registered.png').convert('RGBA')
gen=Image.open(P/'p15-95-elastic-review/feather-2-underpaint.png').convert('RGBA')
hair=Image.open(P/'p15-95-yaw060-motion/inset-front-hair.png').convert('RGBA')
mask=Image.open(P/'p15-95-yaw060-motion/inset-mask.png').convert('L')
rgb=np.asarray(src.convert('RGB')).copy()
m=np.where(np.asarray(mask)>160,255,0).astype('uint8')
yy,xx=np.indices((1024,1024),dtype=np.float32)
def smooth(v):
 v=np.clip(v,0,1)
 return v*v*(3-2*v)
w=smooth((xx-535)/60)*smooth((800-xx)/65)*smooth((yy-294)/70)*smooth((565-yy)/80)
hf=np.asarray(hair,dtype=np.float32)/255
prem=np.concatenate((hf[:,:,:3]*hf[:,:,3:4],hf[:,:,3:4]),axis=2)
def move(dx):
 out=cv2.remap(prem,xx-dx*w,yy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
 a=np.clip(out[:,:,3:4],0,1)
 rgb=np.clip(out[:,:,:3]/np.maximum(a,1e-6),0,1)
 return Image.fromarray(np.uint8(np.rint(np.concatenate((rgb,a),axis=2)*255)),'RGBA')
modeBg={'generated':gen}
for radius in (5,12):
 fill=cv2.inpaint(rgb,m,radius,cv2.INPAINT_TELEA)
 new=src.copy()
 new.putdata([(*v,alpha) for v,alpha in zip(fill.reshape(-1,3),np.asarray(src.getchannel('A')).reshape(-1))])
 # Blend original and inpaint only inside a feathered semantic hair support.
 back=Image.composite(new,src,mask)
 back.save(D/f'inpaint-r{radius}-underpaint.png')
 modeBg[f'inpaint-r{radius}']=back
modeBg['model-and-inpaint']=Image.blend(gen,modeBg['inpaint-r5'],.5)
roi=(485,290,835,670)
sheet=Image.new('RGB',(350*(len(modeBg)+1),405*2),'white');d=ImageDraw.Draw(sheet)
modes=['original']+list(modeBg)
qa={'schema':'KOMA-P15-95_INPAINT_UNDERPAINT_COMPARISON_V1','algorithms':modes,'formalArtMeshAccepted':False,'visualGate':'PENDING_VISUAL_REVIEW','frames':{}}
for dx in (4,12):
 col=0
 for name in modes:
  bg=src if name=='original' else modeBg[name]
  hairmove=move(dx)
  result=Image.alpha_composite(bg,hairmove)
  out=D/f'{name}-{dx:02}.png'
  result.save(out)
  srcAlpha=np.asarray(src.getchannel('A'))>128
  outAlpha=np.asarray(result.getchannel('A'))<32
  holes=int(np.logical_and(srcAlpha,outAlpha).sum())
  qa['frames'][f'{name}:{dx}']={'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'holes':holes}
  white=Image.new('RGBA',src.size,'white');white.alpha_composite(result)
  tile=white.convert('RGB').crop(roi).resize((350,375),Image.Resampling.LANCZOS)
  row=0 if dx==4 else 1
  sheet.paste(tile,(col*350,row*405+25))
  d.text((col*350+5,row*405+7),f'{name} dx{dx}',fill='black')
  col+=1
sheet.save(D/'inpaint-method-contact.jpg',quality=92)
(R/'evidence/p15-95-inpaint-qa.json').write_text(json.dumps(qa,indent=2)+'\n')
print(json.dumps({'methods':list(modeBg),'frames':len(qa['frames'])},indent=2))

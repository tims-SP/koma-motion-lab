#!/usr/bin/env python3
"""Bounded front-hair deformation with image-generated face underdrawing."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,cv2,hashlib,json,statistics
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports';D=P/'p15-95-elastic-review'
D.mkdir(parents=True,exist_ok=True)
read=lambda p:Image.open(p).convert('RGBA')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=read(P/'p15-92-angle-keyart/yaw060-registered.png')
gen=read(P/'p15-95-yaw060-motion/generated-face-aligned.png')
hair=read(P/'p15-95-yaw060-motion/inset-front-hair.png')
mask=Image.open(P/'p15-95-yaw060-motion/inset-mask.png').convert('L')
guard=Image.open(R/'private-assets/p15-95-underpaint/source-underpaint-mask-1024.png').convert('L')
assert src.size==gen.size==hair.size==(1024,1024)
def sstep(t):
 u=np.clip(t,0,1)
 return u*u*(3-2*u)
yy,xx=np.indices((1024,1024),dtype=np.float32)
weight=sstep((xx-535)/60)*sstep((800-xx)/65)*sstep((yy-294)/70)*sstep((565-yy)/80)
print('elastic weight',round(float(weight.max()),3),'mean on hair mask',round(float(weight[np.asarray(mask)>128].mean()),3))
hairFloat=np.asarray(hair,dtype=np.float32)/255
prem=np.concatenate((hairFloat[:,:,:3]*hairFloat[:,:,3:4],hairFloat[:,:,3:4]),axis=2)
roi=(485,290,835,670)
def hmove(dx):
 mapx=xx-dx*weight
 warp=cv2.remap(prem,mapx,yy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
 alpha=np.clip(warp[:,:,3:4],0,1)
 rgb=np.clip(warp[:,:,:3]/np.maximum(alpha,1e-5),0,1)
 arr=np.uint8(np.rint(np.concatenate((rgb,alpha),axis=2)*255))
 return Image.fromarray(arr,'RGBA')
def mae(a,b):
 aa=np.asarray(a.crop(roi).convert('RGB'),dtype=np.float32)
 bb=np.asarray(b.crop(roi).convert('RGB'),dtype=np.float32)
 return float(np.abs(aa-bb).mean())
def blend(*ims):
 out=Image.new('RGBA',(1024,1024))
 for im in ims:out=Image.alpha_composite(out,im)
 return out
modes={'feather-2':2,'feather-5':5,'feather-10':10}
qa={'schema':'KOMA-P15-95-ELASTIC_HAIR_UNDERPAINT_TRIAL_V1',
    'modelSHA256':sha(R/'private-assets/p15-95-underpaint/face-underpaint-native.png'),
    'hairSourceSHA256':sha(P/'p15-95-yaw060-motion/inset-front-hair.png'),
    'motion':'bounded smoothstep spatial displacement 0-12px with premultiplied alpha',
    'sourcePose0Exact':True,'semanticLayerApproved':False,
    'formalArtMeshAccepted':False,'visualGate':'PENDING_DYNAMIC_IMAGE_REVIEW','modes':{}}
for tag,radius in modes.items():
 backMask=mask.filter(ImageFilter.GaussianBlur(radius))
 back=Image.composite(gen,src,backMask)
 back.save(D/f'{tag}-underpaint.png')
 prev=src
 data={}
 for dx in range(13):
  out=src.copy() if dx==0 else blend(back,hmove(dx))
  fp=D/f'{tag}-{dx:02}.png';out.save(fp)
  a=np.asarray(src);b=np.asarray(out)
  changed=np.any(a!=b,axis=2)
  alphaHole=int(((a[:,:,3]>128)&(b[:,:,3]<32)).sum())
  data[str(dx)]={'sha256':sha(fp),'changedPixels':int(changed.sum()),
        'holes':alphaHole,'adjacentRGBMAE':round(mae(prev,out),4) if dx else 0}
  prev=out
 qa['modes'][tag]={'featherRadius':radius,
        'frames':data,'firstStepRatio':round(data['1']['adjacentRGBMAE']/
        max(1e-4,statistics.median(data[str(i)]['adjacentRGBMAE'] for i in range(2,13))),3),
        'underpaintSHA256':sha(D/f'{tag}-underpaint.png')}
# Compare the existing rigid front-hair baseline against elastic trials.
cols=[('Original source',None),('Rigid without underpaint','rigid'),('Elastic r2','feather-2'),('Elastic r5','feather-5'),('Elastic r10','feather-10')]
poses=(0,4,8,12)
sheet=Image.new('RGB',(350*len(cols),405*len(poses)),'white');draw=ImageDraw.Draw(sheet)
for j,dx in enumerate(poses):
 for i,(lab,mode) in enumerate(cols):
  if mode is None: im=src
  elif mode=='rigid':im=read(P/f'p15-95-yaw060-motion/semantic-baseline-{dx:02}.png') if dx else src
  else:im=read(D/f'{mode}-{dx:02}.png')
  img=Image.new('RGBA',im.size,'white');img.alpha_composite(im)
  tile=img.convert('RGB').crop(roi).resize((350,375),Image.Resampling.LANCZOS)
  x=350*i;y=405*j
  sheet.paste(tile,(x,y+25))
  draw.text((x+6,y+7),f'{lab} dx={dx}',fill='black')
sheet.save(D/'elastic-dynamic-contact.jpg',quality=94)
qa['contact']='private-assets/exports/p15-95-elastic-review/elastic-dynamic-contact.jpg'
(R/'evidence/p15-95-elastic-qa.json').write_text(json.dumps(qa,indent=2)+'\n')
print(json.dumps({k:{'firstStepRatio':v['firstStepRatio'],
'frame12Changed':v['frames']['12']['changedPixels'],
'holes12':v['frames']['12']['holes'],
'maxRGBMAE':max(d['adjacentRGBMAE'] for d in v['frames'].values())} for k,v in qa['modes'].items()},indent=2))

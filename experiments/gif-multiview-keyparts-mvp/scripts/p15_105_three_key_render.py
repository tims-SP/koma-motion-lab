#!/usr/bin/env python3
"""Real native 67.5° costume keyart, integrated with shared P15-101 head mesh.

Three pose-specific garment keyframes 60, 67.5 (Codex-generated), 75.
Native 67.5° is used exactly as the source garment, independently of proxy
61/73° interpolation. Compare no-motion, DIS bidirectional and nearest-owner.

All outputs still require artistic visual verification.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import json,cv2,numpy as np,statistics
import p15_101_head_render as head
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-105-three-key-vdd'
D.mkdir(parents=True,exist_ok=True)
Q=json.loads((R/'evidence/p15-105-native-art-qa.json').read_text())
baseline=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
S=512;Y,X=np.indices((S,S),np.float32)
angles=head.angles;keyAngle=67.5
sha=lambda p:sha256(Path(p).read_bytes()).hexdigest()
def source(path):
 return np.asarray(Image.open(path).convert('RGBA').resize((S,S),Image.Resampling.LANCZOS))
# Source-owned torso segments of the original real keyviews, independently of the head hull.
parts={
 '60':head.parts['60']['body'].copy(),
 '67.5':source(R/Q['registeredPath']),
 '75':head.parts['75']['body'].copy()}
# Make head boundary match the original source garment: slight overlap behind face/hair.
for k,v in parts.items():
 Image.fromarray(v,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS).save(D/f'source-yaw{k.replace(".","p")}.png')
def prem(arr):
 f=arr.astype(np.float32)/255
 return np.concatenate([f[:,:,:3]*f[:,:,3:4],f[:,:,3:4]],axis=2)
def unprem(arr):
 a=np.clip(arr[:,:,3:4],0,1)
 rgb=np.divide(arr[:,:,:3],np.maximum(a,1e-6))
 return np.uint8(np.round(np.concatenate([np.clip(rgb,0,1),a],axis=2)*255))
def visual(arr):
 p=prem(arr);rgb=p[:,:,:3]+1-p[:,:,3:4]
 return np.uint8(np.round(np.clip(rgb,0,1)*255))
def dis_flow(a,b):
 dis=cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
 dis.setFinestScale(0)
 dis.setVariationalRefinementIterations(4)
 x=cv2.cvtColor(visual(a),cv2.COLOR_RGB2GRAY)
 y=cv2.cvtColor(visual(b),cv2.COLOR_RGB2GRAY)
 flow=dis.calc(x,y,None)
 flow=np.clip(flow,-30,30)
 return cv2.GaussianBlur(flow,(0,0),1.25)
flows={}
for a,b in [('60','67.5'),('67.5','75')]:
 flows[(a,b)]=(dis_flow(parts[a],parts[b]),dis_flow(parts[b],parts[a]))
 print('flow',a,b,'avg',round(float(np.linalg.norm(flows[(a,b)][0],axis=2).mean()),4),
       'max',round(float(np.linalg.norm(flows[(a,b)][0],axis=2).max()),4),flush=True)
def warp(src,flow,t):
 f=prem(src)
 mx=X-flow[:,:,0]*t;my=Y-flow[:,:,1]*t
 return cv2.remap(f,mx.astype(np.float32),my.astype(np.float32),cv2.INTER_LINEAR,
                  borderMode=cv2.BORDER_CONSTANT)
def alpha_over(dst,top):
 a=top[:,:,3:4]
 return np.concatenate((top[:,:,:3]+dst[:,:,:3]*(1-a),a+dst[:,:,3:4]*(1-a)),axis=2)
def head_surface(t):
 # VDD shared P15-101 head surface: maintain face/hair identity and avoid redrawing.
 maps={v:head.mesh_map(v,t) for v in ('60','75')}
 a=head.warp(head.parts['60']['head'],maps['60'])
 b=head.warp(head.parts['75']['head'],maps['75'])
 merged=(1-t)*a+t*b
 return np.clip(merged,0,1)
def cloth(a,b,t,method):
 if method=='three_key_direct':
  return (1-t)*prem(parts[a])+t*prem(parts[b])
 flowAB,flowBA=flows[(a,b)]
 pa=warp(parts[a],flowAB,t);pb=warp(parts[b],flowBA,1-t)
 if method=='three_key_flow':
  return np.clip(pa*(1-t)+pb*t,0,1)
 if method=='three_key_owner':
  # Source ownership changes only around segment midpoint; outside the transition, one source remains sharp.
  w=np.clip((t-.43)/.14,0,1);w=w*w*(3-2*w)
  return np.clip(pa*(1-w)+pb*w,0,1)
 raise ValueError(method)
methods=['three_key_direct','three_key_flow','three_key_owner']
qa={'schema':'KOMA_P15_105_THREE_KEY_GARMENT_VDD_V1',
 'characterId':'p0_character_001','sourceAngles':[60,67.5,75],'renderedAngles':angles,
 'modelOriginalKeyartSha256':Q['nativeSHA256'],'registeredKeyartSha256':Q['registeredSHA256'],
 'headRenderer':'P15-101 source-owned head-hair ArtMesh',
 'sourceGarments':{'60':'P15-101 native 60 body','67.5':Q['registeredPath'],'75':'P15-101 native 75 body'},
 'registrationVerified':True,'methods':{m:{} for m in methods},
 'nativeMidpointGeometryAccepted':False,'continuousVisualAccepted':False,
 'sourceGenuineMidpoint':True,
 'flowMagnitude':{a+'-'+b:{'meanPx':float(np.linalg.norm(x,axis=2).mean()),
  'maxPx':float(np.linalg.norm(x,axis=2).max())} for (a,b),(x,_) in flows.items()}}
for angle in angles:
 t=(angle-60)/15
 for method in methods:
  if angle in (60,75):
   v='60' if angle==60 else '75'
   im=Image.open(R/head.TOP['views'][v]['sourcePath']).convert('RGBA')
  else:
   if angle<=keyAngle:
    a,b='60','67.5';w=(angle-60)/7.5
   else:
    a,b='67.5','75';w=(angle-67.5)/7.5
   garment=cloth(a,b,w,method)
   h=head_surface(t)
   result=alpha_over(garment,h)
   result=alpha_over(result,head.get_ahoge(t))
   im=Image.fromarray(unprem(result),'RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
   if angle==keyAngle:
    # Preserve actual registered middle keyart texels wherever the face mesh no longer occludes the garment.
    restored=np.asarray(im).copy()
    registered=np.asarray(Image.open(R/Q['registeredPath']).convert('RGBA'))
    restored[750:,:,:]=registered[750:,:,:]
    im=Image.fromarray(restored,'RGBA')
  dest=D/(method+'-yaw'+f'{angle:g}'.replace('.','p')+'.png')
  im.save(dest)
  qa['methods'][method][f'{angle:g}']={'relativePath':str(dest.relative_to(R)),'sha256':sha(dest)}
 print('frame',angle,flush=True)
# Test intended native key middle (opaque garment ROI should copy source pixels from new garment).
middle=np.asarray(Image.open(R/Q['registeredPath']).convert('RGBA'))
midRendered=np.asarray(Image.open(D/'three_key_flow-yaw67p5.png').convert('RGBA'))
# Head surface ends around the neck; measured overwrite is a diagnostic not a secret substitution.
mask=(middle[:,:,3]>220)&(np.indices((1024,1024))[0]>770)
regionDifference=np.abs(middle.astype(np.int16)-midRendered.astype(np.int16)).mean(axis=2)
qa['nativeMidKeyframe']={'clothingOpaquePixelsBelow770':int(mask.sum()),
    'clothingSourceMAE':round(float(regionDifference[mask].mean()),5),
    'clothingSourceExactFraction':round(float(np.mean(regionDifference[mask]<.01)),5)}
# Contact sheet and regional real RGB metrics versus established baseline.
regions={'garment':(335,655,865,1015),'bow':(500,744,790,975),
         'jewel':(595,770,701,862),'collar':(400,665,805,835),
         'head':(440,285,840,640)}
framesBaseline=baseline['methods']['head_alpha_blend']
rows=['P15-101-head_alpha_blend']+methods
contact=Image.new('RGB',(355*len(angles),407*len(rows)),'white');pen=ImageDraw.Draw(contact)
metrics={}
for row,method in enumerate(rows):
 imageArr=[]
 for col,angle in enumerate(angles):
  file=R/(framesBaseline[f'{angle:g}']['relativePath'] if row==0 else qa['methods'][method][f'{angle:g}']['relativePath'])
  art=Image.open(file).convert('RGBA')
  bg=Image.new('RGBA',art.size,'white');bg.alpha_composite(art)
  rgb=np.asarray(bg.convert('RGB'),np.float32)
  imageArr.append(rgb)
  crop=bg.convert('RGB').crop((365,615,845,1015)).resize((355,376),Image.Resampling.LANCZOS)
  contact.paste(crop,(col*355,row*407+26))
  pen.text((col*355+5,row*407+6),method+f' {angle:g}',fill='black')
 for name,(x0,y0,x1,y1) in regions.items():
  diff=[round(float(np.abs(imageArr[i][y0:y1,x0:x1]-imageArr[i-1][y0:y1,x0:x1]).mean()),4) for i in range(1,len(imageArr))]
  metrics.setdefault(method,{})[name]={'adjacentRGBMAE':diff,
   'maxAdjacentRGBMAE':max(diff),'meanAdjacentRGBMAE':round(statistics.mean(diff),4),
   'midpointAdjacentRGBMAE':max(diff[3:5])}
contact.save(D/'three-key-garment-contact.jpg',quality=94)
qa['metrics']=metrics;qa['contact']='private-assets/exports/p15-105-three-key-vdd/three-key-garment-contact.jpg'
(R/'evidence/p15-105-render-qa.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')
print('MIDDLE_NATIVE',json.dumps(qa['nativeMidKeyframe']),flush=True)
print('METRICS',json.dumps({m:{n:(v['maxAdjacentRGBMAE'],v['midpointAdjacentRGBMAE'])
 for n,v in regions.items() if n in ('bow','jewel','collar','head')} for m,regions in metrics.items()},indent=2),flush=True)

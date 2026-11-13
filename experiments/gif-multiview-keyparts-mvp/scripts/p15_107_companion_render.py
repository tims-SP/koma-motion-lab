#!/usr/bin/env python3
"""P0 native 60/67.5/75 consistent-source garment VDD validation.

Codex generated companion keyarts are original PNG, registered by source
brooch pixel. Compare direct and bidirectional DIS garment correspondence,
with original endpoints retained vs companion endpoints for artistic review.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import json,cv2,numpy as np,statistics
import p15_101_head_render as head
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-107-companion-render';D.mkdir(parents=True,exist_ok=True)
aud=json.loads((R/'evidence/p15-107-patch-qa.json').read_text())
native=json.loads((R/'evidence/p15-105-native-art-qa.json').read_text())
previous=json.loads((R/'evidence/p15-105-render-qa.json').read_text())
benchmark=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
assert aud['allDimensionsAndColorsValidated']
S=512;Y,X=np.indices((S,S),np.float32);angles=head.angles
sha=lambda f:sha256(Path(f).read_bytes()).hexdigest()
def load(path):
 return np.asarray(Image.open(path).convert('RGBA').resize((S,S),Image.Resampling.LANCZOS))
sources={'60':load(R/aud['generatedCompanions']['60']['registeredPath']),
 '67.5':load(R/native['registeredPath']),
 '75':load(R/aud['generatedCompanions']['75']['registeredPath'])}
def prem(arr):
 f=arr.astype(np.float32)/255
 return np.concatenate((f[:,:,:3]*f[:,:,3:4],f[:,:,3:4]),axis=2)
def unprem(p):
 alpha=np.clip(p[:,:,3:4],0,1)
 rgb=np.clip(p[:,:,:3]/np.maximum(alpha,1e-6),0,1)
 return np.uint8(np.round(np.concatenate((rgb,alpha),axis=2)*255))
def over(back,fg):
 alpha=np.clip(fg[:,:,3:4],0,1)
 return np.concatenate((fg[:,:,:3]+back[:,:,:3]*(1-alpha),alpha+back[:,:,3:4]*(1-alpha)),axis=2)
def visible(src):
 p=prem(src)
 return np.uint8(np.round((p[:,:,:3]+1-p[:,:,3:4])*255))
def flow(a,b):
 dis=cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
 dis.setFinestScale(0)
 dis.setVariationalRefinementIterations(4)
 F=dis.calc(cv2.cvtColor(visible(a),cv2.COLOR_RGB2GRAY),
            cv2.cvtColor(visible(b),cv2.COLOR_RGB2GRAY),None)
 return cv2.GaussianBlur(np.clip(F,-24,24),(0,0),1.1)
motion={}
for a,b in [('60','67.5'),('67.5','75')]:
 f=flow(sources[a],sources[b]);g=flow(sources[b],sources[a])
 motion[(a,b)]=(f,g)
 print('flow',a,b,'mean',round(float(np.linalg.norm(f,axis=2).mean()),3),flush=True)
def warp(f,F,amount):
 return cv2.remap(f,(X-F[:,:,0]*amount).astype(np.float32),
                       (Y-F[:,:,1]*amount).astype(np.float32),
                       cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
def face(t):
 mapping={v:head.mesh_map(v,t) for v in ('60','75')}
 a=head.warp(head.parts['60']['head'],mapping['60'])
 b=head.warp(head.parts['75']['head'],mapping['75'])
 return head.skin_blend(a,b,t)
def garment(angle,strategy):
 if angle<=67.5:
  a,b='60','67.5';t=(angle-60)/7.5
 else:
  a,b='67.5','75';t=(angle-67.5)/7.5
 t=float(np.clip(t,0,1))
 if strategy=='direct':
  result=(1-t)*prem(sources[a])+t*prem(sources[b])
 elif strategy=='flow':
  f,g=motion[(a,b)]
  A=warp(prem(sources[a]),f,t)
  B=warp(prem(sources[b]),g,1-t)
  result=(1-t)*A+t*B
 elif strategy=='soft_flow':
  f,g=motion[(a,b)]
  A=warp(prem(sources[a]),f,t)
  B=warp(prem(sources[b]),g,1-t)
  w=np.clip((t-.25)/.50,0,1)
  w=w*w*(3-2*w)
  result=(1-w)*A+w*B
 else:raise ValueError(strategy)
 return np.clip(result,0,1)
def render(angle,mode):
 strategy='soft_flow' if mode.startswith('companion_soft') else 'flow' if mode.startswith('companion_flow') else 'direct'
 preserve=not mode.endswith('native_keys')
 if preserve and angle in (60,75):
  view=str(int(angle))
  return Image.open(R/head.TOP['views'][view]['sourcePath']).convert('RGBA')
 t=(angle-60)/15
 body=garment(angle,strategy)
 merged=over(body,face(t))
 merged=over(merged,head.get_ahoge(t))
 output=Image.fromarray(unprem(merged),'RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
 if angle==67.5:
  target=np.asarray(Image.open(R/native['registeredPath']).convert('RGBA'))
  arr=np.asarray(output).copy()
  arr[770:,:,:]=target[770:,:,:]
  output=Image.fromarray(arr,'RGBA')
 return output
methods=['companion_direct_orig_keys','companion_flow_orig_keys',
         'companion_soft_orig_keys','companion_direct_native_keys','companion_flow_native_keys']
report={'schema':'KOMA_P15_107_COMPANION_GARMENT_VDD_V1',
 'characterId':'p0_character_001','angles':angles,
 'sourceAngles':[60,67.5,75],
 'sourceCompanionHashes':{v:aud['generatedCompanions'][v]['registeredSHA256'] for v in ('60','75')},
 'registeredMiddleSHA256':native['registeredSHA256'],
 'originalSourcePreservationInOrigKeyMethods':True,
 'comparators':['P15-101 head_alpha_blend','P15-105 three_key_direct'],
 'methods':{m:{} for m in methods},'artisticAcceptance':False,
 'flowMagnitude':{a+'-'+b:float(np.linalg.norm(f,axis=2).mean()) for (a,b),(f,_) in motion.items()}}
for angle in angles:
 for mode in methods:
  im=render(angle,mode)
  f=D/(mode+'-yaw'+f'{angle:g}'.replace('.','p')+'.png')
  im.save(f)
  report['methods'][mode][f'{angle:g}']={'relativePath':str(f.relative_to(R)),'sha256':sha(f)}
 print('render view',angle,flush=True)
regions={'bow':(500,744,790,975),'collar':(400,665,805,835),
 'jewel':(595,770,701,862),'garment':(335,655,865,1015),'head':(440,285,840,640)}
baseline={
 'P15-101-head_alpha_blend':{k:v['relativePath'] for k,v in benchmark['methods']['head_alpha_blend'].items()},
 'P15-105-three_key_direct':{k:v['relativePath'] for k,v in previous['methods']['three_key_direct'].items()}}
sourceMethods={m:{k:v['relativePath'] for k,v in frames.items()} for m,frames in report['methods'].items()}
allMethods={**baseline,**sourceMethods}
contact=Image.new('RGB',(330*len(angles),382*len(allMethods)),'white');pen=ImageDraw.Draw(contact)
for row,(m,frames) in enumerate(allMethods.items()):
 samples=[]
 for col,a in enumerate(angles):
  path=R/frames[f'{a:g}']
  im=Image.open(path).convert('RGBA')
  bg=Image.new('RGBA',im.size,'white');bg.alpha_composite(im)
  samples.append(np.asarray(bg.convert('RGB'),np.float32))
  contact.paste(bg.convert('RGB').crop((365,615,845,1015)).resize((330,356),Image.Resampling.LANCZOS),(330*col,382*row+22))
  pen.text((330*col+4,382*row+4),m+f' {a:g}',fill='black')
 for region,(x0,y0,x1,y1) in regions.items():
  values=[round(float(np.abs(samples[i][y0:y1,x0:x1]-samples[i-1][y0:y1,x0:x1]).mean()),4)
         for i in range(1,len(samples))]
  report.setdefault('metrics',{}).setdefault(m,{})[region]={
   'adjacentRGBMAE':values,'maxAdjacentRGBMAE':max(values),
   'interiorMaxRGBMAE':max(values[1:7]),
   'meanAdjacentRGBMAE':round(statistics.mean(values),4)}
contact.save(D/'companion-garment-contact.jpg',quality=94)
report['contact']='private-assets/exports/p15-107-companion-render/companion-garment-contact.jpg'
(R/'evidence/p15-107-companion-qa.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print('METRICS',json.dumps({m:{key:(v['maxAdjacentRGBMAE'],v['interiorMaxRGBMAE']) for key,v in zones.items()
 if key in ('bow','collar','jewel')} for m,zones in report['metrics'].items()},indent=2),flush=True)

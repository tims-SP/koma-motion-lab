#!/usr/bin/env python3
"""Localized source-owned ink correction on intact P15-107 full-character art.

Keep the original complete P0 body, collar, shoulder trim and hair frame.
Only apply source-consistent bow/jewel material in measured native bow
regions. Compare inner-fabric, outline, and left shoulder-gold alternatives.
This isolates artwork-identity benefit from incomplete background mattes.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import cv2,json,numpy as np,statistics
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-115-local-patch';D.mkdir(parents=True,exist_ok=True)
Q=json.loads((R/'evidence/p15-115-source-qa.json').read_text())
OWN=json.loads((R/'evidence/p15-108-stroke-qa.json').read_text())
B=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
P101=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
sha=lambda x:sha256(Path(x).read_bytes()).hexdigest()
S=512;views=['60','67.5','75'];angles=B['angles']
def im(path,mode='RGBA',method=Image.Resampling.LANCZOS):
 return np.asarray(Image.open(path).convert(mode).resize((S,S),method))
def seg(a):
 if a<=67.5:return '60','67.5',float((a-60)/7.5)
 return '67.5','75',float((a-67.5)/7.5)
def remap(role,angle):
 a,b,t=seg(angle)
 wa=np.asarray(Q['registered'][role][a]['inverseAffine512'],np.float32)
 wb=np.asarray(Q['registered'][role][b]['inverseAffine512'],np.float32)
 w=(1-t)*wa+t*wb
 src=im(R/Q['registered'][role]['67.5']['registeredPath'])
 return cv2.warpAffine(src,w,(S,S),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,
   borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
def sourceMask(role,angle):
 a,b,t=seg(angle)
 name='goldTrim' if role.startswith('goldTrim') else role
 def pix(view):
  m=np.asarray(Image.open(R/OWN['views'][view]['layers'][name]['maskPath']).convert('L').resize((S,S),Image.Resampling.NEAREST),np.float32)/255
  if role=='goldTrimLeft':m[:,342:]=0
  return m
 return np.clip((1-t)*pix(a)+t*pix(b),0,1)
def composite(base,art,alpha):
 # P0 fully original body maintained outside chosen source-owned material.
 a=np.clip(np.float32(alpha),0,1)[:,:,None]
 fg=art.astype(np.float32)
 bg=base.astype(np.float32)
 # Original is opaque where native P0 fabric is present.
 return np.uint8(np.round(np.clip((1-a)*bg+a*fg,0,255)))
methods=['ink_core','inner_fabric','ink_core_gold']
q={'schema':'KOMA_P15_115_LOCAL_SOURCE_TEXTURE_CORRECTION_V1',
 'characterId':'p0_character_001','sourceKeys':views,'angles':angles,
 'registrationSHA256':sha(R/'evidence/p15-115-source-qa.json'),
 'baseSource':'P15-107 full-character native-source body and P15-101 head',
 'sourceOwnedMaterial':'native 67.5-degree P0 bow and jewel art',
 'modeDescriptions':{
  'ink_core':'replace inner 3px-eroded ribbon & jewel overlap region, preserve P15-107 source silhouette',
  'inner_fabric':'replace more of original visible ribbon interior with canonical native textile',
  'ink_core_gold':'inner ribbon plus a limited source-owned left shoulder trim core'},
 'originalImageOutsidePatchPreserved':True,
 'fullVisualAccepted':False,'methods':{m:{} for m in methods}}
for angle in angles:
 key=f'{angle:g}'
 base=im(R/B['methods']['companion_direct_native_keys'][key]['relativePath'])
 bow=remap('bowFabric',angle)
 gem=remap('jewel',angle)
 nativeMask=sourceMask('bowFabric',angle)
 # Real mapped bow alpha must be present in the original owned silhouette.
 owned=np.clip(nativeMask*(bow[:,:,3].astype(np.float32)/255),0,1)
 confident=np.uint8(owned>.5)
 interior=cv2.erode(confident,np.ones((7,7),np.uint8),iterations=1).astype(np.float32)
 wide=cv2.erode(confident,np.ones((3,3),np.uint8),iterations=1).astype(np.float32)
 gold=remap('goldTrimLeft',angle)
 goldOwner=sourceMask('goldTrimLeft',angle)
 goldConf=cv2.erode(np.uint8(goldOwner>.7),np.ones((3,3),np.uint8),iterations=1)
 for mode in methods:
  if mode=='ink_core':ribbonAlpha=interior*.88
  elif mode=='inner_fabric':ribbonAlpha=wide*.93
  else:ribbonAlpha=interior*.88
  result=composite(base,bow,ribbonAlpha)
  # Jewel is in front of bow at all angles and shares one source-material ID.
  jewelOwned=np.clip(sourceMask('jewel',angle)*(gem[:,:,3].astype(np.float32)/255),0,1)
  jewelArea=cv2.erode(np.uint8(jewelOwned>.5),np.ones((3,3),np.uint8)).astype(np.float32)
  result=composite(result,gem,jewelArea*.96)
  if mode=='ink_core_gold':result=composite(result,gold,goldConf.astype(np.float32)*.65)
  file=D/(mode+'-yaw'+key.replace('.','p')+'.png')
  Image.fromarray(result,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS).save(file)
  residual=np.abs(result.astype(np.int16)-base.astype(np.int16))
  changed=int(np.count_nonzero(np.any(residual>1,axis=2)))
  q['methods'][mode][key]={'path':str(file.relative_to(R)),'sha256':sha(file),
    'actualChanged512Pixels':changed,'sourceMatteRestricted':True}
 print('FRAME',angle,flush=True)
refs={
 'P15-101-original':{k:v['relativePath'] for k,v in P101['methods']['head_alpha_blend'].items()},
 'P15-107-native':{k:v['relativePath'] for k,v in B['methods']['companion_direct_native_keys'].items()},
 **{m:{k:z['path'] for k,z in frames.items()} for m,frames in q['methods'].items()}}
zones={'bow':(500,744,790,975),'collar':(400,665,805,835),
 'goldTrim':(405,775,805,1015),'jewel':(595,770,701,862)}
canvas=Image.new('RGB',(340*len(angles),378*len(refs)),'white');paint=ImageDraw.Draw(canvas)
for row,(mode,frames) in enumerate(refs.items()):
 imgs=[]
 for col,angle in enumerate(angles):
  art=Image.open(R/frames[f'{angle:g}']).convert('RGBA')
  white=Image.new('RGBA',art.size,'white');white.alpha_composite(art)
  imgs.append(np.asarray(white.convert('RGB'),np.float32))
  canvas.paste(white.convert('RGB').crop((365,615,845,1015)).resize((340,354),Image.Resampling.LANCZOS),(col*340,row*378+24))
  paint.text((col*340+4,row*378+4),mode+f' {angle:g}',fill='black')
 for name,(x0,y0,x1,y1) in zones.items():
  diff=[round(float(np.abs(imgs[i][y0:y1,x0:x1]-imgs[i-1][y0:y1,x0:x1]).mean()),4)
        for i in range(1,len(imgs))]
  q.setdefault('metrics',{}).setdefault(mode,{})[name]={
   'maxAdjacentRGBMAE':max(diff),'meanAdjacentRGBMAE':round(statistics.mean(diff),4),
   'interiorMaxRGBMAE':max(diff[1:7]),'adjacentRGBMAE':diff}
canvas.save(D/'localized-garment-contact.jpg',quality=94)
q['contact']=str((D/'localized-garment-contact.jpg').relative_to(R))
(R/'evidence/p15-115-local-qa.json').write_text(json.dumps(q,indent=2,ensure_ascii=False)+'\n')
print('METRICS',json.dumps({m:{k:v['maxAdjacentRGBMAE'] for k,v in z.items()}
 for m,z in q['metrics'].items()},indent=2),flush=True)

#!/usr/bin/env python3
"""P15-116 native P0 local visibility / silhouette repair.

Reconstruct from the proven full-character P15-107 native source frames.
Measured source-owned bow, jewel and left/right trim masks decide where
a single-source registered material should be sampled. Newly uncovered
old-source rim pixels are inpainted only in bounded local strips; everything
outside source-linked regions is pixel exact. Native keyframes are untouched.

This tests three concrete hypotheses against unchanged P15-107 and P15-101:
  1. Only ribbon red ink requires a stronger single-owner edge.
  2. Central jewel source identity should share the ribbon depth owner.
  3. Physical trim visibility must be independently gated per lapel side.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import json,cv2,numpy as np,statistics,shutil
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-116-visibility-repair';D.mkdir(parents=True,exist_ok=True)
Q=json.loads((R/'evidence/p15-115-source-qa.json').read_text())
OWN=json.loads((R/'evidence/p15-108-stroke-qa.json').read_text())
PREV=json.loads((R/'evidence/p15-115-local-qa.json').read_text())
BASE=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
B101=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
sha=lambda f:sha256(Path(f).read_bytes()).hexdigest()
S=512;views=['60','67.5','75'];angles=BASE['angles']
def load(p,mode='RGBA',nearest=False):
 return np.asarray(Image.open(p).convert(mode).resize((S,S),Image.Resampling.NEAREST if nearest else Image.Resampling.LANCZOS))
def segment(angle):
 if angle<=67.5:return '60','67.5',float((angle-60)/7.5)
 return '67.5','75',float((angle-67.5)/7.5)
source={role:load(R/Q['registered'][role]['67.5']['registeredPath'])
        for role in ('bowFabric','jewel','goldTrimLeft','goldTrimRight')}
silhouette={}
for role in source:
 name='goldTrim' if role.startswith('goldTrim') else role
 silhouette[role]={}
 for view in views:
  mask=load(R/OWN['views'][view]['layers'][name]['maskPath'],'L',True)>128
  if role=='goldTrimLeft':mask[:,342:]=False
  if role=='goldTrimRight':mask[:,:342]=False
  silhouette[role][view]=np.uint8(mask)
def soft(a):
 # Native real silhouette per component smoothly interpolated as SDF.
 a=np.uint8(a)
 sd=cv2.distanceTransform(np.uint8(a==0),cv2.DIST_L2,3)-cv2.distanceTransform(a,cv2.DIST_L2,3)
 return sd
sdf={role:{view:soft(m) for view,m in obj.items()} for role,obj in silhouette.items()}
def resampled(role,angle):
 a,b,t=segment(angle)
 W1=np.asarray(Q['registered'][role][a]['inverseAffine512'],np.float32)
 W2=np.asarray(Q['registered'][role][b]['inverseAffine512'],np.float32)
 W=(1-t)*W1+t*W2
 if role=='goldTrimRight' and angle>67.5:
  # Visible right-side source geometry becomes sparse at 75°:
  # the actual 75° right trim stays physically owned by that source.
  src75=load(R/Q['registered'][role]['75']['registeredPath'])
  canonical=cv2.warpAffine(source[role],W,(S,S),
                           flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_CONSTANT)
  blend=t*t*(3-2*t)
  return np.uint8(np.round((1-blend)*canonical+blend*src75))
 return cv2.warpAffine(source[role],W,(S,S),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,
                       borderMode=cv2.BORDER_CONSTANT)
def target(role,angle):
 a,b,t=segment(angle)
 sd=(1-t)*sdf[role][a]+t*sdf[role][b]
 return np.clip((.55-sd)/1.25,0,1).astype(np.float32)
def old_union(role,angle):
 a,b,t=segment(angle)
 return cv2.dilate(np.uint8((silhouette[role][a]>0)|(silhouette[role][b]>0)),np.ones((3,3),np.uint8))
def replace(result,original,art,role,angle,policy):
 """Inpaint exposed old-ink margin; paint one-source material inside target."""
 shape=target(role,angle)
 owned=(art[:,:,3].astype(np.float32)/255)*shape
 union=old_union(role,angle)
 # Most source-owned fabric remains untouched outside a 2px measured rim.
 if policy=='ribbon_core':
  opacity=cv2.GaussianBlur(cv2.erode(np.uint8(owned>.55),np.ones((5,5),np.uint8)),(0,0),.8)*.93
  uncovered=np.zeros((S,S),np.uint8)
 elif policy=='ribbon_edge':
  opacity=cv2.GaussianBlur(np.uint8(owned>.24).astype(np.float32),(0,0),.8)*.94
  uncovered=np.uint8((union>0)&(shape<.22)&(original[:,:,3]>100))
  # disocclusion strictly within 4px of intended target silhouette:
  # source artwork covers the remaining physically visible ribbon.
  perimeter=cv2.dilate(np.uint8(shape>.3),np.ones((9,9),np.uint8))
  uncovered=np.uint8((uncovered>0)&(perimeter>0))
 elif policy=='trim_matte':
  opacity=cv2.GaussianBlur(cv2.erode(np.uint8(owned>.55),np.ones((3,3),np.uint8)),(0,0),.6)*.70
  uncovered=np.zeros((S,S),np.uint8)
 else:raise ValueError(policy)
 # Owner artwork correction only applies between native source keys.
 # Each actual keyframe remains byte-for-byte identical to its input.
 _,_,phase=segment(angle)
 confidence=float(np.sin(np.pi*phase)**2)
 opacity=np.clip(opacity*confidence,0,1)
 out=result.copy()
 changedRemoved=int(np.count_nonzero(uncovered))
 if changedRemoved:
  # Underlying full character is retained; synthesize only pixels that were
  # previously source-owned foreground and became newly uncovered.
  fixed=cv2.inpaint(out[:,:,:3],uncovered*255,3,cv2.INPAINT_TELEA)
  out[:,:,:3]=np.uint8(np.round(out[:,:,:3].astype(np.float32)*(1-confidence)+fixed.astype(np.float32)*confidence))
  # Alpha source is preserved; inpaint here affects visible pigment only.
 fg=art.astype(np.float32)
 bg=out.astype(np.float32)
 alpha=np.clip(opacity,0,1)[:,:,None]
 overlay=np.uint8(np.round(np.clip(bg*(1-alpha)+fg*alpha,0,255)))
 if np.any(overlay[:,:,3]<out[:,:,3]-5):
  # Candidate alpha change is local, but source torso alpha must never drop.
  overlay[:,:,3]=np.maximum(overlay[:,:,3],out[:,:,3])
 return overlay,{'oldRimRemovedPixels':changedRemoved,
                'newOneSourcePixels':int(np.count_nonzero(opacity>.05)),
                'nativeMaterialMaskPixels':int(np.count_nonzero(shape>.5))}
modes=['ribbon_core','ribbon_edge','ribbon_edge_jewel','trim_matte']
report={'schema':'KOMA_P15_116_SOURCE_MATTE_OCCLUSION_REPAIR_V1',
 'characterId':'p0_character_001','sourceViews':[60,67.5,75],
 'renderAngles':angles,'sourceQASHA256':sha(R/'evidence/p15-115-source-qa.json'),
 'physicalSourceOwnership':{'bowFabric':'67.5','jewel':'67.5','goldTrimLeft':'67.5','goldTrimRight75':'75'},
 'base':'P15-107 intact full-character native-key direct garment source',
 'method':'source-part canonical warp, source-material SDF with local inpaint and original torso donor',
 'outsideMaterialRegionPixelExact':True,
 'nativeKeyframeByteExact':True,
 'full360ArtistApproved':False,'models':{name:{} for name in modes}}
for angle in angles:
 key=f'{angle:g}'
 base=load(R/BASE['methods']['companion_direct_native_keys'][key]['relativePath'])
 for mode in modes:
  if angle in (60,67.5,75):
   frame=base.copy();steps={'nativeKeyframeSourceExact':True}
  else:
   frame=base.copy();steps={}
   if mode=='ribbon_core':
    frame,rec=replace(frame,base,resampled('bowFabric',angle),'bowFabric',angle,'ribbon_core')
    steps['bowFabric']=rec
   elif mode in ('ribbon_edge','ribbon_edge_jewel'):
    frame,rec=replace(frame,base,resampled('bowFabric',angle),'bowFabric',angle,'ribbon_edge')
    steps['bowFabric']=rec
    if mode=='ribbon_edge_jewel':
     frame,rec=replace(frame,base,resampled('jewel',angle),'jewel',angle,'ribbon_core')
     steps['jewel']=rec
   elif mode=='trim_matte':
    for role in ('goldTrimLeft','goldTrimRight'):
     frame,rec=replace(frame,base,resampled(role,angle),role,angle,'trim_matte')
     steps[role]=rec
  changed=np.any(np.abs(frame.astype(np.int16)-base.astype(np.int16))>1,axis=2)
  # No geometry warps outside physical component ROI.
  ys,xs=np.where(changed)
  if len(xs):
   bbox=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())]
   assert min(xs)>180 and min(ys)>325,(mode,angle,bbox)
  else:bbox=None
  file=D/(mode+'-yaw'+key.replace('.','p')+'.png')
  if angle in (60,67.5,75):
   shutil.copyfile(R/BASE['methods']['companion_direct_native_keys'][key]['relativePath'],file)
  else:
   native1024=np.asarray(Image.open(R/BASE['methods']['companion_direct_native_keys'][key]['relativePath']).convert('RGBA')).copy()
   candidate1024=np.asarray(Image.fromarray(frame,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS))
   modified=cv2.resize(np.uint8(changed),(1024,1024),interpolation=cv2.INTER_NEAREST)>0
   native1024[modified]=candidate1024[modified]
   Image.fromarray(native1024,'RGBA').save(file)
  report['models'][mode][key]={'path':str(file.relative_to(R)),
       'sha256':sha(file),'changed512Pixels':int(changed.sum()),
       'changedBoundingBox512':bbox,'ownerDebug':steps}
 print('FRAME',angle,flush=True)
refs={'P15-101-original':{k:x['relativePath'] for k,x in B101['methods']['head_alpha_blend'].items()},
      'P15-107-native':{k:x['relativePath'] for k,x in BASE['methods']['companion_direct_native_keys'].items()},
      'P15-115-inkCore':{k:x['path'] for k,x in PREV['methods']['ink_core'].items()},
      **{m:{k:z['path'] for k,z in fs.items()} for m,fs in report['models'].items()}}
regions={'bow':(500,744,790,975),'jewel':(595,770,701,862),
 'collar':(400,665,805,835),'goldTrim':(405,775,805,1015),'rightLap':(683,785,865,1015)}
contact=Image.new('RGB',(325*len(angles),374*len(refs)),'white');pen=ImageDraw.Draw(contact)
for row,(name,frames) in enumerate(refs.items()):
 whiteImages=[]
 for col,angle in enumerate(angles):
  img=Image.open(R/frames[f'{angle:g}']).convert('RGBA')
  white=Image.new('RGBA',img.size,'white');white.alpha_composite(img)
  whiteImages.append(np.asarray(white.convert('RGB'),np.float32))
  contact.paste(white.convert('RGB').crop((365,615,845,1015)).resize((325,350),Image.Resampling.LANCZOS),(col*325,row*374+23))
  pen.text((col*325+4,row*374+4),name+f' {angle:g}',fill='black')
 for area,(x0,y0,x1,y1) in regions.items():
  d=[round(float(np.abs(whiteImages[i][y0:y1,x0:x1]-whiteImages[i-1][y0:y1,x0:x1]).mean()),4)
     for i in range(1,len(whiteImages))]
  report.setdefault('metrics',{}).setdefault(name,{})[area]={
    'maxAdjacentRGBMAE':max(d),'meanAdjacentRGBMAE':round(statistics.mean(d),4),
    'adjacentRGBMAE':d}
contact.save(D/'source-matte-occlusion-contact.jpg',quality=93)
report['contact']=str((D/'source-matte-occlusion-contact.jpg').relative_to(R))
(R/'evidence/p15-116-render-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('RESULT',json.dumps({m:{k:z['maxAdjacentRGBMAE'] for k,z in r.items() if k in ('bow','goldTrim','rightLap')}
 for m,r in report['metrics'].items()},indent=2),flush=True)

#!/usr/bin/env python3
"""P15-109 measured source-ink collar fold path; local garment occlusion proof.

Only P15-109 roles passing three-source path/length/drift acceptance enter this
experiment. Reproject the actual observed collar curve to an interpolated
centerline, underpaint narrow source line marks, then restore one provenance-
weighted stroke above the collar and below the gemstone/head. Keep all full
character keyframes exact, outside the local collar support unchanged.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import cv2,json,numpy as np,statistics
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-109-collar-render';D.mkdir(parents=True,exist_ok=True)
PA=json.loads((R/'evidence/p15-109-path-qa.json').read_text())
QA107=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
QA101=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
QA108=json.loads((R/'evidence/p15-108-stroke-qa.json').read_text())
sha=lambda p:sha256(Path(p).read_bytes()).hexdigest()
role='collar.left_crease'
assert PA['crossViewRoles'][role]['usableForMorph']
assert sum(int(z['usableForMorph']) for z in PA['crossViewRoles'].values())==1
views=['60','67.5','75'];angles=QA107['angles'];S=512
Y,X=np.indices((S,S),np.float32)
def im(path,mode='RGBA'):
 return np.asarray(Image.open(path).convert(mode).resize((S,S),Image.Resampling.LANCZOS))
def prem(a):
 f=a.astype(np.float32)/255
 return np.concatenate([f[:,:,:3]*f[:,:,3:4],f[:,:,3:4]],axis=-1)
def unprem(p):
 a=np.clip(p[:,:,3:4],0,1)
 rgb=np.clip(p[:,:,:3]/np.maximum(a,1e-6),0,1)
 return np.uint8(np.round(np.concatenate([rgb,a],axis=2)*255))
paths={v:np.array(PA['views'][v]['roles'][role]['sourceXY'],np.float32)/2 for v in views}
source={}
for v in views:
 src=im(R/PA['views'][v]['source'])
 line=np.zeros((S,S),np.uint8)
 pts=np.rint(paths[v]).astype(np.int32)
 cv2.polylines(line,[pts],False,255,3,lineType=cv2.LINE_AA)
 # Measured source fold line is removed only from the underpaint, retaining native RGBA files.
 sourceMask=np.array(Image.open(R/QA108['views'][v]['layers']['collarWhite']['maskPath']).convert('L').resize((S,S),Image.Resampling.NEAREST))
 line=np.uint8((line>0)&(sourceMask>100))*255
 line=cv2.dilate(line,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3)))
 clean=src.copy()
 clean[:,:,:3]=cv2.inpaint(src[:,:,:3],line,3,cv2.INPAINT_TELEA)
 t=D/(f'yaw{v.replace(".","p")}-collar-undercoat.png')
 Image.fromarray(clean,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS).save(t)
 samples=[]
 for x,y in paths[v]:
  xx=int(round(x));yy=int(round(y))
  if 0<=xx<S and 0<=yy<S and src[yy,xx,3]>90:
   samples.append(src[yy,xx,:3])
 pigment=np.percentile(np.asarray(samples,np.float32),20,axis=0) if len(samples)>=4 else np.array([92,84,101],np.float32)
 source[v]={'original':src,'undercoat':prem(clean),'path':paths[v],'pigment':pigment,
            'mask':sourceMask/255}
def segment(angle):
 if angle<67.5:return '60','67.5',float((angle-60)/7.5)
 return '67.5','75',float((angle-67.5)/7.5)
def stroke_mask(path,width):
 out=np.zeros((S,S),np.uint8)
 cv2.polylines(out,[np.rint(path).astype(np.int32)],False,255,width,lineType=cv2.LINE_AA)
 return out
def warp_underpaint(a,target,radius):
 pos=source[a]['path']
 center=np.zeros((S,S,2),np.float32)
 weight=np.zeros((S,S),np.float32)
 for p,q in zip(target,pos):
  xx=int(round(p[0]));yy=int(round(p[1]))
  dx,dy=(q-p)
  if 0<=xx<S and 0<=yy<S:
   cv2.circle(center,(xx,yy),2,(float(dx),float(dy)),thickness=-1)
   cv2.circle(weight,(xx,yy),2,1,thickness=-1)
 center=cv2.GaussianBlur(center,(0,0),radius)
 weight=cv2.GaussianBlur(weight,(0,0),radius)
 disp=center/np.maximum(weight[:,:,None],1e-6)
 local=stroke_mask(target,3)
 dist=cv2.distanceTransform(np.uint8(local==0),cv2.DIST_L2,3)
 influence=np.exp(-(dist*dist)/(2*(radius*1.25)**2))
 dx=np.clip(disp[:,:,0]*influence,-24,24)
 dy=np.clip(disp[:,:,1]*influence,-24,24)
 mapx=np.clip(X+dx,0,S-1).astype(np.float32)
 mapy=np.clip(Y+dy,0,S-1).astype(np.float32)
 return cv2.remap(source[a]['undercoat'],mapx,mapy,cv2.INTER_LINEAR,
                  borderMode=cv2.BORDER_CONSTANT)
def render(angle,mode):
 a,b,t=segment(angle)
 pA=paths[a];pB=paths[b]
 if PA['crossViewRoles'][role]['pairOrientations'][0 if a=='60' else 1]=='reverse':
  pB=pB[::-1]
 target=(1-t)*pA+t*pB
 # The clean garment is composited only within a tight, physically measured
 # ink neighborhood. Everything else stays the existing P15-107 full-frame source.
 width=5 if mode=='collar_path_narrow' else 9
 radius=9 if mode=='collar_path_narrow' else 17
 A=warp_underpaint(a,target,radius)
 B=warp_underpaint(b,target,radius)
 new=(1-t)*A+t*B
 line=stroke_mask(target,2)
 pigment=(1-t)*source[a]['pigment']+t*source[b]['pigment']
 alpha=np.float32(line)/255*.86
 color=new[:,:,:3]/np.maximum(new[:,:,3:4],1e-6)
 front=np.concatenate([pigment[None,None,:]/255*alpha[:,:,None],alpha[:,:,None]],axis=-1)
 # Source-stroke opacity is bounded by actual collar material surface support.
 material=source[a]['mask']*(1-t)+source[b]['mask']*t
 front*=np.clip(material[:,:,None]*1.3,0,1)
 candidate=np.concatenate([
   front[:,:,:3]+new[:,:,:3]*(1-front[:,:,3:4]),
   front[:,:,3:4]+new[:,:,3:4]*(1-front[:,:,3:4])
 ],axis=-1)
 baseline=im(R/QA107['methods']['companion_direct_native_keys'][f'{angle:g}']['relativePath'])
 base=prem(baseline)
 area=stroke_mask(target,width)
 feather=cv2.GaussianBlur(area,(0,0),2.0 if width==5 else 3.5).astype(np.float32)/255
 # Multiply region by material to avoid crossing head/hair and bow/gem surface.
 replacement=np.clip(feather*material,0,1)
 # Bound local modification to collar source pixels only.
 result=base*(1-replacement[:,:,None])+candidate*replacement[:,:,None]
 return unprem(np.clip(result,0,1)),{
    'sourceSegment':[a,b],'interpolation':round(t,4),
    'changedMaskPixels':int((replacement>.01).sum()),
    'mappedPathLengthPx':round(float(np.linalg.norm(np.diff(target,axis=0),axis=1).sum()*2),3)}
methods=['collar_path_narrow','collar_path_wide']
qa={'schema':'KOMA_P15_109_VERIFIED_COLLAR_PATH_RENDER_V1','sourceAngles':[60,67.5,75],
 'model':'p0_character_001','sourcePathsSHA256':sha(R/'evidence/p15-109-path-qa.json'),
 'matchedStrokeID':role,'sourcePointCount':24,'allAutomaticSourceRoles':len(PA['candidateStrokeRoles']),
 'sourceQualifiedRoles':sum(z['usableForMorph'] for z in PA['crossViewRoles'].values()),
 'selectedVisualBenchmark':'P15-101 head_alpha_blend',
 'methods':{m:{} for m in methods},'formalArtistApproved':False,
 'continuousAnimationAccepted':False}
for angle in angles:
 for method in methods:
  if angle in (60,67.5,75):
   rec=QA107['methods']['companion_direct_native_keys'][f'{angle:g}']
   out=Image.open(R/rec['relativePath']).convert('RGBA')
   meta={'actualSourceKeyframe':True,'sourceSourceSHA256':rec['sha256'],'changedMaskPixels':0}
  else:
   x,meta=render(angle,method)
   out=Image.fromarray(x,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
  dest=D/(method+'-yaw'+f'{angle:g}'.replace('.','p')+'.png')
  out.save(dest)
  qa['methods'][method][f'{angle:g}']={'path':str(dest.relative_to(R)),'sha256':sha(dest),'diagnostics':meta}
 print('FRAME',angle,flush=True)
refs={
 'P15-101-original':{k:v['relativePath'] for k,v in QA101['methods']['head_alpha_blend'].items()},
 'P15-107-native':{k:v['relativePath'] for k,v in QA107['methods']['companion_direct_native_keys'].items()},
 **{m:{k:v['path'] for k,v in z.items()} for m,z in qa['methods'].items()}}
regions={'fold':(551,685,700,823),'collar':(400,665,805,835),
 'bow':(500,744,790,975),'jewel':(595,770,701,862),'garment':(335,655,865,1015)}
sheet=Image.new('RGB',(345*len(angles),382*len(refs)),'white');draw=ImageDraw.Draw(sheet)
for row,(m,items) in enumerate(refs.items()):
 arr=[]
 for col,angle in enumerate(angles):
  art=Image.open(R/items[f'{angle:g}']).convert('RGBA')
  white=Image.new('RGBA',art.size,'white');white.alpha_composite(art)
  arr.append(np.asarray(white.convert('RGB'),np.float32))
  sheet.paste(white.convert('RGB').crop((370,615,855,1015)).resize((345,357),Image.Resampling.LANCZOS),(col*345,row*382+25))
  draw.text((col*345+5,row*382+5),m+f' {angle:g}',fill='black')
 for roi,(x0,y0,x1,y1) in regions.items():
  diff=[round(float(np.abs(arr[j][y0:y1,x0:x1]-arr[j-1][y0:y1,x0:x1]).mean()),4)
       for j in range(1,len(arr))]
  qa.setdefault('metrics',{}).setdefault(m,{})[roi]={
   'adjacentRGBMAE':diff,'maxAdjacentRGBMAE':max(diff),
   'interiorMaxRGBMAE':max(diff[1:7]),
   'meanAdjacentRGBMAE':round(statistics.mean(diff),4)}
sheet.save(D/'collar-path-contact.jpg',quality=93)
qa['contact']=str((D/'collar-path-contact.jpg').relative_to(R))
(R/'evidence/p15-109-render-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
print('METRICS',json.dumps({m:{r:[s['maxAdjacentRGBMAE'],s['interiorMaxRGBMAE']]
 for r,s in z.items() if r in ('fold','collar','bow')} for m,z in qa['metrics'].items()},indent=2),flush=True)

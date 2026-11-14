#!/usr/bin/env python3
"""Extract, geometrically match and verify native source stroke polylines.

P0 three independent 60°/67.5°/75° drawings only.
A path is source-observed ink, not guessed geometry. Identity accepted for
experimental 2D deforming only if all 3 views have a continuous support
and cross-view center/length/shape checks pass.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import cv2, numpy as np, json, math
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-109-stroke-paths';D.mkdir(exist_ok=True,parents=True)
src=json.loads((R/'evidence/p15-108-stroke-qa.json').read_text())
sha=lambda p:sha256(Path(p).read_bytes()).hexdigest()
angles=['60','67.5','75'];roleIDs=src['roleIDs']
def resample(pts,n=24):
 pts=np.asarray(pts,np.float64)
 diff=np.linalg.norm(pts[1:]-pts[:-1],axis=1)
 cum=np.concatenate([[0],np.cumsum(diff)])
 if cum[-1]<1:return None
 target=np.linspace(0,cum[-1],n)
 x=np.interp(target,cum,pts[:,0]);y=np.interp(target,cum,pts[:,1])
 return np.stack([x,y],axis=1)
def longest_path(mask):
 # Only pixels whose actual ink is visible in the source; no synthetic strokes.
 n,lab,stat,cent=cv2.connectedComponentsWithStats(np.uint8(mask),8)
 candidates=[]
 for idx in range(1,n):
  x,y,w,h,area=stat[idx]
  if area<16 or max(w,h)<11:continue
  region=lab[y:y+h,x:x+w]==idx
  if w>=h:
   ordered=[]
   for col in range(w):
    ys=np.where(region[:,col])[0]
    if len(ys):ordered.append([x+col,y+float(np.median(ys))])
  else:
   ordered=[]
   for row in range(h):
    xs=np.where(region[row])[0]
    if len(xs):ordered.append([x+float(np.median(xs)),y+row])
  if len(ordered)<10:continue
  pts=resample(ordered,24)
  if pts is None:continue
  length=float(np.sum(np.linalg.norm(pts[1:]-pts[:-1],axis=1)))
  score=length*(1+np.log1p(area)/12)
  candidates.append((score,area,[int(x),int(y),int(x+w),int(y+h)],pts,length))
 if not candidates:return None,0,0,[]
 candidates.sort(key=lambda it:it[0],reverse=True)
 selected=candidates[0]
 return selected[3],selected[1],selected[4],selected[2]
info={'schema':'KOMA_P15_109_SOURCE_STROKE_POLYLINE_MATCH_V1','characterId':'p0_character_001',
 'sourceAngles':[60,67.5,75],'candidateStrokeRoles':roleIDs,
 'extraction':'per-source connected visible ink centers, 24 equally-spaced measured points',
 'matching':'three-view support, brooch-relative proximity, length ratio, arc-displacement',
 'views':{},'crossViewRoles':{},'artistVerified':False}
allpaths={}
colors=['#F05542','#20B0E9','#A33ED8','#2D9C53','#E6A923','#D14D87']
for view in angles:
 rec=src['views'][view]
 source=Image.open(R/rec['source']).convert('RGBA')
 base=Image.new('RGBA',source.size,'white');base.alpha_composite(source)
 img=base.convert('RGB')
 draw=ImageDraw.Draw(img)
 anchor=np.asarray(json.loads((R/'evidence/p15-108-source-qa.json').read_text())['views'][view]['goldCenter'],np.float64)
 allpaths[view]={};info['views'][view]={'source':rec['source'],'sourceSHA256':sha(R/rec['source']),
 'anchorGold':anchor.round(3).tolist(),'roles':{}}
 for j,role in enumerate(roleIDs):
  observed=np.asarray(Image.open(R/rec['strokeRegions'][role]['maskPath']).convert('L'))>127
  poly,pixels,length,bounds=longest_path(observed)
  item={'observedPixels':int(observed.sum()),'longestComponentPixels':int(pixels),
   'polylineArcLength':round(float(length),4),'bbox':bounds,
   'supported':bool(poly is not None)}
  if poly is not None:
   item['sourceXY']=poly.round(3).tolist()
   item['relativeGoldXY']=(poly-anchor[None,:]).round(3).tolist()
   points=[tuple(v) for v in poly]
   draw.line(points,fill=colors[j],width=4,joint='curve')
   draw.ellipse((*((poly[0]-4).tolist()),*((poly[0]+4).tolist())),fill=colors[j])
   allpaths[view][role]=poly
  info['views'][view]['roles'][role]=item
 # Draw same-sized real source crop for quantitative visual cross-reference.
 img.crop((410,640,830,1016)).resize((630,564),Image.Resampling.LANCZOS).save(
  D/('yaw'+view.replace('.','p')+'-stroke-paths.png'))
 print('VIEW',view,'supported',sum(x['supported'] for x in info['views'][view]['roles'].values()),flush=True)
for role in roleIDs:
 paths=[allpaths[a].get(role) for a in angles]
 decision={'commonSourceSupport':all(p is not None for p in paths),'reasons':[],
           'sourcePointCount':24,'usableForMorph':False}
 if not decision['commonSourceSupport']:
  decision['reasons'].append('missing measured ink polyline at one or more source views')
 else:
  lengths=[float(np.sum(np.linalg.norm(p[1:]-p[:-1],axis=1))) for p in paths]
  decision['pathLengthsPx']=[round(x,3) for x in lengths]
  ratio=max(lengths)/max(min(lengths),.001)
  decision['lengthRatio']=round(ratio,3)
  anchored=[p-np.asarray(info['views'][view]['anchorGold']) for p,view in zip(paths,angles)]
  deviations=[];orientations=[];strokes=[]
  for first,second in zip(anchored,anchored[1:]):
   front=float(np.linalg.norm(first-second,axis=1).mean())
   reversed_=float(np.linalg.norm(first-second[::-1],axis=1).mean())
   orientations.append('reverse' if reversed_<front else 'forward')
   deviations.append(round(min(front,reversed_),3))
  decision['meanPathDisplacementPx']=deviations
  decision['pairOrientations']=orientations
  if ratio>2.5:decision['reasons'].append('source path length ratio exceeds 2.5')
  if max(deviations)>38:decision['reasons'].append('gold-normalized path drift exceeds 38 pixels')
  if min(lengths)<12:decision['reasons'].append('source line length too short')
  decision['usableForMorph']=not decision['reasons']
 info['crossViewRoles'][role]=decision
 print('ROLE',role,'accepted',decision['usableForMorph'],'ratio',decision.get('lengthRatio'),
       'drift',decision.get('meanPathDisplacementPx'),'reasons',decision['reasons'],flush=True)
# Keep every automatically matched point and its verification metadata. No
# implied artist approval. Actual renderer can select only accepted roles.
out=R/'evidence/p15-109-path-qa.json'
out.write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
print('ACCEPTED',sum(x['usableForMorph'] for x in info['crossViewRoles'].values()),'/',len(roleIDs))

#!/usr/bin/env python3
"""Bow garment-local optical flow on top of source-owned common ArtMesh.
Uses DIS local flow in the geometrically registered bow ROI only; the head
and shoulder remain the tested P15-101 baseline.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import json,numpy as np,cv2,statistics
import p15_103_render as grid
import p15_101_head_render as head
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-103-render';S=grid.S;X,Y=grid.X,grid.Y
sha=lambda f:sha256(Path(f).read_bytes()).hexdigest()
# Source registrations evaluated at the common halfway pose.
base={v:grid.warp(grid.parts[v]['bow'],grid.mappings('bow',.5,v)) for v in ('60','75')}
aa=base['60'][:,:,3];bb=base['75'][:,:,3]
support=(aa>.02)|(bb>.02)
ys,xs=np.where(support)
assert len(xs)>5000,'Local flow support too small'
x0=max(0,int(xs.min())-12);x1=min(S,int(xs.max())+13)
y0=max(0,int(ys.min())-12);y1=min(S,int(ys.max())+13)
def image_of(prem):
 a=prem[:,:,3:4]
 rgb=np.clip(prem[:,:,:3]/np.maximum(a,1e-5),0,1)
 return np.uint8(np.round((rgb*a+(1-a)*np.ones_like(rgb))*255))
a=image_of(base['60'][y0:y1,x0:x1]);b=image_of(base['75'][y0:y1,x0:x1])
gray=lambda a:cv2.cvtColor(a,cv2.COLOR_RGB2GRAY)
dis=cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
dis.setFinestScale(0);dis.setVariationalRefinementIterations(5)
fa=dis.calc(gray(a),gray(b),None);fb=dis.calc(gray(b),gray(a),None)
# Reject texture-flow outliers that cross the component boundary.
fa=cv2.GaussianBlur(np.clip(fa,-10,10),(0,0),1.6)
fb=cv2.GaussianBlur(np.clip(fb,-10,10),(0,0),1.6)
def flow_warp(prem,flow,weight):
 out=prem.copy()
 local=prem[y0:y1,x0:x1]
 x=X[y0:y1,x0:x1]-x0; y=Y[y0:y1,x0:x1]-y0
 mapped=cv2.remap(local,(x-weight*flow[:,:,0]).astype(np.float32),
                         (y-weight*flow[:,:,1]).astype(np.float32),
                         cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
 out[y0:y1,x0:x1]=mapped
 return out
def render(t,variant):
 # Reuse source-backed underpaint and existing head warp from P15-101.
 bg=head.skin_blend(head.prem(grid.clean['60']['bow']),head.prem(grid.clean['75']['bow']),t)
 faceMaps={v:head.mesh_map(v,t) for v in ('60','75')}
 garment=head.skin_blend(head.warp(head.parts['60']['head'],faceMaps['60']),
                         head.warp(head.parts['75']['head'],faceMaps['75']),t)
 srcBow={v:grid.warp(grid.parts[v]['bow'],grid.mappings('bow',t,v)) for v in ('60','75')}
 warpedA=flow_warp(srcBow['60'],fa,t)
 warpedB=flow_warp(srcBow['75'],fb,1-t)
 overlay=grid.union(warpedA,warpedB,t) if variant=='bow_flow_union' else head.skin_blend(warpedA,warpedB,t)
 bg=head.over(bg,overlay)
 # Gold ornament uses the same geometric mapping but no model hallucination.
 goldA=grid.warp(grid.parts['60']['jewel'],grid.mappings('jewel',t,'60'))
 goldB=grid.warp(grid.parts['75']['jewel'],grid.mappings('jewel',t,'75'))
 bg=head.over(bg,head.skin_blend(goldA,goldB,t))
 return head.rgba(head.over(head.over(bg,garment),head.get_ahoge(t)))
methods=['bow_flow_blend','bow_flow_union'];angles=head.angles
qa={'schema':'KOMA_P15_103_LOCAL_COMPONENT_FLOW_QA_V1','localFlowROI':[x0,y0,x1,y1],
    'flowMagnitudeMeanPx':float(np.linalg.norm(fa,axis=2).mean()),
    'flowMagnitudeMaxPx':float(np.linalg.norm(fa,axis=2).max()),
    'model':'DIS local optical flow over actual source bow texture, after per-view UV mesh registration',
    'methods':{m:{} for m in methods},'visualAccepted':False}
for a in angles:
 t=(a-60)/15
 for method in methods:
  if t<=0 or t>=1:
   v='60' if t<=0 else '75'
   image=Image.open(R/grid.Q['views'][v]['source']).convert('RGBA')
  else:
   img=render(t,method);image=Image.fromarray(img,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
  dest=D/(method+'-yaw'+f'{a:g}'.replace('.','p')+'.png')
  image.save(dest);qa['methods'][method][f'{a:g}']={'relativePath':str(dest.relative_to(R)),'sha256':sha(dest)}
 print('flow angle',a,flush=True)
# Compare exact same regions used for P15-103 garment tests.
original=json.loads((R/'evidence/p15-103-render-qa.json').read_text())
regions={'bow':(500,744,790,975),'jewel':(595,770,701,862),
         'collar':(400,668,798,835),'shoulder':(230,693,521,915)}
baseFrames=head.G and json.loads((R/'evidence/p15-101-render-qa.json').read_text())['methods']['head_alpha_blend']
allNames=['P15-101-head_alpha_blend']+methods
contact=Image.new('RGB',(345*len(angles),385*len(allNames)),'white');draw=ImageDraw.Draw(contact)
for row,method in enumerate(allNames):
 arrays=[]
 for col,a in enumerate(angles):
  key=f'{a:g}'
  f=R/(baseFrames[key]['relativePath'] if row==0 else qa['methods'][method][key]['relativePath'])
  art=Image.open(f).convert('RGBA');bg=Image.new('RGBA',art.size,'white');bg.alpha_composite(art)
  arrays.append(np.asarray(bg.convert('RGB'),dtype=np.float32))
  contact.paste(bg.convert('RGB').crop((360,600,830,1015)).resize((345,355),Image.Resampling.LANCZOS),(345*col,385*row+25))
  draw.text((345*col+7,385*row+6),method+f' {a:g}',fill='black')
 for region,(xx0,yy0,xx1,yy1) in regions.items():
  diffs=[round(float(np.abs(arrays[i][yy0:yy1,xx0:xx1]-arrays[i-1][yy0:yy1,xx0:xx1]).mean()),4) for i in range(1,len(arrays))]
  qa.setdefault('metrics',{}).setdefault(method,{})[region]={
   'maxAdjacentMAE':max(diffs),'midpointAdjacentMAE':max(diffs[3:5]),'adjacentMAE':diffs}
contact.save(D/'bow-flow-contact.jpg',quality=93)
qa['contact']='private-assets/exports/p15-103-render/bow-flow-contact.jpg'
(R/'evidence/p15-103-flow-qa.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')
print('FLOW METRICS',json.dumps({m:{r:round(v['maxAdjacentMAE'],3) for r,v in q.items()} for m,q in qa['metrics'].items()},indent=2),flush=True)

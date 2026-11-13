#!/usr/bin/env python3
"""P0 source-observed 3-view bow curve registration and VDD ablation.

Only P15-110 machine-qualified paths control a soft spatial warp on actual
native 60/67.5/75 costume art. No speculative hidden surface is painted.
P15-101 native head ArtMesh, original P0 identity, and all keyframes remain
unchanged. Actual edge alignment and temporal differences are independently
measured; artistic acceptance is a separate gate.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import json,cv2,numpy as np,statistics
import p15_101_head_render as head
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-110-path-vdd';D.mkdir(parents=True,exist_ok=True)
V=json.loads((R/'evidence/p15-110-vision-qa.json').read_text())
A=json.loads((R/'private-assets/p15-110-vision-strokes/vision-stroke-annotations.json').read_text())
Q=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
Q101=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
qa108=json.loads((R/'evidence/p15-108-stroke-qa.json').read_text())
assert V['experimentAcceptedRoles'], 'No grounded view correspondence available'
sha=lambda f:sha256(Path(f).read_bytes()).hexdigest()
S=512;Y,X=np.indices((S,S),np.float32)
source={v:np.asarray(Image.open(R/q['path']).convert('RGBA').resize((S,S),Image.Resampling.LANCZOS)) for v,q in V['sourceImages'].items()}
angles=Q['angles'];views=['60','67.5','75']
def prem(a):
 f=a.astype(np.float32)/255
 return np.concatenate([f[:,:,:3]*f[:,:,3:4],f[:,:,3:4]],axis=-1)
def unprem(p):
 a=np.clip(p[:,:,3:4],0,1)
 col=np.clip(p[:,:,:3]/np.maximum(a,1e-6),0,1)
 return np.uint8(np.round(np.concatenate([col,a],axis=-1)*255))
def over(dst,src):
 alpha=src[:,:,3:4]
 return np.concatenate([src[:,:,:3]+dst[:,:,:3]*(1-alpha),
                         alpha+dst[:,:,3:4]*(1-alpha)],axis=-1)
def interp(pts,n=18):
 pts=np.asarray(pts,np.float32).reshape(-1,2)/2
 arc=np.concatenate([[0],np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))])
 if arc[-1]<.01:raise ValueError('degenerate landmark')
 return np.stack([np.interp(np.linspace(0,arc[-1],n),arc,pts[:,dim]) for dim in range(2)],axis=-1)
def matched_pair(role,a,b):
 x=interp(A['roles'][role]['views'][a]['points']);y=interp(A['roles'][role]['views'][b]['points'])
 # Model supplied consistent start orientations; verify with center-normalized endpoint continuity.
 anchorA=np.asarray({'60':[634.46,810.55],'67.5':[639.29,808.82],'75':[644.12,807.09]}[a])/2
 anchorB=np.asarray({'60':[634.46,810.55],'67.5':[639.29,808.82],'75':[644.12,807.09]}[b])/2
 d1=np.linalg.norm((x-anchorA)-(y-anchorB),axis=1).mean()
 d2=np.linalg.norm((x-anchorA)-(y[::-1]-anchorB),axis=1).mean()
 return x,y[::-1] if d2<d1 else y
def warp_field(srcPaths,dstPaths,sigma=14):
 # Each measured physical ink point proposes a local target-to-source offset.
 w=np.zeros((S,S),np.float32)
 sx=np.zeros_like(w);sy=np.zeros_like(w)
 for src,dst in zip(srcPaths,dstPaths):
  for p,q in zip(src,dst):
   px,py=np.rint(q).astype(int)
   if not (4<=px<S-4 and 4<=py<S-4):continue
   sl=(slice(py-2,py+3),slice(px-2,px+3))
   w[sl]+=1
   sx[sl]+=float(p[0]-q[0])
   sy[sl]+=float(p[1]-q[1])
 bW=cv2.GaussianBlur(w,(0,0),sigma)
 dx=cv2.GaussianBlur(sx,(0,0),sigma)/np.maximum(bW,.00001)
 dy=cv2.GaussianBlur(sy,(0,0),sigma)/np.maximum(bW,.00001)
 strength=np.clip(bW/.08,0,1)
 dx=np.clip(dx*strength,-26,26)
 dy=np.clip(dy*strength,-26,26)
 mx=(X+dx).astype(np.float32);my=(Y+dy).astype(np.float32)
 maxWarp=float(np.max(np.sqrt(dx*dx+dy*dy)))
 return mx,my,maxWarp
def head_surface(t):
 maps={v:head.mesh_map(v,t) for v in ('60','75')}
 return head.skin_blend(head.warp(head.parts['60']['head'],maps['60']),
                        head.warp(head.parts['75']['head'],maps['75']),t)
def sample_segment(a,b,t):
 sA=[];sB=[];targets=[]
 for role in V['experimentAcceptedRoles']:
  p,q=matched_pair(role,a,b)
  sA.append(p);sB.append(q);targets.append((1-t)*p+t*q)
 mapA=warp_field(sA,targets)
 mapB=warp_field(sB,targets)
 rgbaA=cv2.remap(prem(source[a]),mapA[0],mapA[1],cv2.INTER_LINEAR,
                 borderMode=cv2.BORDER_CONSTANT)
 rgbaB=cv2.remap(prem(source[b]),mapB[0],mapB[1],cv2.INTER_LINEAR,
                 borderMode=cv2.BORDER_CONSTANT)
 return rgbaA,rgbaB,{'maxWarpSourceA':round(mapA[2],4),'maxWarpSourceB':round(mapB[2],4)}
def render(angle,mode):
 if angle<67.5:a,b='60','67.5';t=float((angle-60)/7.5)
 else:a,b='67.5','75';t=float((angle-67.5)/7.5)
 x,y,warpQA=sample_segment(a,b,t)
 if mode=='matched_path_direct':weight=t
 elif mode=='matched_path_owner':
  z=float(np.clip((t-.17)/.66,0,1))
  weight=z*z*(3-2*z)
 else:raise ValueError(mode)
 cloth=(1-weight)*x+weight*y
 yawT=(angle-60)/15
 merged=over(np.clip(cloth,0,1),head_surface(yawT))
 merged=over(merged,head.get_ahoge(yawT))
 return unprem(np.clip(merged,0,1)),{'segment':[a,b],'weight':round(weight,5),**warpQA}
methods=['matched_path_direct','matched_path_owner']
qa={'schema':'KOMA_P15_110_VISION_SOURCE_BOW_VDD_V1','characterId':'p0_character_001',
 'sourceAngles':[60,67.5,75],'renderAngles':angles,
 'acceptedSourceStrokeRoles':V['experimentAcceptedRoles'],
 'visionEvidenceSHA256':sha(R/'evidence/p15-110-vision-qa.json'),
 'assetSHA256':{v:z['sha256'] for v,z in V['sourceImages'].items()},
 'method':'source-observed model-grounded stroke landmarks with local Gaussian displacement warp',
 'artistSourceCorrespondenceApproved':False,'naturalYawAccepted':False,
 'layerOcclusionSource':'P15-108 native part alpha and top jewel/head ordering',
 'methods':{m:{} for m in methods},'diagnostics':{}}
for angle in angles:
 for method in methods:
  if angle in (60,67.5,75):
   baseline=Q['methods']['companion_direct_native_keys'][f'{angle:g}']
   im=Image.open(R/baseline['relativePath']).convert('RGBA')
   meta={'sourceOwnedKeyframe':True}
  else:
   rgba,meta=render(angle,method)
   im=Image.fromarray(rgba,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
  path=D/(method+'-yaw'+f'{angle:g}'.replace('.','p')+'.png')
  im.save(path)
  qa['methods'][method][f'{angle:g}']={'path':str(path.relative_to(R)),
    'sha256':sha(path),'diagnostics':meta}
 print('FRAME',angle,flush=True)
# Disoccluded layer support: provenance, not invented backside pixels.
qa['occlusion']={
 'depthOrder':qa108['depthOrder'],
 'sourceViewsWithForegroundJewel':views,
 'actualHiddenUnderBroochPixelsNotObserved':True,
 'syntheticHiddenArtworkApproved':False,
 'sourceSeparation':'P15-108 exact native RGBA per-pixel partition'
}
refs={
 'P15-101-original':{k:v['relativePath'] for k,v in Q101['methods']['head_alpha_blend'].items()},
 'P15-107-three-native':{k:v['relativePath'] for k,v in Q['methods']['companion_direct_native_keys'].items()},
 **{m:{k:r['path'] for k,r in rows.items()} for m,rows in qa['methods'].items()}}
regions={'bow':(500,744,790,975),'jewel':(595,770,701,862),
 'collar':(400,665,805,835),'garment':(335,655,865,1015),'head':(440,285,840,640)}
contact=Image.new('RGB',(347*len(angles),391*len(refs)),'white')
draw=ImageDraw.Draw(contact)
for row,(method,frames) in enumerate(refs.items()):
 images=[]
 for col,angle in enumerate(angles):
  src=Image.open(R/frames[f'{angle:g}']).convert('RGBA')
  bg=Image.new('RGBA',src.size,'white');bg.alpha_composite(src)
  images.append(np.asarray(bg.convert('RGB'),np.float32))
  crop=bg.convert('RGB').crop((365,615,845,1015)).resize((347,366),Image.Resampling.LANCZOS)
  contact.paste(crop,(col*347,row*391+25))
  draw.text((col*347+4,row*391+5),method+f' {angle:g}',fill='black')
 for part,(x0,y0,x1,y1) in regions.items():
  delta=[round(float(np.abs(images[j][y0:y1,x0:x1]-images[j-1][y0:y1,x0:x1]).mean()),4)
         for j in range(1,len(images))]
  qa.setdefault('metrics',{}).setdefault(method,{})[part]={
   'adjacentRGBMAE':delta,'maxAdjacentRGBMAE':max(delta),
   'meanAdjacentRGBMAE':round(statistics.mean(delta),4),
   'interiorMaxRGBMAE':max(delta[1:7])}
contact.save(D/'vision-matched-bow-contact.jpg',quality=94)
qa['contact']=str((D/'vision-matched-bow-contact.jpg').relative_to(R))
(R/'evidence/p15-110-render-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
print('METRICS',json.dumps({m:{k:round(v['maxAdjacentRGBMAE'],3) for k,v in r.items() if k in ('bow','collar','jewel')}
 for m,r in qa['metrics'].items()},indent=2),flush=True)

#!/usr/bin/env python3
"""P15-107: source-owned garment ink transport with 2D TPS and occlusion.

A coherent 67.5-degree source is transported onto per-yaw 60–67.5–75
correspondence geometry. A single image source controls interior garment
linework rather than averaging inconsistent bow/collar folds from two sources.

TPS control points are existing P15-106 source-owned vertices. The native
source image and its SHA are not changed. Candidate visual metrics do not
establish artist acceptance.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,cv2,numpy as np,statistics
import p15_101_head_render as head
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-107-canonical-ink';D.mkdir(parents=True,exist_ok=True)
Q=json.loads((R/'evidence/p15-105-native-art-qa.json').read_text())
M=json.loads((P/'p15-106-three-key-mesh/garment-three-key-mesh.json').read_text())
P106=json.loads((R/'evidence/p15-106-render-qa.json').read_text())
P101=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
S=512;yy,xx=np.indices((S,S),np.float32)
tpos=np.stack([xx,yy],axis=-1)
angles=head.angles
def load(f):return np.asarray(Image.open(f).convert('RGBA').resize((S,S),Image.Resampling.LANCZOS))
def prem(arr):
 f=arr.astype(np.float32)/255.0
 return np.concatenate((f[:,:,:3]*f[:,:,3:4],f[:,:,3:4]),axis=-1)
def unprem(p):
 a=np.clip(p[:,:,3:4],0,1)
 rgb=np.clip(p[:,:,:3]/np.maximum(a,1e-6),0,1)
 return np.uint8(np.round(np.concatenate((rgb,a),axis=-1)*255))
def over(back,front):
 a=np.clip(front[:,:,3:4],0,1)
 return np.concatenate((front[:,:,:3]+back[:,:,:3]*(1-a),a+back[:,:,3:4]*(1-a)),axis=-1)
def target_positions(angle):
 if angle<=67.5:
  a,b='60','67.5';t=(angle-60)/7.5
 else:
  a,b='67.5','75';t=(angle-67.5)/7.5
 pts={}
 for role,part in M['roles'].items():
  pA=np.asarray([x['sourcePosition'][a] for x in part['vertices']],np.float32)/2
  pB=np.asarray([x['sourcePosition'][b] for x in part['vertices']],np.float32)/2
  pts[role]=(1-t)*pA+t*pB
 return pts
def anchors(angle,roles):
 pos=target_positions(angle)
 src={role:np.asarray([x['sourcePosition']['67.5'] for x in M['roles'][role]['vertices']],np.float32)/2
      for role in roles}
 target=[];canonical=[];descriptions=[]
 for role in roles:
  # Use center, mid-ring cardinal, full-outline octants.
  indices=[0,1,5,9,13,17,19,21,23,25,27,29,31]
  for i in indices:
   a=pos[role][i];b=src[role][i]
   # deterministic eliminate near-duplicate coincident landmarks
   if any(np.linalg.norm(np.asarray(x)-a)<7 for x in target):continue
   target.append(a.tolist());canonical.append(b.tolist());descriptions.append(role+':'+str(i))
 # Stationary canvas anchors pin the outer region to avoid global TPS collapse.
 for x,y in [(0,0),(256,0),(511,0),(0,150),(511,150),(0,300),(511,300),
             (0,511),(128,511),(256,511),(384,511),(511,511)]:
  if any(np.linalg.norm(np.asarray(p)-[x,y])<7 for p in target):continue
  target.append([x,y]);canonical.append([x,y]);descriptions.append('canvas')
 return np.asarray(target,np.float64),np.asarray(canonical,np.float64),descriptions
def tps(target,source,lam=.005):
 # Coordinates normalized by 512, regularized TPS interpolation.
 target=target/512;source=source/512
 n=len(target)
 delta=target[:,None,:]-target[None,:,:]
 d2=np.maximum(np.sum(delta*delta,axis=-1),1e-12)
 kernel=d2*np.log(d2)
 Pmat=np.column_stack((np.ones(n),target))
 L=np.zeros((n+3,n+3),np.float64)
 L[:n,:n]=kernel+np.eye(n)*lam
 L[:n,n:]=Pmat
 L[n:,:n]=Pmat.T
 target2=np.concatenate((source,np.zeros((3,2))),axis=0)
 coef=np.linalg.solve(L,target2)
 return coef
def make_map(target,coefs):
 c=target/512
 n=len(c)
 out=np.empty((S*S,2),np.float32)
 # 8192-pixel chunks cap intermediate memory and work on rootless VPS.
 coords=np.stack((xx.flatten(),yy.flatten()),axis=1).astype(np.float64)/512
 for k in range(0,len(coords),8192):
  p=coords[k:k+8192]
  d2=np.maximum(np.sum((p[:,None,:]-c[None,:,:])**2,axis=2),1e-12)
  v=d2*np.log(d2)
  phi=np.column_stack((v,np.ones(len(p)),p))
  out[k:k+len(p)]=(phi@coefs*512).astype(np.float32)
 return out.reshape(S,S,2)
def smooth_bow_mask(data):
 x=np.uint8(data[:,:,3]>15)*255
 return cv2.dilate(x,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)))
native=load(R/Q['registeredPath'])
nativePrem=prem(native)
P0=R/'private-assets/exports/p15-106-three-key-mesh/yaw67p5'
sourceForeground=np.zeros_like(native)
for role in ('bow','jewel'):
 layer=load(P0/(role+'.png'))
 m=layer[:,:,3]>10
 sourceForeground[m]=layer[m]
# Simpler native source colors at art original pixels inside role matte;
# this avoids pre-composited edge halos from independently scaled layers.
mids=[load(P0/(role+'-ownership.png'))[:,:,0]>80 for role in ('bow','jewel')]
mask=np.uint8(mids[0]|mids[1])*255
mask=cv2.dilate(mask,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)))
sourceForeground=native.copy()
sourceForeground[:,:,3]=np.uint8(np.round(native[:,:,3].astype(np.float32)*mask/255))
foregroundPrem=prem(sourceForeground)
# Bow source removal before independent opaque compositing.
clean={}
for v in ('60','75'):
 orig=head.parts[v]['body'].copy()
 own=P/f'p15-106-three-key-mesh/yaw{v}'
 ink=np.zeros((S,S),np.uint8)
 for role in ('bow','jewel'):
  alpha=load(own/(role+'-ownership.png'))[:,:,0]
  ink=np.maximum(ink,np.uint8(alpha>70)*255)
 ink=cv2.dilate(ink,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(13,13)))
 ink=np.uint8((ink>0)&(orig[:,:,3]>0))*255
 # Inpaint the actual original garment RGB; background alpha remains owned by source.
 rgb=cv2.cvtColor(orig[:,:,:3],cv2.COLOR_RGB2BGR)
 fixed=cv2.cvtColor(cv2.inpaint(rgb,ink,7,cv2.INPAINT_TELEA),cv2.COLOR_BGR2RGB)
 out=orig.copy();out[:,:,:3]=fixed
 clean[v]=prem(out)
 Image.fromarray(out,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS).save(D/f'yaw{v}-bow-undercoat.png')
def get_head(t):
 maps={v:head.mesh_map(v,t) for v in ('60','75')}
 return head.skin_blend(head.warp(head.parts['60']['head'],maps['60']),
                        head.warp(head.parts['75']['head'],maps['75']),t)
def apply_transport(image,flow):
 return cv2.remap(image,flow[:,:,0],flow[:,:,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
def render(angle,method,mapData):
 t=(angle-60)/15
 cloth=head.skin_blend(clean['60'],clean['75'],t)
 full=apply_transport(nativePrem,mapData)
 bow=apply_transport(foregroundPrem,mapData)
 # Avoid phantom source in undercoat when foreground carries the same art.
 if method=='canonical_full':
  base=full
 elif method=='canonical_bow':
  base=over(cloth,bow)
 elif method=='canonical_bow_soft_edge':
  # One source owns all bow ink, but feather alpha only along its boundary.
  a=cv2.GaussianBlur(bow[:,:,3],(0,0),.55)
  alpha=np.clip(a,0,1)[:,:,None]
  rgb=np.where(bow[:,:,3:4]>1e-7,bow[:,:,:3]/np.maximum(bow[:,:,3:4],1e-6),0)
  front=np.concatenate((rgb*alpha,alpha),axis=-1)
  base=over(cloth,front)
 else:raise ValueError(method)
 result=over(base,get_head(t))
 result=over(result,head.get_ahoge(t))
 return unprem(np.clip(result,0,1))
methods=['canonical_full','canonical_bow','canonical_bow_soft_edge']
qa={'schema':'KOMA_P15_107_SOURCE_INK_SINGLE_OWNER_V1','character':'p0_character_001',
 'sourceModel':'genuine registered 67.5-degree native garment artwork',
 'sourceImageSHA256':Q['registeredSHA256'],
 'baseTopologySHA256':sha(P/'p15-106-three-key-mesh/garment-three-key-mesh.json'),
 'method':'regularized piecewise two-dimensional TPS on existing P15-106 multiview semantic anchors',
 'angles':angles,'methods':{m:{} for m in methods},'maps':{},
 'sourceFoldArtistApproved':False,'fullYawVisualAccepted':False}
for angle in angles:
 if angle in (60,75):
  # Keep exact original keyframes, avoiding any unapproved native source edits.
  for m in methods:
   image=Image.open(R/head.TOP['views'][str(int(angle))]['sourcePath']).convert('RGBA')
   f=D/(m+'-yaw'+f'{angle:g}'.replace('.','p')+'.png')
   image.save(f);qa['methods'][m][f'{angle:g}']={'path':str(f.relative_to(R)),'sha256':sha(f)}
  continue
 control,target,descriptions=anchors(angle,['shoulder.left','collar','bow','jewel'])
 coeff=tps(control,target,.0075)
 mapData=make_map(control,coeff)
 # Pixel warp Jacobian quality on a coarse step-8 grid
 dx=np.diff(mapData[::8,::8,:],axis=1)
 dy=np.diff(mapData[::8,::8,:],axis=0)
 jac=dx[:-1,:,0]*dy[:,:-1,1]-dx[:-1,:,1]*dy[:,:-1,0]
 qa['maps'][f'{angle:g}']={'landmarks':len(control),
    'minimumJacobian':round(float(np.min(jac)),5),
    'negativeJacobianSamples':int(np.count_nonzero(jac<=0)),
    'meanWarpPixelShift':round(float(np.mean(np.linalg.norm(mapData-tpos,axis=2))),4)}
 for method in methods:
  frame=render(angle,method,mapData)
  im=Image.fromarray(frame,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
  f=D/(method+'-yaw'+f'{angle:g}'.replace('.','p')+'.png')
  im.save(f);qa['methods'][method][f'{angle:g}']={'path':str(f.relative_to(R)),'sha256':sha(f)}
 print('source ink',angle,'landmarks',len(control),
       'jacobian',qa['maps'][f'{angle:g}']['minimumJacobian'],flush=True)
# Compare exactly the previously used 1024 pixel RGB ROIs and retain per-step metrics.
comparators={
 'P15-101-head_alpha_blend':{k:v['relativePath'] for k,v in P101['methods']['head_alpha_blend'].items()},
 'P15-105-three_key_direct':{k:v['relativePath'] for k,v in json.loads((R/'evidence/p15-105-render-qa.json').read_text())['methods']['three_key_direct'].items()}}
comparators.update({m:{k:v['path'] for k,v in frames.items()} for m,frames in qa['methods'].items()})
regions={'garment':(335,655,865,1015),'bow':(500,744,790,975),
 'jewel':(595,770,701,862),'collar':(400,665,805,835),'head':(440,285,840,640)}
contact=Image.new('RGB',(350*len(angles),400*len(comparators)),'white')
pen=ImageDraw.Draw(contact)
for row,(method,frames) in enumerate(comparators.items()):
 imageArray=[]
 for col,a in enumerate(angles):
  src=R/frames[f'{a:g}']
  im=Image.open(src).convert('RGBA');bg=Image.new('RGBA',im.size,'white');bg.alpha_composite(im)
  imageArray.append(np.asarray(bg.convert('RGB'),np.float32))
  contact.paste(bg.convert('RGB').crop((365,615,845,1015)).resize((350,370),Image.Resampling.LANCZOS),
   (col*350,row*400+25))
  pen.text((col*350+5,row*400+6),method+f' {a:g}',fill=(0,0,0))
 for region,(x0,y0,x1,y1) in regions.items():
  mae=[round(float(np.abs(imageArray[i][y0:y1,x0:x1]-imageArray[i-1][y0:y1,x0:x1]).mean()),4)
       for i in range(1,len(imageArray))]
  qa.setdefault('metrics',{}).setdefault(method,{})[region]={
    'adjacentRGBMAE':mae,'maxAdjacentRGBMAE':max(mae),
    'interiorMaxRGBMAE':max(mae[1:7]),
    'midpointRGBMAE':max(mae[3:5]),
    'meanAdjacentRGBMAE':round(statistics.mean(mae),4)}
contact.save(D/'single-source-ink-contact.jpg',quality=94)
qa['contact']=str((D/'single-source-ink-contact.jpg').relative_to(R))
(R/'evidence/p15-107-ink-qa.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')
print('METRICS',json.dumps({k:{reg:[v['maxAdjacentRGBMAE'],v['interiorMaxRGBMAE']] for reg,v in m.items() if reg in ('bow','collar','jewel')} for k,m in qa['metrics'].items()},indent=2),flush=True)

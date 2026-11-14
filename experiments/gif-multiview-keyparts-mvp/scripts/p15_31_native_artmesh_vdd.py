#!/usr/bin/env python3
"""P15-31 real per-role RGBA VDD interpolation, not whole-frame crossfade.

Each source ArtMesh is interpolated independently in premultiplied RGBA on
the 443px native canvas; compositing remains depth sorted. P15-30 tracked
eye and gold-clip art replace only those two roles at keyframes.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
from p1_front_semantic import alpha_over
R=Path(__file__).resolve().parent.parent
P=R/'private-assets'
OUT=P/'p15-31-per-role-vdd';OUT.mkdir(parents=True,exist_ok=True)
MAN=json.loads((R/'evidence/p15-21-intermediate-components-qa.json').read_text())
TRACK=json.loads((R/'evidence/p15-30-tracked-qa.json').read_text())
REVIEW=P/'exports/p15-30-tracked-review'
ANGLES=[55.,57.5,60.,62.5,65.]
ROLE_EYE='eye.far';ROLE_CLIP='hair.clip.cross_gold'
def slug(y):return 'yaw'+(str(int(y)) if float(y).is_integer() else str(y).replace('.','p'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return np.asarray(Image.open(p).convert('RGBA'))
def write(p,arr):Image.fromarray(arr.astype('uint8'),'RGBA').save(p)
def lerp_pm(left,right,t):
 a=left.astype(np.float32);b=right.astype(np.float32)
 la=a[:,:,3:4]/255.;ra=b[:,:,3:4]/255.
 prem=(1-t)*a[:,:,:3]*la+t*b[:,:,:3]*ra
 alpha=(1-t)*la+t*ra
 rgb=np.divide(prem,alpha,out=np.zeros_like(prem),where=alpha>1.e-6)
 return np.concatenate([np.clip(np.rint(rgb),0,255),np.clip(np.rint(alpha*255),0,255)],axis=2).astype('uint8')
def keyframe(yaw):
 f=next(q for q in MAN['frames'] if float(q['yaw'])==yaw)
 tracked=P/'p15-30-camera-tracked'/slug(yaw)
 result=[]
 for part in f['roles']:
  role=part['role']
  if role==ROLE_EYE:img=read(tracked/'eye-tracked-bridge-proxy.png')
  elif role==ROLE_CLIP:img=read(tracked/'clip-tracked.png')
  else:img=read(P/part['native'])
  if role in (ROLE_EYE,ROLE_CLIP):
   img=np.asarray(Image.fromarray(img,'RGBA').resize((443,443),Image.Resampling.LANCZOS))
  if img.shape!=(443,443,4):raise ValueError(role)
  result.append((role,img,part['depthOrder']))
 return result
def composite(parts):
 canvas=np.zeros((443,443,4),dtype='uint8')
 for _,pix,_ in sorted(parts,key=lambda x:x[2]):
  canvas=alpha_over(canvas,pix)
 return np.asarray(Image.fromarray(canvas,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS))
def alpha_iou(a,b):
 aa=a[:,:,3]>16;bb=b[:,:,3]>16
 return round(float(np.count_nonzero(aa&bb)/max(1,np.count_nonzero(aa|bb))),6)
def centroid(a):
 alpha=a[:,:,3].astype('float64')/255.
 mass=alpha.sum();yy,xx=np.indices(alpha.shape)
 return [float((xx*alpha).sum()/mass),float((yy*alpha).sum()/mass)]
def main():
 frames=[]
 keyframes={x:keyframe(x) for x in ANGLES}
 angle_seq=[]
 for i,a in enumerate(ANGLES):
  angle_seq.append((a,a,a,0.))
  if i+1<len(ANGLES):
   b=ANGLES[i+1]
   angle_seq.append(((a+b)/2,a,b,.5))
 for yaw,lo,hi,t in angle_seq:
  folder=OUT/slug(yaw);folder.mkdir(parents=True,exist_ok=True)
  a=keyframes[lo];b=keyframes[hi]
  if [x[0] for x in a]!=[x[0] for x in b]:raise AssertionError('semantic roles drift')
  parts=[]
  for (role,aa,depth),(_,bb,_) in zip(a,b):
   pix=aa if t==0 else lerp_pm(aa,bb,t)
   parts.append((role,pix,depth))
  full=composite(parts)
  whole=folder/'composite.png';write(whole,full)
  # Preserve independent native RGBA ArtMesh layers for every intermediate frame.
  paths=[]
  for role,pix,depth in parts:
   file=folder/(role+'.png');write(file,pix)
   paths.append({'role':role,'depthOrder':depth,'path':str(file.relative_to(P)),'sha256':sha(file)})
  # At the five anchors, output must reproduce P15-30 exact tracked composite.
  diff=None
  if t==0:
   reference=read(P/'p15-30-camera-tracked'/slug(yaw)/'whole-tracked.png')
   diff=int(np.count_nonzero(np.any(reference!=full,axis=2)))
   if diff:raise AssertionError('P15-30 keyframe pixel mismatch: '+str((yaw,diff)))
  eyepix=next(x[1] for x in parts if x[0]==ROLE_EYE)
  clippix=next(x[1] for x in parts if x[0]==ROLE_CLIP)
  # Native centre *1024/443 is only approximate geometric diagnostic.
  clip_c=centroid(clippix)
  frames.append({'yaw':yaw,'lower':lo,'upper':hi,'factor':t,
   'kind':'tracked-keyframe' if t==0 else 'true-native-per-role-vdd',
   'partCount':len(parts),'parts':paths,'composite':str(whole.relative_to(P)),
   'compositeSHA256':sha(whole),'keyframePixelError':diff,
   'clipCentroidNative':np.round(clip_c,4).tolist(),
   'eyeVisibleMassNative':round(float(eyepix[:,:,3].sum()/255),3),
   'fullFrameAlphaMass':round(float(full[:,:,3].sum()/255),3)})
 for i,f in enumerate(frames):
  if i:
   previous=read(P/frames[i-1]['composite']);now=read(P/f['composite'])
   f['previousAlphaIoU']=alpha_iou(previous,now)
   f['previousMeanAbsChannelDelta']=round(float(np.abs(previous.astype('float32')-now.astype('float32')).mean()),5)
 q={'schema':'KOMA-P15-31-NATIVE-ARTMESH-VDD-V1',
 'characterId':'p0_character_001','roleCount':13,'frames':frames,
 'interpolation':'PER_ROLE_PREMULTIPLIED_RGBA_LINEAR_ON_443_NATIVE',
 'fullFrameCrossfadeUsed':False,'actualIndependentRoleFramesGenerated':True,
 'newIndependentPaintings':0,'physicalDepthFromP15_21LayerOrder':True,
 'nasalBridgeMaskIsOnlyP15_29Proxy':True,'goldClipSideArtApproved':False,
 'artisticallyAccepted':False,'productionVddModified':False,
 'next':'Verify optical continuity, replace per-role linear blending with geometry-based VDD where needed; source art and true nasal bridge/clip occlusion gate remain'}
 (R/'evidence/p15-31-native-vdd-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'frames':len(frames),'nativeParts':sum(x['partCount'] for x in frames),
 'keyframeExact':all(x['keyframePixelError']==0 for x in frames if x['kind']=='tracked-keyframe'),
 'midpointKinds':[x['yaw'] for x in frames if x['kind']=='true-native-per-role-vdd'],
 'minAdjacentIoU':min(x['previousAlphaIoU'] for x in frames[1:]),
 'maxAdjacentMAE':max(x['previousMeanAbsChannelDelta'] for x in frames[1:])}))
if __name__=='__main__':main()

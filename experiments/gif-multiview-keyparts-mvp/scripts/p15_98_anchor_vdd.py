#!/usr/bin/env python3
"""Compare optical-flow and semantic-anchor VDD across 52.5°, 60° and 75°.
Uses landmark RBF prewarp, eye/hair ownership and source RGBA for yaw+bang motion.
Keyview endpoints remain pixel-exact P15-97 independently rendered source frames.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json,statistics,sys
import cv2,numpy as np
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports';D=P/'p15-98-vdd-review';D.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(R/'scripts'))
from flow_render import get_flow,morph
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
L=json.loads((R/'evidence/p15-98-landmarks.json').read_text())
views=['52p5','60','75'];pairs=[('52p5','60',52.5,60),('60','75',60,75)]
# Nine yaw steps in original angle units; exact generated independent sources at keyframe boundary.
steps={('52p5','60'):[52.5,54.375,56.25,58.125,60],
       ('60','75'):[60,63.75,67.5,71.25,75]}
N=512
Y,X=np.indices((N,N),dtype=np.float32)
GRID=np.stack((X,Y),axis=2)
keys={}
sourceFiles={}
for view in views:
 p=P/'p15-97-multiview-motion'/f'yaw{view}-frame-06.png'
 sourceFiles[view]=p
 keys[view]=np.asarray(Image.open(p).convert('RGBA').resize((N,N),Image.Resampling.LANCZOS)).copy()
anchors=L['correspondenceRoles']
canvas=list(L['fixedCanvasAnchors'])
def keypoints(view):
 info=L['viewLandmarks'][view]
 return np.asarray([info[f] for f in anchors]+[L['fixedCanvasAnchors'][k] for k in canvas],dtype=np.float32)/2
def pairwise_basis(src,tgt):
 # Smooth, regularized Gaussian RBF interpolation of target -> source inverse mapping.
 # A thin-plate/mesh correspondence proxy, not a learned deformable 3D model.
 sigma=67.0
 diff=tgt[:,None,:]-tgt[None,:,:]
 kernel=np.exp(-np.sum(diff*diff,axis=2)/(2*sigma*sigma))
 residual=(src-tgt)
 coeff=np.linalg.solve(kernel+np.eye(len(src),dtype=np.float32)*.025,residual).astype(np.float32)
 pos=GRID.reshape(-1,2)
 field=np.empty((len(pos),2),dtype=np.float32)
 block=12000
 for i in range(0,len(pos),block):
  row=pos[i:i+block]
  q=row[:,None,:]-tgt[None,:,:]
  phi=np.exp(-np.sum(q*q,axis=2)/(2*sigma*sigma)).astype(np.float32)
  field[i:i+block]=phi@coeff
 field=field.reshape(N,N,2)
 field=np.clip(field,-65,65)
 backward=GRID+field
 gx=np.gradient(backward[:,:,0],axis=1);gy=np.gradient(backward[:,:,0],axis=0)
 hx=np.gradient(backward[:,:,1],axis=1);hy=np.gradient(backward[:,:,1],axis=0)
 jac=(gx*hy-gy*hx)
 roi=jac[125:360,220:445]
 diag={'maxDisplacementPxHalfRes':round(float(np.linalg.norm(field,axis=2).max()),3),
       'negativeJacobianFractionInFaceROI':round(float((roi<=0).mean()),6),
       'minJacobianFaceROI':round(float(roi.min()),5)}
 return backward.astype(np.float32),diag
def warp_rgba(rgba,coordinates):
 af=rgba.astype(np.float32)/255
 prem=np.concatenate((af[:,:,:3]*af[:,:,3:4],af[:,:,3:4]),axis=2)
 warped=cv2.remap(prem,coordinates[:,:,0],coordinates[:,:,1],
                  cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
 a=np.clip(warped[:,:,3:4],0,1)
 rgb=np.clip(warped[:,:,:3]/np.maximum(a,1e-5),0,1)
 return np.concatenate((rgb,a),axis=2)
def compose(a,b,t):
 c=a*(1-t)+b*t
 c=np.clip(c,0,1)
 return np.uint8(np.round(c*255))
def normal_blend(a,b,t):
 return compose(a,b,t)
def sem_eye_weight(t):
 # Smoothly favor the sharper owner in eye/bang areas at each endpoint.
 if t<=0.30:return 0.0
 if t>=0.70:return 1.0
 v=(t-.30)/.40
 return float(v*v*(3-2*v))
def visibility_union(a,b,t):
 # Independently modeled source silhouettes: fill visible regions from either source,
 # using premultiplied coverage weights for RGB and union alpha to avoid grey ghost holes.
 alphaA=a[:,:,3:4];alphaB=b[:,:,3:4]
 wa=alphaA*(1-t);wb=alphaB*t
 rgb=np.divide(a[:,:,:3]*wa+b[:,:,:3]*wb,np.maximum(wa+wb,1e-6))
 alpha=np.maximum(alphaA,alphaB)
 return np.concatenate((rgb,np.clip(alpha,0,1)),axis=2)
def feature_roi(a,b,t,viewA,viewB,union=False):
 out=visibility_union(a,b,t) if union else normal_blend(a,b,t).astype(np.float32)/255
 wanted=sem_eye_weight(t)
 if wanted==t:return np.uint8(np.round(np.clip(out,0,1)*255))
 # Art proxy eye region; keep source-clipped iris/eyelid sharp.
 coordsA=L['viewLandmarks'][viewA];coordsB=L['viewLandmarks'][viewB]
 centers=[]
 for feature,radius in [('eye.near.center',(56,42)),('eye.far.center',(36,35)),
                        ('hair.front.tip',(62,85))]:
  if feature=='eye.far.center' and (not L['farEyeVisibleByView'][viewA] or not L['farEyeVisibleByView'][viewB]):continue
  xy=np.array(coordsA[feature])*(1-t)+np.array(coordsB[feature])*t
  centers.append((xy/2,np.array(radius)/2))
 mask=np.zeros((N,N),np.float32)
 for (cx,cy),(rx,ry) in centers:
  dist=((X-cx)/max(2,rx))**2+((Y-cy)/max(2,ry))**2
  ellipse=np.clip((1.4-dist)/.40,0,1)
  mask=np.maximum(mask,ellipse*ellipse*(3-2*ellipse))
 p=visibility_union(a,b,wanted) if union else (a*(1-wanted)+b*wanted)
 out=out*(1-mask[:,:,None])+p*mask[:,:,None]
 return np.uint8(np.round(np.clip(out,0,1)*255))
methods=['dis_blend','landmark_blend','landmark_eye_owner','landmark_visibility_union','landmark_visibility_eye_owner']
QA={'schema':'KOMA_P15_98_SEMANTIC_ANCHOR_VDD_ABLATION_V1',
 'source':'P15-97 6px hair-tip pose with independent keyed RGBA and generated semantic underpaint',
 'geometry':'regularized Gaussian landmark inverse warp with fixed canvas points and facial correspondences',
 'manualLandmarkProxies':True,'geometricYawMeasured':False,
 'anglesDegrees':[52.5,54.375,56.25,58.125,60,63.75,67.5,71.25,75],
 'sourceHashes':{k:sha(v) for k,v in sourceFiles.items()},
 'methodFrames':{m:{} for m in methods},'landmarkQA':{},
 'continuousYawVisualAccepted':False,'formalArtMeshAccepted':False}
cache={}
for a,b,start,end in pairs:
 src=keys[a];target=keys[b];coordsA=keypoints(a);coordsB=keypoints(b)
 fwd,rev=get_flow(src,target,'dis')
 segment=f'{a}-{b}';cache[segment]={}
 for ang in steps[(a,b)]:
  t=(ang-start)/(end-start)
  if t<=0:
   arr=src.copy()
   diag={'sourceKeyview':a}
  elif t>=1:
   arr=target.copy()
   diag={'sourceKeyview':b}
  else:
   mid=coordsA*(1-t)+coordsB*t
   mapA,da=pairwise_basis(coordsA,mid)
   mapB,db=pairwise_basis(coordsB,mid)
   cache[segment][str(ang)]=(mapA,mapB)
   diag={'sourceA':da,'sourceB':db}
  QA['landmarkQA'][str(ang)]=diag
  for method in methods:
   if t<=0:
    frame=src
   elif t>=1:
    frame=target
   elif method=='dis_blend':
    frame=morph(src,target,fwd,rev,t,GRID)
   else:
    ra=warp_rgba(src,mapA);rb=warp_rgba(target,mapB)
    if method=='landmark_blend':frame=compose(ra,rb,t)
    elif method=='landmark_eye_owner':frame=feature_roi(ra,rb,t,a,b)
    elif method=='landmark_visibility_union':frame=compose(visibility_union(ra,rb,t),visibility_union(ra,rb,t),0)
    else:frame=feature_roi(ra,rb,t,a,b,union=True)
   key=f'{ang:g}'
   file=D/f'{method}-yaw{key.replace(".","p")}.png'
   # All source-angle keys use the exact full size original key image.
   if t<=0 or t>=1:
    full=Image.open(sourceFiles[a if t<=0 else b]).convert('RGBA')
   else:
    full=Image.fromarray(frame,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
   full.save(file)
   QA['methodFrames'][method][key]={'sha256':sha(file),
     'relativePath':str(file.relative_to(R)),'independentKeyframe':t==0 or t==1}
  print('generated',segment,ang,flush=True)
# summarize quantitative adjacent changes within face, after compositing over white
crop=(455,300,835,650)
qaContact=Image.new('RGB',(360*9,382*len(methods)),'white')
d=ImageDraw.Draw(qaContact)
for row,method in enumerate(methods):
 seq=[]
 for col,ang in enumerate(QA['anglesDegrees']):
  key=f'{ang:g}'
  file=R/QA['methodFrames'][method][key]['relativePath']
  im=Image.open(file).convert('RGBA')
  bg=Image.new('RGBA',im.size,'white');bg.alpha_composite(im)
  cropImage=bg.convert('RGB').crop(crop)
  seq.append(np.asarray(cropImage,dtype=np.float32))
  tile=cropImage.resize((360,360),Image.Resampling.LANCZOS)
  qaContact.paste(tile,(col*360,row*382+20))
  d.text((col*360+6,row*382+4),f'{method} yaw {ang:g}',fill='black')
 errors=[round(float(np.abs(seq[i]-seq[i-1]).mean()),4) for i in range(1,len(seq))]
 QA.setdefault('methodMetrics',{})[method]={'faceAdjacentMAE':errors,'maxFaceAdjacentMAE':max(errors),
   'meanFaceAdjacentMAE':round(statistics.mean(errors),4),
   'keyview60BoundaryRatio':round(max(errors[3:5])/max(0.001,statistics.median(errors)),4)}
qaContact.save(D/'three-method-contact.jpg',quality=94)
QA['contact']='private-assets/exports/p15-98-vdd-review/three-method-contact.jpg'
(R/'evidence/p15-98-anchor-vdd-qa.json').write_text(json.dumps(QA,indent=2,ensure_ascii=False)+'\n')
print('QA',json.dumps(QA['methodMetrics'],indent=2))

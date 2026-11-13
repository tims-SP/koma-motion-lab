#!/usr/bin/env python3
"""Diagnose real cross-view SIFT garment ink correspondences with a source-owned mask."""
from pathlib import Path
import cv2,numpy as np,json
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-104-detail-landmarks';D.mkdir(exist_ok=True,parents=True)
parts=json.loads((R/'evidence/p15-103-parts-qa.json').read_text())
sift=cv2.SIFT_create(nfeatures=650,contrastThreshold=.007,edgeThreshold=15)
qa={'schema':'KOMA_P15_104_FEATURE_DISCOVERY_V1','method':'independent source texture SIFT, mutual ratio test and RANSAC','candidates':{}}
def extract(view,role):
 img=np.asarray(Image.open(P/f'p15-103-parts/yaw{view}/{role.replace(".","_")}.png').convert('RGBA'))
 mask=img[:,:,3]>60
 ys,xs=np.where(mask)
 x0,y0,x1,y1=int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)
 # Warped canonical crops eliminate most large view motion and keep actual source ink.
 edge=max(x1-x0,y1-y0)
 pad=int(round(edge*.10))
 x0=max(0,x0-pad);y0=max(0,y0-pad);x1=min(1024,x1+pad);y1=min(1024,y1+pad)
 crop=img[y0:y1,x0:x1]
 h,w=crop.shape[:2]
 rgb=np.clip(crop[:,:,:3].astype(np.float32)*crop[:,:,3:4]/255+255*(1-crop[:,:,3:4]/255),0,255).astype(np.uint8)
 gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
 ratio=512/max(h,w)
 target=(int(round(w*ratio)),int(round(h*ratio)))
 gray=cv2.resize(gray,target,interpolation=cv2.INTER_CUBIC)
 valid=cv2.resize(crop[:,:,3],target,interpolation=cv2.INTER_LINEAR)
 kp,des=sift.detectAndCompute(gray,np.uint8(valid>110)*255)
 return kp,des,gray,(x0,y0,w,h),ratio
for role in ['bow','jewel','collar','shoulder.left']:
 a=extract('60',role);b=extract('75',role)
 kpa,da,ga,ca,scaleA=a;kpb,db,gb,cb,scaleB=b
 rec={'keypoints':{'60':len(kpa),'75':len(kpb)},'tentative':0,'mutual':0,'ransacInliers':0}
 matches=[]
 if da is not None and db is not None and min(len(kpa),len(kpb))>=4:
  matcher=cv2.BFMatcher(cv2.NORM_L2)
  forward=matcher.knnMatch(da,db,k=2)
  backward=matcher.knnMatch(db,da,k=2)
  f={m.queryIdx:m for pair in forward if len(pair)==2 for m,n in [pair] if m.distance<.82*n.distance}
  rev={m.queryIdx:m for pair in backward if len(pair)==2 for m,n in [pair] if m.distance<.82*n.distance}
  matches=[m for i,m in f.items() if m.trainIdx in rev and rev[m.trainIdx].trainIdx==i]
  rec['tentative']=len(f);rec['mutual']=len(matches)
 if len(matches)>=4:
  ptsa=np.asarray([kpa[m.queryIdx].pt for m in matches],np.float32)
  ptsb=np.asarray([kpb[m.trainIdx].pt for m in matches],np.float32)
  affine,inlier=cv2.estimateAffinePartial2D(ptsa,ptsb,method=cv2.RANSAC,ransacReprojThreshold=11,maxIters=2500)
  if affine is not None:
   consistent=np.asarray(inlier,dtype=bool).ravel()
   matches=[m for i,m in enumerate(matches) if consistent[i]]
   rec['ransacInliers']=len(matches)
   rec['inlierRatio']=round(len(matches)/max(1,rec['mutual']),4)
   rec['canonicalTransform']=affine.round(4).tolist()
  else:matches=[]
 else:matches=[]
 rec['sourcePairs']=[]
 for m in matches:
  pa=np.array(kpa[m.queryIdx].pt);pb=np.array(kpb[m.trainIdx].pt)
  sourceA=[float(ca[0]+pa[0]/scaleA),float(ca[1]+pa[1]/scaleA)]
  sourceB=[float(cb[0]+pb[0]/scaleB),float(cb[1]+pb[1]/scaleB)]
  rec['sourcePairs'].append({'60':[round(x,3) for x in sourceA],'75':[round(x,3) for x in sourceB],
                            'descriptorDistance':round(float(m.distance),3)})
 h=max(ga.shape[0],gb.shape[0])
 contact=np.full((h,ga.shape[1]+gb.shape[1],3),255,np.uint8)
 contact[:ga.shape[0],:ga.shape[1]]=cv2.cvtColor(ga,cv2.COLOR_GRAY2RGB)
 contact[:gb.shape[0],ga.shape[1]:ga.shape[1]+gb.shape[1]]=cv2.cvtColor(gb,cv2.COLOR_GRAY2RGB)
 for j,m in enumerate(matches):
  u=np.array(kpa[m.queryIdx].pt).astype(int)
  v=np.array(kpb[m.trainIdx].pt).astype(int)+[ga.shape[1],0]
  cv2.line(contact,tuple(u),tuple(v),(255,70,20),1,cv2.LINE_AA)
  cv2.circle(contact,tuple(u),3,(10,120,210),-1);cv2.circle(contact,tuple(v),3,(10,120,210),-1)
 Image.fromarray(contact,'RGB').save(D/(role.replace('.','_')+'-sift-matches.jpg'),quality=94)
 qa['candidates'][role]=rec
 print('ROLE',role,'KEYS',rec['keypoints'],'MUTUAL',rec['mutual'],'INLIERS',rec['ransacInliers'],flush=True)
(R/'evidence/p15-104-feature-qa.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')

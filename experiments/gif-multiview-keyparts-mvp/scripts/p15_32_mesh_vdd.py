#!/usr/bin/env python3
"""P15-32 2D piecewise-affine mesh VDD pilot using per-role optical flow."""
import json,hashlib,shutil
from pathlib import Path
import cv2,numpy as np
from PIL import Image
from p1_front_semantic import alpha_over
R=Path(__file__).resolve().parent.parent;P=R/'private-assets'
SRC=P/'p15-31-per-role-vdd';OUT=P/'p15-32-mesh-vdd';OUT.mkdir(parents=True,exist_ok=True)
ANGLES=[55.,57.5,60.,62.5,65.]
ROLES=['eye.far','hair.clip.cross_gold','hair.side'];GRID=7
def slug(y):return 'yaw'+(str(int(y)) if float(y).is_integer() else str(y).replace('.','p'))
def read(p):return np.asarray(Image.open(p).convert('RGBA'))
def write(p,a):Image.fromarray(np.clip(a,0,255).astype('uint8'),'RGBA').save(p)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def over(a,b):return alpha_over(a,b)
def gray(x):
 rgb=x[:,:,:3].astype(np.float32)*(x[:,:,3:4].astype(np.float32)/255)
 return cv2.cvtColor(np.clip(rgb,0,255).astype('uint8'),cv2.COLOR_RGB2GRAY)
def flow_pair(a,b):
 return (cv2.calcOpticalFlowFarneback(gray(a),gray(b),None,.5,4,25,5,7,1.5,0),
         cv2.calcOpticalFlowFarneback(gray(b),gray(a),None,.5,4,25,5,7,1.5,0))
def bounds(a,b):
 ys,xs=np.where((a[:,:,3]>8)|(b[:,:,3]>8))
 return (max(0,int(xs.min())-8),max(0,int(ys.min())-8),
         min(442,int(xs.max())+8),min(442,int(ys.max())+8))
def points(flow,box,scale):
 x0,y0,x1,y1=box
 pts=np.stack(np.meshgrid(np.linspace(x0,x1,GRID),np.linspace(y0,y1,GRID)),axis=-1).astype(np.float32)
 ix=np.clip(np.rint(pts[:,:,0]).astype(int),0,442);iy=np.clip(np.rint(pts[:,:,1]).astype(int),0,442)
 delta=np.clip(flow[iy,ix]*scale,-42,42)
 return pts.reshape(-1,2), (pts+delta).reshape(-1,2),delta

def warp_mesh(img,src,dst):
 h,w=img.shape[:2];mx=np.full((h,w),-1,np.float32);my=mx.copy()
 tris=[]
 for gy in range(GRID-1):
  for gx in range(GRID-1):
   i=gy*GRID+gx;j=i+1;k=i+GRID;l=k+1
   tris.extend([(i,j,l),(i,l,k)])
 for ids in tris:
  s=src[list(ids)];d=dst[list(ids)]
  if abs(cv2.contourArea(d.astype(np.float32)))<.05:continue
  x0=max(0,int(np.floor(d[:,0].min())));x1=min(w,int(np.ceil(d[:,0].max()))+1)
  y0=max(0,int(np.floor(d[:,1].min())));y1=min(h,int(np.ceil(d[:,1].max()))+1)
  if x1<=x0 or y1<=y0:continue
  xx,yy=np.meshgrid(np.arange(x0,x1,dtype=np.float32),np.arange(y0,y1,dtype=np.float32))
  mat=cv2.getAffineTransform(d.astype(np.float32),s.astype(np.float32))
  sx=mat[0,0]*xx+mat[0,1]*yy+mat[0,2];sy=mat[1,0]*xx+mat[1,1]*yy+mat[1,2]
  v0=d[1]-d[0];v1=d[2]-d[0];den=v0[0]*v1[1]-v1[0]*v0[1]
  if abs(den)<1e-6:continue
  qx=xx-d[0,0];qy=yy-d[0,1]
  u=(qx*v1[1]-v1[0]*qy)/den;v=(v0[0]*qy-qx*v0[1])/den
  inside=(u>=-1e-3)&(v>=-1e-3)&(u+v<=1.001)
  mx[y0:y1,x0:x1][inside]=sx[inside];my[y0:y1,x0:x1][inside]=sy[inside]
 valid=mx>=0
 out=cv2.remap(img,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
 out[~valid]=0
 return out,int(valid.sum())
def deform(img,flow,t,box):
 src,dst,delta=points(flow,box,t);out,covered=warp_mesh(img,src,dst)
 ratios=[];flips=0
 for gy in range(GRID-1):
  for gx in range(GRID-1):
   i=gy*GRID+gx;j=i+1;k=i+GRID;l=k+1
   for ids in ((i,j,l),(i,l,k)):
    a,b,c=src[list(ids)];u,v,w=dst[list(ids)]
    sa=np.cross(b-a,c-a);da=np.cross(v-u,w-u)
    ratios.append(abs(float(da))/max(abs(float(sa)),1e-6))
    flips+=int(sa*da<=0)
 return out,{'meanPx':round(float(np.linalg.norm(delta,axis=2).mean()),4),
 'maxPx':round(float(np.linalg.norm(delta,axis=2).max()),4),'covered':covered,
 'triangleFlipCount':flips,'minTriangleAreaRatio':round(min(ratios),5)}
def iou(a,b):
 x=a[:,:,3]>16;y=b[:,:,3]>16
 return round(float((x&y).sum()/max(1,(x|y).sum())),5)
def blend(a,b):
 x=a.astype(np.float32);y=b.astype(np.float32);ax=x[:,:,3:4]/255;ay=y[:,:,3:4]/255
 al=(ax+ay)*.5;prem=(x[:,:,:3]*ax+y[:,:,:3]*ay)*.5
 rgb=np.divide(prem,al,out=np.zeros_like(prem),where=al>1e-6)
 return np.dstack([np.clip(np.rint(rgb),0,255),np.clip(np.rint(al[:,:,0]*255),0,255)]).astype('uint8')
def main():
 base=json.loads((R/'evidence/p15-31-native-vdd-qa.json').read_text());frames=[]
 for yaw in ANGLES:
  f=next(x for x in base['frames'] if x['yaw']==yaw);folder=OUT/slug(yaw);folder.mkdir(parents=True,exist_ok=True)
  for p in f['parts']:shutil.copyfile(P/p['path'],folder/(p['role']+'.png'))
  canvas=np.zeros((443,443,4),np.uint8)
  for part in sorted(f['parts'],key=lambda x:x['depthOrder']):canvas=over(canvas,read(folder/(part['role']+'.png')))
  write(folder/'composite-native.png',canvas)
  srccomposite=P/f['composite']
  shutil.copyfile(srccomposite,folder/'composite.png')
  frames.append({'yaw':yaw,'kind':'exact-keyframe','parts':13,'meshRoles':[]})

 for lo,hi in zip(ANGLES[:-1],ANGLES[1:]):
  mid=(lo+hi)/2;folder=OUT/slug(mid);folder.mkdir(parents=True,exist_ok=True)
  lf=next(x for x in base['frames'] if x['yaw']==lo);rf=next(x for x in base['frames'] if x['yaw']==hi);diag={}
  for role in ROLES:
   left=read(SRC/slug(lo)/(role+'.png'));right=read(SRC/slug(hi)/(role+'.png'))
   box=bounds(left,right);fw,bw=flow_pair(left,right)
   lw,ld=deform(left,fw,.5,box);rw,rd=deform(right,bw,.5,box);out=blend(lw,rw)
   write(folder/(role+'.png'),out)
   diag[role]={'bbox':box,'forward':ld,'backward':rd,
    'iouLeft':iou(out,left),'iouRight':iou(out,right),
    'grid':[GRID,GRID],'triangles':72,'flowClampPx':42,
    'method':'FARNEBACK_7X7_PIECEWISE_AFFINE'}
  for part in lf['parts']:
   role=part['role']
   if role in ROLES:continue
   aa=read(P/part['path']);bb=read(P/next(x['path'] for x in rf['parts'] if x['role']==role))
   write(folder/(role+'.png'),blend(aa,bb))
  canvas=np.zeros((443,443,4),np.uint8)
  for part in sorted(lf['parts'],key=lambda x:x['depthOrder']):
   canvas=over(canvas,read(folder/(part['role']+'.png')))
  write(folder/'composite-native.png',canvas)
  Image.fromarray(canvas).resize((1024,1024),Image.Resampling.LANCZOS).save(folder/'composite.png')
  frames.append({'yaw':mid,'kind':'mesh-deformed-midpoint','from':[lo,hi],
   'parts':13,'meshDiagnostics':diag})
 frames.sort(key=lambda x:x['yaw'])
 q={'schema':'KOMA-P15-32-PIECEWISE-AFFINE-MESH-VDD-V1','characterId':'p0_character_001',
  'angles':frames,'meshRoles':ROLES,'meshGrid':[GRID,GRID],'trianglesPerRole':72,
  'meshMethod':'FARNEBACK_OPTICAL_FLOW_SAMPLED_ON_7X7_GRID_PIECEWISE_AFFINE_TRIANGLE_WARP',
  'meshRolesAreImageDerived2DNotPhysical3D':True,'nonMeshRolesContinueP15_31PerRoleRGBA':True,
  'keyframesRemainP15_31ExactSource':True,'physicalNasalBridgeValidated':False,
  'physicalClipHairAttachmentValidated':False,'independentOriginalArtAdded':False,
  'artisticallyAccepted':False,'productionVddModified':False}
 (R/'evidence/p15-32-mesh-vdd-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'frames':len(frames),'meshMidpoints':sum(x['kind']=='mesh-deformed-midpoint' for x in frames),
  'meshRoles':ROLES,'maxDisplacement':max(v['forward']['maxPx'] for f in frames if f['kind']=='mesh-deformed-midpoint' for v in f['meshDiagnostics'].values())}))
if __name__=='__main__':main()

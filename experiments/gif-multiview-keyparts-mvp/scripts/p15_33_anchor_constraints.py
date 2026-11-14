#!/usr/bin/env python3
"""P15-33 constrained 2D per-role vertex warp.

Anchors are from registered P15-12 camera proxies plus measured alpha support
points. These *are not* artist-approved eye corner or crossed-bar endpoints.
"""
import numpy as np
from p15_32_mesh_vdd import GRID,points,warp_mesh,gray,bounds

def support_points(a,role,primary):
 alpha=a[:,:,3]>32
 yy,xx=np.where(alpha)
 if len(xx)<20:raise ValueError("no painted support: "+role)
 xlo,xhi=np.percentile(xx,[7,93]); ylo,yhi=np.percentile(yy,[7,93])
 if role=="eye.far":
  cy=float(np.median(yy))
  return np.array([primary,[float(xlo),cy],[float(xhi),cy]],np.float32),["iris.camera","eye.left.alpha.proxy","eye.right.alpha.proxy"]
 if role=="hair.clip.cross_gold":
  return np.array([primary,[float(xlo),float(ylo)],[float(xhi),float(yhi)]],np.float32),["clip.center.camera","cross.tip_a.alpha.proxy","cross.tip_b.alpha.proxy"]
 # side hair root registered; tip from lower 7% of nontransparent region
 bottom=yy>=np.percentile(yy,93)
 tip=[float(np.median(xx[bottom])),float(np.median(yy[bottom]))]
 return np.array([primary,tip],np.float32),["hair.side.root.camera.proxy","hair.tip.alpha.proxy"]

def correction_mesh(src,dst,flow,box,anchor_src,anchor_target):
 """Enforce multiple source->target landmarks on a 7x7 grid using RBF correction."""
 base,dest,delta=points(flow,box,.5)
 width=max(8.,box[2]-box[0]);height=max(8.,box[3]-box[1])
 sigma=max(9.,.42*max(width,height))
 # Predict source-anchor movement by bilinear control-grid interpolation.
 xy=base.reshape(GRID,GRID,2)
 increments=(dest-base).reshape(GRID,GRID,2)
 def interp(at):
  fx=np.clip((at[0]-box[0])/max(1,box[2]-box[0])*(GRID-1),0,GRID-1-1e-4)
  fy=np.clip((at[1]-box[1])/max(1,box[3]-box[1])*(GRID-1),0,GRID-1-1e-4)
  i,j=int(fx),int(fy);tx,ty=fx-i,fy-j
  return ((1-tx)*(1-ty)*increments[j,i]+tx*(1-ty)*increments[j,i+1]+
          (1-tx)*ty*increments[j+1,i]+tx*ty*increments[j+1,i+1])
 original=np.array([interp(p) for p in anchor_src])
 wanted=anchor_target-anchor_src
 residual=wanted-original
 # Gaussian response at each feature and each mesh vertex.
 dist=np.linalg.norm(base[:,None,:]-anchor_src[None,:,:],axis=2)
 W=np.exp(-.5*(dist/sigma)**2)
 pairdist=np.linalg.norm(anchor_src[:,None,:]-anchor_src[None,:,:],axis=2)
 kernel=np.exp(-.5*(pairdist/sigma)**2)
 coeff=np.linalg.solve(kernel+.001*np.eye(len(anchor_src)),residual)
 adjustment=W@coeff
 # Bound deformation to preserve topology; caller checks for flips.
 adjustment=np.clip(adjustment,-8.,8.)
 corrected=dest+adjustment.astype(np.float32)
 predicted=[]
 for k,p in enumerate(anchor_src):
  dd=(corrected-base).reshape(GRID,GRID,2)
  fx=np.clip((p[0]-box[0])/max(1,box[2]-box[0])*(GRID-1),0,GRID-1-1e-4)
  fy=np.clip((p[1]-box[1])/max(1,box[3]-box[1])*(GRID-1),0,GRID-1-1e-4)
  i,j=int(fx),int(fy);tx,ty=fx-i,fy-j
  v=((1-tx)*(1-ty)*dd[j,i]+tx*(1-ty)*dd[j,i+1]+
          (1-tx)*ty*dd[j+1,i]+tx*ty*dd[j+1,i+1])
  predicted.append(p+v)
 return base,corrected,np.array(predicted),{
  "maxCorrectionPx":round(float(np.linalg.norm(adjustment,axis=1).max()),5),
  "maxConstraintResidualPx":round(float(np.linalg.norm(np.array(predicted)-anchor_target,axis=1).max()),5)}
def constrained_warp(img,flow,box,src_features,tgt_features):
 src,dst,pred,diag=correction_mesh(img,img,flow,box,src_features,tgt_features)
 triangles=[]
 for gy in range(GRID-1):
  for gx in range(GRID-1):
   i=gy*GRID+gx;j=i+1;k=i+GRID;l=k+1
   triangles.extend([(i,j,l),(i,l,k)])
 flips=0;ratios=[]
 for tri in triangles:
  s=src[list(tri)];d=dst[list(tri)]
  sa=np.cross(s[1]-s[0],s[2]-s[0]);da=np.cross(d[1]-d[0],d[2]-d[0])
  flips+=int(sa*da<=0)
  ratios.append(abs(float(da))/max(abs(float(sa)),1e-6))
 warped,coverage=warp_mesh(img,src,dst)
 diag.update({"triangleFlips":flips,"minAreaRatio":round(min(ratios),6),
              "coveredPixels":coverage,"featureTargets":np.round(tgt_features,3).tolist(),
              "featurePredictions":np.round(pred,3).tolist()})
 return warped,diag

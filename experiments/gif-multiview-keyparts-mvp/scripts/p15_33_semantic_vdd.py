#!/usr/bin/env python3
"""P15-33 pilot semantic camera-anchor and alpha-support constrained 2D mesh."""
import json,shutil,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
from p15_32_mesh_vdd import (R,P,ANGLES,ROLES,GRID,slug,read,write,
                             flow_pair,bounds,blend,over)
from p15_33_anchor_constraints import support_points,constrained_warp
SRC=P/'p15-31-per-role-vdd';REF=P/'p15-32-mesh-vdd'
OUT=P/'p15-33-anchor-mesh';OUT.mkdir(parents=True,exist_ok=True)
CAMERA={
 'eye.far':'eye.far.iris',
 'hair.clip.cross_gold':'hair.clip.center',
 'hair.side':'hair.side'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def make():
 cam=json.loads((R/'evidence/p15-12-camera-proxy-qa.json').read_text())
 baseline=json.loads((R/'evidence/p15-31-native-vdd-qa.json').read_text())
 anchors={}
 for yaw in ANGLES:
  cf=next(f for f in cam['frames'] if f['yaw']==yaw)
  anchors[yaw]={role:np.array(cf['anchors'][key]['xy'],np.float32)*(443./1024.)
                for role,key in CAMERA.items()}
 reports=[]
 for yaw in ANGLES:
  name=slug(yaw);source=REF/name;folder=OUT/name;folder.mkdir(parents=True,exist_ok=True)
  f=next(x for x in baseline['frames'] if x['yaw']==yaw)
  for p in f['parts']:shutil.copy2(source/(p['role']+'.png'),folder/(p['role']+'.png'))
  shutil.copy2(source/'composite.png',folder/'composite.png')
  reports.append({'yaw':yaw,'kind':'exact-source-keyframe',
                  'compositeSha256':sha(folder/'composite.png'),
                  'roles':13,'keyframeExact':True})
 for lower,upper in zip(ANGLES[:-1],ANGLES[1:]):
  yaw=(lower+upper)/2.;name=slug(yaw)
  folder=OUT/name;folder.mkdir(parents=True,exist_ok=True)
  lf=next(x for x in baseline['frames'] if x['yaw']==lower)
  diagnostics={}
  # Do not redraw or alter the other ten roles.
  for part in lf['parts']:
   role=part['role']
   if role not in ROLES:
    shutil.copy2(REF/name/(role+'.png'),folder/(role+'.png'))
  for role in ROLES:
   left=read(SRC/slug(lower)/(role+'.png'))
   right=read(SRC/slug(upper)/(role+'.png'))
   src_l,names_l=support_points(left,role,anchors[lower][role])
   src_r,names_r=support_points(right,role,anchors[upper][role])
   assert names_l==names_r
   dest=(src_l+src_r)/2
   box=bounds(left,right)
   fw,bw=flow_pair(left,right)
   warped_l,diag_l=constrained_warp(left,fw,box,src_l,dest)
   warped_r,diag_r=constrained_warp(right,bw,box,src_r,dest)
   mixed=blend(warped_l,warped_r)
   write(folder/(role+'.png'),mixed)
   optical=read(REF/name/(role+'.png'))
   changed=int(np.count_nonzero(np.any(mixed!=optical,axis=2)))
   diagnostics[role]={
    'constraintIds':names_l,'targetFeatures443':np.round(dest,3).tolist(),
    'left':diag_l,'right':diag_r,
    'changedPixelsVsP15_32':changed,'outputSha256':sha(folder/(role+'.png')),
    'sourceKind':'P0_DERIVED_2D_CAMERA_AND_ALPHA_SUPPORT_PROXIES',
    'independentArtistApproved':False}
  canvas=np.zeros((443,443,4),np.uint8)
  for part in sorted(lf['parts'],key=lambda p:p['depthOrder']):
   canvas=over(canvas,read(folder/(part['role']+'.png')))
  write(folder/'composite-native.png',canvas)
  Image.fromarray(canvas,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS).save(folder/'composite.png')
  reports.append({'yaw':yaw,'kind':'semantic-anchor-constrained-mesh',
   'from':[lower,upper],'compositeSha256':sha(folder/'composite.png'),
   'roles':13,'meshDiagnostics':diagnostics})
 reports.sort(key=lambda x:x['yaw'])
 q={'schema':'KOMA-P15-33-SEMANTIC-ANCHOR-CONSTRAINED-2D-MESH-V1',
 'characterId':'p0_character_001','frames':reports,'meshRoles':ROLES,
 'meshSize':[7,7],'trianglesPerRole':72,
 'registeredCameraAnchorSource':'evidence/p15-12-camera-proxy-qa.json',
 'roleFeatureTypes':{'eye.far':['iris.camera','eye.left.alpha.proxy','eye.right.alpha.proxy'],
                     'hair.clip.cross_gold':['clip.center.camera','cross.tip_a.alpha.proxy','cross.tip_b.alpha.proxy'],
                     'hair.side':['hair.side.root.camera.proxy','hair.tip.alpha.proxy']},
 'secondaryFeaturesAreUnapprovedAlphaDerivedProxies':True,
 'physical3DModelUsed':False,'trueNoseOcclusionVerified':False,
 'clipPhysicalHairLockMountVerified':False,'independentOriginalPaint':False,
 'artisticallyAccepted':False,'productionVddModified':False}
 (R/'evidence/p15-33-anchor-vdd-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
 mids=[f for f in reports if f['kind']=='semantic-anchor-constrained-mesh']
 print(json.dumps({'frames':len(reports),'midpoints':len(mids),
  'maxResidualPx':max(d[x]['maxConstraintResidualPx'] for f in mids for d in f['meshDiagnostics'].values() for x in ['left','right']),
  'meshFlips':sum(d[x]['triangleFlips'] for f in mids for d in f['meshDiagnostics'].values() for x in ['left','right']),
  'changedPixels':[sum(v['changedPixelsVsP15_32'] for v in f['meshDiagnostics'].values()) for f in mids]}))
if __name__=='__main__':make()

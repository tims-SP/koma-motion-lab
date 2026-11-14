#!/usr/bin/env python3
"""P15-30 tracked original P0 eye and clip with P15-12 camera anchors.

Pixel registration with bilinear subpixel translation. Eye uses RELATIVE
camera-anchor displacement from 55 deg because eye alpha centroid != iris.
Clip gets absolute camera-anchor centering, explicitly a candidate.
No production VDD change or independent original art claim.
"""
import json,hashlib
from pathlib import Path
import numpy as np,cv2
from PIL import Image
from p1_front_semantic import alpha_over
R=Path(__file__).resolve().parent.parent;P=R/'private-assets'
S=P/'p15-29-defade-bridge'
O=P/'p15-30-camera-tracked';O.mkdir(parents=True,exist_ok=True)
YAW=[55.,57.5,60.,62.5,65.]
def slug(a):return 'yaw'+(str(int(a)) if a.is_integer() else str(a).replace('.','p'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return np.asarray(Image.open(p).convert('RGBA'))
def save(p,im):Image.fromarray(im.astype('uint8'),'RGBA').save(p)
def center(arr):
 alpha=arr[:,:,3].astype('float64')/255.
 yy,xx=np.indices(alpha.shape)
 mass=alpha.sum()
 return [float((alpha*xx).sum()/mass),float((alpha*yy).sum()/mass)]
def moved(arr,dx,dy):
 mat=np.array([[1.,0.,dx],[0.,1.,dy]],dtype=np.float32)
 return cv2.warpAffine(arr,mat,(arr.shape[1],arr.shape[0]),
  flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
def compose(layers,changes):
 img=np.zeros((443,443,4),np.uint8)
 for role in layers:
  layer=changes.get(role['role'])
  if layer is None:part=load(P/role['native'])
  else:part=np.asarray(Image.fromarray(layer,'RGBA').resize((443,443),Image.Resampling.LANCZOS))
  img=alpha_over(img,part)
 return np.asarray(Image.fromarray(img,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS))
def iou(a,b):
 a=a[:,:,3]>16;b=b[:,:,3]>16
 return float(np.count_nonzero(a&b)/max(1,np.count_nonzero(a|b)))
def main():
 cam=json.loads((R/'evidence/p15-12-camera-proxy-qa.json').read_text())
 p15=json.loads((R/'evidence/p15-21-intermediate-components-qa.json').read_text())
 eye_qa=json.loads((R/'evidence/p15-29-defade-bridge-qa.json').read_text())
 clip_qa=json.loads((R/'evidence/p15-29-clip-mount-qa.json').read_text())
 first=next(f for f in cam['frames'] if f['yaw']==55)['anchors']
 eye_ref=np.array(first['eye.far.iris']['xy'],float)
 frames=[]
 for yaw in YAW:
  name=slug(yaw);folder=O/name;folder.mkdir(exist_ok=True)
  layer=next(f['roles'] for f in p15['frames'] if f['yaw']==yaw)
  anchors=next(f['anchors'] for f in cam['frames'] if f['yaw']==yaw)
  far=np.array(anchors['eye.far.iris']['xy'],float)
  clip_anchor=np.array(anchors['hair.clip.center']['xy'],float)
  nose=np.array(anchors['nose']['xy'],float)
  eye_src=load(S/name/'inverse-fade.png')
  clip_src=load(S/name/'clip-recovered.png')
  # Iris semantic location is NOT the entire eye's pixel Alpha centroid:
  # keep original location at 55, only track yaw-induced anchor motion.
  eye_shift=far-eye_ref
  eye_tracked=moved(eye_src,*eye_shift)
  clip_start=np.array(center(clip_src))
  clip_shift=clip_anchor-clip_start
  clip_tracked=moved(clip_src,*clip_shift)
  eyep=folder/'eye-tracked.png';clipp=folder/'clip-tracked.png'
  save(eyep,eye_tracked);save(clipp,clip_tracked)
  # Track bridge proxy in same camera space. Existing P15-29 mathematical
  # mask is a *diagnostic hypothesis*, not physically calibrated geometry.
  from p15_29_recover_eye import proxy_mask
  mask,_=proxy_mask((1024,1024),nose,far,yaw)
  eye_cut=eye_tracked.copy()
  eye_cut[:,:,3]=np.rint(eye_cut[:,:,3].astype(np.float32)*mask).astype(np.uint8)
  cutp=folder/'eye-tracked-bridge-proxy.png';save(cutp,eye_cut)
  # Compare far eye alone, attached clip alone, and both in source depth stack.
  baseline=load(P/'p15-21-layered-anatomy'/(name+'.png'))
  both=compose(layer,{'eye.far':eye_cut,'hair.clip.cross_gold':clip_tracked})
  only_eye=compose(layer,{'eye.far':eye_cut})
  only_clip=compose(layer,{'hair.clip.cross_gold':clip_tracked})
  newp=folder/'whole-tracked.png';save(newp,both)
  save(folder/'eye-only.png',only_eye);save(folder/'clip-only.png',only_clip)
  original_clip_center=center(clip_src);tracked_clip_center=center(clip_tracked)
  expected=clip_anchor.tolist()
  raw_clip_err=float(np.linalg.norm(np.array(original_clip_center)-clip_anchor))
  reg_clip_err=float(np.linalg.norm(np.array(tracked_clip_center)-clip_anchor))
  eye_registered_center=center(eye_tracked);eye_original_center=center(eye_src)
  measured_eye_motion=np.array(eye_registered_center)-eye_original_center
  camera_eye_motion=eye_shift
  alpha_eye_retention=float(eye_tracked[:,:,3].sum()/max(1,eye_src[:,:,3].sum()))
  alpha_clip_retention=float(clip_tracked[:,:,3].sum()/max(1,clip_src[:,:,3].sum()))
  frames.append({'yaw':yaw,'anchorEye':far.tolist(),'anchorNose':nose.tolist(),
    'anchorClip':expected,'eyeShift':np.round(eye_shift,4).tolist(),
    'eyeSourceCentroid':np.round(eye_original_center,3).tolist(),
    'eyeTrackedCentroid':np.round(eye_registered_center,3).tolist(),
    'eyeRelativeMotionErrorPx':round(float(np.linalg.norm(measured_eye_motion-camera_eye_motion)),4),
    'clipShift':np.round(clip_shift,4).tolist(),
    'clipSourceCentroid':np.round(original_clip_center,3).tolist(),
    'clipRegisteredCentroid':np.round(tracked_clip_center,3).tolist(),
    'clipCentroidErrorBefore':round(raw_clip_err,4),
    'clipCentroidErrorAfter':round(reg_clip_err,4),
    'eyeRetainedAlphaFraction':round(alpha_eye_retention,6),
    'clipRetainedAlphaFraction':round(alpha_clip_retention,6),
    'wholeFrameAlphaIoUToP15_21':round(iou(baseline,both),6),
    'images':{x:sha(folder/(x+'.png')) for x in ['eye-tracked','clip-tracked','eye-tracked-bridge-proxy',
      'whole-tracked','eye-only','clip-only']}})
 q={'schema':'KOMA-P15-30-P0-CAMERA-TRACKED-CANDIDATES-V1',
 'characterId':'p0_character_001','angles':YAW,'source':'P15-29 restored P0 eye and gold clip',
 'eyeRegistration':'RELATIVE_IRIS_ANCHOR_DELTA_55_REFERENCE_NOT_ALPHA_CENTER',
 'clipRegistration':'ABSOLUTE_GOLD_CLIP_ALPHA_CENTROID_TO_CAMERA_ANCHOR',
 'bridgeMaskStatus':'P15-29_2D_PROXY_NOT_REAL_3D_HEAD_OCCLUSION',
 'originalIndependentPaint':False,'formalArtAccepted':False,'productionVddModified':False,
 'frames':frames,'next':'Verify continuous interpolation with real part anchors and visually approve clip physical mounting and far-eye occlusion'}
 (R/'evidence/p15-30-tracked-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'frames':len(frames),
  'clipAnchorErrorBefore':[f['clipCentroidErrorBefore'] for f in frames],
  'clipAnchorErrorAfter':[f['clipCentroidErrorAfter'] for f in frames],
  'eyeMotionError':[f['eyeRelativeMotionErrorPx'] for f in frames],
  'alphaIoU':[f['wholeFrameAlphaIoUToP15_21'] for f in frames]}))
if __name__=='__main__':main()

#!/usr/bin/env python3
"""P15-27 per-pixel semantic occlusion decomposition and preservation audit.

Do not rewrite P15-21 painted source alpha. Explicit visible/hidden layers
are diagnostic: front hair + nose cover far eye, side/front hair cover clip.
"""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent.parent;P=R/'private-assets'
SRC=P/'p15-21-intermediate-components'
OUT=P/'p15-27-occlusion'
OUT.mkdir(parents=True,exist_ok=True)
ANGLES=[55,57.5,60,62.5,65]
def slug(a):return 'yaw'+(str(int(a)) if a%1==0 else str(a).replace('.','p'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(folder,role):
 return np.asarray(Image.open(folder/(role+'.png')).convert('RGBA'))
def save(path,arr):
 path.parent.mkdir(parents=True,exist_ok=True)
 Image.fromarray(arr.astype('uint8'),'RGBA').save(path)
def layer(arr,alpha):
 dst=arr.copy()
 dst[:,:,3]=np.rint(np.clip(alpha,0,1)*255).astype(np.uint8)
 return dst
def run():
 frames=[]
 for yaw in ANGLES:
  name=slug(yaw);folder=SRC/name;dest=OUT/name;dest.mkdir(exist_ok=True)
  eye=load(folder,'eye.far');nose=load(folder,'nose')
  bangs=load(folder,'hair.front');side=load(folder,'hair.side')
  clip=load(folder,'hair.clip.cross_gold')
  eyea=eye[:,:,3].astype(np.float64)/255
  nose_a=nose[:,:,3].astype(np.float64)/255
  bangs_a=bangs[:,:,3].astype(np.float64)/255
  side_a=side[:,:,3].astype(np.float64)/255
  clipa=clip[:,:,3].astype(np.float64)/255
  # Source alpha is retained; physical in-front elements own occlusion.
  front_bang=eyea*bangs_a
  front_nose=eyea*(1-bangs_a)*nose_a
  eye_visible=eyea*(1-bangs_a)*(1-nose_a)
  eye_hidden=eyea-eye_visible
  # Clip in P8 is drawn ABOVE hair. Check both possible strands
  # without assuming overlap implies a physical mounting point.
  front_hair_a=1-(1-bangs_a)*(1-side_a)
  clip_hair_under=clipa*front_hair_a
  clip_hair_out=clipa*(1-front_hair_a)
  paths={}
  for key,arr in {
   'eye-visible':layer(eye,eye_visible),
   'eye-hidden-paint':layer(eye,eye_hidden),
   'eye-underpaint-original':eye,
   'eye-occluder-bangs':layer(bangs,bangs_a*eyea),
   'eye-occluder-nose':layer(nose,nose_a*eyea*(1-bangs_a)),
   'clip-over-hair':layer(clip,clip_hair_under),
   'clip-unmounted':layer(clip,clip_hair_out),
  }.items():
   path=dest/(key+'.png');save(path,arr);paths[key]={'path':str(path.relative_to(P)),'sha256':sha(path)}
  # Floating point per-pixel decomposition has near-machine-zero error
  maxerr=float(np.max(np.abs((eye_visible+eye_hidden)-eyea)))
  mass=float(eyea.sum())
  metrics={'eyeSourceAlphaMass':round(mass,2),
   'bangOccludedEyeAlphaMass':round(float(front_bang.sum()),2),
   'noseOccludedEyeAlphaMass':round(float(front_nose.sum()),2),
   'visibleEyeAlphaMass':round(float(eye_visible.sum()),2),
   'hiddenEyeAlphaMass':round(float(eye_hidden.sum()),2),
   'visibleEyeFraction':round(float(eye_visible.sum()/max(mass,1)),5),
   'clipSourceAlphaMass':round(float(clipa.sum()),2),
   'clipOverHairAlphaMass':round(float(clip_hair_under.sum()),2),
   'clipWithoutHairAlphaMass':round(float(clip_hair_out.sum()),2),
   'clipMountCoverageFraction':round(float(clip_hair_under.sum()/max(clipa.sum(),1)),5),
   'maxEyeDecompositionError':maxerr}
  frames.append({'yaw':yaw,'paths':paths,'metrics':metrics,
    'sourceSHA256':{'eye.far':sha(folder/'eye.far.png'),
      'hair.front':sha(folder/'hair.front.png'),'nose':sha(folder/'nose.png'),
      'hair.side':sha(folder/'hair.side.png'),
      'hair.clip.cross_gold':sha(folder/'hair.clip.cross_gold.png')}})
 report={'schema':'KOMA-P15-27-SEMANTIC-PIXEL-OCCLUSION-AUDIT-V1',
  'characterId':'p0_character_001','angles':ANGLES,'frames':frames,
  'method':'EXACT_ALPHA_COVERAGE_HAIR_FRONT_AND_NOSE_DEPTH_ORDER_WITH_EYE_UNDERPAINT_RETAINED',
  'newOriginalPaintingCreated':False,'productionVddModified':False,
  'formalArtisticAcceptance':False,
  'visualGate':'FAIL_SOURCE_FAR_EYE_VISIBILITY_HIGH_AND_CLIP_MOUNT_COVERAGE_LOW',
  'next':'Require keyframe-specific pose-aware eye occlusion and clip-on-hair mounting; manually sign off visible original painting before production'}
 q=R/'evidence/p15-27-occlusion-audit.json'
 q.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'frames':len(frames),'eyeVisibleFraction':[x['metrics']['visibleEyeFraction'] for x in frames],
  'clipMountFraction':[x['metrics']['clipMountCoverageFraction'] for x in frames],
  'maxDecompositionError':max(x['metrics']['maxEyeDecompositionError'] for x in frames)},ensure_ascii=False))
if __name__=='__main__':run()

#!/usr/bin/env python3
"""P15-28 physically composited far-eye candidate; no global fade.

The only occluders are existing, source-derived front hair and nose alpha.
Hidden eye pixels are retained as underpaint in a separate RGBA asset.
"""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
from p1_front_semantic import alpha_over
R=Path(__file__).resolve().parent.parent;P=R/'private-assets'
Q=json.loads((R/'evidence/p15-21-intermediate-components-qa.json').read_text())
OUT=P/'p15-28-physical-occlusion';OUT.mkdir(exist_ok=True)
ANGLES=[55,57.5,60,62.5,65]
def slug(a):return 'yaw'+(str(int(a)) if a%1==0 else str(a).replace('.','p'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rgba(p):return np.asarray(Image.open(p).convert('RGBA'))
def with_alpha(src,a):
 x=src.copy();x[:,:,3]=np.rint(np.clip(a,0,1)*255).astype('uint8');return x
def run():
 frames=[]
 for angle in ANGLES:
  name=slug(angle);entry=next(x for x in Q['frames'] if x['yaw']==angle)
  roles={x['role']:x for x in entry['roles']}
  paths={k:P/v['native'] for k,v in roles.items()}
  eye=rgba(paths['eye.far']);bang=rgba(paths['hair.front']);nose=rgba(paths['nose'])
  ea=eye[:,:,3].astype(float)/255
  ba=bang[:,:,3].astype(float)/255
  na=nose[:,:,3].astype(float)/255
  # Existing depth stack: hair.front > nose > eye.far. Alpha compositing
  # preserves original eye RGB and underpaint; no yaw-wide opacity multiplier.
  visible=ea*(1-ba)*(1-na)
  hidden=ea-visible
  candidates={
   'eye-visible':with_alpha(eye,visible),
   'eye-hidden-underpaint':with_alpha(eye,hidden),
   'eye-original-full':eye,
   'eye-front-hair-occlusion':with_alpha(bang,ba*ea),
   'eye-nose-occlusion':with_alpha(nose,na*ea*(1-ba)),
  }
  dest=OUT/name;dest.mkdir(exist_ok=True);files={}
  for key,arr in candidates.items():
   f=dest/(key+'.png');Image.fromarray(arr,'RGBA').save(f);files[key]={'path':str(f.relative_to(P)),'sha256':sha(f)}
  # Recompose complete 443 native stack using exactly the approved role order.
  comp=np.zeros((443,443,4),np.uint8)
  for layer in sorted(entry['roles'],key=lambda x:x['depthOrder']):
   part=rgba(paths[layer['role']])
   if layer['role']=='eye.far':
    part=candidates['eye-visible']
   part=np.asarray(Image.fromarray(part,'RGBA').resize((443,443),Image.Resampling.LANCZOS))
   comp=alpha_over(comp,part)
  out=dest/'physical-occlusion-composite.png'
  Image.fromarray(comp,'RGBA').save(out)
  # Source composite, unmodified, used to measure localized difference.
  base=np.zeros_like(comp)
  for layer in sorted(entry['roles'],key=lambda x:x['depthOrder']):
   part=rgba(paths[layer['role']])
   part=np.asarray(Image.fromarray(part,'RGBA').resize((443,443),Image.Resampling.LANCZOS))
   base=alpha_over(base,part)
  bpath=dest/'baseline-composite.png';Image.fromarray(base,'RGBA').save(bpath)
  diff=np.any(np.abs(comp.astype('int16')-base.astype('int16'))>1,axis=2)
  frames.append({'yaw':angle,'files':files,
   'composite':'private-assets/'+str(out.relative_to(P)),
   'baseline':'private-assets/'+str(bpath.relative_to(P)),
   'eyeSourceAlphaMass':round(float(ea.sum()),2),
   'eyeVisibleAlphaMass':round(float(visible.sum()),2),
   'eyeHiddenAlphaMass':round(float(hidden.sum()),2),
   'eyeVisibleFraction':round(float(visible.sum()/max(ea.sum(),1)),6),
   'decompositionError':float(np.max(np.abs(ea-visible-hidden))),
   'changedCompositePixels443':int(diff.sum()),
   'wholeEyeFadeApplied':False,
   'sourceEyeSHA256':sha(paths['eye.far']),
   'frontHairSHA256':sha(paths['hair.front']),
   'noseSHA256':sha(paths['nose'])})
 report={'schema':'KOMA-P15-28-PHYSICAL-FAR-EYE-OCCLUSION-V1',
  'characterId':'p0_character_001','angles':ANGLES,'frames':frames,
  'occlusion':'SOURCE_RGBA_ALPHA_FRONT_HAIR_AND_NOSE_OVER_EYE',
  'wholeLayerOpacityFade':False,'sourceEyePreservedAsUnderpaint':True,
  'sourceArtModified':False,'productionVddModified':False,
  'artisticAcceptance':'PENDING_FACE_GEOMETRY_REVIEW',
  'knownGap':'Existing near-hair and nose alpha masks do not yet cover enough of far eye; do not add invented occlusion geometry',
  'next':'Obtain face-surface occlusion contour from approved 3D anchors or independent painted key views; verify eye placement before VDD'}
 (R/'evidence/p15-28-physical-occlusion-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'frames':len(frames),'visibleFractions':[x['eyeVisibleFraction'] for x in frames],
  'changedPixels':[x['changedCompositePixels443'] for x in frames],
  'maxPartitionError':max(x['decompositionError'] for x in frames)}))
if __name__=='__main__':run()

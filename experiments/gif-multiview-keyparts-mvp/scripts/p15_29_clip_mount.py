#!/usr/bin/env python3
"""P15-29 restore source-backed clip alpha and test camera-anchored hair mounting.

Clip recovered by inverting P8 HIDE_WINDOWS (48,70); mount mask uses the
existing hair alpha union. No claims about unseen physical side.
"""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
from p1_front_semantic import alpha_over
ROOT=Path(__file__).resolve().parent.parent;P=ROOT/'private-assets'
OUT=P/'p15-29-defade-bridge';ANGLES=[55,57.5,60,62.5,65]
def slug(y):return 'yaw'+(str(int(y)) if y%1==0 else str(y).replace('.','p'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):return np.asarray(Image.open(p).convert('RGBA'))
def save(p,a):Image.fromarray(a.astype('uint8'),'RGBA').save(p)
def sched(y):
 t=np.clip((y-48)/(70-48),0,1)
 return 1-t*t*(3-2*t)
def run():
 m=json.loads((P/'p5-see-through/mv-candidate/parts.json').read_text())
 source=next(x for x in m['parts'] if x['yawDeg']==45 and x['semanticId']=='hair.clip.cross_gold')
 if sha(P/source['path'])!=source['frameSha256']:raise AssertionError('P0 clip drift')
 vdd=json.loads((ROOT/'evidence/p15-21-intermediate-components-qa.json').read_text())
 proxy=json.loads((ROOT/'evidence/p15-12-camera-proxy-qa.json').read_text())
 q=[]
 for yaw in ANGLES:
  name=slug(yaw);d=OUT/name;layer=next(x['roles'] for x in vdd['frames'] if x['yaw']==yaw)
  slots={x['role']:x for x in layer}
  original=rgba(P/slots['hair.clip.cross_gold']['path']);fade=sched(yaw)
  restored=original.copy();restored[:,:,3]=np.minimum(255,np.rint(original[:,:,3].astype(float)/fade)).astype('uint8')
  bangs=rgba(P/slots['hair.front']['path'])[:,:,3].astype('float64')/255.
  side=rgba(P/slots['hair.side']['path'])[:,:,3].astype('float64')/255.
  mount=1-(1-bangs)*(1-side)
  full=restored[:,:,3].astype(float)/255.
  attached=restored.copy()
  attached[:,:,3]=np.rint(full*mount*255).astype('uint8')
  detached=restored.copy()
  detached[:,:,3]=np.rint(full*(1-mount)*255).astype('uint8')
  save(d/'clip-legacy.png',original)
  save(d/'clip-recovered.png',restored)
  save(d/'clip-hair-attached.png',attached)
  save(d/'clip-off-hair.png',detached)
  # Measure clip alpha centroid vs physically registered anchor in P15-12.
  yy,xx=np.mgrid[0:1024,0:1024]
  mass=full.sum()
  center=[round(float((xx*full).sum()/mass),3),round(float((yy*full).sum()/mass),3)]
  c=next(f for f in proxy['frames'] if f['yaw']==yaw)['anchors']['hair.clip.center']['xy']
  delta=round(float(np.hypot(center[0]-c[0],center[1]-c[1])),3)
  q.append({'angle':yaw,'scheduleFactor':round(float(fade),6),
   'sourceP0_45_SHA256':sha(P/source['path']),
   'legacyMass':round(float(original[:,:,3].sum()/255.),2),
   'recoveredMass':round(float(mass),2),
   'clipAttachedMassFraction':round(float((full*mount).sum()/mass),6),
   'clipCenter':center,'registeredAnchor':c,
   'centerToAnchorPixels':delta,
   'sourceClipSHA256':sha(P/slots['hair.clip.cross_gold']['path']),
   'images':{key:sha(d/(key+'.png')) for key in ('clip-legacy','clip-recovered','clip-hair-attached','clip-off-hair')}})
 (ROOT/'evidence/p15-29-clip-mount-qa.json').write_text(json.dumps({
 'schema':'KOMA-P15-29-CLIP-INVERSE-FADE-MOUNT-V1',
 'characterId':'p0_character_001','angles':ANGLES,'frames':q,
 'model':'P8_HIDDEN_WINDOWS_CLIP_48_TO_70_ALPHA_INVERSE_WITH_SOURCE_HAIR_UNION',
 'hairMountingGeometricallyVerified3D':False,'artAccepted':False,'productionVddModified':False,
 'next':'Verify clip physically correct side across face turn, not just hair-overlap and camera-anchor stability'},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'frames':len(q),'clipLegacyMass':[x['legacyMass'] for x in q],
 'restoredMass':[x['recoveredMass'] for x in q],
 'clipOnHairFractions':[x['clipAttachedMassFraction'] for x in q],
 'clipAnchorDistances':[x['centerToAnchorPixels'] for x in q]}))
if __name__=='__main__':run()

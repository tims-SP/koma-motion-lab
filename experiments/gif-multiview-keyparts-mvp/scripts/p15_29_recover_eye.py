#!/usr/bin/env python3
"""P15-29: recover P8 globally faded far-eye alpha and test anchored bridge clipping.

P8 HIDE_WINDOWS is a legacy opacity schedule. Inverse-alpha images are recovered
raster estimates, not new artistic key drawings. The 2.5D nasal-bridge clipping
contour is an explicit proxy hypothesis, NOT approved face geometry.
"""
import json,hashlib,math
from pathlib import Path
import numpy as np
from PIL import Image
from p1_front_semantic import alpha_over
ROOT=Path(__file__).resolve().parent.parent
P=ROOT/'private-assets'
OUT=P/'p15-29-defade-bridge';OUT.mkdir(parents=True,exist_ok=True)
ANGLES=[55,57.5,60,62.5,65]
ROLE='eye.far'
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def slug(a):return 'yaw'+(str(int(a)) if a%1==0 else str(a).replace('.','p'))
def as_rgba(path):return np.asarray(Image.open(path).convert('RGBA'))
def save(path,arr):
 path.parent.mkdir(exist_ok=True,parents=True)
 Image.fromarray(arr.astype(np.uint8),'RGBA').save(path)
def fade(angle):
 u=np.clip((angle-52)/(75-52),0,1)
 return float(1-u*u*(3-2*u))
def proxy_mask(shape,nose,eye,angle):
 """2.5D camera-anchored near-surface test, not validated 3D occlusion."""
 H,W=shape
 gy,gx=np.ogrid[:H,:W]
 # The iris-nose camera gap narrows with yaw. Place an occluder between
 # the projected nose bridge and far-eye iris, using ONLY registered anchors.
 gap=max(0.,float(eye[0])-float(nose[0]))
 t=(angle-55)/10.
 bridge_x=float(nose[0])+gap*(.15+.55*t)
 bridge_y=float(nose[1])
 eye_y=float(eye[1])
 # Bridge is a sloped edge near the far eye, not a uniform eye alpha fade.
 # The y gradient is limited and anchored to the iris height.
 edge=bridge_x+0.085*(gy-eye_y)
 blur=2.6
 return np.clip((gx-edge)/blur*.5+.5,0,1).astype(np.float32),round(bridge_x,3)
def main():
 m=json.loads((P/'p5-see-through/mv-candidate/parts.json').read_text())
 s=next(x for x in m['parts'] if x['yawDeg']==45 and x['semanticId']==ROLE)
 source=P/s['path']
 if h(source)!=s['frameSha256']:raise ValueError('Canonical P0 45 eye SHA mismatch')
 p15=json.loads((ROOT/'evidence/p15-21-intermediate-components-qa.json').read_text())
 cam=json.loads((ROOT/'evidence/p15-12-camera-proxy-qa.json').read_text())
 if cam['characterId']!='p0_character_001':raise ValueError('camera identity')
 rows=[]
 for angle in ANGLES:
  name=slug(angle);folder=OUT/name;folder.mkdir(exist_ok=True)
  layers=next(f['roles'] for f in p15['frames'] if f['yaw']==angle)
  lr={p['role']:p for p in layers}
  src=P/lr[ROLE]['path'];old=as_rgba(src)
  factor=fade(angle)
  if not 0.15<factor<1:raise ValueError('Invalid schedule')
  recovered=old.copy()
  restored=np.minimum(255,np.round(old[:,:,3].astype(np.float32)/factor)).astype(np.uint8)
  recovered[:,:,3]=restored
  cp=next(f for f in cam['frames'] if float(f['yaw'])==angle)
  anchors=cp['anchors']
  nose=anchors['nose']['xy'];eye=anchors['eye.far.iris']['xy']
  if not (nose and eye and nose[0]<eye[0]):raise ValueError('Anchor mismatch')
  open_weight,edge=proxy_mask(restored.shape,nose,eye,angle)
  geometric=recovered.copy()
  geometric[:,:,3]=np.rint(restored.astype(np.float32)*open_weight).astype(np.uint8)
  legacy=folder/'legacy-faded.png';recovery=folder/'inverse-fade.png';bridge=folder/'bridge-proxy.png'
  save(legacy,old);save(recovery,recovered);save(bridge,geometric)
  # P0 source is not overwritten. Compare three complete native composites.
  def composed(candidate):
   comp=np.zeros((443,443,4),np.uint8)
   for layer in layers:
    if layer['role']==ROLE:
     resized=np.asarray(Image.fromarray(candidate,'RGBA').resize((443,443),Image.Resampling.LANCZOS))
    else:
     resized=as_rgba(P/layer['native'])
    comp=alpha_over(comp,resized)
   return np.asarray(Image.fromarray(comp,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS))
  a=composed(old);b=composed(recovered);c=composed(geometric)
  save(folder/'legacy-composite.png',a);save(folder/'recovered-composite.png',b);save(folder/'bridge-composite.png',c)
  base=as_rgba(P/'p15-21-layered-anatomy'/(name+'.png'))
  # Reconstruct source exactly from its native 443-layer manifest.
  original=np.zeros((443,443,4),np.uint8)
  for layer in layers:original=alpha_over(original,as_rgba(P/layer['native']))
  baseline_native=np.asarray(Image.fromarray(original,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS))
  if not np.array_equal(baseline_native,base):raise AssertionError('P15-21 baseline not pixel exact '+name)
  baseline_diff=int(np.count_nonzero(np.any(a!=base,axis=2)))
  old_mass=float(old[:,:,3].sum()/255.)
  new_mass=float(restored.sum()/255.)
  geo_mass=float(geometric[:,:,3].sum()/255.)
  rows.append({'angle':angle,'scheduleFactor':round(factor,6),
    'sourceP0_45SHA256':h(source),'oldIntermediateSHA256':h(src),
    'p15LayerExactSHA256':lr[ROLE]['sha256'],'anchors':{'nose':nose,'farEye':eye,'bridgeX':edge},
    'legacyEyeMass':round(old_mass,2),'restoredEyeMass':round(new_mass,2),
    'restoredToLegacyMassRatio':round(new_mass/old_mass,5),
    'bridgeEyeMass':round(geo_mass,2),'bridgeVisibleFractionOfRestored':round(geo_mass/new_mass,5),
    'uncutRestoredPixels':int(np.count_nonzero(restored>16)),
    'proxyVisiblePixels':int(np.count_nonzero(geometric[:,:,3]>16)),
    'wholeFrameChangedFromBaseline':int(np.count_nonzero(np.any(base!=c,axis=2))),
    'resampledLegacyToOriginalPixelDifference':baseline_diff,
    'nativeBaselineExact':True,
    'images':{v:h(folder/(v+'.png')) for v in
      ('legacy-faded','inverse-fade','bridge-proxy','legacy-composite','recovered-composite','bridge-composite')}})
 q={'schema':'KOMA-P15-29-P0-FAR-EYE-DEFADE-AND-BRIDGE-PROXY-V1',
   'characterId':'p0_character_001','angles':ANGLES,
   'sourceP0_45':str(source.relative_to(P)),'sourceP0_SHA256':h(source),
   'legacyFade':'P8_HIDDEN_WINDOWS_EYE_FAR_52_TO_75_SMOOTHSTEP',
   'recoveryMethod':'inverse_alpha_known_schedule_preserving_existing_RGB',
   'recoveryIsOriginalIndependentPainting':False,
   'geometry':'P15-12_CAMERA_ANCHOR_NOSE_TO_FAR_EYE_SLOPED_EDGE_PROXY',
   'geometryIsValidatedPhysical3D':False,'artAccepted':False,'productionVddModified':False,
   'frames':rows,'next':'Visually approve, then replace heuristic nose bridge proxy with verified head-surface occlusion and independently painted eye keyviews'}
 (ROOT/'evidence/p15-29-defade-bridge-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'frames':len(rows),'fade':[x['scheduleFactor'] for x in rows],
  'originalMass':[x['legacyEyeMass'] for x in rows],
  'restoredMass':[x['restoredEyeMass'] for x in rows],
  'bridgeVisible':[x['bridgeVisibleFractionOfRestored'] for x in rows],
  'changedPixels':[x['wholeFrameChangedFromBaseline'] for x in rows]}))
if __name__=='__main__':main()

#!/usr/bin/env python3
"""P15-21 source-derived 13-part intermediate ArtMesh export + roundtrip QA.

Source-derived retargeted textures are NOT independently painted art.
"""
import hashlib, json, shutil, zipfile
from pathlib import Path
import numpy as np
from PIL import Image
from p1_front_semantic import alpha_over
from p7_semantic_dense_flow import CANVAS
ROOT=Path(__file__).resolve().parent.parent
AS=ROOT/'private-assets'
SRC=AS/'p15-21-layered-anatomy'
DEST=AS/'p15-21-intermediate-components'
MAN=AS/'p15-20-canonical-source-views/qa.json'
REPORT=ROOT/'evidence/p15-21-intermediate-components-qa.json'
ANGLES=[55,57.5,60,62.5,65]
def name(a):
 return 'yaw'+(str(int(a)) if float(a).is_integer() else str(a).replace('.','p'))
def source_name(a):
 return str(float(a)).replace('.','p')
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()
def main():
 source_manifest=json.loads(MAN.read_text())
 original_p12=AS/'p15-17-anatomical-5frame/qa.json'
 roles=[p['semanticId'] for p in sorted(source_manifest['views'][1]['parts'],key=lambda a:a['depthOrder'])]
 assert len(roles)==13 and len(set(roles))==13
 outputs=[]
 for angle in ANGLES:
  yaw=name(angle);srcdir=SRC/'layers'/source_name(angle)
  target_dir=DEST/yaw;target_dir.mkdir(parents=True,exist_ok=True)
  whole=np.zeros((CANVAS,CANVAS,4),np.uint8)
  rows=[]
  visible_layers=[]
  for order,role in enumerate(roles):
   native=srcdir/(role+'.png')
   if native.is_file():
    with Image.open(native) as im:
     assert im.size==(CANVAS,CANVAS) and im.mode=='RGBA'
     arr=np.array(im)
    status='SOURCE_WARPED_VISIBLE_OR_PARTIAL'
   else:
    arr=np.zeros((CANVAS,CANVAS,4),np.uint8)
    status='HIDDEN_TRANSPARENT_PLACEHOLDER'
   nativeout=target_dir/'native'/f'{role}.png'
   nativeout.parent.mkdir(parents=True,exist_ok=True)
   Image.fromarray(arr,'RGBA').save(nativeout)
   # Keep 1024px independently editable *derived* texture.
   full=Image.fromarray(arr,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
   derived=target_dir/(role+'.png');full.save(derived)
   visible_layers.append(arr)
   whole=alpha_over(whole,arr)
   rows.append({'role':role,'depthOrder':order,'sourceStatus':status,
       'native':str(nativeout.relative_to(AS)),'nativeSHA256':sha(nativeout),
       'path':str(derived.relative_to(AS)),'sha256':sha(derived),
       'visiblePixels':int(np.count_nonzero(arr[:,:,3]>16)),
       'sourceImageExists':native.is_file()})
  # Check exact reconstruction using the same internal CANVAS-size blending order.
  actual=np.array(Image.fromarray(whole,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS))
  gold=np.array(Image.open(SRC/(yaw+'.png')).convert('RGBA'))
  delta=np.abs(actual.astype(np.int16)-gold.astype(np.int16))
  maxdelta=int(delta.max());changed=int(np.count_nonzero(np.any(delta>0,axis=2)))
  # P12 unmodified frame hash is the source-controlled baseline.
  prior=AS/'p15-17-anatomical-5frame'/(yaw+'.png')
  baseline_same=sha(prior)==sha(SRC/(yaw+'.png'))
  undercovered={}
  coverage=np.zeros((CANVAS,CANVAS),np.float32)
  for role,arr in reversed(list(zip(roles,visible_layers))):
   alpha=arr[:,:,3].astype(np.float32)/255
   occ=(alpha>16/255)&(coverage>0.98)
   undercovered[role]=int(occ.sum())
   coverage=1-(1-alpha)*(1-coverage)
  outputs.append({'yaw':angle,'whole':str((SRC/(yaw+'.png')).relative_to(AS)),
   'wholeSHA256':sha(SRC/(yaw+'.png')),'unchangedFromP15_17Baseline':baseline_same,
   'nativeRoundtripMaxPixelDelta':maxdelta,'nativeRoundtripChangedPixels':changed,
   'hiddenOccludedPixelInstances':undercovered,
   'roles':rows,'nonEmptyParts':sum(x['visiblePixels']>0 for x in rows)})
 report={'schema':'KOMA-P15-21-SOURCE-DERIVED-INTERMEDIATE-PARTS-V1',
    'characterId':'p0_character_001','sourceP15_20CanonicalQA_SHA256':sha(MAN),
    'sourceP15_17AnatomyQA_SHA256':sha(original_p12),
    'angles':ANGLES,'roleCount':len(roles),'roles':roles,'frames':outputs,
    'newIndependentPaintingCount':0,'hiddenUnderpaintArtApproval':False,
    'artisticAcceptance':False,
    'assetType':'SOURCE_DERIVED_ANATOMICAL_VDD_ARTMESH_NOT_INDEPENDENT_ART',
    'disposition':'ENGINEERING_REVIEW_ONLY',
    'next':'Independent brush-authored 55-65 keypart paintings still required; verify P0 identity, stroke continuity and physical hidden underpainting'}
 REPORT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps({'frames':len(outputs),'outputSlots':len(outputs)*13,
  'nonemptySlots':sum(x['nonEmptyParts'] for x in outputs),
  'maxRoundtripDelta':max(x['nativeRoundtripMaxPixelDelta'] for x in outputs),
  'changedPixels':[x['nativeRoundtripChangedPixels'] for x in outputs],
  'baselineFrameSHAUnchanged':all(x['unchangedFromP15_17Baseline'] for x in outputs),
  'keyParts':[{'yaw':x['yaw'],
              'hair.side':next(y['visiblePixels'] for y in x['roles'] if y['role']=='hair.side'),
              'hair.ahoge':next(y['visiblePixels'] for y in x['roles'] if y['role']=='hair.ahoge'),
              'hair.clip.cross_gold':next(y['visiblePixels'] for y in x['roles'] if y['role']=='hair.clip.cross_gold'),
              'eye.far':next(y['visiblePixels'] for y in x['roles'] if y['role']=='eye.far')} for x in outputs]},ensure_ascii=False))
if __name__=='__main__':main()

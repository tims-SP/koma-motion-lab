#!/usr/bin/env python3
"""P15-22 source-painted RGB, derived-alpha semantic candidate extraction.

Independent RGB originates from previously generated Qwen candidate, alpha masks
from P15-21 source-derived VDD. This does NOT create independent part drawings.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
import cv2
from p1_front_semantic import alpha_over
ROOT=Path(__file__).resolve().parent.parent
AS=ROOT/'private-assets'
PRE=AS/'p15-21-intermediate-components'
GENERATED=json.loads((ROOT/'evidence/p15-12-guided-candidate-qa.json').read_text())
LAYERS=json.loads((ROOT/'evidence/p15-21-intermediate-components-qa.json').read_text())
OUT=AS/'p15-22-painted-rgb-semantic-candidates'
REPORT=ROOT/'evidence/p15-22-painted-rgb-candidate-qa.json'
KEYS=['hair.side','hair.ahoge','hair.clip.cross_gold','eye.far']
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def im(p):return np.array(Image.open(p).convert('RGBA'))
def iou(a,b):return float((a&b).sum())/max(1,int((a|b).sum()))
def run():
 OUTPUT=[]
 for a in GENERATED['generated']:
  angle=float(a['angle'])
  rec=next(f for f in LAYERS['frames'] if f['yaw']==angle)
  source=AS/a['sourcePath']
  if sha(source)!=a['sourceSHA256']:raise ValueError('Unverified independent painting source')
  rgb=np.array(Image.open(source).convert('RGB'))
  if rgb.shape!=(1024,1024,3):raise ValueError('Canvas mismatch')
  # RGB ink heuristic: exclude near-white background, independently of alpha.
  hsv=cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV)
  ink=(rgb.min(axis=2)<218)&(np.max(rgb,axis=2)-np.min(rgb,axis=2)>9)
  subdir=OUT/('yaw57p5' if angle==57.5 else 'yaw60')
  subdir.mkdir(parents=True,exist_ok=True)
  rows=[]
  for role in rec['roles']:
   mask=im(AS/role['path'])[:,:,3]
   rgba=np.concatenate([rgb,mask[:,:,None]],axis=2).astype(np.uint8)
   filepath=subdir/(role['role']+'.png');Image.fromarray(rgba,'RGBA').save(filepath)
   visible=mask>16
   n=int(visible.sum())
   # Detect white/background contamination from pose mismatch; not absolute art score.
   contamination=int((visible&(~ink)).sum())
   rows.append({'role':role['role'],'path':str(filepath.relative_to(AS)),
      'sha256':sha(filepath),'sourceRGBSHA256':sha(source),
      'alphaSourceSHA256':role['sha256'],
      'alphaExactSource':bool(np.array_equal(mask,im(AS/role['path'])[:,:,3])),
      'visiblePixels':n,'inkCoveredPixels':int((visible&ink).sum()),
      'whiteBackgroundRiskPixels':contamination,
      'whiteBackgroundRiskRatio':round(contamination/max(n,1),5),
      'independentRgb':True,'independentSilhouette':False})
  # Composite: preserve stacking and candidate source alignment, used for visual QA only.
  comp=np.zeros((1024,1024,4),dtype=np.uint8)
  for role in rows:
   comp=alpha_over(comp,im(AS/role['path']))
  comp_path=subdir/'paint-rgb-alpha-derived-composite.png'
  Image.fromarray(comp,'RGBA').save(comp_path)
  alpha=comp[:,:,3]>16
  painted_iou=iou(alpha,ink)
  OUTPUT.append({'yaw':angle,'sourceImage':a['sourcePath'],'sourceSHA256':sha(source),
    'sourceModel':GENERATED['model'],'angleGuideAcceptance':a['visualReview'],
    'sourceForegroundIoUWithSourceDerivedAlpha':round(painted_iou,5),
    'sourceForegroundCount':int(ink.sum()),'extractedAlphaForegroundCount':int(alpha.sum()),
    'roles':rows,'keyRoleRisks':{r['role']:r['whiteBackgroundRiskRatio'] for r in rows if r['role'] in KEYS},
    'compositePath':str(comp_path.relative_to(AS)),'compositeSHA256':sha(comp_path),
    'acceptedSemanticPaintedParts':0})
 q={'schema':'KOMA-P15-22-PAINTED-RGB-ALPHA-DERIVED-TRIAL-V1','characterId':'p0_character_001',
   'sourceGeneratedCandidateQA_SHA256':sha(ROOT/'evidence/p15-12-guided-candidate-qa.json'),
   'sourceVDDLayerQA_SHA256':sha(ROOT/'evidence/p15-21-intermediate-components-qa.json'),
   'processing':'RGB-from-independent-generated-painting; Alpha-from-original-VDD-source',
   'isIndependentlyPaintedSemanticArt':False,
   'newModelGenerationP15_22':False,'newGeneratedPaintedRgbCandidateAngles':[57.5,60],
   'views':OUTPUT,'acceptedIndependentPaintedKeyparts':0,
   'acceptedNewUnderpainting':0,'artisticAcceptance':False,
   'status':'PAINTED_RGB_SOURCE_INTEGRATED_AS_REVIEW_CANDIDATE_NOT_ARTMESH_ACCEPTED'}
 REPORT.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'angles':[v['yaw'] for v in OUTPUT],
  'translucentPaintedRgbCandidates':sum(len(v['roles']) for v in OUTPUT),
  'paintSourceOverlapIoU':[v['sourceForegroundIoUWithSourceDerivedAlpha'] for v in OUTPUT],
  'keyPartWhiteBackgroundRisk':[v['keyRoleRisks'] for v in OUTPUT],
  'acceptedIndependentArt':0},ensure_ascii=False))
if __name__=='__main__':run()

#!/usr/bin/env python3
"""P15-23 image-generated source component extraction & registration.

Unlike P15-22, the alpha silhouette comes from NEW model image pixels,
not the old P15-21 VDD alpha. Registration uses bbox for spatial placement.
No art-quality acceptance is implied.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
import cv2
from PIL import Image
from p1_front_semantic import alpha_over
R=Path(__file__).resolve().parent.parent
P=R/'private-assets'
RAW=P/'p15-23-hf-independent-parts'
OUT=P/'p15-23-cutout-candidates'
QA=R/'evidence/p15-23-model-generated-keypart-qa.json'
SOURCE=P/'p15-21-intermediate-components/yaw60'
ROLES={
 'hair.ahoge':('ahoge-yaw060-raw.webp','ahoge',602302,'wfswhytrjutrj'),
 'hair.side':('side-hair-yaw060-raw.webp','side-hair',602304,'kkdcgtx'),
 'eye.far':('far-eye-yaw060-raw.webp','far-eye',602303,'dfvswegwseg'),
 'hair.clip.cross_gold':('clip-yaw060-raw.webp','clip',602301,'kkdcgtx'),
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def threshold(src,kind):
 h,w=src.shape[:2]
 hsv=cv2.cvtColor(src,cv2.COLOR_RGB2HSV)
 H,S,V=cv2.split(hsv)
 Y,X=np.ogrid[:h,:w]
 # Deterministic source-specific palette+spatial extraction.
 if kind=='clip':
  m=((H>=16)&(H<=38)&(S>55)&(V>142)&(src[:,:,0]>src[:,:,2]*1.32))
  m &= (X>round(w*.28))&(X<round(w*.9))&(Y>round(h*.10))&(Y<round(h*.78))
 elif kind=='ahoge':
  m=((H>=115)&(H<=178)&(S>17)&(V>60))
  m &= (X>round(w*.23))&(X<round(w*.8))&(Y<round(h*.26))
 elif kind=='side-hair':
  m=((H>=112)&(H<=178)&(S>23)&(V>65))
  m &= (X>round(w*.38))&(Y>round(h*.23))&(Y<round(h*.93))
 elif kind=='far-eye':
  # Purple iris plus dark upper lashes near centered facial eye.
  purple=(H>123)&(H<177)&(S>65)&(V>30)
  dark=(np.max(src,axis=2)<100)
  m=(purple|dark)&(X>round(w*.16))&(X<round(w*.84))&(Y>round(h*.27))&(Y<round(h*.80))
 else:raise ValueError(kind)
 m=np.uint8(m)*255
 m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
 n,label,stats,_=cv2.connectedComponentsWithStats(m,connectivity=8)
 if n<2:return np.zeros_like(m)
 # Keep sizeable subject clusters; clip sometimes consists of separated rods.
 areas=stats[1:,cv2.CC_STAT_AREA];top=int(areas.max())
 accepted=[j for j in range(1,n) if stats[j,cv2.CC_STAT_AREA]>=max(30,int(top*.04))]
 if not accepted:return np.zeros_like(m)
 out=np.uint8(np.isin(label,accepted))*255
 out=cv2.morphologyEx(out,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
 return cv2.GaussianBlur(out,(3,3),.6)
def bbox(mask):
 ys,xs=np.where(mask>16)
 if len(xs)==0:return None
 return [int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
def crop_rgba(p):
 rgb=np.asarray(Image.open(p).convert('RGB'))
 mask=threshold(rgb,p.stem.split('-yaw')[0])
 return np.concatenate([rgb,mask[:,:,None]],axis=2)
def extract():
 OUT.mkdir(parents=True,exist_ok=True)
 parts=[]
 for role,(file,key,seed,account) in ROLES.items():
  p=RAW/file
  rgb=np.asarray(Image.open(p).convert('RGB'))
  srcmask=threshold(rgb,key)
  bb=bbox(srcmask)
  if bb is None:raise AssertionError('No independent color component '+role)
  cut=np.concatenate([rgb,srcmask[:,:,None]],axis=2).astype(np.uint8)
  iso=OUT/(role+'.isolated.png')
  Image.fromarray(cut,'RGBA').save(iso)
  old=np.asarray(Image.open(SOURCE/(role+'.png')).convert('RGBA'))
  target=bbox(old[:,:,3]);assert target is not None
  # Crop to generated silhouette bounds, then scale and register to VDD anchor bbox.
  reg=np.zeros((1024,1024,4),dtype=np.uint8)
  crop=cut[bb[1]:bb[3],bb[0]:bb[2]]
  width=target[2]-target[0];height=target[3]-target[1]
  scaled=np.asarray(Image.fromarray(crop,'RGBA').resize((width,height),Image.Resampling.LANCZOS))
  reg[target[1]:target[3],target[0]:target[2]]=scaled
  output=OUT/(role+'.registered.png')
  Image.fromarray(reg,'RGBA').save(output)
  # Independent silhouette must differ from VDD alpha, unlike P15-22.
  new_a=reg[:,:,3]>16;old_a=old[:,:,3]>16
  union=int(np.count_nonzero(new_a|old_a))
  overlap=int(np.count_nonzero(new_a&old_a))
  iou=overlap/max(1,union)
  if np.array_equal(reg[:,:,3],old[:,:,3]):raise AssertionError('Incorrect copied VDD alpha')
  parts.append({'role':role,'model':'Qwen-Image-Fast','seed':seed,'account':account,
   'source':str(p.relative_to(P)),'sourceSHA256':sha(p),'sourceImageCanvas':list(rgb.shape[:2][::-1]),
   'sourceBBox':bb,'registeredTargetBBox':target,
   'isolated':str(iso.relative_to(P)),'isolatedSHA256':sha(iso),
   'registered':str(output.relative_to(P)),'registeredSHA256':sha(output),
   'originalModelSilhouetteRetained':True,'reusedOldVddAlpha':False,
   'nontransparentPixels':int(new_a.sum()),'alphaIoUWithVDD':round(iou,5),
   'registeredNontransparentOutsideTargetBBox':0,
   'generatedSourceWasIsolated':False,
   'identityAccepted':False,'artisticAcceptance':False})
 # Composite original 13 layers with four model-extracted candidates to visualize.
 generated={x['role']:np.asarray(Image.open(P/x['registered']).convert('RGBA')) for x in parts}
 source_qa=json.loads((R/'evidence/p15-21-intermediate-components-qa.json').read_text())
 f=next(x for x in source_qa['frames'] if x['yaw']==60)
 comp=np.zeros((1024,1024,4),np.uint8)
 for row in f['roles']:
  layer=generated.get(row['role'])
  if layer is None:layer=np.asarray(Image.open(P/row['path']).convert('RGBA'))
  comp=alpha_over(comp,layer)
 compout=OUT/'yaw060-four-keyparts-diagnostic-composite.png'
 Image.fromarray(comp,'RGBA').save(compout)
 q={'schema':'KOMA-P15-23-GENERATED-PART-CUTOUT-QA-V1','characterId':'p0_character_001',
 'sourceGeneration':'Connected Hugging Face Qwen-Image-Fast, four independently invoked model outputs',
 'modelGeneratedSourceCount':4,'sourceCompliance': 'FULL_HEAD_OR_FACE_GENERATED_DESPITE_ISOLATION_PROMPT',
 'isolatedNativeSemanticSourcesCount':0,
 'extractMethod':'PALETTE_AND_SPATIAL_MASK_FROM_NEW_MODEL_IMAGE_NO_VDD_ALPHA_REUSE',
 'targetAngle':60,'sourceVddQaSHA256':sha(R/'evidence/p15-21-intermediate-components-qa.json'),
 'parts':parts,'candidateCount':len(parts),
 'diagnosticComposite':str(compout.relative_to(P)),'diagnosticCompositeSHA256':sha(compout),
 'approvedIndependentSemanticPaintingCount':0,'hiddenUnderpaintApproval':False,
 'formalArtGate':'FAIL_GENERATED_SOURCE_CONTAINS_WHOLE_HEAD_AND_COMPONENT_MASK_HEURISTIC',
 'next':'Isolated transparent part-specific model generation/paint correction and artist inspection required before VDD production'}
 QA.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'candidates':len(parts),'sourceGenerated':4,'results':
 [{k:p[k] for k in ('role','sourceBBox','registeredTargetBBox','nontransparentPixels','alphaIoUWithVDD')} for p in parts],
 'artAccepted':0},ensure_ascii=False))
if __name__=='__main__':extract()

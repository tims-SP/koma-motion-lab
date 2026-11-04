#!/usr/bin/env python3
"""Compare established dense optical-flow interpolation baselines on PMX keys.

Farneback and DIS come from OpenCV; flow is estimated using only 45/90 key
frames and evaluated on withheld 55/67/82 renders. This is a research baseline,
not source artwork, and does not upgrade the independent 2D visual gate.
"""
import argparse,hashlib,json
from pathlib import Path
import cv2
import numpy as np

ANGLES=(55,67,82)
THRESHOLDS={'IoU':0.90,'MAE':20.0,'minArea':0.92,'maxArea':1.08}

def imread_rgba(path):
 image=cv2.imread(str(path),cv2.IMREAD_UNCHANGED)
 if image is None or image.shape!=(640,640,4):
  raise ValueError('Source not 640x640 BGRA '+str(path))
 return image

def flow_gray(image):
 alpha=image[:,:,3:4].astype(np.float32)/255
 bg=image[:,:,:3].astype(np.float32)*alpha+(1-alpha)*np.array([240,240,240],np.float32)
 return cv2.cvtColor(np.uint8(bg),cv2.COLOR_BGR2GRAY)

def compute_flow(first,second,method):
 a,b=flow_gray(first),flow_gray(second)
 if method=='farneback':
  def run(i,j):
   return cv2.calcOpticalFlowFarneback(i,j,None,.5,5,35,5,7,1.5,
                                          cv2.OPTFLOW_FARNEBACK_GAUSSIAN)
  return run(a,b),run(b,a)
 if method=='dis':
  aa=cv2.resize(a,(320,320),interpolation=cv2.INTER_AREA)
  bb=cv2.resize(b,(320,320),interpolation=cv2.INTER_AREA)
  alg=cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
  f=alg.calc(aa,bb,None)
  r=alg.calc(bb,aa,None)
  return (cv2.resize(f,(640,640),interpolation=cv2.INTER_LINEAR)*2,
          cv2.resize(r,(640,640),interpolation=cv2.INTER_LINEAR)*2)
 raise ValueError(method)

def morph(a,b,flowAB,flowBA,t):
 ys,xs=np.mgrid[:640,:640].astype(np.float32)
 # Approximate inverse maps from key-to-key forward/backward image flows.
 aa=cv2.remap(a,(xs-flowAB[:,:,0]*t),(ys-flowAB[:,:,1]*t),
              cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
 bb=cv2.remap(b,(xs-flowBA[:,:,0]*(1-t)),(ys-flowBA[:,:,1]*(1-t)),
              cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
 a0=aa[:,:,3:4].astype(np.float32)/255
 a1=bb[:,:,3:4].astype(np.float32)/255
 opacity=(1-t)*a0+t*a1
 weighted=(1-t)*aa[:,:,:3].astype(np.float32)*a0+t*bb[:,:,:3].astype(np.float32)*a1
 rgb=np.divide(weighted,opacity,out=np.zeros_like(weighted),where=opacity>1e-7)
 rgba=np.concatenate((rgb,np.clip(opacity*255,0,255)),axis=2)
 return np.uint8(np.round(np.clip(rgba,0,255)))

def measure(pred,reference):
 a=pred.astype(np.float32);b=reference.astype(np.float32)
 pa=a[:,:,3]>40;pb=b[:,:,3]>40
 inter=np.count_nonzero(pa & pb)
 union=np.count_nonzero(pa | pb)
 npa=int(np.count_nonzero(pa));npb=int(np.count_nonzero(pb))
 aa=a[:,:,3:4]/255;ba=b[:,:,3:4]/255
 va=a[:,:,:3]*aa+(1-aa)*240
 vb=b[:,:,:3]*ba+(1-ba)*240
 mask=pa|pb
 mae=np.mean(np.abs(va-vb)[mask]) if np.any(mask) else 255.
 return {'IoU':round(inter/union,6) if union else 0,
         'RGBMAE255':round(float(mae),3),
         'predictionAreaRatio':round(npa/npb,6) if npb else 0,
         'predictedForeground':npa,'referenceForeground':npb}

def run(keys,truths,output):
 output.mkdir(parents=True,exist_ok=True)
 a=imread_rgba(keys/'preview-yaw045-semantic-composite.png')
 b=imread_rgba(keys/'preview-yaw090-semantic-composite.png')
 holdouts={yaw:imread_rgba(truths/f'holdout-yaw{yaw:03d}-head.png') for yaw in ANGLES}
 reports=[]
 for method in ('farneback','dis'):
  f,r=compute_flow(a,b,method)
  method_res=[]
  for yaw in ANGLES:
   t=(yaw-45)/45
   candidate=morph(a,b,f,r,t)
   fname=f'flow-{method}-yaw{yaw:03d}.png'
   cv2.imwrite(str(output/fname),candidate)
   metrics=measure(candidate,holdouts[yaw])
   sha=hashlib.sha256((output/fname).read_bytes()).hexdigest()
   method_res.append({'yawDeg':yaw,'file':fname,'sha256':sha,**metrics})
  meanIoU=sum(x['IoU'] for x in method_res)/3
  meanMAE=sum(x['RGBMAE255'] for x in method_res)/3
  quality=all(x['IoU']>=THRESHOLDS['IoU'] and x['RGBMAE255']<=THRESHOLDS['MAE'] and
              THRESHOLDS['minArea']<=x['predictionAreaRatio']<=THRESHOLDS['maxArea'] for x in method_res)
  reports.append({'algorithm':method,'medianHoldoutCount':3,'meanIoU':round(meanIoU,6),
    'meanRGBMAE255':round(meanMAE,3),'qualityGate':'PASS' if quality else 'NEEDS_REFINEMENT',
    'holdouts':method_res})
 result={'schema':'R1999-PMX-OPTICAL-FLOW-BENCHMARK-V1',
   'sourceRole':'licensed_3d_semantic_proxy',
   'independent2DArtCount':0,
   'trainViews':[45,90],'testViews':list(ANGLES),
   'baselines':['OpenCV Farneback','OpenCV DIS'],
   'paperRelated':'OpenCV two-frame motion estimation; 2.5D cartoon VDD research',
   'thresholds':THRESHOLDS,'candidates':reports,
   'bestMeasuredCandidate':max(reports,key=lambda r:(r['meanIoU'],-r['meanRGBMAE255']))['algorithm']}
 (output/'flow-benchmark.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'candidates':[{k:x[k] for k in ('algorithm','meanIoU','meanRGBMAE255','qualityGate')} for x in reports],
   'best':result['bestMeasuredCandidate']}))
 return result

if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--keys',type=Path,required=True)
 p.add_argument('--holdouts',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True)
 a=p.parse_args()
 run(a.keys.resolve(),a.holdouts.resolve(),a.output.resolve())

#!/usr/bin/env python3
"""Regularize the 90°–135° head-flow field, preserving native source paint."""
import json
from pathlib import Path
import numpy as np
import cv2
from PIL import Image,ImageDraw
from p15_121_rear_arc_render import load,sha
from p15_122_source_owned import warp_source
from p15_124_face_safe import blend_premultiplied,source,composite_rgb,key
from flow_render import get_flow
ROOT=Path(__file__).resolve().parent.parent;P=ROOT/'private-assets';OUT=P/'exports/p15-125-hair-flow-regularization'
E=ROOT/'evidence/p15-125-hair-flow-qa.json'
ANGLES=(90.,101.25,112.5,123.75,135.)

def produce(sigma):
 keys=load();a,b=keys[90],keys[135];h,w=a.shape[:2]
 flow=get_flow(a,b,'dis');yy,xx=np.indices((h,w),dtype=np.float32);grid=np.stack([xx,yy],axis=-1)
 if sigma>0:flow=tuple(cv2.GaussianBlur(f,(0,0),sigma) for f in flow)
 frames=[]
 for angle in ANGLES:
  if angle in (90.,135.):frames.append(keys[int(angle)].copy());continue
  t=(angle-90)/45
  src=a if t<.5 else b;f=flow[0] if t<.5 else flow[1];dist=t if t<.5 else 1-t
  head=warp_source(src,f,dist,grid)
  garment=source(angle,'123-part-vdd')
  y=np.arange(h,dtype=np.float32)[:,None,None]
  mask=np.broadcast_to(np.clip((y-318)/24,0,1),head[...,3:4].shape)
  mask=mask*mask*(3-2*mask)
  frames.append(blend_premultiplied(head,garment,mask))
 return frames

def build():
 OUT.mkdir(parents=True,exist_ok=True)
 configs={'head_flow_raw':0,'head_flow_smooth4':4,'head_flow_smooth10':10}
 results={k:produce(v) for k,v in configs.items()}
 contact=Image.new('RGB',(320*5,350*4),(35,41,49));draw=ImageDraw.Draw(contact)
 diagnostics={}
 for row,(label,frames) in enumerate(results.items()):
  jumps=[round(float(np.abs(composite_rgb(a)-composite_rgb(b)).mean()),4) for a,b in zip(frames,frames[1:])]
  diagnostics[label]={'sigma':configs[label],'maxAdjacentCompositeRGBMAE':max(jumps),'adjacentCompositeRGBMAE':jumps,'nativeKeyframesPixelExact':all(np.array_equal(frames[i],load()[angle]) for i,angle in [(0,90),(4,135)])}
  d=OUT/label;d.mkdir(exist_ok=True)
  for i,(angle,frame) in enumerate(zip(ANGLES,frames)):
   Image.fromarray(frame,'RGBA').save(d/key(angle))
   tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
   contact.paste(tile.convert('RGB').resize((315,315),Image.Resampling.LANCZOS),(i*320,row*350+25))
   draw.text((i*320+5,row*350+5),f'{label} / {angle:g}',fill='white')
 # First row shows actual prior baseline.
 for i,angle in enumerate(ANGLES):
  arr=source(angle,'124-face-safe');tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(arr,'RGBA'))
  contact.paste(tile.convert('RGB').resize((315,315),Image.Resampling.LANCZOS),(i*320,3*350+25))
  draw.text((i*320+5,3*350+5),f'P15-124 reference / {angle:g}',fill='white')
 contact.save(OUT/'comparison.jpg',quality=94)
 (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 90-135 hair-flow comparison</title><style>body{font:16px system-ui;background:#202731;color:white}img{max-width:100%}</style><h2>90–135° head flow field regularization</h2><p>Native ink preserved at keyviews. A parameter study of smoothed optical-flow fields against previous source-owned head and garment render. Hidden surface art and physical correspondence remain unverified.</p><img src="comparison.jpg">')
 qa={'schema':'KOMA_P15_125_HAIR_FLOW_REGULARIZATION_V1','characterId':'p0_character_001','angles':ANGLES,'methods':diagnostics,
     'sourceKeyframeSHA256':{'90':sha(P/'extracted/whole/yaw090.png'),'135':sha(P/'extracted/whole/yaw135.png')},
     'nativeKeyframePixelExact':all(x['nativeKeyframesPixelExact'] for x in diagnostics.values()),
     'review':'private-assets/exports/p15-125-hair-flow-regularization/index.html',
     'physicalArtMeshVerified':False,'hiddenSurfaceArtVerified':False,'artistVisualAccepted':False,
     'next':'Use actual source-authored scalp/face/neck and coat layer outlines and anchors to address the documented hair line and neckline transition errors.'}
 E.write_text(json.dumps(qa,indent=2)+'\n')
 print(json.dumps(diagnostics,indent=2))
if __name__=='__main__':build()

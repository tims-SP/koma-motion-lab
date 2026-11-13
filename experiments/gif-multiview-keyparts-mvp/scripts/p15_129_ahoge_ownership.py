#!/usr/bin/env python3
"""90–135° ahoge owner tests on independent native-keyframe inbetweens."""
import json,sys
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT/'scripts'))
from p15_128_keyart_registration import frame_interp,jumps
from p15_121_rear_arc_render import load
from p15_122_source_owned import warp_source
from flow_render import get_flow
P=ROOT/'private-assets';OUT=P/'exports/p15-129-ahoge-owner';E=ROOT/'evidence/p15-129-ahoge-owner-qa.json'
KEYS=(90.,112.5,135.);ANGLES=(90.,101.25,112.5,123.75,135.)
def keyframes():
  original=load()
  mid=np.asarray(Image.open(P/'exports/p15-128-keyart-registration/yaw112p5-registration-candidate.png').convert('RGBA')).copy()
  return {90.:original[90],112.5:mid,135.:original[135]}
def top_components(frame):
  mask=(frame[:92,:,3]>48).astype('uint8')
  n,labels,stats,_=cv2.connectedComponentsWithStats(mask,8)
  return sum(1 for i in range(1,n) if stats[i,cv2.CC_STAT_AREA]>=10)
def merge_top(base,alternative,cutoff=83,feather=17):
  y=np.arange(base.shape[0],dtype=np.float32)[:,None,None]
  w=np.clip((cutoff+feather-y)/feather,0,1);w=w*w*(3-2*w)
  aa=base.astype(np.float32)/255;bb=alternative.astype(np.float32)/255
  alpha=aa[...,3:4]*(1-w)+bb[...,3:4]*w
  rgb=(aa[...,:3]*aa[...,3:4]*(1-w)+bb[...,:3]*bb[...,3:4]*w)/np.maximum(alpha,1e-6)
  result=np.uint8(np.round(np.clip(np.concatenate([rgb,alpha],axis=2)*255,0,255)))
  result[result[...,3]==0]=0
  return result
def run(save=True):
  keys=keyframes();base=frame_interp(keys[90.],keys[112.5],keys[135.])
  h,w=keys[90.].shape[:2];yy,xx=np.indices((h,w),dtype=np.float32);grid=np.stack((xx,yy),axis=-1)
  flows={(a,b):get_flow(keys[a],keys[b],'dis') for a,b in ((90.,112.5),(112.5,135.))}
  candidates={'bidirectional_blend':base}
  for method in ('intermediate_owner','nearest_key_owner'):
    frames=[]
    for angle,frame in zip(ANGLES,base):
      if angle in keys:frames.append(frame.copy());continue
      a,b=(90.,112.5) if angle<112.5 else (112.5,135.)
      t=(angle-a)/(b-a)
      left=(method=='nearest_key_owner' and t<=.5)
      owner=a if left else b
      alt=warp_source(keys[owner],flows[a,b][0 if left else 1],t if left else 1-t,grid)
      frames.append(merge_top(frame,alt))
    candidates[method]=frames
  qa={'schema':'KOMA_P15_129_AHOGE_OWNER_STUDY_V1','characterId':'p0_character_001','sourceAngles':list(KEYS),
      'samples':list(ANGLES),'methods':{},'nativeArtPreserved':True,'physicalStrandCorrespondenceVerified':False,
      'garmentAndFaceCorrespondenceVerified':False,'hiddenUnderpaintVerified':False,'artistVisualApproved':False,
      'review':'private-assets/exports/p15-129-ahoge-owner/index.html'}
  for name,frames in candidates.items():
    exact=all(np.array_equal(frames[ANGLES.index(a)],keys[a]) for a in KEYS)
    assert exact
    errors=jumps(frames)
    qa['methods'][name]={'maxAdjacentCompositeRGBMAE':max(errors),'adjacentCompositeRGBMAE':errors,
                         'topConnectedComponents':[top_components(f) for f in frames], 'nativeKeyframesPixelExact':exact}
  if save:
    OUT.mkdir(parents=True,exist_ok=True)
    canvas=Image.new('RGB',(320*5,355*3),(34,41,51));draw=ImageDraw.Draw(canvas)
    for j,(method,frames) in enumerate(candidates.items()):
      folder=OUT/method;folder.mkdir(exist_ok=True)
      for i,(angle,frame) in enumerate(zip(ANGLES,frames)):
        dest=folder/(f'yaw{angle:06.2f}'.replace('.','p')+'.png');Image.fromarray(frame,'RGBA').save(dest)
        tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
        canvas.paste(tile.convert('RGB').resize((315,315),Image.Resampling.LANCZOS),(320*i,355*j+28))
        draw.text((i*320+7,j*355+7),f'{method}: {angle:g}',fill='white')
    canvas.save(OUT/'comparison.jpg',quality=94)
    (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 hair-top ownership</title><style>body{background:#202733;color:white;font:16px system-ui}img{max-width:100%}</style><h2>90°–135° ahoge ownership comparison</h2><p>Isolated upper-head source ownership versus native keyframe optical flow. Geometry and hidden art remain provisional.</p><img src="comparison.jpg">')
    E.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
  return qa
if __name__=='__main__':print(json.dumps(run()['methods'],indent=2))

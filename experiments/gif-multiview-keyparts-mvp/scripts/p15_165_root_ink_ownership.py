#!/usr/bin/env python3
"""Remove source-owned loop ink around the crown before independent loop compositing.

The source reference is immutable. Locally masked RGB inpainting is a
diagnostic underpaint, not accepted key artwork.
"""
import json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_163_canonical_registration import OUT as ALIGN,P,ROOT
from p15_129_ahoge_ownership import keyframes,ANGLES,KEYS,top_components
from p15_128_keyart_registration import frame_interp,jumps
from p15_158_loop_correspondence import anchors,similarity,warp
from p15_153_source_topology import extract
from p15_134_underpaint_probe import compose,background_rgb
OUT=P/'exports/p15-165-root-ink-ownership'
E=ROOT/'evidence/p15-165-root-ink-ownership-qa.json'
TAGS={90.:'yaw090',112.5:'yaw112p5',135.:'yaw135'}
CUT=54
def registered():
 return {k:np.asarray(Image.open(ALIGN/TAGS[k]/'aligned.png').convert('RGBA')) for k in KEYS}
def root_mask(frame,angle,extent=12):
 y,x=np.indices(frame.shape[:2])
 if angle in KEYS:
  root=anchors(angle)[0]
 else:
  start,end=(90.,112.5) if angle<112.5 else (112.5,135.)
  root=anchors(start)[0]*(1-(angle-start)/(end-start))+anchors(end)[0]*((angle-start)/(end-start))
 # Conservative local root band; never erase whole hair crown.
 roi=(y>=CUT-5)&(y<=min(95,root[1]+extent))&(abs(x-root[0])<=extent)
 rgb=frame[...,:3].astype(np.float32)
 gray=cv2.cvtColor(frame[...,:3],cv2.COLOR_RGB2GRAY)
 # Dark existing original ink contrasted with surrounding local crown color.
 local=cv2.GaussianBlur(gray,(0,0),5)
 ink=gray<np.minimum(local-7,154)
 mask=roi&ink&(frame[...,3]>80)
 return mask
def clean_old_loop(frame,angle,extent=12):
 root=root_mask(frame,angle,extent)
 y,x=np.indices(root.shape)
 free=(y<CUT)&(frame[...,3]>24)
 mask=free|root
 base=frame.copy()
 base[free]=0
 crown=np.uint8(root)*255
 rgb=cv2.cvtColor(frame[...,:3],cv2.COLOR_RGB2BGR)
 repaired=cv2.inpaint(rgb,crown,3,cv2.INPAINT_TELEA)
 base[root,:3]=cv2.cvtColor(repaired,cv2.COLOR_BGR2RGB)[root]
 return base,{'freeLoopPixels':int(free.sum()),'rootInkPixels':int(root.sum()),
   'sourceBelowY96Exact':bool(np.array_equal(base[96:],frame[96:])),
   'alphaCrownPreserved':bool(np.array_equal(base[CUT:,:,3],frame[CUT:,:,3]))}
def evaluate(save=True):
 keys=keyframes();parts=registered()
 reference=frame_interp(keys[90.],keys[112.5],keys[135.])
 variants={'reference':reference}
 reports={}
 for extent in (8,12,16):
  label=f'root_ink_{extent}'
  frames=[];readings={}
  for i,angle in enumerate(ANGLES):
   if angle in KEYS: frames.append(keys[angle].copy());continue
   start,end=(90.,112.5) if angle<112.5 else (112.5,135.)
   t=(angle-start)/(end-start)
   owner=start if t<=.5 else end
   dest=anchors(start)*(1-t)+anchors(end)*t
   bg,diagnostic=clean_old_loop(reference[i],angle,extent)
   moving=warp(parts[owner],similarity(anchors(owner),dest))
   frames.append(compose(bg,moving))
   readings[f'{angle:g}']=diagnostic
  variants[label]=frames
  reports[label]=readings
 results={}
 for label,frames in variants.items():
  results[label]={'maxAdjacentRGBMAE':max(jumps(frames)),
    'topConnectedComponents':[top_components(v) for v in frames],
    'nativeKeysExact':all(np.array_equal(frames[ANGLES.index(k)],keys[k]) for k in KEYS),
    'crownAlphaChangedPixels':{f'{a:g}':int(np.count_nonzero(frames[ANGLES.index(a)][CUT:95,:,3]!=reference[ANGLES.index(a)][CUT:95,:,3])) for a in (101.25,123.75)}}
 q={'schema':'KOMA_P15_165_ROOT_INK_OWNERSHIP_V1','characterId':'p0_character_001',
   'sourceAngles':list(KEYS),'samples':list(ANGLES),
   'maskStudy':reports,'renderers':results,
   'nativeArtPreserved':True,'independentRootArtworkArtistApproved':False,
   'sourceMatchedScalpArtworkApproved':False,'continuousVisualAccepted':False,
   'productionSelected':False,
   'review':'private-assets/exports/p15-165-root-ink-ownership/index.html',
   'next':'Paint rootless crown at 90,112.5,135 degrees and fully attached source-matched loop root; verify crown pixels and single connected loop at both intermediate angles.'}
 q['gate']={'nativeKeyframesExact':all(x['nativeKeysExact'] for x in results.values()),
     'midframesOneTopComponent':any(all(results[k]['topConnectedComponents'][i]==1 for i in (1,3)) for k in reports),
     'crownAlphaUnchanged':any(all(v==0 for v in results[k]['crownAlphaChangedPixels'].values()) for k in reports),
     'beatsReference':any(results[k]['maxAdjacentRGBMAE']<=results['reference']['maxAdjacentRGBMAE'] for k in reports),
     'artistSourceApproved':False,'passes':False}
 if save:
  OUT.mkdir(parents=True,exist_ok=True)
  board=Image.new('RGB',(310*5,217*len(variants)),(36,43,54));d=ImageDraw.Draw(board)
  for row,(label,frames) in enumerate(variants.items()):
   folder=OUT/label;folder.mkdir(parents=True,exist_ok=True)
   for col,(angle,frame) in enumerate(zip(ANGLES,frames)):
    Image.fromarray(frame,'RGBA').save(folder/(f'yaw{angle:06.2f}'.replace('.','p')+'.png'))
    tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
    crop=tile.crop((135,0,360,120)).resize((303,180),Image.Resampling.NEAREST)
    board.paste(crop.convert('RGB'),(col*310,row*217+28))
    d.text((col*310+6,row*217+5),f'{label} {angle:g}',fill='white')
  board.save(OUT/'root-closeup.jpg',quality=95)
  (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 crown ink ownership</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Root-ink ownership and crown repair</h2><p>Three bounded root-removal candidates against existing reference interpolation. Source canonical keyviews stay intact. Synthetic inpainting is a diagnostics-only crown candidate.</p><img src="root-closeup.jpg">')
  E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
 return q
if __name__=='__main__':
 q=evaluate()
 print(json.dumps({'methods':q['renderers'],'gate':q['gate']},indent=2))

"""P15-191 source-root alpha/color registration experiment."""
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from p15_129_ahoge_ownership import keyframes,KEYS
from p15_134_underpaint_probe import P,background_rgb
from p15_184_alpha_aware_temporal_sweep import ANGLES,local_metrics
from p15_189_root_emergence_audit import color_seam
ROOT=Path(__file__).resolve().parents[1]
OUT=P/'exports/p15-191-source-root-color'
E=ROOT/'evidence/p15-191-source-root-color-qa.json'
MODES={'original':(0,0.),'radius_5':(5,.55),'radius_8':(8,.55),'radius_12':(12,.55),'radius_8_strong':(8,.85)}
BG=np.asarray([49,61,78],np.float32)
def comp(im):
 a=im[...,3:4].astype(np.float32)/255.
 return im[...,:3].astype(np.float32)*a+(1-a)*BG
def palette(image,point):
 x,y=np.rint(point).astype(int);x0=max(0,x-4);x1=min(443,x+5);y0=max(0,y-4);y1=min(443,y+5)
 alpha=image[y0:y1,x0:x1,3].astype(np.float32)/255
 w=.2+.8*alpha
 return (comp(image)[y0:y1,x0:x1]*w[...,None]).sum((0,1))/w.sum()
def correct(im,point,target,radius,strength):
 out=im.copy()
 if radius<=0:return out,0
 x,y=point;extent=radius*3
 x0=max(0,int(x-extent));x1=min(443,int(x+extent+1))
 y0=max(0,int(y-extent));y1=min(443,int(y+extent+1))
 patch=out[y0:y1,x0:x1]
 yy,xx=np.mgrid[y0:y1,x0:x1]
 a=patch[...,3].astype(np.float32)/255
 w=np.exp(-((xx-x)**2+(yy-y)**2)/(2*radius*radius))*strength*np.clip((a-.15)/.55,0,1)
 before=comp(patch)
 desired=before*(1-w[...,None])+target*w[...,None]
 rgb=(desired-(1-a[...,None])*BG)/np.maximum(a[...,None],1.e-4)
 changed=np.uint8(np.clip(np.rint(rgb),0,255))
 count=int(np.any(changed!=patch[...,:3],axis=2).sum())
 patch[...,:3]=changed
 return out,count
def run(save=True):
 audit=json.loads((ROOT/'evidence/p15-189-root-emergence-audit-qa.json').read_text())
 native=keyframes()
 keys={a:palette(native[a],audit['diagnostics'][f'{a:g}']['crossing']) for a in KEYS}
 baseline={}
 for a in ANGLES:
  if a in KEYS:baseline[a]=native[a].copy()
  else:
   path=P/'exports/p15-188-root-occlusion-sweep/crown_front'/(f'yaw{a:06.2f}'.replace('.','p')+'.png')
   with Image.open(path) as im:baseline[a]=np.asarray(im.convert('RGBA')).copy()
 metrics={};frames={};details={}
 for name,(radius,strength) in MODES.items():
  seq=[];observations={};seams={}
  for a in ANGLES:
   image=baseline[a];data=audit['diagnostics'][f'{a:g}']
   if a in KEYS:
    updated=image.copy();count=0
   else:
    l,r=(90.,112.5) if a<112.5 else (112.5,135.)
    t=(a-l)/(r-l)
    target=keys[l]*(1-t)+keys[r]*t
    updated,count=correct(image,data['crossing'],target,radius,strength)
   seam=color_seam(updated,updated,np.asarray(data['crossing']),np.asarray(data['tangent']))['rootContactColorDeltaRGB']
   seams[f'{a:g}']=seam
   observations[f'{a:g}']={'changedRGBPixels':count,'seam':seam,
      'alphaExact':bool(np.array_equal(updated[...,3],image[...,3])),
      'below125Exact':bool(np.array_equal(updated[125:],image[125:]))}
   seq.append(updated)
  local,global_e=local_metrics(seq)
  changes=[round(abs(seams[f'{b:g}']-seams[f'{a:g}']),4) for a,b in zip(ANGLES,ANGLES[1:])]
  metrics[name]={'maxAdjacentRootColorSeamChange':max(changes),
    'middleSeamChanges':[changes[5],changes[6]],
    'maxAdjacentLocalRGBMAE':max(local),'maxAdjacentGlobalRGBMAE':max(global_e),
    'changedRGBPixels':sum(v['changedRGBPixels'] for v in observations.values()),
    'alphaExact':all(v['alphaExact'] for v in observations.values()),
    'below125Exact':all(v['below125Exact'] for v in observations.values()),
    'nativeKeysExact':all(np.array_equal(seq[ANGLES.index(k)],native[k]) for k in KEYS)}
  frames[name]=seq;details[name]=observations
 preferred=min(MODES,key=lambda k:(metrics[k]['maxAdjacentRootColorSeamChange'],metrics[k]['maxAdjacentLocalRGBMAE']))
 qa={'schema':'KOMA_P15_191_ROOT_COLOR_V1','characterId':'p0_character_001',
   'sourceAngles':list(KEYS),'renderAngles':list(ANGLES),
   'rootAnchorVsCrossing':{f'{k:g}':{'anchor':audit['diagnostics'][f'{k:g}']['rootAnchor'],
      'crossing':audit['diagnostics'][f'{k:g}']['crossing'],
      'distance':audit['diagnostics'][f'{k:g}']['rootAnchorToCrossingPixels']} for k in KEYS},
   'nativeVisibleColorPalette':{f'{k:g}':np.round(v,3).tolist() for k,v in keys.items()},
   'methods':metrics,'details':details,'selectedDiagnosticMethod':preferred,
   'referenceDISLocalMAE':7.9475,'referenceDISGlobalMAE':6.6299,
   'sourceAssetsModified':False,'productionRendererUpdated':False,'visualAccepted':False,
   'review':'private-assets/exports/p15-191-source-root-color/index.html'}
 m=metrics[preferred]
 qa['gate']={'nativeKeysExact':all(x['nativeKeysExact'] for x in metrics.values()),
    'allAlphaExact':all(x['alphaExact'] for x in metrics.values()),
    'deepBodyExact':all(x['below125Exact'] for x in metrics.values()),
    'rootSeamImproved':m['maxAdjacentRootColorSeamChange']<metrics['original']['maxAdjacentRootColorSeamChange'],
    'localTemporalBeatsDIS':m['maxAdjacentLocalRGBMAE']<=qa['referenceDISLocalMAE'],
    'globalTemporalBeatsDIS':m['maxAdjacentGlobalRGBMAE']<=qa['referenceDISGlobalMAE'],
    'sourceRootIdentityApproved':False,'visualAccepted':False,'passes':False}
 if save:
  OUT.mkdir(parents=True,exist_ok=True)
  board=Image.new('RGB',(204*len(ANGLES),177*len(MODES)),(35,43,54));draw=ImageDraw.Draw(board)
  for row,(name,seq) in enumerate(frames.items()):
   folder=OUT/name;folder.mkdir(exist_ok=True)
   for col,(a,im) in enumerate(zip(ANGLES,seq)):
    Image.fromarray(im,'RGBA').save(folder/(f'yaw{a:06.2f}'.replace('.','p')+'.png'))
    tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(im,'RGBA'))
    board.paste(tile.crop((115,0,375,130)).resize((198,149),Image.Resampling.LANCZOS).convert('RGB'),(col*204,row*177+23))
    draw.text((col*204+3,row*177+3),f'{name} {a:g}',fill='white')
  board.save(OUT/'13-yaw-color-bridge.jpg',quality=94)
  (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P15-191 source root color</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Alpha-aware root-contact color study</h2><p>Bounded Gaussian RGB correction of intermediate views using native source-key composite colors. Source keys, alpha and deep head remain unchanged.</p><img src="13-yaw-color-bridge.jpg">')
  E.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
 return qa
if __name__=='__main__':
 q=run()
 print(json.dumps({'selected':q['selectedDiagnosticMethod'],'metrics':q['methods'],'gate':q['gate']},indent=2))

#!/usr/bin/env python3
"""P15-24 independent authored vector X-clip, five-view registration.

This is fresh programmatically hand-authored vector paint with real transparent
alpha, not a diffusion result or a copied P15-21 alpha mask. Engineering-only.
"""
from pathlib import Path
import hashlib,json,math
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from p1_front_semantic import alpha_over

R=Path(__file__).resolve().parent.parent
P=R/'private-assets'
BASE=P/'p15-21-intermediate-components'
OUT=P/'p15-24-reference-conditioned'
OUT.mkdir(parents=True,exist_ok=True)
QA=R/'evidence/p15-24-vector-cross-clip-qa.json'
ART='hair.clip.cross_gold'
ANG=[55,57.5,60,62.5,65]
SOURCE45=P/'p15-20-canonical-source-views/yaw045/hair.clip.cross_gold.png'

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def draw_rod(draw,path,degree,thickness):
 # path already transformed into high-res coordinates
 def line(w,color,offset=0):
  if offset:
   x,y=offset
   xy=[(a+x,b-y) for a,b in path]
  else:xy=path
  draw.line(xy,fill=color,width=w,joint='curve')
  r=w/2
  for x,y in (xy[0],xy[-1]):
   draw.ellipse((round(x-r),round(y-r),round(x+r),round(y+r)),fill=color)
 line(thickness+10,(94,46,65,255))
 line(thickness+5,(129,72,49,255))
 line(thickness,(202,140,52,255))
 line(thickness-5,(240,187,78,255),offset=(-1,-1))
 line(max(3,thickness//5),(255,233,151,255),offset=(-3,-2))
 # thin uneven warm lower-edge line to give hand-painted cel bevel
 line(max(2,thickness//7),(251,214,118,230),offset=(2,1))

def create_raw(foreshorten):
 S=512
 art=Image.new('RGBA',(S,S),(0,0,0,0))
 d=ImageDraw.Draw(art,'RGBA')
 # Deliberately new X-shaped two-rod geometry. Source P0 determines topology,
 # crossing direction, warm gold palette, not raster pixel shape.
 rods=[
  [(115,128),(245,242),(373,350)],
  [(313,67),(271,207),(191,441)]
 ]
 # decreasing projected width for profile tilt (5 angles across 55..65)
 def tr(x,y):
  return (round(256+(x-256)*foreshorten),y)
 for n,rod in enumerate(rods):
  path=[tr(x,y) for x,y in rod]
  draw_rod(d,path,n,59 if n==0 else 56)
 # small crossing glint at intersection
 cx,cy=tr(264,254)
 d.ellipse((cx-11,cy-11,cx+11,cy+11),fill=(252,219,131,180))
 d.ellipse((cx-5,cy-5,cx+5,cy+5),fill=(255,242,178,225))
 return art

def run():
 source_manifest=json.loads((R/'evidence/p15-21-intermediate-components-qa.json').read_text())
 outputs=[]
 for angle in ANG:
  slug='yaw'+(str(int(angle)) if float(angle).is_integer() else str(angle).replace('.','p'))
  original=BASE/slug/(ART+'.png')
  orig=np.array(Image.open(original).convert('RGBA'))
  bbox=Image.fromarray(orig[:,:,3],'L').getbbox()
  if not bbox:raise ValueError(slug+' clip missing')
  x0,y0,x1,y1=bbox
  targetw=x1-x0;targeth=y1-y0
  # Within the exact P15-21 registration envelope, not identical silhouette.
  w=max(5,int(targetw*.88));h=max(5,int(targeth*.9))
  center=((x0+x1)/2,(y0+y1)/2)
  raw=create_raw(foreshorten=1-(angle-55)*.009)
  # Crop the newly painted geometry rather than copied-alpha mask
  content=raw.getchannel('A').getbbox()
  raw=raw.crop(content)
  scaled=raw.resize((w,h),Image.Resampling.LANCZOS)
  reg=Image.new('RGBA',(1024,1024),(0,0,0,0))
  px=round(center[0]-w/2);py=round(center[1]-h/2)
  reg.alpha_composite(scaled,(px,py))
  rowdir=OUT/slug;rowdir.mkdir(exist_ok=True)
  dest=rowdir/(ART+'.png');reg.save(dest)
  a=np.asarray(reg)[:,:,3]>16
  b=orig[:,:,3]>16
  area=int(np.count_nonzero(a))
  if area<100:raise AssertionError('empty independent stroke image')
  if np.array_equal(np.asarray(reg)[:,:,3],orig[:,:,3]):raise AssertionError('alpha copied from source')
  inter=int(np.count_nonzero(a&b));union=int(np.count_nonzero(a|b))
  rows=next(f for f in source_manifest['frames'] if f['yaw']==angle)['roles']
  # Correctly composite P8/P12 at native 443px, then resize once to 1024.
  # Compositing 1024px per-layer rescales produces unrelated pixel errors.
  W=443
  current=np.zeros((W,W,4),np.uint8)
  baseline=np.zeros_like(current)
  registered_native=np.asarray(reg.resize((W,W),Image.Resampling.LANCZOS))
  for layer in rows:
   arr=np.array(Image.open(P/layer['native']).convert('RGBA'))
   if arr.shape!=(W,W,4):raise AssertionError('Unexpected native layer')
   baseline=alpha_over(baseline,arr)
   if layer['role']==ART:arr=registered_native
   current=alpha_over(current,arr)
  baseline=np.asarray(Image.fromarray(baseline,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS))
  current=np.asarray(Image.fromarray(current,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS))
  baseline_path=P/'p15-21-layered-anatomy'/(slug+'.png')
  baseline_actual=np.array(Image.open(baseline_path).convert('RGBA'))
  comp=rowdir/'diagnostic-with-painted-clip.png'
  Image.fromarray(current,'RGBA').save(comp)
  outputs.append({'angle':angle,'role':ART,'path':str(dest.relative_to(P)),
    'pathSHA256':sha(dest),'diagnostic':str(comp.relative_to(P)),
    'diagnosticSHA256':sha(comp),'referenceOriginalClip45SHA256':sha(SOURCE45),
    'priorVddClipSHA256':sha(original),'baselineCompositeDiffPixels':
      int(np.count_nonzero(np.any(baseline.astype('int16')!=baseline_actual.astype('int16'),axis=2))),
    'alphaChangedFromVDD':True,'paintedVisiblePixels':area,
    'clipAlphaIoUWithVDD':round(inter/max(1,union),5),
    'sourcePaint': 'NEW_PROGRAMMATIC_VECTOR_STROKES',
    'alphaOrigin':'NEW_VECTOR_STROKE_GEOMETRY',
    'productionPromoted':False})
 q={'schema':'KOMA-P15-24-REFERENCE_CONDITIONED-CLIP-VECTOR-V1',
    'characterId':'p0_character_001','sourceHeroIdentity':'P0 canonical cross-gold clip 45°',
    'sourceHeroClip45SHA256':sha(SOURCE45),
    'newDrawingMethod':'NEW_ORIGINAL_VECTOR_STROKES_COLOR_GUIDED_BY_P0_45_SOURCE',
    'notDiffusionOutput':True,
    'imagesGenerated':len(outputs),'semanticRolesCreated':[ART],
    'rolesAccepted':0,'hiddenUnderpaintAccepted':0,
    'artisticAcceptance':False,'referenceEditAttempt':'ZERO_GPU_QUOTA_EXCEEDED',
    'angles':ANG,'results':outputs,'productionVDDUnchanged':True,
    'next':'Visual approval of crossed gold clip and independent AI/brush painted far eye/hair; per-layer underpainting before VDD promotion'}
 QA.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'frames':len(outputs),
    'visiblePixels':[r['paintedVisiblePixels'] for r in outputs],
    'alphaIoU':[r['clipAlphaIoUWithVDD'] for r in outputs],
    'newClipAlpha':all(r['alphaChangedFromVDD'] for r in outputs),
    'artisticApproved':q['rolesAccepted'],
    'baselineRegroupPixelChanges':[r['baselineCompositeDiffPixels'] for r in outputs]},
     ensure_ascii=False))
if __name__=='__main__':run()

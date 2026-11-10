#!/usr/bin/env python3
"""P15-25 new source-guided procedural painted keypart candidates. NOT artist approved."""
import hashlib,json,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from p1_front_semantic import alpha_over
R=Path(__file__).resolve().parent.parent
P=R/'private-assets'
OUT=P/'p15-25-procedural-paint';OUT.mkdir(parents=True,exist_ok=True)
ANGLES=[55,57.5,60,62.5,65]
ROLES=['hair.side','hair.ahoge','eye.far']
C={'pink':(191,126,165,255),'light':(228,171,201,255),'dark':(140,82,137,255),
'edge':(83,47,99,255),'iris':(166,84,163,255),'pupil':(80,36,111,255)}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def curve(a,b,c,d,n=25):
 out=[]
 for i in range(n+1):
  t=i/n;u=1-t
  out.append((round(u**3*a[0]+3*u*u*t*b[0]+3*u*t*t*c[0]+t**3*d[0]),
              round(u**3*a[1]+3*u*u*t*b[1]+3*u*t*t*c[1]+t**3*d[1])))
 return out
def paint(role,angle):
 im=Image.new('RGBA',(512,512),(0,0,0,0));d=ImageDraw.Draw(im,'RGBA')
 t=(angle-55)/10
 if role=='hair.side':
  path=curve((325,34),(420,115),(417,250),(449,425))+curve((449,425),(385,439),(319,469),(267,505))
  path+=curve((267,505),(290,402),(250,360),(235,280))+curve((235,280),(197,205),(270,65),(325,34))
  d.polygon(path,fill=C['pink']);d.line(path+[path[0]],fill=C['edge'],width=9,joint='curve')
  shade=curve((335,57),(408,143),(396,305),(415,419))+curve((415,419),(371,418),(321,447),(299,478))
  shade+=curve((299,478),(337,342),(307,183),(335,57))
  d.polygon(shade,fill=C['dark'])
  d.line(curve((300,101),(310,212),(343,284),(320,435)),fill=C['light'],width=15,joint='curve')
  d.line(curve((315,76),(365,198),(355,284),(366,399)),fill=(249,199,224,255),width=7)
  lock=curve((234,222),(211,315),(250,411),(211,495))+curve((211,495),(251,482),(275,448),(287,427))
  lock+=curve((287,427),(273,340),(259,272),(234,222))
  d.polygon(lock,fill=C['pink']);d.line(lock+[lock[0]],fill=C['edge'],width=7)
 elif role=='hair.ahoge':
  path=curve((282,490),(252,380),(156,230),(103+20*t,65))
  path+=curve((103+20*t,65),(154,120),(202,124),(234,167))
  path+=curve((234,167),(290,245),(292,379),(324,490))
  d.polygon(path,fill=C['pink']);d.line(path+[path[0]],fill=C['edge'],width=10,joint='curve')
  d.line(curve((271,460),(255,330),(197,216),(136+20*t,100)),fill=C['light'],width=8)
 elif role=='eye.far':
  shrink=1-.24*t
  def X(x):return 256+round((x-256)*shrink)
  upper=curve((X(65),245),(X(155),147),(X(358),169),(X(451),248))
  lower=curve((X(451),248),(X(333),307),(X(173),326),(X(65),245))
  d.polygon(upper+lower,fill=(249,229,246,255))
  d.line(upper,fill=C['edge'],width=19,joint='curve')
  d.line(lower,fill=C['dark'],width=8,joint='curve')
  d.ellipse((X(200),205,X(320),339),fill=C['iris'],outline=C['edge'],width=8)
  d.ellipse((X(246),236,X(285),318),fill=C['pupil'])
  d.ellipse((X(215),228,X(248),260),fill=(255,247,255,255))
  d.line(curve((X(90),172),(X(210),124),(X(330),139),(X(415),175)),fill=C['edge'],width=8)
 else:raise ValueError(role)
 return im
def register(role,angle,bbox):
 art=paint(role,angle)
 bb=art.getchannel('A').getbbox()
 if not bb:raise ValueError('empty '+role)
 x0,y0,x1,y1=bbox
 art=art.crop(bb).resize((x1-x0,y1-y0),Image.Resampling.LANCZOS)
 result=Image.new('RGBA',(1024,1024),(0,0,0,0))
 result.alpha_composite(art,(x0,y0))
 return result
def run():
 q21=json.loads((R/'evidence/p15-21-intermediate-components-qa.json').read_text())
 frames=[]
 for angle in ANGLES:
  slug='yaw'+(str(int(angle)) if angle%1==0 else str(angle).replace('.','p'))
  rows=next(f['roles'] for f in q21['frames'] if f['yaw']==angle)
  dest=OUT/slug;dest.mkdir(exist_ok=True)
  new={};parts=[]
  for role in ROLES:
   old=np.asarray(Image.open(P/'p15-21-intermediate-components'/slug/(role+'.png')).convert('RGBA'))
   bbox=Image.fromarray(old[:,:,3],'L').getbbox()
   art=register(role,angle,bbox)
   file=dest/(role+'.png');art.save(file)
   pixels=np.asarray(art);a=pixels[:,:,3]>16;b=old[:,:,3]>16
   if np.array_equal(old[:,:,3],pixels[:,:,3]):raise AssertionError('Alpha copied: '+role)
   iou=np.count_nonzero(a&b)/max(1,np.count_nonzero(a|b))
   parts.append({'role':role,'path':str(file.relative_to(P)),'sha256':sha(file),
      'visiblePixels':int(a.sum()),'alphaIoU':round(iou,5),'alphaFromVDD':False,
      'registeredBBox':list(bbox),'artApproved':False})
   new[role]=np.asarray(art.resize((443,443),Image.Resampling.LANCZOS))
  old_comp=np.zeros((443,443,4),np.uint8)
  new_comp=np.zeros_like(old_comp)
  for layer in rows:
   arr=np.asarray(Image.open(P/layer['native']).convert('RGBA'))
   old_comp=alpha_over(old_comp,arr)
   new_comp=alpha_over(new_comp,new.get(layer['role'],arr))
  old_full=np.asarray(Image.fromarray(old_comp,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS))
  actual=np.asarray(Image.open(P/'p15-21-layered-anatomy'/(slug+'.png')).convert('RGBA'))
  if not np.array_equal(old_full,actual):raise AssertionError('Baseline reconstruction failed at '+slug)
  comp=dest/'diagnostic-three-part-composite.png'
  Image.fromarray(new_comp,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS).save(comp)
  changed=np.asarray(Image.open(comp).convert('RGBA'))
  a=actual[:,:,3]>16;b=changed[:,:,3]>16
  frames.append({'angle':angle,'parts':parts,'diagnostic':str(comp.relative_to(P)),
       'diagnosticSHA256':sha(comp),'baselineExact':True,
       'compositeAlphaIoU':round(np.count_nonzero(a&b)/max(1,np.count_nonzero(a|b)),5)})
 report={'schema':'KOMA-P15-25-NEW-PAINTED-PROCEDURAL-KEYPARTS-V1',
  'characterId':'p0_character_001','roles':ROLES,'angles':ANGLES,
  'sourceMethod':'NEW_PROCEDURAL_VECTOR_STROKES_P0_PALETTE_VDD_BBOX_GUIDES',
  'independentPaintedGeometry':True,'actualAIModelPainting':False,
  'inheritedVddAlpha':False,'hiddenFarEyeIrisPixelsDrawn':True,
  'hiddenFarEyeOcclusionCorrectnessVerified':False,
  'productionVddModified':False,'artisticAcceptance':False,
  'independentPartsArtisticallyApproved':0,
  'frames':frames,'next':'Human-grade art and depth/occlusion approval needed before promotion'}
 (R/'evidence/p15-25-original-keypart-paint-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'frames':len(frames),'newPartFiles':sum(len(f['parts']) for f in frames),
  'compositeAlphaIoU':[f['compositeAlphaIoU'] for f in frames],
  'baselineExact':all(f['baselineExact'] for f in frames)},ensure_ascii=False))
if __name__=='__main__':run()

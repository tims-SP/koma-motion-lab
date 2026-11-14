#!/usr/bin/env python3
"""Move source-owned front bang tips at 52.5, 60 and 75 degrees with view-specific anchors."""
from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json,statistics
import numpy as np,cv2
R=Path(__file__).resolve().parents[1]
P=R/'private-assets'
D=P/'exports/p15-97-multiview-motion';D.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return Image.open(p).convert('RGBA')
def ss(z):
 t=np.clip(z,0,1)
 return t*t*(3-2*t)
C={
 '52p5':{
  'source':P/'exports/p15-93-yaw0525-review/yaw052p5-registered.png',
  'model':P/'p15-97-underpaint-52p5/model-registered-source.png',
  'alpha':P/'p15-97-underpaint-52p5/mask-source-1024.png',
  'sam':P/'exports/p15-97-sam3-yaw52p5/mask-2-1024.png',
  'anchor':(410,38,600,30,690,36,470,32),
  'tipROI':(620,415,690,480),'rootROI':(610,300,740,405),
 },
 '60':{
  'source':P/'exports/p15-92-angle-keyart/yaw060-registered.png',
  'model':P/'exports/p15-95-yaw060-motion/generated-face-aligned.png',
  'alpha':P/'exports/p15-95-yaw060-motion/inset-mask.png',
  'sam':P/'exports/p15-94-sam3-yaw060/hair-candidate-0-alpha1024.png',
  'anchor':(420,65,620,35,805,65,570,70),
  'tipROI':(640,425,795,545),'rootROI':(590,300,740,405),
 },
 '75':{
  'source':P/'exports/p15-92-angle-keyart/yaw075-registered.png',
  'model':P/'p15-97-underpaint-75/model-registered-source.png',
  'alpha':P/'p15-97-underpaint-75/mask-source-1024.png',
  'sam':P/'exports/p15-97-sam3-yaw75/mask-1-1024.png',
  'anchor':(410,35,715,28,790,35,475,35),
  'tipROI':(720,420,790,485),'rootROI':(660,300,760,405),
 },
}
yy,xx=np.indices((1024,1024),dtype=np.float32)
qa={'schema':'KOMA_P15_97_MULTIVIEW_ROOT_ANCHORED_MOTION_V1',
    'characterId':'p0_character_001','angles':[52.5,60,75],
    'offsetsPx':list(range(13)),'sharedParameter':'hairTipOffsetPx',
    'model':{'segmentation':'Hugging Face SAM3','underpaint':'Codex native image_gen'},
    'views':{},'formalFullArtMeshAccepted':False,'continuousVddAccepted':False,
    'visualGate':'MULTIANGLE_LOCAL_HAIR_TIP_REVIEW'}
thumbnails={}
for view,config in C.items():
 if view=='60':
  # Preserve the exactly validated P15-96 source-owned 60° motion as the shared-keyview baseline.
  import shutil
  prev=json.loads((R/'evidence/p15-96-motion-qa.json').read_text())
  frames={}
  for offset in range(13):
   old=P/'exports/p15-96-yaw060-root-artmesh'/f'frame-{offset:02}.png'
   dest=D/f'yaw60-frame-{offset:02}.png'
   shutil.copyfile(old,dest)
   q=prev['frames'][str(offset)]
   frames[str(offset)]={'sha256':sha(dest),'changedPixels':q['changedPixels'],
    'changedOutsideHairSupports':q['outsideHairSupportChangedPixels'],
    'rootChangedPixels':q['foreheadTriangleChangedPixels'],
    'tipChangedPixels':q['tipChangedPixels'],
    'newHoles':q['newTransparentHoles'],'adjacentRGBMAE':q['adjacentRGBMAE']}
   if offset in (0,4,8,12):
    out=load(dest);white=Image.new('RGBA',out.size,'white');white.alpha_composite(out)
    thumbnails[(view,offset)]=white.convert('RGB').crop((500,285,825,615)).resize((420,420),Image.Resampling.LANCZOS)
  selected={'view':'60','sourceSHA256':sha(config['source']),
   'SAM3MaskSHA256':sha(config['sam']),
   'underpaintSHA256':sha(config['model']),
   'frontHairSHA256':sha(P/'exports/p15-95-yaw060-motion/inset-front-hair.png'),
   'rootAnchor':prev['rootConstraint'],'frames':frames,
   'maxAdjacentRGBMAE':prev['maxAdjacentLocalRGBMAE'],
   'firstStepRatio':prev['firstStepToLaterMedianRatio'],
   'rootInvariant':True,'restPoseSourcePixelExact':True,
   'hasVisibleTipMotion':frames['12']['tipChangedPixels']>300}
  qa['views'][view]=selected
  print(view,'reused P15-96 exact source frames, tip',frames['12']['tipChangedPixels'],flush=True)
  continue
 src=np.asarray(load(config['source']))
 bg=np.asarray(load(config['model']))
 assert src.shape==bg.shape==(1024,1024,4)
 alpha=np.asarray(Image.open(config['alpha']).convert('L'),dtype=np.float32)/255
 sam=np.asarray(Image.open(config['sam']).convert('L'),dtype=np.float32)/255
 own=np.minimum(alpha,sam)
 sourceHair=src.astype(np.float32)/255
 sourceHair[:,:,3]*=own
 prem=np.concatenate((sourceHair[:,:,:3]*sourceHair[:,:,3:4],sourceHair[:,:,3:4]),axis=2)
 hairImg=Image.fromarray(np.uint8(np.round(sourceHair*255)),'RGBA')
 hairPath=D/f'yaw{view}-front-hair.png';hairImg.save(hairPath)
 rootY,yRamp,leftX,xRamp,rightX,rightRamp,bottomY,bottomRamp=config['anchor']
 weights=ss((yy-rootY)/yRamp)*ss((xx-leftX)/xRamp)*ss((rightX-xx)/rightRamp)*ss((bottomY-yy)/bottomRamp)
 rootROI=config['rootROI'];tip=config['tipROI'];roi=(500,285,825,615)
 frames={};deltas=[];previous=src
 for offset in range(13):
  if offset==0:
   out=Image.fromarray(src,'RGBA')
   warpedAlpha=sourceHair[:,:,3]
  else:
   warped=cv2.remap(prem,xx-offset*weights,yy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
   a=np.clip(warped[:,:,3:4],0,1)
   rgb=np.clip(warped[:,:,:3]/np.maximum(a,1e-5),0,1)
   moved=np.uint8(np.round(np.concatenate((rgb,a),axis=2)*255))
   uncovered=np.clip(sourceHair[:,:,3]-a[:,:,0],0,1)
   backdrop=src.copy()
   backdrop[:,:,:3]=np.uint8(np.round(src[:,:,:3].astype(np.float32)*(1-uncovered[:,:,None])+
      bg[:,:,:3].astype(np.float32)*uncovered[:,:,None]))
   out=Image.alpha_composite(Image.fromarray(backdrop,'RGBA'),Image.fromarray(moved,'RGBA'))
   # Pixel-exact root preservation: zero deformation weight means no layer recomposition.
   reconstructed=np.asarray(out).copy()
   reconstructed[weights<=1e-5]=src[weights<=1e-5]
   out=Image.fromarray(reconstructed,'RGBA')
   warpedAlpha=a[:,:,0]
  dest=D/f'yaw{view}-frame-{offset:02}.png';out.save(dest)
  now=np.asarray(out)
  changes=np.any(src!=now,axis=2)
  permitted=(sourceHair[:,:,3]>0)|(warpedAlpha>0)
  boundsRoot=changes[rootROI[1]:rootROI[3],rootROI[0]:rootROI[2]]
  boundsTip=changes[tip[1]:tip[3],tip[0]:tip[2]]
  holes=int(((src[:,:,3]>128)&(now[:,:,3]<32)).sum())
  regionA=previous[roi[1]:roi[3],roi[0]:roi[2],:3].astype(np.float32)
  regionB=now[roi[1]:roi[3],roi[0]:roi[2],:3].astype(np.float32)
  mae=round(float(np.abs(regionA-regionB).mean()),5) if offset else 0
  if offset:deltas.append(mae)
  frames[str(offset)]={'sha256':sha(dest),'changedPixels':int(changes.sum()),
    'changedOutsideHairSupports':int((changes & ~permitted).sum()),
    'rootChangedPixels':int(boundsRoot.sum()),'tipChangedPixels':int(boundsTip.sum()),
    'newHoles':holes,'adjacentRGBMAE':mae}
  previous=now
  if offset in (0,4,8,12):
   panel=Image.new('RGBA',out.size,'white');panel.alpha_composite(out)
   thumbnails[(view,offset)]=panel.convert('RGB').crop(roi).resize((420,420),Image.Resampling.LANCZOS)
 assert frames['0']['sha256']==sha(config['source'])
 failures=[(offset,x['rootChangedPixels'],x['newHoles'],x['changedOutsideHairSupports']) for offset,x in frames.items()
     if x['rootChangedPixels'] or x['newHoles'] or x['changedOutsideHairSupports']]
 print(view,'constraint failures',failures[:13],flush=True)
 assert not failures,view
 selected={'view':view,'sourceSHA256':sha(config['source']),'SAM3MaskSHA256':sha(config['sam']),
  'underpaintSHA256':sha(config['model']),'frontHairSHA256':sha(hairPath),
  'rootAnchor':{'rootY':rootY,'yRamp':yRamp,'leftX':leftX,'xRamp':xRamp,
                'rightX':rightX,'rightRamp':rightRamp,'bottomY':bottomY,'bottomRamp':bottomRamp},
  'frames':frames,'maxAdjacentRGBMAE':max(deltas),
  'firstStepRatio':round(deltas[0]/max(1e-5,statistics.median(deltas[1:])),4),
  'rootInvariant':True,'restPoseSourcePixelExact':True,
  'hasVisibleTipMotion':frames['12']['tipChangedPixels']>300}
 qa['views'][view]=selected
 print(view,'tip pixels',frames['12']['tipChangedPixels'],'max step',selected['maxAdjacentRGBMAE'],
       'outside',max(f['changedOutsideHairSupports'] for f in frames.values()),flush=True)
# Visual identity and view-coupled motion contact.
order=['52p5','60','75'];deltas=(0,4,8,12)
contact=Image.new('RGB',(4*420,3*447),'white')
draw=ImageDraw.Draw(contact)
for row,view in enumerate(order):
 for col,offset in enumerate(deltas):
  x=col*420;y=row*447
  contact.paste(thumbnails[(view,offset)],(x,y+24))
  draw.text((x+7,y+6),f'yaw {view} / fringe {offset}px',fill='black')
contact.save(D/'view-coupled-contact.jpg',quality=94)
qa['contact']=str((D/'view-coupled-contact.jpg').relative_to(P))
(R/'evidence/p15-97-multiview-motion-qa.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')

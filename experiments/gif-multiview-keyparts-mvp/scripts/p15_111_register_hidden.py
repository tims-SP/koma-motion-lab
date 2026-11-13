#!/usr/bin/env python3
"""Register six genuine imagegen hidden-surface garment illustrations.

Six model-native transparent images remain byte-exact. Registration uses
color/material centroids from each known real source, then limits alpha
to physically occluded bow-brooch and collar-under-bow areas. Each layer
is one transparent image per view and garment component.

The artwork is an *inferred* continuation of non-observed hidden surfaces.
Geometry and material checks do not imply anatomical correctness.
"""
from pathlib import Path
from hashlib import sha256
from PIL import Image,ImageDraw
import cv2,json,numpy as np
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
N=R/'private-assets/p15-111-hidden-art';D=P/'p15-111-hidden-registered';D.mkdir(parents=True,exist_ok=True)
refQ=json.loads((R/'evidence/p15-108-stroke-qa.json').read_text())
srcQ=json.loads((R/'evidence/p15-110-vision-qa.json').read_text())
sha=lambda f:sha256(Path(f).read_bytes()).hexdigest()
views=['60','67p5','75'];viewKeys={'60':'60','67p5':'67.5','75':'75'}
material={'bow':'crimson ribbon textile','collar':'white collar and shirt fabric'}
HSV_ROI={
 'collar':(635,835,370,790),
 'bow':(760,1017,460,790)}
def colored(rgb,role):
 hsv=cv2.cvtColor(rgb[:,:,:3],cv2.COLOR_RGB2HSV);h,s,v=cv2.split(hsv)
 opaque=rgb[:,:,3]>90
 if role=='bow':
  return (((h>=150)|(h<=8))&(s>=55)&(v>40)&opaque)
 return ((s<120)&(v>118)&(rgb[:,:,2]>=rgb[:,:,0]-38)&opaque)
def centroid(mask,roi):
 y0,y1,x0,x1=roi
 crop=np.zeros(mask.shape,np.uint8);crop[y0:y1,x0:x1]=np.uint8(mask[y0:y1,x0:x1])
 ys,xs=np.where(crop)
 if len(xs)<125:raise ValueError(('insufficient material pixels',roi,len(xs)))
 return np.array([float(xs.mean()),float(ys.mean())]),len(xs)
record={'schema':'KOMA_P15_111_GENUINE_OCCLUDED_MATERIAL_ART_V1',
 'character':'p0_character_001','sourceAngles':[60,67.5,75],
 'artSource':'Codex builtin image_gen.imagegen',
 'meaning':'source-conditioned illustrated continuation of non-observed garment material',
 'nativeSourcePreserved':True,
 'sourceImageSHA256':{v:z['sha256'] for v,z in srcQ['sourceImages'].items()},
 'hiddenMaterialIsObservedGroundTruth':False,
 'layers':{},'sourceMasks':{}}
contact=Image.new('RGB',(4*420,3*390),'white');draw=ImageDraw.Draw(contact)
for row,view in enumerate(views):
 key=viewKeys[view]
 srcPath=R/srcQ['sourceImages'][key]['path']
 src=np.asarray(Image.open(srcPath).convert('RGBA'))
 base=Image.new('RGBA',(1024,1024),'white');base.alpha_composite(Image.fromarray(src,'RGBA'))
 col=base.convert('RGB').crop((345,625,840,1015)).resize((420,365),Image.Resampling.LANCZOS)
 contact.paste(col,(0,row*390+23));draw.text((7,row*390+5),f'{key} original source',fill='black')
 owner=refQ['views'][key]['layers']
 bowMask=np.asarray(Image.open(R/owner['bowFabric']['maskPath']).convert('L'))>128
 gemMask=np.asarray(Image.open(R/owner['jewel']['maskPath']).convert('L'))>128
 cx,cy=srcQ['roles']['bow.left_outer_outline']['sourceView'][key]['points'][-1]
 # Original source-defined jewel foreground + collar region support.
 jx,jy={'60':(634.46,810.55),'67p5':(639.29,808.82),'75':(644.12,807.09)}[view]
 y,x=np.indices((1024,1024))
 nearJewel=((x-jx)**2/(34**2)+(y-jy)**2/(38**2)<=1)
 jewelTarget=gemMask&nearJewel
 collarRegion=(np.abs(x-jx)<107)&(y>690)&(y<905)
 collarTarget=bowMask&collarRegion
 assert int(jewelTarget.sum())>30 and int(collarTarget.sum())>250,(view,int(jewelTarget.sum()),int(collarTarget.sum()))
 targets={'bow':jewelTarget,'collar':collarTarget}
 record['layers'][key]={}
 record['sourceMasks'][key]={
  'jewelForegroundPath':owner['jewel']['maskPath'],
  'bowForegroundPath':owner['bowFabric']['maskPath'],
  'hiddenBowTestPixels':int(jewelTarget.sum()),
  'hiddenCollarTestPixels':int(collarTarget.sum())}
 for colidx,role in enumerate(('collar','bow'),start=1):
  native=N/f'yaw{view}-{role}-native.png'
  assert native.is_file(),native
  img=Image.open(native)
  assert img.mode=='RGBA' and min(img.size)>=1024,(native,img.mode,img.size)
  raw=np.asarray(img)
  nativeBox=img.getbbox()
  normalized=np.asarray(img.resize((1024,1024),Image.Resampling.LANCZOS))
  materialMask=colored(normalized,role)
  refMaterial=colored(src,role)
  roi=HSV_ROI[role]
  targetCenter,targetCount=centroid(refMaterial,roi)
  candidateCenter,candidateCount=centroid(materialMask,roi)
  shift=targetCenter-candidateCenter
  # Keep original art provenance exact and reject wildly misplaced native output.
  if max(np.abs(shift))>95:raise ValueError(('registration inconsistent with native art',view,role,shift.tolist()))
  matrix=np.float32([[1,0,shift[0]],[0,1,shift[1]]])
  reg=cv2.warpAffine(normalized,matrix,(1024,1024),flags=cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
  # Native output can include blurry alpha fringe; crop only to known body region.
  reg[:590,:,:]=0;reg[:,:320,:]=0;reg[:,890:,:]=0
  reg[:,:,3][reg[:,:,3]<=7]=0
  registered=D/f'yaw{view}-{role}-registered.png'
  Image.fromarray(reg,'RGBA').save(registered)
  visibility=targets[role]
  alpha=reg[:,:,3]>70
  valid=int((alpha&visibility).sum());total=int(visibility.sum())
  hidden=reg.copy()
  hidden[:,:,3]=np.uint8(hidden[:,:,3].astype(np.float32)*visibility)
  only=D/f'yaw{view}-{role}-hidden.png'
  Image.fromarray(hidden,'RGBA').save(only)
  # Original source and underpainting on white to inspect material alignment.
  render=Image.new('RGBA',(1024,1024),'white');render.alpha_composite(Image.fromarray(reg,'RGBA'))
  vis=render.convert('RGB').crop((345,625,840,1015)).resize((420,365),Image.Resampling.LANCZOS)
  contact.paste(vis,(colidx*420,row*390+23));draw.text((colidx*420+5,row*390+5),view+' '+role+' material',fill='black')
  record['layers'][key][role]={
   'nativePath':str(native.relative_to(R)),'nativeSHA256':sha(native),
   'nativeDimensions':list(img.size),'nativeMode':img.mode,
   'nativeAlphaBBox':nativeBox,
   'registeredPath':str(registered.relative_to(R)),'registeredSHA256':sha(registered),
   'hiddenOnlyPath':str(only.relative_to(R)),'hiddenOnlySHA256':sha(only),
   'sourceMaterialCenter':targetCenter.round(3).tolist(),
   'nativeNormalizedMaterialCenter':candidateCenter.round(3).tolist(),
   'registrationShift1024':shift.round(3).tolist(),
   'colorMaterialSourcePixels':targetCount,
   'colorMaterialGeneratedPixels':candidateCount,
   'hiddenTargetPixels':total,'hiddenCoveragePixels':valid,
   'hiddenCoverageFraction':round(valid/max(total,1),5),
   'sourceArtOriginalUnchanged':True}
  print('REGISTER',key,role,'shift',shift.round(1),'coverage',round(valid/total,3),
        'sourceRGB',targetCount,'genRGB',candidateCount,flush=True)
 # Comparison underlay revelation for one known hidden zone: not animation.
 composite=src.copy()
 for role,target in targets.items():
  fill=np.asarray(Image.open(D/f'yaw{view}-{role}-hidden.png').convert('RGBA'))
  opaque=fill[:,:,3]>70
  # Create matte-only reveal, preserving everything outside named source occluders.
  use=target&opaque
  composite[use]=fill[use]
 reveal=Image.new('RGBA',(1024,1024),'white')
 reveal.alpha_composite(Image.fromarray(composite,'RGBA'))
 contact.paste(reveal.convert('RGB').crop((345,625,840,1015)).resize((420,365),Image.Resampling.LANCZOS),
              (3*420,row*390+23))
 draw.text((3*420+5,row*390+5),view+' hidden-surface reveal',fill='black')
 Image.fromarray(composite,'RGBA').save(D/f'yaw{view}-source-reveal.png')
record['nativeImageCount']=6
record['sourceViewsRegistered']=3
record['contact']='private-assets/exports/p15-111-hidden-registered/underpaint-source-contact.jpg'
contact.save(D/'underpaint-source-contact.jpg',quality=94)
(R/'evidence/p15-111-source-qa.json').write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n')
print('SOURCE_QA',record['contact'],flush=True)

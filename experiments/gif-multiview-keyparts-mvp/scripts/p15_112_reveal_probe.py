#!/usr/bin/env python3
"""P0 source-native 3-view local occlusion/disocclusion geometry proof.

Displace source-owned bow or jewel on its actual 1024 canvas. Use 6 newly
AI-generated hidden-surface layers solely behind the original occluders,
never over visible source fabric. Compare same displacement with/without
hidden layers and quantify newly exposed owner pixels, inferred donor ink,
and visible alpha coverage. This isolates the mechanism from full-yaw
cross-view correspondence, which is still not artist-verified.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import numpy as np,cv2,json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-112-occlusion-probe';D.mkdir(parents=True,exist_ok=True)
Own=json.loads((R/'evidence/p15-108-stroke-qa.json').read_text())
Art=json.loads((R/'evidence/p15-111-source-qa.json').read_text())
sha=lambda p:sha256(Path(p).read_bytes()).hexdigest()
SIZE=1024
views=['60','67.5','75']
poses=[('neutral',0,0),('bow_left',-10,0),('bow_right',10,0),
       ('jewel_left',0,-7),('jewel_right',0,7)]
def load(path):
 return np.asarray(Image.open(path).convert('RGBA'))
def pre(image):
 f=image.astype(np.float32)/255.
 return np.concatenate((f[:,:,:3]*f[:,:,3:4],f[:,:,3:4]),axis=2)
def unpre(p):
 a=np.clip(p[:,:,3:4],0,1)
 rgb=np.clip(p[:,:,:3]/np.maximum(a,1e-6),0,1)
 return np.uint8(np.round(np.concatenate((rgb,a),axis=2)*255))
def over(a,b):
 alpha=b[:,:,3:4]
 return np.concatenate((b[:,:,:3]+a[:,:,:3]*(1-alpha),alpha+a[:,:,3:4]*(1-alpha)),axis=2)
def shift(image,delta):
 mat=np.float32([[1,0,delta],[0,1,0]])
 return cv2.warpAffine(image,mat,(SIZE,SIZE),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,
                       borderValue=(0,0,0,0))
report={'schema':'KOMA_P15_112_SOURCE_OCCLUSION_REVEAL_QA_V1',
 'characterId':'p0_character_001','sourceAngles':[60,67.5,75],
 'poseLabels':[x[0] for x in poses],
 'mechanism':'source-owned 1024x1024 alpha mattes with separate bow, jewel and inferred underpaint layers',
 'sourceVisibleArtUnchanged':True,
 'viewRecords':{},'sourcePixelReconstructionTolerance':'RGBA MAE per-channel at zero displacement',
 'artisticHiddenSurfaceApproval':False}
contact=Image.new('RGB',(420*len(poses),365*len(views)*2),'white')
drawer=ImageDraw.Draw(contact)
for row,view in enumerate(views):
 layers={}
 for role,z in Own['views'][view]['layers'].items():
  layers[role]=pre(load(R/z['texturePath']))
 for role,z in Art['layers'][view].items():
  layers[role+'Under']=pre(load(R/z['hiddenOnlyPath']))
 raw=load(R/Own['views'][view]['source'])
 origAlphaBow=layers['bowFabric'][:,:,3]
 origAlphaJewel=layers['jewel'][:,:,3]
 rec={'sourceImage':Own['views'][view]['source'],
      'sourceSHA256':Own['views'][view]['sourceSHA256'],
      'hiddenArtSHA256':{k:z['nativeSHA256'] for k,z in Art['layers'][view].items()},
      'poseMetrics':{},'files':{}}
 def compose(bowDx,jewelDx,hidden):
  layersOut={
   'background':layers['background'],'goldTrim':layers['goldTrim'],
   'collarUnder':layers['collarUnder'] if hidden else np.zeros_like(layers['collarUnder']),
   'collarWhite':layers['collarWhite'],
   'bowUnder':shift(layers['bowUnder'],bowDx) if hidden else np.zeros_like(layers['bowUnder']),
   'bowFabric':shift(layers['bowFabric'],bowDx),
   'jewel':shift(layers['jewel'],bowDx+jewelDx)}
  canvas=np.zeros_like(layers['background'])
  for role in ('background','goldTrim','collarUnder','collarWhite','bowUnder','bowFabric','jewel'):
   canvas=over(canvas,layersOut[role])
  return canvas
 for col,(pose,bowDx,jewelDx) in enumerate(poses):
  plain=compose(bowDx,jewelDx,False)
  filled=compose(bowDx,jewelDx,True)
  # Explicit moved-surface source-owner masks.
  if bowDx:
   original=origAlphaBow
   displaced=shift(layers['bowFabric'],bowDx)[:,:,3]
   donor=layers['collarUnder'][:,:,3]
   occluder='bowFabric';donorRole='collar'
  elif jewelDx:
   original=origAlphaJewel
   displaced=shift(layers['jewel'],jewelDx)[:,:,3]
   donor=layers['bowUnder'][:,:,3]
   occluder='jewel';donorRole='bow'
  else:
   original=np.zeros((SIZE,SIZE),np.float32)
   displaced=original
   donor=original;occluder='none';donorRole='none'
  exposure=(original>.50)&(displaced<.20)
  total=int(exposure.sum())
  donorCover=int(np.count_nonzero(exposure&(donor>.50)))
  baselineOpaque=int(np.count_nonzero(exposure&(plain[:,:,3]>.5)))
  filledOpaque=int(np.count_nonzero(exposure&(filled[:,:,3]>.5)))
  delta=np.abs(filled-plain)
  changed=int(np.count_nonzero(np.any(delta>1e-4,axis=2)))
  identity=float(np.abs(unpre(plain).astype(np.int16)-raw.astype(np.int16)).mean()) if pose=='neutral' else None
  rec['poseMetrics'][pose]={
   'bowShiftPx':bowDx,'jewelRelativeShiftPx':jewelDx,
   'movingOccluder':occluder,'exposureDonor':donorRole,
   'newlyExposedSourceOwnedPixels':total,
   'donorAlphaCoveredExposedPixels':donorCover,
   'donorCoverageOfExposureFraction':round(donorCover/max(1,total),6),
   'opaquePixelsWithoutHidden':baselineOpaque,
   'opaquePixelsWithHidden':filledOpaque,
   'hiddenArtChangedPixels':changed,
   'zeroPoseSourceRGBAMAEPixel':round(identity,6) if identity is not None else None}
  rec['files'][pose]={}
  for on,premResult in [('with_underpaint',filled),('source_matte',plain)]:
   im=Image.fromarray(unpre(premResult),'RGBA')
   file=D/(f'yaw{view.replace(".","p")}-{pose}-{on}.png')
   im.save(file)
   rec['files'][pose][on]={'path':str(file.relative_to(R)),'sha256':sha(file)}
   white=Image.new('RGBA',im.size,'white');white.alpha_composite(im)
   crop=white.convert('RGB').crop((345,620,845,1015)).resize((420,332),Image.Resampling.LANCZOS)
   targetRow=row*2+(0 if on=='source_matte' else 1)
   contact.paste(crop,(col*420,targetRow*365+22))
   drawer.text((col*420+3,targetRow*365+3),f'{view} {pose} {on}',fill='black')
  print(view,pose,'exposed',total,'donor',donorCover,'gainOpaque',filledOpaque-baselineOpaque,
        'changed',changed,'zeroBaseMAE',identity,flush=True)
 report['viewRecords'][view]=rec
contact.save(D/'three-view-occlusion-reveal-contact.jpg',quality=94)
report['contact']=str((D/'three-view-occlusion-reveal-contact.jpg').relative_to(R))
(R/'evidence/p15-112-reveal-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')

#!/usr/bin/env python3
"""P15-114: source-owned canonical collar art registered to 60° and 75°.

Real pixel support from each native source is used ONLY for geometric
registration and a silhouette-constrained comparison. All reauthored collar
color, ink, and fold highlights originate in the same genuine 67.5° art.
Canonical RGBA, inverse-affine, and native target masks are provenance-tracked.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import cv2,numpy as np,json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-114-collar-art';D.mkdir(parents=True,exist_ok=True)
Q=json.loads((R/'evidence/p15-108-stroke-qa.json').read_text())
AN=json.loads((R/'private-assets/p15-110-vision-strokes/vision-stroke-annotations.json').read_text())
sha=lambda f:sha256(Path(f).read_bytes()).hexdigest()
S=512
views=('60','67.5','75')
def im(file,mode='RGBA',size=1024):
 return np.asarray(Image.open(file).convert(mode).resize((size,size),Image.Resampling.NEAREST if mode=='L' else Image.Resampling.LANCZOS))
def mask(v,size=512):
 return im(R/Q['views'][v]['layers']['collarWhite']['maskPath'],'L',size)>128
def IoU(a,b):
 return float((a&b).sum())/max(1,int((a|b).sum()))
canonical=im(R/Q['views']['67.5']['layers']['collarWhite']['texturePath'])
report={'schema':'KOMA_P15_114_SOURCE_COLLAR_REGISTRATION_V1','characterId':'p0_character_001',
 'canonicalAngle':67.5,'sourceAngles':[60,67.5,75],
 'canonicalRGBA':Q['views']['67.5']['layers']['collarWhite']['texturePath'],
 'canonicalSourceSHA256':Q['views']['67.5']['layers']['collarWhite']['textureSHA256'],
 'geometryMode':'inverse affine ECC on original 512-mask, source-owned 1024 RGBA texture',
 'sourceColorsAndInk':'single native 67.5-degree collar drawing at all output angles',
 'nativeTargetMasksUsedOnlyForGeometricAlignmentAndSeparateSilhouetteVariant':True,
 'originalSourcePreserved':True,'views':{}}
contact=Image.new('RGB',(440*3,470*4),'white');pen=ImageDraw.Draw(contact)
def render_contact(imagedata,col,row,label):
 image=Image.fromarray(imagedata,'RGBA')
 bg=Image.new('RGBA',image.size,'white');bg.alpha_composite(image)
 crop=bg.convert('RGB').crop((385,600,825,1040)).resize((440,440),Image.Resampling.LANCZOS)
 contact.paste(crop,(col*440,row*470+26));pen.text((col*440+5,row*470+5),label,fill='black')
for col,v in enumerate(views):
 sourceMask=mask('67.5')
 destMask=mask(v)
 if v=='67.5': inverse=np.float32([[1,0,0],[0,1,0]]);cc=1.
 else:
  orig=np.uint8(sourceMask)
  target=np.uint8(destMask)
  delta=np.array([np.where(destMask)[1].mean()-np.where(sourceMask)[1].mean(),
                  np.where(destMask)[0].mean()-np.where(sourceMask)[0].mean()])
  inverse=np.float32([[1,0,-delta[0]],[0,1,-delta[1]]])
  cc,inverse=cv2.findTransformECC(
     cv2.GaussianBlur(target.astype(np.float32),(0,0),2.5),
     cv2.GaussianBlur(orig.astype(np.float32),(0,0),2.5),
     inverse,cv2.MOTION_AFFINE,
     (cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,250,1e-7))
  assert float(np.linalg.det(inverse[:,:2]))>.75
 inv1024=inverse.copy();inv1024[:,2]*=2
 targetMap=cv2.warpAffine(canonical,inv1024,(1024,1024),
                         flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,
                         borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
 rawTarget=im(R/Q['views'][v]['layers']['collarWhite']['texturePath'])
 nativeMask=im(R/Q['views'][v]['layers']['collarWhite']['maskPath'],'L')
 warpedMask=cv2.warpAffine(np.uint8(sourceMask)*255,inverse,(512,512),
                        flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP)>128
 iou=IoU(warpedMask,destMask)
 # A comparison variant keeps the native silhouette but never borrows the
 # native target's linework or pigment; it is a test of art topology.
 strict=targetMap.copy()
 strict[:,:,3]=np.uint8(np.round(strict[:,:,3].astype(float)*(nativeMask.astype(float)/255)))
 pathA=D/f'yaw{v.replace(".","p")}-canonical-collar.png'
 pathB=D/f'yaw{v.replace(".","p")}-native-silhouette-collar.png'
 Image.fromarray(targetMap,'RGBA').save(pathA)
 Image.fromarray(strict,'RGBA').save(pathB)
 _,_,_,alpha=Image.fromarray(targetMap,'RGBA').split()
 rec={'sourceTarget':Q['views'][v]['layers']['collarWhite']['texturePath'],
      'sourceTargetSHA256':Q['views'][v]['layers']['collarWhite']['textureSHA256'],
      'inverseMap512':inverse.tolist(),'inverseMap1024':inv1024.tolist(),
      'determinant':float(np.linalg.det(inverse[:,:2])),
      'maskECC':float(cc),'mappedNativeTargetIoU':round(iou,5),
      'canonicalCollarPath':str(pathA.relative_to(R)),'canonicalCollarSHA256':sha(pathA),
      'nativeSilhouetteCollarPath':str(pathB.relative_to(R)),'nativeSilhouetteSHA256':sha(pathB),
      'targetCollarMaskPath':Q['views'][v]['layers']['collarWhite']['maskPath'],
      'sourceOwnedCanonRGBA':True}
 # Measure two semantic seam IDs separately from silhouette quality.
 seam={}
 for role in ('collar.left_inner_edge','collar.right_inner_edge'):
  src=np.asarray(AN['roles'][role]['views']['67.5']['points'],np.float32)
  goal=np.asarray(AN['roles'][role]['views'][v]['points'],np.float32)
  # forward affine is inverse mapping native->source, so invert it.
  forward=cv2.invertAffineTransform(inv1024)
  pred=src @ forward[:,:2].T+forward[:,2]
  dist=np.linalg.norm(pred-goal,axis=1)
  seam[role]={'meanSourceLineDriftPx':round(float(dist.mean()),3),
              'maxSourceLineDriftPx':round(float(dist.max()),3)}
 rec['nativeObservedSeamDrift']=seam
 report['views'][v]=rec
 for row,texture in enumerate((rawTarget,targetMap,strict)):
  render_contact(texture,col,row,f'{v} '+('native original' if row==0 else 'canonical art registered' if row==1 else 'canonical art native support'))
 if col==1:preview=Image.fromarray(strict)
 render_contact(targetMap,col,3,f'{v} canonical fold identity | IoU {iou:.3f}')
 print(v,'IoU',round(iou,5),'det',round(rec['determinant'],4),
       'fold drift',{r:z['meanSourceLineDriftPx'] for r,z in seam.items()},flush=True)
contact.save(D/'collar-registration-contact.jpg',quality=95)
report['contact']=str((D/'collar-registration-contact.jpg').relative_to(R))
(R/'evidence/p15-114-source-qa.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')

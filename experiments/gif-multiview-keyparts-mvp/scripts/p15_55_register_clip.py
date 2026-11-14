#!/usr/bin/env python3
"""Repair P15-51 clip registration on the generated head; leave approved keyframes untouched."""
import json,hashlib,math
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-55-registration'
D.mkdir(parents=True,exist_ok=True)
SOURCE=R/'private-assets/exports/p15-52-transparency-geometry/camera-plus20-transparent.png'
CLIP=R/'private-assets/exports/p15-53-gold-clip-repair/hair.clip.cross_gold.png'
FORMER=R/'private-assets/exports/p15-54-edge-landmark-review/candidate-refined.png'
BASE=Image.open(SOURCE).convert('RGBA')
ASSET=Image.open(CLIP).convert('RGBA')
assert BASE.size==ASSET.size==(1024,1024)
src=BASE.load()
# Hair-contour registration points are derived from scanning the visible silhouette
# on the original generated view and excluding gold pixels in the damaged sector.
knots=[(250,744),(270,752),(280,756),(290,760),(310,764),(330,769),(350,773),(375,775),(400,775)]
def boundary(y):
 for (y0,x0),(y1,x1) in zip(knots,knots[1:]):
  if y0<=y<=y1:return x0+(x1-x0)*(y-y0)/(y1-y0)
 return 744 if y<250 else 775
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)))
 return t*t*(3-2*t)
results={}
for dx in (-22,-28):
 layer=Image.new('RGBA',BASE.size,(0,0,0,0))
 layer.paste(ASSET,(dx,0))  # no mask: source already has correct alpha
 under=BASE.copy()
 dst=under.load()
 for y in range(275,397):
  for x in range(723,802):
   weight=smooth(725,746,x)*(1-smooth(374,395,y))*smooth(275,292,y)
   if weight<0.001:continue
   hair=src[max(0,x-43),y]
   edge=boundary(y)
   target_alpha=255 if x<edge-2 else int(max(0,255*(edge+2-x)/4))
   synth=(hair[0],hair[1],hair[2],target_alpha)
   orig=src[x,y]
   dst[x,y]=tuple(round(a*(1-weight)+b*weight) for a,b in zip(orig,synth))
 # Side silhouette edge correction removes remaining exterior-connected clipped-pink fragment.
 for y in range(265,406):
  edge2=boundary(y)
  for x in range(740,814):
   r,g,b,a=dst[x,y]
   if x>edge2+1:dst[x,y]=(r,g,b,0)
   elif x>edge2-1:dst[x,y]=(r,g,b,min(a,int(max(0,255*(edge2+1-x)/2))))
 merged=Image.alpha_composite(under,layer)
 under.save(D/f'underlay-{dx}.png')
 layer.save(D/f'clip-{dx}.png')
 merged.save(D/f'candidate-{dx}.png')
 merged.crop((670,240,820,410)).resize((600,680),Image.Resampling.LANCZOS).save(D/f'crop-{dx}.png')
 for name,bg in [('light',(237,239,244,255)),('blue',(65,115,176,255)),('pink',(244,199,214,255))]:
  plate=Image.new('RGBA',BASE.size,bg);plate.alpha_composite(merged)
  plate.convert('RGB').save(D/f'preview-{dx}-{name}.png')
 results[str(dx)]={'clip_bbox':list(layer.getchannel('A').getbbox()),'composite_sha256':hashlib.sha256((D/f'candidate-{dx}.png').read_bytes()).hexdigest()}
# The -28 variant sits the full X on hair rather than outside silhouette.
chosen=-28
old=Image.open(FORMER).convert('RGBA')
new=Image.open(D/f'candidate-{chosen}.png').convert('RGBA')
old.crop((670,240,820,410)).resize((600,680),Image.Resampling.LANCZOS).save(D/'crop-former.png')
# Document the limits explicitly: previous 443->1024 rescale is not a calibrated source-to-target map.
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
qa={
 'schema':'KOMA-P15-55-CLIP-REGISTRATION-V1','characterId':'p0_character_001',
 'sourceCandidateSHA256':sha(SOURCE),'sourceIndependentClipSHA256':sha(CLIP),
 'formerCandidateSHA256':sha(FORMER),
 'variants':results,'selectedOffsetFromP1553Px':chosen,
 'selectedClipBBox':results[str(chosen)]['clip_bbox'],
 'selectedCandidateSHA256':sha(D/f'candidate-{chosen}.png'),
 'registeredGoldClipCenterEstimatePx':[725.5,324.5],
 'proxyClipCenterPx':[789.948,320.1],
 'proxyComparisonStatus':'NOT_CALIBRATED; do not force clip to proxy single point',
 'source443To1024Mapping':'Legacy source clip was previously scaled; target attachment estimated from generated hair silhouette, NOT a physical UV or calibrated camera map',
 'silhouetteControlKnots':knots,'poseAbsolute65Verified':False,
 'visualAssessment':'Cross clip lies farther inside hair; former floating edge substantially reduced. Small dark jagged edge and hair texture clone differences remain at 4x zoom.',
 'visualIdentityApproved':False,'formalArtMeshChanged':False,'formalKeyframeAccepted':False,
 'next':'Refine hair-edge alpha and validate calibrated yaw/character identity before keyframe acceptance'
}
(R/'evidence/p15-55-registration-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'variants':results,'selected':chosen},ensure_ascii=False))

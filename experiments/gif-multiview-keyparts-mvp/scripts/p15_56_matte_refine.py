#!/usr/bin/env python3
"""Tighten the detached clip's alpha matte without repainting its gold pixels."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageFilter
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-56-edge-matting';D.mkdir(parents=True,exist_ok=True)
src=R/'private-assets/exports/p15-55-registration/clip--28.png'
under=R/'private-assets/exports/p15-55-registration/underlay--28.png'
clip=Image.open(src).convert('RGBA');base=Image.open(under).convert('RGBA')
r,g,b,a=clip.split()
results={}
for radius in (1,2,3):
 alpha=a.filter(ImageFilter.MinFilter(2*radius+1))
 layer=Image.merge('RGBA',(r,g,b,alpha))
 merged=Image.alpha_composite(base,layer)
 layer.save(D/f'clip-erode-{radius}.png')
 merged.save(D/f'candidate-erode-{radius}.png')
 merged.crop((670,240,820,410)).resize((900,1020),Image.Resampling.LANCZOS).save(D/f'crop-erode-{radius}.png')
 for name,bg in [('light',(237,239,244,255)),('blue',(65,115,176,255)),('pink',(244,199,214,255))]:
  plate=Image.new('RGBA',(1024,1024),bg);plate.alpha_composite(merged)
  plate.convert('RGB').save(D/f'preview-{radius}-{name}.png')
 results[str(radius)]={'bbox':list(alpha.getbbox()),'nonzeroAlpha':sum(1 for v in alpha.getdata() if v>0),'alphaPixelsReduced':sum(1 for x,y in zip(a.getdata(),alpha.getdata()) if x>0 and y==0),'candidateSHA256':hashlib.sha256((D/f'candidate-erode-{radius}.png').read_bytes()).hexdigest()}
# Choose 2px: 1px leaves the pink fringe; 3px visibly thins the rounded metal tips.
selected=2
qa={'schema':'KOMA-P15-56-ALPHA-MATTE-V1','characterId':'p0_character_001',
 'sourceClipSHA256':hashlib.sha256(src.read_bytes()).hexdigest(),
 'underlaySHA256':hashlib.sha256(under.read_bytes()).hexdigest(),
 'sourceClipRGBPreserved':True,'variants':results,'selectedErosionPx':selected,
 'selectedCandidateSHA256':results[str(selected)]['candidateSHA256'],
 'selectedClipBBox':results[str(selected)]['bbox'],
 'visualAssessment':'2px alpha erosion suppresses pink matte fringe while retaining both gold crossing arms; 3px is visibly too aggressive, 1px leaves more pink fringe. Hair/face source remains unchanged.',
 'formalArtMeshChanged':False,'absoluteYaw65Verified':False,'identityApproved':False,'formalKeyframeAccepted':False}
(R/'evidence/p15-56-alpha-matte-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(qa,ensure_ascii=False))

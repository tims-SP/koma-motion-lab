#!/usr/bin/env python3
"""Refine 2px lower lid; reject polygon-bounded false hair occlusion."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter,ImageChops
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-65-eyelid-refinement'
D.mkdir(parents=True,exist_ok=True)
source=R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'
under=R/'private-assets/exports/p15-63-masked-lama/underpaint-full.png'
old_layer=R/'private-assets/exports/p15-64-semantic-eye/eye.near.tight-layer.png'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source_img=Image.open(source).convert('RGBA')
under_img=Image.open(under).convert('RGBA')
prev_img=Image.open(old_layer).convert('RGBA')
prev=Image.open(R/'private-assets/exports/p15-64-semantic-eye/near-eye-shift-18.png').convert('RGBA')
# Geometry based on inspected P15-64 eye contour. The lower lip is trimmed
# by ~2px while iris border and upper eyelashes are preserved.
polygon=[
(526,449),(539,442),(554,434),(567,427),(586,424),(607,425),
(627,433),(642,451),(646,461),(640,462),(632,452),(627,449),
(627,470),(621,484),(613,495),(591,498),(573,494),(559,486),
(550,469),(545,453),(536,449)]
mask=Image.new('L',source_img.size,0)
ImageDraw.Draw(mask).polygon(polygon,fill=255)
mask=mask.filter(ImageFilter.GaussianBlur(1.0))
layer=Image.new('RGBA',source_img.size)
layer.paste(source_img,(0,0),mask)
mask.save(D/'eye.near.refined-mask.png')
layer.save(D/'eye.near.refined-layer.png')
frames=[]
for dx in (0,9,18):
    moved=Image.new('RGBA',source_img.size)
    moved.alpha_composite(layer,(dx,0))
    out=Image.alpha_composite(under_img,moved)
    name=f'eye-shift-{dx:02d}.png'
    out.save(D/name)
    out.crop((470,390,760,660)).resize((870,810),Image.Resampling.LANCZOS).save(D/f'eye-shift-{dx:02d}-face.png')
    frames.append({'shiftPx':dx,'sha256':sha(D/name),'image':name})
prev.crop((470,390,760,660)).resize((870,810),Image.Resampling.LANCZOS).save(D/'p15-64-shift18-face.png')
source_img.crop((470,390,760,660)).resize((870,810),Image.Resampling.LANCZOS).save(D/'original-face.png')
# Side-by-side failed hair masks are diagnostics only. They must not be
# treated as ArtMesh or shown as accepted reference output.
for label in ['hairA','hairB','hairC']:
    p=D/f'{label}-test.png'
    assert p.exists()
def visible(p):return sum(v>0 for v in Image.open(p).getchannel('A').getdata())
def alpha_holes(ref,test,rect=(510,400,690,545)):
    x=ref.getchannel('A').crop(rect).getdata()
    y=test.getchannel('A').crop(rect).getdata()
    return sum(a>128 and b<32 for a,b in zip(x,y))
report={
 'schema':'KOMA-P15-65-LOWER-LID-REFINE-V1','characterId':'p0_character_001',
 'sourceSHA256':sha(source),'reusedLaMaUnderpaintSHA256':sha(under),
 'previousNearEyeLayerSHA256':sha(old_layer),
 'newNearEyeLayerSHA256':sha(D/'eye.near.refined-layer.png'),
 'newMaskSHA256':sha(D/'eye.near.refined-mask.png'),
 'maskMethod':'hand-inspected tight eye contour; ~2px lower lid trim, 1.0px Gaussian matte',
 'oldLayerNonzeroAlphaPixels':visible(old_layer),
 'newLayerNonzeroAlphaPixels':visible(D/'eye.near.refined-layer.png'),
 'frames':frames,
 'holesByShift':{str(f['shiftPx']):alpha_holes(source_img,Image.open(D/f['image']).convert('RGBA')) for f in frames},
 'foregroundHairAttempts':['hairA','hairB','hairC'],
 'foregroundHairGate':'FAIL_POLYGON_SEAMS_ALL_THREE',
 'acceptedForegroundHairOverlay':False,
 'selectedCandidate':'eye.near.refined-layer.png',
 'visualAssessment':'~2px lower lid trim reduces grey halo at enlarged 18px preview compared with P15-64; stronger trim clips iris/lower white. Eyelash and nose-side front-hair true occlusion still imperfect.',
 'formalKeyframeAccepted':False,'formalArtMeshAccepted':False,'visualGate':'IMPROVED_EYELID_NOT_APPROVED_FOREGROUND_HAIR_UNRESOLVED',
 'next':'P15-66 solve front-bang occlusion using independently painted or matting-clean hair layer instead of polygons; recheck eyelash seam at 0/9/18.'}
assert all(n==0 for n in report['holesByShift'].values())
(R/'evidence/p15-65-eyelid-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'oldPixels':report['oldLayerNonzeroAlphaPixels'],'newPixels':report['newLayerNonzeroAlphaPixels'],'holes':report['holesByShift'],'hairGate':report['foregroundHairGate']}))

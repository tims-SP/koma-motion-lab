#!/usr/bin/env python3
"""Finalize visually selected tight anatomical near-eye mask with existing LaMa skin."""
import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter,ImageChops
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-64-semantic-eye'
D.mkdir(parents=True,exist_ok=True)
prev=R/'private-assets/exports/p15-63-masked-lama'
source=R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'
S=Image.open(source).convert('RGBA')
B=Image.open(prev/'underpaint-full.png').convert('RGBA')
old=Image.open(prev/'eye-near-cutout.png').convert('RGBA')
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
old_qa=json.loads((R/'evidence/p15-63-masked-lama-qa.json').read_text())
assert sha(prev/'underpaint-full.png')==old_qa['underpaintSHA256']
# Tight outline follows eyelash tips, white sclera and lower eyelid.
# This is an artwork-specific hand-selected mask, not an AI semantic segmentation.
poly=[(526,449),(539,442),(554,434),(567,427),(586,424),(607,425),
 (627,433),(642,451),(646,461),(640,462),(632,452),(627,449),
 (627,472),(622,486),(614,497),(591,500),(573,496),(558,488),
 (548,470),(545,453),(536,449)]
mask=Image.new('L',S.size,0)
ImageDraw.Draw(mask).polygon(poly,fill=255)
mask=mask.filter(ImageFilter.GaussianBlur(1.5))
sprite=Image.new('RGBA',S.size)
sprite.paste(S,(0,0),mask)
mask.save(D/'eye.near.tight-mask.png')
sprite.save(D/'eye.near.tight-layer.png')
# Visible pink hair remains in the source underpaint instead of moving with the eye.
# No synthetic hair overlay is composited; earlier pigment based mask had square seams.
frames=[]
for dx in (0,9,18):
    move=Image.new('RGBA',S.size,(0,0,0,0))
    move.alpha_composite(sprite,(dx,0))
    out=Image.alpha_composite(B,move)
    name=f'near-eye-shift-{dx:02d}.png'
    out.save(D/name)
    out.crop((470,390,760,660)).resize((870,810),Image.Resampling.LANCZOS).save(D/f'near-eye-shift-{dx:02d}-face.png')
    frames.append({'dx':dx,'image':name,'sha256':sha(D/name)})
# Diagnostic comparisons from P15-63.
for name,img in [('source',S),('previous',Image.open(prev/'eye-shift18.png').convert('RGBA'))]:
    img.crop((470,390,760,660)).resize((870,810),Image.Resampling.LANCZOS).save(D/f'{name}-face.png')
oldalpha=old.getchannel('A')
newalpha=sprite.getchannel('A')
oldcount=sum(v>0 for v in oldalpha.getdata())
newcount=sum(v>0 for v in newalpha.getdata())
# Movement must preserve full-opacity underpaint over the local face region.
original_a=S.getchannel('A').crop((510,400,680,540)).getdata()
shift_a=Image.open(D/'near-eye-shift-18.png').getchannel('A').crop((510,400,680,540)).getdata()
holes=sum(aa>128 and bb<32 for aa,bb in zip(original_a,shift_a))
assert holes==0 and newcount<oldcount
q={'schema':'KOMA-P15-64-NEAR-EYE-TIGHT-MATTE-V1',
'characterId':'p0_character_001',
'sourceSHA256':sha(source),
'originalLaMaUnderpaintSHA256':sha(prev/'underpaint-full.png'),
'originalP1563CutoutSHA256':sha(prev/'eye-near-cutout.png'),
'maskSHA256':sha(D/'eye.near.tight-mask.png'),
'eyeLayerSHA256':sha(D/'eye.near.tight-layer.png'),
'oldVisibleCutoutPixels':oldcount,
'newVisibleCutoutPixels':newcount,
'reducedVisibleCutoutPixels':oldcount-newcount,
'semanticBoundaryMethod':'HAND_TIGHT_EYE_CONTOUR_WITH_1P5PX_FEATHER',
'foregroundHairHandling':'HAIR_REMAINS_IN_UNDERPAINT_NO_RECTANGULAR_HAIR_OVERLAY',
'eyeShiftFrames':frames,'shift18TransparentHolePixels':holes,
'visualAssessment':'Significantly reduces polygon skin/hair island and eyelid box outline compared with P15-63. At 3x enlarged preview, small lower-lid grey halo and eyebrow/eyelash alignment remain, so no final anime art admission.',
'semanticIdentityApproved':False,'independentlyPaintedEye':False,
'visualGate':'IMPROVED_NOT_APPROVED_REMAINING_LOWER_LID_FRINGE',
'formalArtMeshAccepted':False,'formalKeyframeAccepted':False,
'next':'P15-65 use high quality manually refined eyelid alpha/semantic eye artwork, then verify multi-direction deformation and front-hair occlusion'}
(R/'evidence/p15-64-semantic-eye-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'oldCutoutPixels':oldcount,'newCutoutPixels':newcount,'removed':oldcount-newcount,'transparentHoles':holes,'visualGate':q['visualGate']}))

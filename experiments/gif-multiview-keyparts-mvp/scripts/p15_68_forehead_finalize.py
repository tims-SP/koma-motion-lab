#!/usr/bin/env python3
"""Hard-mask neural forehead generation, then test V2 front-hair candidate and moving eye."""
import json,hashlib
from pathlib import Path
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-68-forehead'
SRC=R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'
LAYER=R/'private-assets/exports/p15-67-front-hair/hair.front.eye-excluded-v2.png'
EYE=R/'private-assets/exports/p15-65-eyelid-refinement/eye.near.refined-layer.png'
qpath=R/'evidence/p15-68-forehead-qa.json';q=json.loads(qpath.read_text())
src=Image.open(SRC).convert('RGBA')
pred=Image.open(D/'model-512.png').convert('RGBA')
assert pred.size==(512,512)
mask=Image.open(D/'mask-full.png').convert('L')
box=tuple(q['imageCropBox'])
patched=Image.composite(pred,src.crop(box),mask.crop(box))
under=src.copy();under.paste(patched,box)
under.save(D/'forehead-neural-underpaint.png')
hair=Image.open(LAYER).convert('RGBA')
eye=Image.open(EYE).convert('RGBA')
srcbytes=src.tobytes();underbytes=under.tobytes();maskbytes=mask.tobytes()
inside=sum(srcbytes[i*4:i*4+4]!=underbytes[i*4:i*4+4] for i,k in enumerate(maskbytes) if k)
outside=sum(srcbytes[i*4:i*4+4]!=underbytes[i*4:i*4+4] for i,k in enumerate(maskbytes) if not k)
for dx in (0,9,18):
 moving=Image.new('RGBA',src.size,(0,0,0,0));moving.alpha_composite(eye,(dx,0))
 frame=Image.alpha_composite(Image.alpha_composite(under,moving),hair)
 frame.save(D/f'with-hair-eye-{dx:02d}.png')
 frame.crop((445,265,795,605)).resize((700,680),Image.Resampling.LANCZOS).save(D/f'with-hair-eye-{dx:02d}-face.png')
for name,im in [('source',src),('underpaint',under)]:
 im.crop((445,265,795,605)).resize((700,680),Image.Resampling.LANCZOS).save(D/f'{name}-face.png')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
q.update({'modelStatus':'SUCCESS','modelSHA256':sha(D/'model-512.png'),
 'underpaintSHA256':sha(D/'forehead-neural-underpaint.png'),
 'hairCandidateSHA256':sha(LAYER),'eyeSHA256':sha(EYE),
 'changedInsideMaskPixels':inside,'changedOutsideMaskPixels':outside,
 'reconstructionCompleteness':'PARTIAL_ONLY_FRONT_FRINGE_REGION',
 'fullHiddenForeheadApproved':False,'hairMattingPassed':False,
 'finalArtMeshAccepted':False,
 'visualGate':'PENDING_DIRECT_INSPECTION',
 'frameSHA256s':{str(dx):sha(D/f'with-hair-eye-{dx:02d}.png') for dx in (0,9,18)}})
assert outside==0 and inside>1000
qpath.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'changedInsideMaskPixels':inside,'changedOutsideMaskPixels':outside,'frameSHA256s':q['frameSHA256s']}))

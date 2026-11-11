#!/usr/bin/env python3
"""Restrict true neural inpaint to mask, generate moved-eye diagnostic, and record exact QA."""
import json,hashlib
from pathlib import Path
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-63-masked-lama'
SRC=R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'
qpath=R/'evidence/p15-63-masked-lama-qa.json'
q=json.loads(qpath.read_text())
src=Image.open(SRC).convert('RGBA')
model=Image.open(D/'model-512.png').convert('RGBA')
box=tuple(q['inputCrop']);assert model.size==(512,512)
mask=Image.open(D/'mask-full.png').convert('L')
local=mask.crop(box)
under=src.copy()
patched=Image.composite(model,src.crop(box),local)
under.paste(patched,box)
under.save(D/'underpaint-full.png')
eye=Image.composite(src,Image.new('RGBA',src.size,(0,0,0,0)),mask)
eye.save(D/'eye-near-cutout.png')
sh=Image.new('RGBA',src.size,(0,0,0,0));sh.alpha_composite(eye,(18,0))
moved=under.copy();moved.alpha_composite(sh)
moved.save(D/'eye-shift18.png')
for name,im in [('source',src),('underpaint',under),('shift',moved)]:
 im.crop((470,390,760,660)).resize((870,810),Image.Resampling.LANCZOS).save(D/(name+'-face.png'))
p1=src.tobytes();p2=under.tobytes();mb=mask.tobytes()
outside=sum(p1[i*4:i*4+4]!=p2[i*4:i*4+4] for i,m in enumerate(mb) if m==0)
inside=sum(p1[i*4:i*4+4]!=p2[i*4:i*4+4] for i,m in enumerate(mb) if m>0)
old=src.getchannel('A').crop((510,400,680,540)).getdata()
new=moved.getchannel('A').crop((510,400,680,540)).getdata()
holes=sum(a>128 and b<32 for a,b in zip(old,new))
sha=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()
q.update({'provider':'pg56714/Inpaint-Anything',
 'providerModel':'LaMa neural image inpainting CPU, via Gradio6',
 'modelStatus':'SUCCESS',
 'modelSHA256':sha(D/'model-512.png'),
 'underpaintSHA256':sha(D/'underpaint-full.png'),
 'eyeCutoutSHA256':sha(D/'eye-near-cutout.png'),
 'eyeShiftSHA256':sha(D/'eye-shift18.png'),
 'outsideMaskChangedPixels':outside,'insideMaskChangedPixels':inside,
 'shift18TransparentHolePixels':holes,
 'fixedMaskOutOfScopePixelChange':outside==0,
 'formalArtMeshAccepted':False,'formalKeyframeAccepted':False,
 'visualGate':'PENDING_VISUAL_INSPECTION',
 'independentNearEyePurityValidated':False,
 'note':'Neural model made genuine new hidden skin content. Eye ROI is still a polygon containing surrounding skin/hair, not a clean ArtMesh semantic cutout.'})
assert inside>0 and outside==0 and holes==0
qpath.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'provider':q['provider'],'modelStatus':q['modelStatus'],
 'insideChanged':inside,'outsideChanged':outside,'eyeShiftHoles':holes}))

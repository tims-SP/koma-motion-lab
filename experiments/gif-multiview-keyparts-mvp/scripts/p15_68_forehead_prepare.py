#!/usr/bin/env python3
"""Prepare same-view forehead/roots region for neural inpainting, not approved art."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFilter
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-68-forehead';D.mkdir(parents=True,exist_ok=True)
SRC=R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'
image=Image.open(SRC).convert('RGBA')
# Work on same-view hair-shadow face region, retain eye features outside the mask.
box=(350,125,862,637)
mask=Image.new('L',image.size,0)
d=ImageDraw.Draw(mask)
# The region covered by the front fringe where a clean forehead/roots is missing.
# Do not remove eye pixels. This is not a full hidden forehead mask.
d.polygon([(529,302),(567,266),(630,241),(696,251),(743,308),
 (742,377),(729,411),(689,412),(668,395),(633,401),
 (594,409),(555,401),(533,377)],fill=255)
mask=mask.filter(ImageFilter.GaussianBlur(1.0))
input_rgb=Image.new('RGBA',image.size,(255,255,255,255));input_rgb.alpha_composite(image)
input_rgb.crop(box).convert('RGB').save(D/'input-512.png')
mask.crop(box).save(D/'mask-512.png')
mask.save(D/'mask-full.png')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
q={'schema':'KOMA-P15-68-FOREHEAD-UNDERPAINT-V1','inputSourceSHA256':sha(SRC),'imageCropBox':list(box),
'inputSHA256':sha(D/'input-512.png'),'maskSHA256':sha(D/'mask-512.png'),
'maskScope':'visible/front fringe over forehead, excludes eyes; incomplete full hair underpaint',
'provider':'pg56714/Inpaint-Anything','model':'LaMa neural inpainting CPU',
'modelStatus':'PREPARED','visualGate':'NOT_ASSESSED','formalArtMeshAccepted':False}
(R/'evidence/p15-68-forehead-qa.json').write_text(json.dumps(q,indent=2)+'\n')
print('prepared',q['maskSHA256'])

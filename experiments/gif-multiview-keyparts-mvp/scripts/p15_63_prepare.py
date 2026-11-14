#!/usr/bin/env python3
"""Prepare provenance-checked 512px image/mask input for native LaMa inference."""
import os,json,hashlib,uuid,time,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import requests
R=Path(__file__).resolve().parents[1];P=R/'private-assets';D=P/'exports/p15-63-masked-lama';D.mkdir(parents=True,exist_ok=True)
SRC=P/'exports/p15-56-edge-matting/candidate-erode-2.png'
source=Image.open(SRC).convert('RGBA')
assert source.size==(1024,1024)
# Crop 512 square to keep full surrounding context for LaMa, at original resolution
box=(385,290,897,802)
crop=source.crop(box)
bg=Image.new('RGBA',crop.size,(255,255,255,255));bg.alpha_composite(crop)
rgb=bg.convert('RGB')
rgb.save(D/'input-512.png')
fullmask=Image.new('L',source.size,0)
# Near-eye visible silhouette incl lashes; mask is deliberately a candidate rather than approved semantic boundary
poly=[(521,450),(527,436),(541,427),(568,417),(602,416),(627,423),(651,438),(660,454),(657,471),(653,489),(638,508),(614,520),(574,519),(547,506),(526,482)]
ImageDraw.Draw(fullmask).polygon(poly,fill=255)
fullmask.save(D/'mask-full.png')
localmask=fullmask.crop(box)
localmask.save(D/'mask-512.png')
sha=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()
q={'schema':'KOMA-P15-63-MASKED-LAMA-V1','sourceSHA256':sha(SRC),'inputCrop':list(box),
'cropInputSHA256':sha(D/'input-512.png'),'maskSHA256':sha(D/'mask-512.png'),
'maskPolygon':poly,'provider':'pg56714/Inpaint-Anything','providerModel':'LaMa neural image inpainting CPU',
'modelStatus':'PENDING','formalArtMeshAccepted':False,'formalKeyframeAccepted':False}
def persist(): (R/'evidence/p15-63-masked-lama-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
persist()
print('PREPARED',str(D/'mask-512.png'),q['maskSHA256'])

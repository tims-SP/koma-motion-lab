#!/usr/bin/env python3
"""Prepare provenance-bound Codex face underpaint input and register native output."""
from pathlib import Path
import hashlib,json
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageChops
R=Path(__file__).resolve().parents[1]
A=R/'private-assets';G=A/'p15-95-underpaint'
G.mkdir(parents=True,exist_ok=True)
SOURCE=A/'exports/p15-92-angle-keyart/yaw060-registered.png'
SEG=A/'exports/p15-94-sam3-yaw060/hair-candidate-0-alpha1024.png'
NATIVE=G/'face-underpaint-native.png'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=Image.open(SOURCE).convert('RGBA')
sam=Image.open(SEG).convert('L')
assert src.size==sam.size==(1024,1024)
region=Image.new('L',src.size,0)
ImageDraw.Draw(region).polygon([(560,338),(645,316),(726,330),(789,381),
 (794,492),(763,546),(669,558),(570,513),(532,445)],fill=255)
mask=ImageChops.multiply(sam,region).filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.GaussianBlur(1.8))
mask.save(G/'source-underpaint-mask-1024.png')
box=(450,275,870,695)
bg=Image.new('RGBA',src.size,'white');bg.alpha_composite(src)
reference=bg.convert('RGB').crop(box).resize((1024,1024),Image.Resampling.LANCZOS)
closemask=mask.crop(box).resize((1024,1024),Image.Resampling.LANCZOS)
reference.save(G/'closeup-reference.png')
closemask.save(G/'closeup-mask.png')
preview=reference.convert('RGBA');overlay=Image.new('RGBA',preview.size,(245,30,45,0))
overlay.putalpha(closemask.point(lambda x:int(x*.46)))
Image.alpha_composite(preview,overlay).save(G/'reference-mask-preview.png')
report={'schema':'KOMA-P15-95-REPRODUCIBLE_UNDERPAINT_SOURCE_V1',
 'sourceSHA256':sha(SOURCE),'sam3MaskSHA256':sha(SEG),
 'inputReferenceSHA256':sha(G/'closeup-reference.png'),
 'inputMaskSHA256':sha(G/'closeup-mask.png'),
 'sourceMaskSHA256':sha(G/'source-underpaint-mask-1024.png'),
 'sourceCropBox':list(box),
 'modelReturned':False,'formalArtMeshAccepted':False}
if NATIVE.exists():
 meta=json.loads((G/'generation-result.json').read_text())
 assert meta['actual_image_tool_used'] and meta['tool']=='image_gen.imagegen'
 assert meta['sha256']==sha(NATIVE)
 with Image.open(NATIVE) as im:
  assert im.size==(1254,1254)
 raw=cv2.imread(str(NATIVE));re=cv2.imread(str(G/'closeup-reference.png'))
 native=cv2.resize(raw,(1024,1024),interpolation=cv2.INTER_AREA)
 cm=cv2.imread(str(G/'closeup-mask.png'),cv2.IMREAD_GRAYSCALE)
 good=(cm<4).astype('uint8')*255
 to_gray=lambda im:cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
 score,warp=cv2.findTransformECC(to_gray(re),to_gray(native),
      np.eye(2,3,dtype=np.float32),cv2.MOTION_TRANSLATION,
      (cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,90,1e-5),good,5)
 aligned=cv2.warpAffine(native,warp,(1024,1024),
      flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REFLECT)
 cv2.imwrite(str(G/'registered-translation.png'),aligned)
 error=np.abs(aligned.astype(np.float32)-re).mean(axis=2)
 report.update({'modelReturned':True,'nativeModelSHA256':sha(NATIVE),
  'registeredSHA256':sha(G/'registered-translation.png'),
  'registeredOutsideMaskMAE':round(float(error[cm<4].mean()),4),
  'registeredInsideMaskMAE':round(float(error[cm>128].mean()),4),
  'registrationScore':round(float(score),6),
  'registrationWarp':warp.tolist(),
  'actualStrictMaskEditing':False,
  'modelImageLimitations':meta.get('limitations',[])})
(R/'evidence/p15-95-model-registration-qa.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({k:report.get(k) for k in ('modelReturned','inputReferenceSHA256','inputMaskSHA256','nativeModelSHA256','registeredSHA256','registeredOutsideMaskMAE')},indent=2))

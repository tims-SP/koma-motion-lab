#!/usr/bin/env python3
"""Assess true SAM3 hair masks and source-owned front-hair RGBA for independent yaw60 art."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import hashlib,json,numpy as np
R=Path(__file__).resolve().parents[1]
A=R/'private-assets'; D=A/'exports/p15-94-sam3-yaw060'
qpath=R/'evidence/p15-94-sam3-provider-qa.json'
q=json.loads(qpath.read_text());assert q['status']=='MODEL_RETURNED'
source=Image.open(A/'exports/p15-92-angle-keyart/yaw060-registered.png').convert('RGBA')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
allMasks=[]
stats=[]
for i in (0,1):
 m=Image.open(D/f'annotation-{i}.png').convert('RGBA')
 alpha=m.getchannel('A')
 assert alpha.size==(640,640)
 # Resize segmentation confidence via bilinear antialiasing; source RGB stays unchanged.
 high=alpha.resize((1024,1024),Image.Resampling.BILINEAR)
 maskPath=D/f'hair-candidate-{i}-alpha1024.png'
 high.save(maskPath)
 orig=np.asarray(source).copy()
 a=np.asarray(high,dtype=np.uint16)
 orig[:,:,3]=((orig[:,:,3].astype(np.uint16)*a+127)//255).astype(np.uint8)
 out=D/f'hair-candidate-{i}-source-rgba.png'
 Image.fromarray(orig,'RGBA').save(out)
 present=np.asarray(high)>=128
 ys,xs=np.where(present)
 assert len(xs)>10000
 stats.append({'index':i,
   'annotationSHA256':sha(D/f'annotation-{i}.png'),
   'maskSHA256':sha(maskPath),'rgbaSHA256':sha(out),
   'alpha128Pixels':int(present.sum()),
   'alpha128BBox':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],
   'rgbPreservesSource':np.array_equal(orig[:,:,:3],np.asarray(source)[:,:,:3]),
   'roleCandidate':'hair.front' if i==0 else 'hair.all'})
 allMasks.append(present)
overlap=int(np.logical_and(*allMasks).sum())
q['segmentationValidation']={
 'candidateMasks':stats,
 'intersectionPixels':overlap,
 'frontWithinAllRatio':round(overlap/max(1,stats[0]['alpha128Pixels']),5),
 'actualSourceRGBPreserved':True,
 'sourceUnderdrawingAvailable':False,
 'semanticMaskApproved':False,
 'formalArtMeshAccepted':False}
contact=Image.new('RGB',(3*420,460),'white')
dr=ImageDraw.Draw(contact)
white=Image.new('RGBA',source.size,'white');white.alpha_composite(source)
for i,(name,img) in enumerate([
 ('Original yaw60',white.convert('RGB')),
 ('SAM3 bangs candidate',Image.open(D/'hair-candidate-0-source-rgba.png').convert('RGBA')),
 ('SAM3 complete hair candidate',Image.open(D/'hair-candidate-1-source-rgba.png').convert('RGBA'))]):
 if img.mode=='RGBA':
  bg=Image.new('RGBA',img.size,'white');bg.alpha_composite(img);img=bg.convert('RGB')
 im=img.resize((420,420),Image.Resampling.LANCZOS)
 contact.paste(im,(i*420,28))
 dr.text((i*420+7,8),name,fill='black')
contact.save(D/'semantic-mask-contact.jpg',quality=93)
q['segmentationValidation']['contact']='private-assets/exports/p15-94-sam3-yaw060/semantic-mask-contact.jpg'
q['visualGate']='SOURCE_OWNED_SAM3_MASK_CANDIDATES_REQUIRE_LAYER_OWNERSHIP_AND_UNDERPAINT'
qpath.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(q['segmentationValidation'],indent=2))

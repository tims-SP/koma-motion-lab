#!/usr/bin/env python3
"""Source-owned P0 garment layer priorities and provisional stroke role identities.

IDs are geometric-semantic *regions*, not manually verified point-to-point
stroke correspondence. They bind candidate ink to the same layer location and
include validation evidence for all three original garment source views.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import numpy as np,cv2,json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-108-stroke-identity';D.mkdir(parents=True,exist_ok=True)
src=json.loads((R/'evidence/p15-108-source-qa.json').read_text())
sha=lambda f:sha256(Path(f).read_bytes()).hexdigest()
ids=['bow.left_loop','bow.right_loop','bow.left_tail','bow.right_tail',
     'collar.left_crease','collar.right_crease']
layers=['background','goldTrim','collarWhite','bowFabric','jewel']
q={'schema':'KOMA_P15_108_SOURCE_STROKE_ROLE_IDENTITY_V1',
   'characterId':'p0_character_001','views':{},'roleIDs':ids,
   'depthOrder':layers,'identityKind':'color-and-position role proposal',
   'sameStrokeAcrossViewsArtistVerified':False,'sourcePixelPartitionExact':True}
for view,record in src['views'].items():
 image=np.asarray(Image.open(R/record['source']).convert('RGBA'))
 center=record['goldCenter'];cx,cy=center
 Y,X=np.indices((1024,1024))
 xd=X-cx;yd=Y-cy
 folder=P/('p15-108-stroke-sources/yaw'+view.replace('.','p'))
 def get(name):
  return np.asarray(Image.open(folder/(name+'.png')).convert('L'))>127
 bow=get('bowFabric');gold=get('goldTrim');collar=get('collarWhite')
 # gold gem foreground masks are measured around the emblem center
 yy=yd;xx=xd
 gem=(np.abs(xx)<32)&(np.abs(yy)<39)&(gold|((image[:,:,3]>128)&(np.sqrt(xx*xx+yy*yy)<23)))
 gem=cv2.morphologyEx(np.uint8(gem)*255,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))>0
 owner=np.zeros((1024,1024),np.uint8)
 for i,mask in enumerate([gold,collar,bow,gem],start=1):
  owner[mask&(image[:,:,3]>0)]=i
 outdir=D/('yaw'+view.replace('.','p'));outdir.mkdir(parents=True,exist_ok=True)
 layersQA={}
 reconstructed=np.zeros_like(image)
 perPixelCount=np.zeros((1024,1024),np.uint8)
 for i,role in enumerate(layers):
  selection=owner==i
  layer=np.zeros_like(image);layer[selection]=image[selection]
  reconstructed[selection]=layer[selection]
  mask=np.uint8(selection)*255
  name=role.replace('.','_')
  path=outdir/(name+'.png');Image.fromarray(layer,'RGBA').save(path)
  maskpath=outdir/(name+'-mask.png');Image.fromarray(mask,'L').save(maskpath)
  perPixelCount+=selection.astype(np.uint8)
  layersQA[role]={'texturePath':str(path.relative_to(R)),'textureSHA256':sha(path),
                  'maskPath':str(maskpath.relative_to(R)),'maskSHA256':sha(maskpath),
                  'sourcePixels':int(np.sum(selection)),
                  'opaquePixels':int(np.count_nonzero(selection&(image[:,:,3]>128)))}
 assert np.array_equal(reconstructed,image)
 assert np.all(perPixelCount==1)
 path=outdir/'reconstructed.png';Image.fromarray(reconstructed,'RGBA').save(path)
 bowInk=get('bowInk')&(owner==3)
 collarInk=get('collarInk')&(owner==2)
 regions={
   ids[0]:bowInk&(yd<42)&(xd<0),
   ids[1]:bowInk&(yd<42)&(xd>=0),
   ids[2]:bowInk&(yd>=42)&(xd<0),
   ids[3]:bowInk&(yd>=42)&(xd>=0),
   ids[4]:collarInk&(xd<0),
   ids[5]:collarInk&(xd>=0)}
 identityQA={}
 for role,mask in regions.items():
  file=outdir/(role.replace('.','_')+'.png')
  Image.fromarray(np.uint8(mask)*255,'L').save(file)
  ys,xs=np.where(mask)
  length=int(mask.sum())
  identityQA[role]={'maskPath':str(file.relative_to(R)),'maskSHA256':sha(file),
   'pixelCount':length,
   'boundingBox':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)] if length else None,
   'meanPosition':[round(float(xs.mean()),3),round(float(ys.mean()),3)] if length else None}
 # Identity regions are mutually exclusive and complete for filtered candidate ink
 assert sum(m.sum() for m in list(regions.values())[:4])==int(bowInk.sum())
 assert sum(m.sum() for m in list(regions.values())[4:])==int(collarInk.sum())
 q['views'][view]={'source':record['source'],'sourceSHA256':record['sourceSHA256'],
   'reassembledPixelExact':True,'reconstructedSHA256':sha(path),
   'layers':layersQA,'strokeRegions':identityQA,
   'bowInkPixelsOwned':int(bowInk.sum()),'collarInkPixelsOwned':int(collarInk.sum())}
 print('ROLE',view,[(role,z['pixelCount']) for role,z in identityQA.items()],flush=True)
q['sourcePixelPartitionExact']=True
(R/'evidence/p15-108-stroke-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')

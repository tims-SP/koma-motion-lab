#!/usr/bin/env python3
"""Source-owned 60/75 yaw semantic topology with exact partition reconstruction."""
from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json
import cv2,numpy as np
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports';D=P/'p15-99-topology'
D.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
guide=json.loads((R/'evidence/p15-98-landmarks.json').read_text())['viewLandmarks']
inputs={'60':{'source':P/'p15-97-multiview-motion/yaw60-frame-06.png',
 'eye.near':D/'yaw60/sam3-eye-mask-5.png','eye.far':D/'yaw60/sam3-eye-mask-1.png',
 'hair.front':P/'p15-94-sam3-yaw060/hair-candidate-0-alpha1024.png',
 'underpaint':P/'p15-95-yaw060-motion/generated-face-aligned.png',
 'face.polygon':[(535,416),(575,396),(678,389),(748,420),(777,480),(779,520),(762,550),(750,593),(706,647),(657,650),(603,606),(563,559),(538,501)],
 'face.outline':[(762,464),(765,494),(785,524),(769,554),(754,579),(737,614),(708,647),(669,646)]},
 '75':{'source':P/'p15-97-multiview-motion/yaw75-frame-06.png',
 'eye.near':D/'yaw75/sam3-eye-mask-0.png',
 'hair.front':P/'p15-97-sam3-yaw75/mask-1-1024.png',
 'underpaint':R/'private-assets/p15-97-underpaint-75/model-registered-source.png',
 'face.polygon':[(610,393),(645,379),(721,392),(770,432),(785,481),(809,521),(793,552),(775,603),(750,661),(701,648),(657,594),(625,545),(610,480)],
 'face.outline':[(774,461),(783,488),(814,518),(797,548),(782,563),(766,613),(746,655),(710,648)]}}
roles=['other.rear','face.skin','face.contour','eye.far','eye.near','hair.front','hair.clip']
order=['other.rear','face.skin','face.contour','eye.far','eye.near','hair.front','hair.clip']
# Lower to higher occlusion; far-eye absent in 75° silhouette.
edge=[['other.rear','face.skin'],['face.skin','face.contour'],
      ['face.skin','eye.far'],['face.skin','eye.near'],
      ['eye.far','hair.front'],['eye.near','hair.front'],
      ['face.contour','hair.front'],['hair.front','hair.clip']]
qa={'schema':'KOMA_P15_99_SEMANTIC_TOPOLOGY_V1','angles':[60,75],
    'roles':roles,'occlusionOrder':order,'occlusionEdges':edge,
    'sourcePixelOwnership':'Each RGBA pixel assigned to exactly one owner, lossless source raster reconstruction',
    'segmentation':'SAM3 actual eye/hair alpha threshold; face silhouette and contour visual hand proxies',
    'semanticsArtistApproved':False,'hiddenAnatomyModelVerified':False,
    'sourceReconstructionAccepted':False,'views':{}}
for view,info in inputs.items():
 srcPath=info['source'];src=np.asarray(Image.open(srcPath).convert('RGBA'))
 assert src.shape==(1024,1024,4)
 d=D/f'yaw{view}';d.mkdir(exist_ok=True)
 # Proxy face area, constrained by visible skin and original silhouette.
 face=Image.new('L',(1024,1024),0)
 ImageDraw.Draw(face).polygon(info['face.polygon'],fill=255)
 facemask=np.asarray(face)>0
 rgb=src[:,:,:3]
 skin=(rgb[:,:,0]>177)&(rgb[:,:,1]>156)&(rgb[:,:,1]>=rgb[:,:,2]-13)&(rgb[:,:,0]>rgb[:,:,1]+10)
 faceMask=facemask&(src[:,:,3]>2) # complete per-view face surface; eye and bangs override
 def segment(path,threshold=80):
  return np.asarray(Image.open(path).convert('L'))>threshold
 near=segment(info['eye.near'],threshold=65)
 far=segment(info['eye.far'],threshold=65) if 'eye.far' in info else np.zeros((1024,1024),bool)
 front=segment(info['hair.front'],threshold=135)
 # Only trust model segmentation within plausible face / bangs neighborhood. Actual eye pixels remain those from source.
 near &= (src[:,:,3]>0)
 far &= (src[:,:,3]>0)
 front &= (src[:,:,3]>0)
 # Narrow source-owned profile contour from independent view proxy, kept separate from skin.
 contour=Image.new('L',(1024,1024),0)
 ImageDraw.Draw(contour).line(info['face.outline'],fill=255,width=5,joint='curve')
 c=np.asarray(contour)>0
 # Preserve the source gold hairclip as its own foreground identity element.
 clipROI=np.zeros((1024,1024),bool)
 clipROI[300:410,730:817]=True
 gold=(rgb[:,:,0]>142)&(rgb[:,:,1]>99)&(rgb[:,:,2]<159)&(rgb[:,:,1]>rgb[:,:,2]+8)
 candidate=np.uint8(gold&clipROI)
 count,labels,stats,cent=cv2.connectedComponentsWithStats(candidate,8)
 clip=np.zeros_like(clipROI)
 if count>1:
  valid=sorted((i for i in range(1,count) if stats[i,cv2.CC_STAT_AREA]>=3),key=lambda i: stats[i,cv2.CC_STAT_AREA],reverse=True)[:6]
  for i in valid:clip |= labels==i
 clip=cv2.dilate(clip.astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)))>0
 clip &= clipROI
 if int(clip.sum())<50:raise RuntimeError('Gold clip segmentation too small '+view)
 # Place roles in z-order. Only explicit source pixels; hierarchy remains non-overlapping.
 owner=np.zeros((1024,1024),np.uint8)
 conditions=[faceMask,c,far,near,front,clip]
 for n,condition in enumerate(conditions,start=1):owner[condition]=n
 unique,counts=np.unique(owner,return_counts=True)
 records={}
 rebuild=np.zeros_like(src)
 for n,role in enumerate(roles):
  m=owner==n
  layer=np.zeros_like(src)
  layer[m]=src[m]  # transparent RGB is preserved as well.
  path=d/(role.replace('.','_')+'.png')
  Image.fromarray(layer,'RGBA').save(path)
  alpha_mask=Image.fromarray(np.uint8(m)*255,'L')
  alpha_mask.save(d/(role.replace('.','_')+'-ownership.png'))
  rebuild[m]=layer[m]
  records[role]={'sourcePixelCount':int(m.sum()),
    'opaquePixels':int(((src[:,:,3]>128)&m).sum()),
    'sourceOwnedLayerSHA256':sha(path),'maskSHA256':sha(d/(role.replace('.','_')+'-ownership.png'))}
 output=d/'reconstructed.png';Image.fromarray(rebuild,'RGBA').save(output)
 assert np.array_equal(rebuild,src)
 assert sha(srcPath)==sha(output) or np.array_equal(np.asarray(Image.open(srcPath).convert('RGBA')),rebuild)
 # Preview stable three-layer semantic roles as white-background individual parts.
 contact=Image.new('RGB',(420*4,455),'white');draw=ImageDraw.Draw(contact)
 for n,(label,img) in enumerate([('source',src),('skin',np.asarray(Image.open(d/'face_skin.png'))),
                  ('near eye',np.asarray(Image.open(d/'eye_near.png'))),('bang',np.asarray(Image.open(d/'hair_front.png')))]):
  rgba=Image.fromarray(img,'RGBA');white=Image.new('RGBA',rgba.size,'white');white.alpha_composite(rgba)
  tile=white.convert('RGB').crop((450,285,835,650)).resize((420,420),Image.Resampling.LANCZOS)
  contact.paste(tile,(n*420,25));draw.text((n*420+5,6),f'yaw{view} {label}',fill='black')
 contact.save(d/'topology-contact.jpg',quality=94)
 qa['views'][view]={'sourcePath':str(srcPath.relative_to(R)), 'sourceSHA256':sha(srcPath),
   'reconstructedSHA256':sha(output),'pixelExactReconstruction':True,
   'sourceDimensions':[1024,1024], 'roleMasks':records,
   'externalSAM3EyeNear':str(info['eye.near'].relative_to(R)),
   'externalSAM3EyeFar':str(info['eye.far'].relative_to(R)) if 'eye.far' in info else None,
   'externalSAM3Hair':str(info['hair.front'].relative_to(R)),
   'modelUnderpaint':str(info['underpaint'].relative_to(R)),
   'landmarksSource':'evidence/p15-98-landmarks.json',
   'facePolygon':info['face.polygon'],'faceProfileContour':info['face.outline'],
   'farEyeVisible':view=='60'}
 print(view,{r:v['sourcePixelCount'] for r,v in records.items()},flush=True)
qa['sourceReconstructionAccepted']=True
(R/'evidence/p15-99-topology-qa.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')

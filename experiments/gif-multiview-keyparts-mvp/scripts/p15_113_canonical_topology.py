#!/usr/bin/env python3
"""P15-113 single native garment ink topology, 60/67.5/75 continuous yaw.

One original 67.5-degree garment supplies ALL costume ink, fabric color,
collar, jewel and jacket trim. Three-view shared 33-vertex/48-triangle
ArtMesh per relevant garment role drives source to 9 target angles.

Keyview wardrobe is a new consistent source-derived candidate. Original
P0 source keyview sprites and all prior benchmarks remain untouched. The
P15-101 head mesh is used separately. This experiment tests cross-view
ink identity and topology, not whether source-side geometry is artistically
equivalent to true profile garment artwork.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,cv2,json,hashlib,statistics
import p15_101_head_render as head
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-113-canonical-topology';D.mkdir(parents=True,exist_ok=True)
M=json.loads((P/'p15-106-three-key-mesh/garment-three-key-mesh.json').read_text())
mq=json.loads((R/'evidence/p15-106-mesh-qa.json').read_text())
O=json.loads((R/'evidence/p15-108-stroke-qa.json').read_text())
H=json.loads((R/'evidence/p15-111-source-qa.json').read_text())
vision=json.loads((R/'evidence/p15-110-vision-qa.json').read_text())
p101=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
p107=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
p112=json.loads((R/'evidence/p15-112-render-qa.json').read_text())
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
assert M['viewKeys']==['60','67.5','75'] or set(M['viewKeys'])=={'60','67.5','75'}
S=512;Y,X=np.indices((S,S),np.float32)
angles=p107['angles'];views=['60','67.5','75'];central='67.5'
def load(src):
 return np.asarray(Image.open(src).convert('RGBA').resize((S,S),Image.Resampling.LANCZOS))
def prem(im):
 f=im.astype(np.float32)/255
 return np.concatenate((f[:,:,:3]*f[:,:,3:4],f[:,:,3:4]),axis=-1)
def unprem(p):
 alpha=np.clip(p[:,:,3:4],0,1)
 return np.uint8(np.round(np.clip(np.concatenate((p[:,:,:3]/np.maximum(alpha,1e-6),alpha),axis=-1),0,1)*255))
def over(bg,fg):
 a=np.clip(fg[:,:,3:4],0,1)
 return np.concatenate((fg[:,:,:3]+bg[:,:,:3]*(1-a),a+bg[:,:,3:4]*(1-a)),axis=-1)
def seg(angle):
 if angle<=67.5:return '60','67.5',float((angle-60)/7.5)
 return '67.5','75',float((angle-67.5)/7.5)
def signed(x):
 a,b,c=x
 return float((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
def target(role,angle):
 a,b,t=seg(angle)
 pts=M['roles'][role]['vertices']
 source=np.asarray([v['sourcePosition'][central] for v in pts],np.float32)/2
 endA=np.asarray([v['sourcePosition'][a] for v in pts],np.float32)/2
 endB=np.asarray([v['sourcePosition'][b] for v in pts],np.float32)/2
 return source,(1-t)*endA+t*endB
def matmap(role,angle):
 src,dst=target(role,angle)
 tris=M['roles'][role]['triangles']
 outX=np.zeros((S,S),np.float32);outY=np.zeros((S,S),np.float32)
 covered=np.zeros((S,S),np.uint8)
 mindet=1e6;negative=0
 for tri in tris:
  a,b=src[tri],dst[tri]
  orient=signed(b)
  mindet=min(mindet,orient)
  if orient<=0:negative+=1;continue
  x0=max(0,int(np.floor(b[:,0].min()))-2);x1=min(S,int(np.ceil(b[:,0].max()))+3)
  y0=max(0,int(np.floor(b[:,1].min()))-2);y1=min(S,int(np.ceil(b[:,1].max()))+3)
  if x0>=x1 or y0>=y1:continue
  pix=b-np.array([x0,y0])
  poly=np.zeros((y1-y0,x1-x0),np.uint8)
  cv2.fillConvexPoly(poly,np.rint(pix).astype(np.int32),255)
  select=poly>0
  affine=cv2.getAffineTransform(b,a)
  xx=X[y0:y1,x0:x1];yy=Y[y0:y1,x0:x1]
  outX[y0:y1,x0:x1][select]=(affine[0,0]*xx+affine[0,1]*yy+affine[0,2])[select]
  outY[y0:y1,x0:x1][select]=(affine[1,0]*xx+affine[1,1]*yy+affine[1,2])[select]
  covered[y0:y1,x0:x1][select]=255
 # P15-106's outer ring vertices define this component's interpolation support.
 ring=dst[17:]
 support=np.zeros((S,S),np.uint8)
 cv2.fillPoly(support,[np.rint(ring).astype(np.int32)],255)
 cracks=np.uint8((support>0)&(covered==0))*255
 if cracks.any():
  outX=cv2.inpaint(outX,cracks,2,cv2.INPAINT_TELEA)
  outY=cv2.inpaint(outY,cracks,2,cv2.INPAINT_TELEA)
 return outX,outY,support.astype(np.float32)/255,{
   'minimumTriangleOrientation':round(float(mindet),5),
   'negativeTargetTriangles':negative,
   'rasterCrackPixels':int(np.count_nonzero(cracks))}
def warp(pre,mapInfo):
 mx,my,sup,_=mapInfo
 return cv2.remap(pre,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)*sup[:,:,None]
parts={}
for role,entry in O['views'][central]['layers'].items():
 parts[role]=prem(load(R/entry['texturePath']))
parts['collarUnder']=prem(load(R/H['layers'][central]['collar']['hiddenOnlyPath']))
parts['bowUnder']=prem(load(R/H['layers'][central]['bow']['hiddenOnlyPath']))
nativeSource=load(R/O['views'][central]['source'])
# Background is the real single-source garment; holes are filled only under
# occluder masks, so a moving physical boundary has plausible fabric behind.
holes=(load(R/O['views'][central]['layers']['bowFabric']['texturePath'])[:,:,3]>12) | (
       load(R/O['views'][central]['layers']['collarWhite']['texturePath'])[:,:,3]>12) | (
       load(R/O['views'][central]['layers']['jewel']['texturePath'])[:,:,3]>12)
mask=np.uint8(holes)*255
bg=nativeSource.copy()
bg[:,:,:3]=cv2.inpaint(nativeSource[:,:,:3],mask,7,cv2.INPAINT_TELEA)
bg[:,:,3]=cv2.inpaint(nativeSource[:,:,3],mask,7,cv2.INPAINT_TELEA)
# Native source torso has no face/hair. Preserve visible jacket base in
# a single affine warp per angle, anchored at shoulder and brooch.
parts['base']=prem(bg)
Image.fromarray(bg,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS).save(D/'canonical-garment-base.png')
anchorC=np.asarray(M['roles']['shoulder.left']['vertices'][0]['sourcePosition'][central],np.float32)/2
centerC=np.asarray(M['roles']['bow']['vertices'][0]['sourcePosition'][central],np.float32)/2
def background_map(angle):
 a,b,t=seg(angle)
 def pose(view):
  shoulder=np.asarray(M['roles']['shoulder.left']['vertices'][0]['sourcePosition'][view],np.float32)/2
  center=np.asarray(M['roles']['bow']['vertices'][0]['sourcePosition'][view],np.float32)/2
  return shoulder,center
 sA,cA=pose(a);sB,cB=pose(b)
 targetS=sA*(1-t)+sB*t;targetC=cA*(1-t)+cB*t
 # Similarity scale + translation constrained by the measured shoulder-to-brooch
 # distance; do not rotate torso texture as the original garment is 2D art.
 sourceSpan=np.linalg.norm(centerC-anchorC)
 targetSpan=np.linalg.norm(targetC-targetS)
 scalar=float(np.clip(targetSpan/max(sourceSpan,1),.87,1.14))
 ox=float(centerC[0]-(targetC[0])/scalar)
 oy=float(centerC[1]-(targetC[1])/scalar)
 xx=(X/scalar+ox).astype(np.float32);yy=(Y/scalar+oy).astype(np.float32)
 return xx,yy,{'scale':round(scalar,5),'translation':(round(ox,3),round(oy,3)),
               'targetBrooch':targetC.tolist(),'targetShoulder':targetS.tolist()}
def render(angle,mode):
 m={role:matmap(role,angle) for role in ('shoulder.left','collar','bow','jewel')}
 x,y,bodyQA=background_map(angle)
 underlying=cv2.remap(parts['base'],x,y,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
 def p(role,meshRole):
  return np.clip(warp(parts[role],m[meshRole]),0,1)
 # Draw all source-owned islands with one source UV per physical layer.
 cloth=underlying
 if mode=='canonical_full':
  for name,mesh in [('collarUnder','collar'),('goldTrim','shoulder.left'),
                    ('collarWhite','collar'),('bowUnder','bow'),
                    ('bowFabric','bow'),('jewel','jewel')]:
   cloth=over(cloth,p(name,mesh))
 elif mode in ('canonical_bow_native_torso','canonical_bow_owner_torso'):
  # Native background with removed native bow and jewel in both source angles.
  a,b,t=seg(angle)
  donor=[]
  for view in (a,b):
   original=load(R/O['views'][view]['source'])
   cover=np.zeros((S,S),np.uint8)
   for name in ('bowFabric','jewel'):
    layer=load(R/O['views'][view]['layers'][name]['texturePath'])
    cover=np.maximum(cover,np.uint8(layer[:,:,3]>12)*255)
   cover=cv2.dilate(cover,np.ones((3,3),np.uint8))
   matte=original.copy()
   matte[:,:,:3]=cv2.inpaint(original[:,:,:3],cover,4,cv2.INPAINT_TELEA)
   matte[:,:,3]=cv2.inpaint(original[:,:,3],cover,4,cv2.INPAINT_TELEA)
   donor.append(prem(matte))
  if mode=='canonical_bow_owner_torso':
   # A single source owns jacket and collar pixels; align the brooch anchor.
   owner=a if t<.5 else b
   srcPart=donor[0] if owner==a else donor[1]
   current=np.asarray(M['roles']['bow']['vertices'][0]['sourcePosition'][owner],np.float32)/2
   cA=np.asarray(M['roles']['bow']['vertices'][0]['sourcePosition'][a],np.float32)/2
   cB=np.asarray(M['roles']['bow']['vertices'][0]['sourcePosition'][b],np.float32)/2
   delta=(1-t)*cA+t*cB-current
   cloth=cv2.warpAffine(srcPart,np.float32([[1,0,delta[0]],[0,1,delta[1]]]),(S,S),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
  else:cloth=(1-t)*donor[0]+t*donor[1]
  for name,mesh in [('bowUnder','bow'),
                    ('bowFabric','bow'),('jewel','jewel')]:
   cloth=over(cloth,p(name,mesh))
 else:raise ValueError(mode)
 yawT=(angle-60)/15
 faceMap={v:head.mesh_map(v,yawT) for v in ('60','75')}
 face=head.skin_blend(head.warp(head.parts['60']['head'],faceMap['60']),
                      head.warp(head.parts['75']['head'],faceMap['75']),yawT)
 assembled=over(over(cloth,face),head.get_ahoge(yawT))
 return unprem(np.clip(assembled,0,1)),{
  'triangleGeometry':{role:m[role][3] for role in m},
  'background':bodyQA,
  'canonicalBowTextureSHA256':O['views'][central]['layers']['bowFabric']['textureSHA256'],
  'canonicalJewelTextureSHA256':O['views'][central]['layers']['jewel']['textureSHA256'],
  'sourceOwnerCount':1}
models=['canonical_full','canonical_bow_native_torso','canonical_bow_owner_torso']
qa={'schema':'KOMA_P15_113_CANONICAL_GARMENT_SHARED_TOPOLOGY_V1',
 'characterId':'p0_character_001','sourceAngles':[60,67.5,75],
 'canonicalTextureAngle':67.5,'angles':angles,'models':models,
 'sourceMeshSHA256':sha(P/'p15-106-three-key-mesh/garment-three-key-mesh.json'),
 'canonicalSourceRGBA':O['views'][central]['source'],
 'canonicalSourceSHA256':O['views'][central]['sourceSHA256'],
 'textures':{role:rec['textureSHA256'] for role,rec in O['views'][central]['layers'].items()},
 'sharedMeshPerPart':{'vertices':33,'triangles':48,'sourceUVCount':1},
 'sourceColorAndInkIdentity':'one 67.5° bow/jewel source UV for all yaw; canonical_full also shares collar/trim, native-torso modes retain independent background artwork',
 'pixelSourceNativeKeyframesAlteredInCandidates':True,
 'nativeOriginalArtPreservedOnDisk':True,
 'independentArtistArtworkApproval':False,
 'full360YawVisualAccepted':False,
 'methods':{m:{} for m in models}}
for angle in angles:
 for method in models:
  rgba,data=render(angle,method)
  file=D/(method+'-yaw'+f'{angle:g}'.replace('.','p')+'.png')
  Image.fromarray(rgba,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS).save(file)
  qa['methods'][method][f'{angle:g}']={'path':str(file.relative_to(R)),
     'sha256':sha(file),'geometry':data}
 print('FRAME',angle,flush=True)
ref={
 'P15-101-original':{k:z['relativePath'] for k,z in p101['methods']['head_alpha_blend'].items()},
 'P15-107-native':{k:z['relativePath'] for k,z in p107['methods']['companion_direct_native_keys'].items()},
 'P15-112-edgeGuard':{k:z['path'] for k,z in p112['methods']['edge_guard'].items()},
 **{m:{k:z['path'] for k,z in q.items()} for m,q in qa['methods'].items()}}
regions={'bow':(500,744,790,975),'collar':(400,665,805,835),
 'jewel':(595,770,701,862),'garment':(335,655,865,1015),'head':(440,285,840,640)}
contact=Image.new('RGB',(345*len(angles),390*len(ref)),'white');pen=ImageDraw.Draw(contact)
for row,(model,frames) in enumerate(ref.items()):
 arr=[]
 for col,angle in enumerate(angles):
  im=Image.open(R/frames[f'{angle:g}']).convert('RGBA')
  white=Image.new('RGBA',im.size,'white');white.alpha_composite(im)
  arr.append(np.asarray(white.convert('RGB'),np.float32))
  contact.paste(white.convert('RGB').crop((365,615,845,1015)).resize((345,360),Image.Resampling.LANCZOS),(345*col,390*row+25))
  pen.text((345*col+4,390*row+5),model+f' {angle:g}',fill='black')
 for role,(x0,y0,x1,y1) in regions.items():
  dif=[round(float(np.abs(arr[i][y0:y1,x0:x1]-arr[i-1][y0:y1,x0:x1]).mean()),4) for i in range(1,len(arr))]
  qa.setdefault('metrics',{}).setdefault(model,{})[role]={
   'maxAdjacentRGBMAE':max(dif),'meanAdjacentRGBMAE':round(statistics.mean(dif),4),
   'interiorMaxRGBMAE':max(dif[1:7]),'adjacentRGBMAE':dif}
contact.save(D/'canonical-garment-contact.jpg',quality=94)
qa['contact']=str((D/'canonical-garment-contact.jpg').relative_to(R))
(R/'evidence/p15-113-render-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
print('METRICS',json.dumps({m:{k:round(v['maxAdjacentRGBMAE'],3) for k,v in z.items()
 if k in ('bow','collar','jewel')} for m,z in qa['metrics'].items()},indent=2),flush=True)

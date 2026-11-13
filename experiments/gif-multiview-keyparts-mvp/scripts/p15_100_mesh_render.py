#!/usr/bin/env python3
"""Render real P0 face-surface shared-mesh UV morphing against P15-99 layered baseline.

The face-mesh is a single indexed triangulation, not a recovered 3D surface.
Each keyview has source-owned 2D UVs and explicit near/far eye, hair depth roles.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import hashlib,json,cv2,numpy as np,statistics
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports'
D=P/'p15-100-mesh-vdd';D.mkdir(parents=True,exist_ok=True)
M=json.loads((P/'p15-100-shared-face-mesh/face-shared-mesh.json').read_text())
meshQa=json.loads((R/'evidence/p15-100-mesh-qa.json').read_text())
previous=json.loads((R/'evidence/p15-99-topology-qa.json').read_text())
vdd=json.loads((R/'evidence/p15-99-topology-vdd-qa.json').read_text())
roles=previous['roles']
angles=[60,61.875,63.75,65.625,67.5,69.375,71.25,73.125,75]
S=512
Y,X=np.indices((S,S),dtype=np.float32)
SRC={}
for v in ('60','75'):
 path=R/previous['views'][v]['sourcePath']
 src=np.asarray(Image.open(path).convert('RGBA').resize((S,S),Image.Resampling.LANCZOS))
 layers={}
 for role in roles:
  name=role.replace('.','_')
  layers[role]=np.asarray(Image.open(P/f'p15-99-topology/yaw{v}/{name}.png').convert('RGBA').resize((S,S),Image.Resampling.LANCZOS))
 donorPath=R/previous['views'][v]['modelUnderpaint']
 donor=np.asarray(Image.open(donorPath).convert('RGBA').resize((S,S),Image.Resampling.LANCZOS))
 face=src[:,:,:3].copy()
 # Inpaint source eye+hair pixels in face surface, reserving real eye and hair layers for the front pass.
 mask=np.zeros((S,S),np.uint8)
 face_poly=np.asarray(previous['views'][v]['facePolygon'],np.float32)/2
 support=np.zeros((S,S),np.uint8)
 cv2.fillPoly(support,[np.round(face_poly).astype(np.int32)],255)
 for role in ('eye.near','eye.far','hair.front'):
  a=layers[role][:,:,3]
  mask=np.maximum(mask,np.where(a>110,255,0).astype(np.uint8))
 mask=cv2.bitwise_and(mask,support)
 mask=cv2.dilate(mask,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)))
 fill=cv2.inpaint(cv2.cvtColor(face,cv2.COLOR_RGB2BGR),mask,4,cv2.INPAINT_TELEA)
 inpaint=cv2.cvtColor(fill,cv2.COLOR_BGR2RGB)
 # P15-95/P15-97 model underpaint supplies only the concealed fringe area; fit source tone elsewhere.
 donorSkin=face.copy()
 front=(layers['hair.front'][:,:,3]>120)&(support>0)
 donorSkin[front]=donor[:,:,:3][front]
 # Blend model-substituted source and inpaint only where the corresponding source pixels are occluded.
 under=np.clip(.6*donorSkin.astype(np.float32)+.4*inpaint.astype(np.float32),0,255).astype(np.uint8)
 under[mask==0]=face[mask==0]
 SRC[v]={'image':src,'layers':layers,'undercoat':np.dstack((under,src[:,:,3])),'support':support}
 for name,img in [('source',src),('undercoat',np.dstack((under,src[:,:,3])))]:
  Image.fromarray(img,'RGBA').save(D/f'yaw{v}-{name}.png')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
vertices={v:np.array([point['sourcePosition'][v] for point in M['vertices']],dtype=np.float32)/2 for v in ('60','75')}
triangles=M['triangles']
def signed(pts):
 a,b,c=pts
 return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def mapping(t,v):
 target=vertices['60']*(1-t)+vertices['75']*t
 source=vertices[v]
 mapx=np.zeros((S,S),np.float32);mapy=np.zeros((S,S),np.float32)
 assigned=np.zeros((S,S),np.uint8)
 for tri in triangles:
  triSource=source[tri].astype(np.float32);triDest=target[tri].astype(np.float32)
  if signed(triDest)<=0:raise RuntimeError(('fold',t,v,tri))
  # Draw each triangle at its own destination, then sample the matching UV source triangle.
  xmin=max(0,int(np.floor(triDest[:,0].min()))-1)
  ymin=max(0,int(np.floor(triDest[:,1].min()))-1)
  xmax=min(S,int(np.ceil(triDest[:,0].max()))+2)
  ymax=min(S,int(np.ceil(triDest[:,1].max()))+2)
  if xmin>=xmax or ymin>=ymax:continue
  mask=np.zeros((ymax-ymin,xmax-xmin),np.uint8)
  cv2.fillConvexPoly(mask,np.round(triDest-[xmin,ymin]).astype(np.int32),255)
  keep=mask>0
  # Explicit inverse mapping with matched triangle indices; UV is view-dependent.
  affine=cv2.getAffineTransform(triDest,triSource)
  rows=Y[ymin:ymax,xmin:xmax];cols=X[ymin:ymax,xmin:xmax]
  ux=affine[0,0]*cols+affine[0,1]*rows+affine[0,2]
  uy=affine[1,0]*cols+affine[1,1]*rows+affine[1,2]
  mapx[ymin:ymax,xmin:xmax][keep]=ux[keep]
  mapy[ymin:ymax,xmin:xmax][keep]=uy[keep]
  assigned[ymin:ymax,xmin:xmax][keep]=255
 # Polygon masks guarantee sample ownership only inside the interpolated face outline.
 contour=target[:13]
 poly=np.zeros((S,S),np.uint8)
 cv2.fillPoly(poly,[np.round(contour).astype(np.int32)],255)
 valid=cv2.bitwise_and(poly,assigned)
 coverage=float(np.sum(valid>0)/max(1,np.sum(poly>0)))
 return mapx,mapy,valid,coverage
def sample(arr,maps):
 mx,my,mask,_=maps
 # Pre-multiplied texture avoids black matte fringes.
 f=arr.astype(np.float32)/255
 prem=np.concatenate([f[:,:,:3]*f[:,:,3:4],f[:,:,3:4]],axis=2)
 w=cv2.remap(prem,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
 a=np.clip(w[:,:,3:4],0,1)
 rgb=np.clip(w[:,:,:3]/np.maximum(a,1e-6),0,1)
 return np.concatenate([rgb,a],axis=2)*np.asarray(mask[:,:,None]>0,dtype=np.float32)
def blend(a,b,t):
 return a*(1-t)+b*t
def over(dst,top):
 alpha=np.clip(top[:,:,3:4],0,1)
 dstA=dst[:,:,3:4]
 outA=alpha+dstA*(1-alpha)
 comp=(top[:,:,:3]*alpha+dst[:,:,:3]*dstA*(1-alpha))/np.maximum(outA,1e-5)
 return np.concatenate([np.clip(comp,0,1),np.clip(outA,0,1)],axis=2)
def convert(f):
 return np.uint8(np.rint(np.clip(f,0,1)*255))
def stage(t,mode,images):
 # Compare actual face mesh strategies against P15-99 layered backdrop in the same viewport.
 a=images['60'];b=images['75']
 if mode=='mesh_source_blend':
  base=blend(a['image'],b['image'],t) # mesh samples below replace face
 elif mode=='mesh_undercoat_blend':
  base=blend(a['undercoat'],b['undercoat'],t)
 else:
  base=a['undercoat'] if t<.5 else b['undercoat']
 return base
def move_angle(angle,mode):
 t=(angle-60)/15
 if t<=0:return Image.open(R/previous['views']['60']['sourcePath']).convert('RGBA'),{'endpoint':True}
 if t>=1:return Image.open(R/previous['views']['75']['sourcePath']).convert('RGBA'),{'endpoint':True}
 maps={v:mapping(t,v) for v in ('60','75')}
 # Use P15-99 staged rear/head environment; face has independent mesh texture.
 p=R/vdd['methods']['topology_rear_owner' if mode=='mesh_rear_owned' else 'topology_staged'][f'{angle:g}']['file']
 env=np.asarray(Image.open(p).convert('RGBA').resize((S,S),Image.Resampling.LANCZOS),dtype=np.float32)/255
 sourceParts={v:SRC[v] for v in ('60','75')}
 under={v:sample(sourceParts[v]['undercoat'],maps[v]) for v in ('60','75')}
 near={v:sample(sourceParts[v]['layers']['eye.near'],maps[v]) for v in ('60','75')}
 far=sample(sourceParts['60']['layers']['eye.far'],maps['60'])
 bang={v:sample(sourceParts[v]['layers']['hair.front'],maps[v]) for v in ('60','75')}
 # Target face polygon is where shared mesh controls the geometry; keep outer silhouette from previous system.
 mask=np.asarray(maps['60'][2],dtype=np.float32)/255
 mask=cv2.GaussianBlur(mask,(0,0),1.0)[:,:,None]
 colorA=under['60'];colorB=under['75']
 eyeA=near['60'];eyeB=near['75']
 if mode in ('mesh_source_blend','mesh_rear_owned'):
  rgbA=sample(sourceParts['60']['image'],maps['60'])
  rgbB=sample(sourceParts['75']['image'],maps['75'])
  face=blend(rgbA,rgbB,t)
 elif mode=='mesh_undercoat_blend':
  face=blend(colorA,colorB,t)
  face=over(face,blend(eyeA,eyeB,t))
  far[:,:,3]*=np.clip((.65-t)/.65,0,1)
  face=over(face,far)
  face=over(face,blend(bang['60'],bang['75'],t))
 else:
  # Occluded far eye decreases; source near-eye color stays crisp on a shared mesh.
  face=blend(colorA,colorB,t)
  far[:,:,3]*=np.clip((.55-t)/.55,0,1)
  face=over(face,far)
  nearP=eyeA if t<.5 else eyeB
  face=over(face,nearP)
  hairP=bang['60'] if t<.5 else bang['75']
  face=over(face,hairP)
 # Keep face source outside mesh unchanged, blend only within rasterized coverage.
 result=env*(1-mask)+face*mask
 im=Image.fromarray(convert(result),'RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
 diag={'endpoint':False,'maskCoverage':min(maps['60'][3],maps['75'][3]),
       'sharedTriangles':len(triangles)}
 return im,diag
methods=['mesh_source_blend','mesh_undercoat_blend','mesh_owner_eyes','mesh_rear_owned']
qa={'schema':'KOMA_P15_100_SHARED_TRIANGULAR_FACE_VDD_V1',
 'sourceAngles':[60,75],'interpolatedAngles':angles,
 'meshJSON':'private-assets/exports/p15-100-shared-face-mesh/face-shared-mesh.json',
 'meshSHA256':meshQa['meshSHA256'],
 'sourceTopology':'P15-99 seven owner layers per view, real SAM3 eye/hair masks',
 'methods':{m:{} for m in methods},
 'geometryFoldCount':sum(q['foldedTriangleCount'] for q in meshQa['signedTriangleAreas']),
 'texelsArtistApproved':False,'continuousYawVisualAccepted':False}
for angle in angles:
 for method in methods:
  im,diag=move_angle(angle,method)
  path=D/(method+'-yaw'+f'{angle:g}'.replace('.','p')+'.png')
  im.save(path)
  qa['methods'][method][f'{angle:g}']={'sha256':sha(path),'path':str(path.relative_to(R)),
    'geometry':diag}
 print('rendered',angle,flush=True)
# Compare local face across P15-99 baseline and new mesh candidates.
contact=Image.new('RGB',(360*len(angles),390*(1+len(methods))),'white')
draw=ImageDraw.Draw(contact)
metrics={}
crop=(475,310,845,680)
for row,method in enumerate(['p15-99-topology_staged']+methods):
 frames=[]
 for col,angle in enumerate(angles):
  if row==0:
   path=R/vdd['methods']['topology_staged'][f'{angle:g}']['file']
  else:path=R/qa['methods'][method][f'{angle:g}']['path']
  source=Image.open(path).convert('RGBA')
  white=Image.new('RGBA',source.size,'white');white.alpha_composite(source)
  tile=white.convert('RGB').crop(crop)
  frames.append(np.asarray(tile,dtype=np.float32))
  contact.paste(tile.resize((360,360),Image.Resampling.LANCZOS),(col*360,row*390+25))
  draw.text((col*360+5,row*390+7),f'{method} {angle:g}',fill='black')
 diff=[round(float(np.abs(frames[i]-frames[i-1]).mean()),4) for i in range(1,len(frames))]
 metrics[method]={'adjacentFaceMAE':diff,'maxAdjacentMAE':max(diff),
   'meanAdjacentMAE':round(statistics.mean(diff),4),
   'midpointJumpMAE':max(diff[3:5])}
contact.save(D/'mesh-vdd-contact.jpg',quality=94)
qa['metrics']=metrics
qa['contact']='private-assets/exports/p15-100-mesh-vdd/mesh-vdd-contact.jpg'
(R/'evidence/p15-100-render-qa.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')
print('METRICS',json.dumps({k:{m:v[m] for m in ('maxAdjacentMAE','midpointJumpMAE')} for k,v in metrics.items()},indent=2))

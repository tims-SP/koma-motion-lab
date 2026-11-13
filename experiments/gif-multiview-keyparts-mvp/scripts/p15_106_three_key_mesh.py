#!/usr/bin/env python3
"""P0 60/67.5/75 source garment layers and shared radial ArtMesh correspondences.

Convex outer hull control points are sampled at identical semantic polar angles
around a repeatable part center; mid-radius points lock internal material
deformation. Triangulation is indexed and immutable across three views.
This is source-owned 2D texture correspondence, not inferred 3D geometry.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import json,cv2,numpy as np
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-106-three-key-mesh';D.mkdir(parents=True,exist_ok=True)
Q=json.loads((R/'evidence/p15-105-native-art-qa.json').read_text())
older=json.loads((R/'evidence/p15-103-parts-qa.json').read_text())
sourcePaths={
 '60':P/'p15-97-multiview-motion/yaw60-frame-06.png',
 '67.5':R/Q['registeredPath'],
 '75':P/'p15-97-multiview-motion/yaw75-frame-06.png'}
images={view:np.asarray(Image.open(path).convert('RGBA')) for view,path in sourcePaths.items()}
nativeBody={}
for view,im in images.items():
 if view=='67.5':
  nativeBody[view]=im.copy()
 else:
  # Match head/garment occlusion ownership to P15-101 source head mask exactly.
  from PIL import Image as PILImage
  headSource=np.asarray(PILImage.open(P/f'p15-101-head-render/yaw{view}-body.png').convert('RGBA').resize((1024,1024),PILImage.Resampling.NEAREST))
  nativeBody[view]=im.copy()
  nativeBody[view][:,:,3]=np.uint8((im[:,:,3].astype(np.float32)*headSource[:,:,3].astype(np.float32)/255))
roles=['shoulder.left','collar','bow','jewel']
def sha(f):return sha256(Path(f).read_bytes()).hexdigest()
def poly(points):
 p=np.zeros((1024,1024),np.uint8)
 cv2.fillPoly(p,[np.rint(points).astype(np.int32)],255)
 return p
masks={}
for view,src in images.items():
 hsv=cv2.cvtColor(src[:,:,:3],cv2.COLOR_RGB2HSV)
 h,s,v=cv2.split(hsv);a=(src[:,:,3]>24)
 body=(nativeBody[view][:,:,3]>15)
 semantic={}
 if view in ('60','75'):
  for role in roles:
   filename=P/f'p15-103-parts/yaw{view}/{role.replace(".","_")}-ownership.png'
   semantic[role]=np.asarray(Image.open(filename).convert('L'))>128
 else:
  # A single specific registered source: source-garment keyframe without head art.
  bowROI=np.zeros((1024,1024),bool);bowROI[737:1020,478:795]=True
  rose=((((h>=140)&(h<=179))|((h<=8)&(s>=65)))&(s>=55)&(v>=42)&bowROI&a)
  num,labels,stats,ct=cv2.connectedComponentsWithStats(rose.astype(np.uint8),8)
  picked=np.zeros((1024,1024),np.uint8)
  for i in range(1,num):
   if stats[i,cv2.CC_STAT_AREA]>150 and stats[i,cv2.CC_STAT_TOP]<990:
    picked[labels==i]=255
  picked=cv2.morphologyEx(picked,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(13,13)))
  picked=cv2.dilate(picked,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)))
  semantic['bow']=picked>0
  gemROI=np.zeros((1024,1024),bool);gemROI[770:853,603:685]=True
  gold=((h>=9)&(h<=36)&(s>65)&(v>68)&gemROI&a)
  n,lab,st,cent=cv2.connectedComponentsWithStats(gold.astype(np.uint8),8)
  ranks=[]
  for i in range(1,n):
   if st[i,cv2.CC_STAT_AREA]>80:
    ranks.append((st[i,cv2.CC_STAT_AREA]/(1+np.linalg.norm(cent[i]-[639,809])/15),i))
  assert ranks,'middle jewel not found'
  keep=max(ranks)[1]
  mask=cv2.dilate(np.uint8(lab==keep)*255,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9)))
  semantic['jewel']=mask>0
  # Collar: sampled from source white regions under the per-view collar polygon.
  mA=np.asarray(older['views']['60']['collarPolygon'],np.float32)
  mB=np.asarray(older['views']['75']['collarPolygon'],np.float32)
  bounds=poly((mA+mB)/2)>0
  white=(s<115)&(v>127)&bounds&a
  white=cv2.dilate(np.uint8(white)*255,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(13,13)))
  semantic['collar']=white>0
  shoulderA=np.asarray(older['views']['60']['shoulderPolygon'],np.float32)
  shoulderB=np.asarray(older['views']['75']['shoulderPolygon'],np.float32)
  semantic['shoulder.left']=(poly((shoulderA+shoulderB)/2)>0)
 # Make roles mutually exclusive, clip every role to actual source garment body.
 owner=np.zeros((1024,1024),np.uint8)
 for i,role in enumerate(roles,start=1):
  own=(semantic[role]&body&a)
  owner[own]=i
 masks[view]={}
 outdir=D/('yaw'+view.replace('.','p'));outdir.mkdir(parents=True,exist_ok=True)
 for idx,role in enumerate(roles,start=1):
  m=(owner==idx)
  layer=np.zeros_like(src);layer[m]=nativeBody[view][m]
  Image.fromarray(layer,'RGBA').save(outdir/(role.replace('.','_')+'.png'))
  Image.fromarray(np.uint8(m)*255,'L').save(outdir/(role.replace('.','_')+'-ownership.png'))
  masks[view][role]=m
 # all garment pixels not semantically owned form background garment source
 background=nativeBody[view].copy()
 background[owner!=0]=[0,0,0,0]
 Image.fromarray(background,'RGBA').save(outdir/'remainder.png')
 # source partition exactly covers body input
 recombined=background.copy()
 for role in roles:
  img=np.asarray(Image.open(outdir/(role.replace('.','_')+'.png')).convert('RGBA'))
  alpha=img[:,:,3]>0
  recombined[alpha]=img[alpha]
 assert np.array_equal(recombined,nativeBody[view])
 print('MASKS',view,{role:int(mask.sum()) for role,mask in masks[view].items()},flush=True)
angles=np.linspace(-np.pi,np.pi,16,endpoint=False,dtype=np.float32)
def cross(a,b):
 return float(a[0]*b[1]-a[1]*b[0])
def sample_polygon_hull(pixels,center):
 yy,xx=np.where(pixels)
 assert len(xx)>1000,(center,len(xx))
 cloud=np.column_stack((xx,yy)).astype(np.float32)
 hull=cv2.convexHull(cloud).reshape(-1,2)
 rings=[]
 for th in angles:
  direction=np.array([np.cos(th),np.sin(th)],np.float32)
  ts=[]
  for i in range(len(hull)):
   a=hull[i];b=hull[(i+1)%len(hull)];seg=b-a
   den=cross(direction,seg)
   if abs(den)<1e-6:continue
   diff=a-center
   t=cross(diff,seg)/den
   u=cross(diff,direction)/den
   if t>1e-5 and -1e-3<=u<=1.001:ts.append(t)
  assert ts,('ray outside hull',tuple(center),th)
  radius=max(ts)
  # Move 0.25px outward so all garment edge samples retain a valid alpha silhouette.
  rings.append(center+direction*(radius+.25))
 return np.asarray(rings,np.float32)
def signed(points):
 a,b,c=points
 return cross(b-a,c-a)
parts={}
qa={'schema':'KOMA_P15_106_THREE_VIEW_ARTMESH_QA_V1','sourceAngles':[60,67.5,75],
 'characterId':'p0_character_001','sourceRegSHA256':Q['registeredSHA256'],
 'depthOrder':roles,'parts':{},'sourcePixelReconstruction':True,'artistApproved':False}
for role in roles:
 anchors={}
 for view in ('60','67.5','75'):
  m=masks[view][role]
  yy,xx=np.where(m)
  center=np.array([float(xx.mean()),float(yy.mean())],np.float32)
  if role in ('bow','jewel'):
   center=np.array({'60':[634.46,810.55],'67.5':[639.29,808.82],
                         '75':[644.12,807.09]}[view],np.float32)
  outside=cv2.pointPolygonTest(cv2.convexHull(np.column_stack([xx,yy]).astype(np.float32)),tuple(center),False)<0
  if outside: center=np.array([float(xx.mean()),float(yy.mean())],np.float32)
  hull=sample_polygon_hull(m,center)
  mid=center[None,:]+.54*(hull-center[None,:])
  anchors[view]=np.concatenate([center[None,:],mid,hull],axis=0)
 triangles=[]
 # center fan (0, midpoint_i, midpoint_i+1) orientation in screen coords
 for i in range(16):
  j=(i+1)%16
  triangles.extend([[0,1+i,1+j],[1+i,17+i,17+j],[1+i,17+j,1+j]])
 def areaStats(pts):return [signed(pts[t]) for t in triangles]
 geo=[]
 for x in np.linspace(0,1,9):
  for a,b in [('60','67.5'),('67.5','75')]:
   pts=(1-x)*anchors[a]+x*anchors[b]
   ar=areaStats(pts)
   if min(ar)<=0:raise AssertionError((role,a,b,x,min(ar)))
   geo.append({'segment':[a,b],'fraction':round(float(x),4),
                'minSignedArea':round(min(ar),5),'negativeTriangles':sum(v<=0 for v in ar)})
 parts[role]={
  'vertices':[{'id':i,'label':f'{role}.center' if i==0 else f'{role}.middle.{i-1}' if i<=16 else f'{role}.outline.{i-17}',
               'sourcePosition':{a:anchors[a][i].round(3).tolist() for a in anchors},
               'viewUV':{a:(anchors[a][i]/1024).round(6).tolist() for a in anchors}}
               for i in range(33)],
  'triangles':triangles,'viewSourceImages':{a:f'private-assets/exports/p15-106-three-key-mesh/yaw{a.replace(".","p")}/{role.replace(".","_")}.png' for a in anchors},
  'viewOpacityMasks':{a:f'private-assets/exports/p15-106-three-key-mesh/yaw{a.replace(".","p")}/{role.replace(".","_")}-ownership.png' for a in anchors}}
 qa['parts'][role]={
  'vertices':33,'triangles':48,'sampledGeometry':geo,
  'pixelCount':{a:int(masks[a][role].sum()) for a in anchors}}
 for view in ('60','67.5','75'):
  canvas=Image.open(sourcePaths[view]).convert('RGBA')
  bg=Image.new('RGBA',canvas.size,'white');bg.alpha_composite(canvas)
  thumb=bg.convert('RGB');draw=ImageDraw.Draw(thumb)
  pts=anchors[view]
  for tri in triangles:
   poly=[tuple(pts[j].round().astype(int)) for j in tri]
   draw.line(poly+[poly[0]],fill=(30,130,240),width=1)
  for i,(x,y) in enumerate(pts):
   rad=5 if i==0 else 2
   color=(215,40,35) if i==0 else (32,179,225)
   draw.ellipse((x-rad,y-rad,x+rad,y+rad),fill=color)
  thumb.crop((300,630,850,1020)).save(D/(role.replace('.','_')+'-yaw'+view.replace('.','p')+'.png'))
 print('MESH',role,'33 vertices 48 faces',flush=True)
model={'schema':'KOMA_P15_106_SHARED_GARMENT_3_KEY_MESH_V1',
 'characterId':'p0_character_001','viewKeys':['60','67.5','75'],
 'geometryType':'source silhouette support / common polar indexed 2D ArtMesh',
 'roles':parts,'triangleOrientation':'positive in all sampled segments',
 'maskGeneration':'source-owned HSV and P15-103 SAM/region ownership; native middle independently segmented',
 'formalArtistApproval':False}
out=D/'garment-three-key-mesh.json';out.write_text(json.dumps(model,indent=2,ensure_ascii=False)+'\n')
qa['meshPath']=str(out.relative_to(R));qa['meshSHA256']=sha(out)
(R/'evidence/p15-106-mesh-qa.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')
print('TOTAL',len(parts)*33,'vertices',len(parts)*48,'triangles, 18 interpolated samples/part',flush=True)

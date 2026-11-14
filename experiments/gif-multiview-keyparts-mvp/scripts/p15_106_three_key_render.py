#!/usr/bin/env python3
"""Render three-source garment ArtMesh over P15-101 head, compare real animations.

P15-106: source-view silhouette control correspondences with 4 source-owned
semantic layers, shared radial triangle identities, 3 independent source UVs.
Ablate bow/jewel-only and full-component occlusion and alpha composition.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import json,cv2,numpy as np,statistics
import p15_101_head_render as head
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-106-three-key-render';D.mkdir(parents=True,exist_ok=True)
M=json.loads((P/'p15-106-three-key-mesh/garment-three-key-mesh.json').read_text())
MQ=json.loads((R/'evidence/p15-106-mesh-qa.json').read_text())
prior=json.loads((R/'evidence/p15-105-render-qa.json').read_text())
old=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
native=json.loads((R/'evidence/p15-105-native-art-qa.json').read_text())
sha=lambda f:sha256(Path(f).read_bytes()).hexdigest()
S=512;Y,X=np.indices((S,S),np.float32);angles=head.angles
roles=['shoulder.left','collar','bow','jewel']
views=['60','67.5','75'];src={};regionMasks={}
for view in views:
 directory=P/('p15-106-three-key-mesh/yaw'+view.replace('.','p'))
 # Assemble semantic parts at the original 1024 source resolution first.
 # Rasterizing masks at 512 independently creates alpha holes and trim artifacts.
 partsFull={role:np.asarray(Image.open(directory/(role.replace('.','_')+'.png')).convert('RGBA'))
            for role in roles}
 leftoverFull=np.asarray(Image.open(directory/'remainder.png').convert('RGBA'))
 wholeFull=leftoverFull.copy()
 for layer in partsFull.values():
  use=layer[:,:,3]>0
  wholeFull[use]=layer[use]
 whole=np.asarray(Image.fromarray(wholeFull,'RGBA').resize((S,S),Image.Resampling.LANCZOS))
 layers={role:np.asarray(Image.fromarray(image,'RGBA').resize((S,S),Image.Resampling.LANCZOS))
         for role,image in partsFull.items()}
 # Inpaint once at 512 for each tested ownership strategy, retaining native source opacity.
 clean={}
 for group,maskRoles in [('bow',['bow','jewel']),('all',roles)]:
  mask=np.zeros((S,S),np.uint8)
  for role in maskRoles:
   mm=(layers[role][:,:,3]>12).astype(np.uint8)*255
   mask=cv2.max(mask,mm)
  mask=cv2.dilate(mask,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)))
  mask=np.uint8((mask>0)&(whole[:,:,3]>1))*255
  rgb=cv2.cvtColor(whole[:,:,:3],cv2.COLOR_RGB2BGR)
  fixed=cv2.cvtColor(cv2.inpaint(rgb,mask,5,cv2.INPAINT_TELEA),cv2.COLOR_BGR2RGB)
  tmp=whole.copy();tmp[:,:,:3]=fixed
  clean[group]=tmp
  Image.fromarray(tmp,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS).save(D/(f'source-{view.replace(".","p")}-{group}-undercoat.png'))
 src[view]={'whole':whole,'parts':layers,'clean':clean}
def signed(p):
 a,b,c=p
 return float((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
def mapping(role,view,a,b,t):
 data=M['roles'][role]
 pos={key:np.asarray([v['sourcePosition'][key] for v in data['vertices']],np.float32)/2 for key in (a,b,view)}
 source=pos[view];dst=(pos[a]*(1-t)+pos[b]*t).astype(np.float32)
 mapx=np.zeros((S,S),np.float32);mapy=np.zeros((S,S),np.float32)
 assigned=np.zeros((S,S),np.uint8)
 for tri in data['triangles']:
  s=source[tri];q=dst[tri]
  if signed(q)<=.005:raise RuntimeError((role,view,a,b,t,'fold'))
  x0=max(0,int(np.floor(q[:,0].min()))-1);x1=min(S,int(np.ceil(q[:,0].max()))+2)
  y0=max(0,int(np.floor(q[:,1].min()))-1);y1=min(S,int(np.ceil(q[:,1].max()))+2)
  if x0>=x1 or y0>=y1:continue
  mask=np.zeros((y1-y0,x1-x0),np.uint8)
  cv2.fillConvexPoly(mask,np.rint(q-[x0,y0]).astype(np.int32),255)
  visible=mask>0
  af=cv2.getAffineTransform(q,s)
  x=X[y0:y1,x0:x1];y=Y[y0:y1,x0:x1]
  mapx[y0:y1,x0:x1][visible]=(af[0,0]*x+af[0,1]*y+af[0,2])[visible]
  mapy[y0:y1,x0:x1][visible]=(af[1,0]*x+af[1,1]*y+af[1,2])[visible]
  assigned[y0:y1,x0:x1][visible]=255
 support=np.zeros((S,S),np.uint8)
 cv2.fillPoly(support,[np.rint(dst[17:]).astype(np.int32)],255)
 cracks=np.uint8((support>0)&(assigned==0))*255
 crackCount=int(np.count_nonzero(cracks))
 if crackCount:
  mapx=cv2.inpaint(mapx,cracks,2,cv2.INPAINT_TELEA)
  mapy=cv2.inpaint(mapy,cracks,2,cv2.INPAINT_TELEA)
 return mapx,mapy,support.astype(np.float32)/255,crackCount
def prem(im):
 f=im.astype(np.float32)/255
 return np.concatenate([f[:,:,:3]*f[:,:,3:4],f[:,:,3:4]],axis=2)
def unprem(p):
 alpha=np.clip(p[:,:,3:4],0,1)
 color=np.clip(p[:,:,:3]/np.maximum(alpha,1e-6),0,1)
 return np.uint8(np.round(np.concatenate([color,alpha],axis=2)*255))
def warp(image,m):
 mx,my,support,_=m
 f=prem(image)
 mapped=cv2.remap(f,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
 return np.clip(mapped,0,1)*support[:,:,None]
def over(bg,fg):
 alpha=fg[:,:,3:4]
 return np.concatenate([fg[:,:,:3]+bg[:,:,:3]*(1-alpha),alpha+bg[:,:,3:4]*(1-alpha)],axis=2)
def smooth(x):
 x=np.clip(x,0,1)
 return x*x*(3-2*x)
def warpSource(a,b,t):
 data={}
 for role in roles:
  data[role]={key:mapping(role,key,a,b,t) for key in (a,b)}
 return data
def headSurface(t):
 maps={v:head.mesh_map(v,t) for v in ('60','75')}
 return np.clip((1-t)*head.warp(head.parts['60']['head'],maps['60'])+
                t*head.warp(head.parts['75']['head'],maps['75']),0,1)
def render(angle,mode):
 if angle<=67.5:
  a,b='60','67.5';p=(angle-60)/7.5
 else:
  a,b='67.5','75';p=(angle-67.5)/7.5
 p=np.clip(p,0,1);t=(angle-60)/15
 roleMaps=warpSource(a,b,p)
 group='bow' if mode.startswith('bow_') else 'all'
 cloth=(1-p)*prem(src[a]['clean'][group])+p*prem(src[b]['clean'][group])
 used=['bow','jewel'] if group=='bow' else roles
 maxCracks=0
 for role in used:
  p0=warp(src[a]['parts'][role],roleMaps[role][a])
  p1=warp(src[b]['parts'][role],roleMaps[role][b])
  maxCracks=max(maxCracks,roleMaps[role][a][3],roleMaps[role][b][3])
  if mode=='bow_radial_soft_visibility' and role=='bow':
   # Crossfades concentrated around turn midpoint retain stronger ink near each source.
   w=smooth((p-.20)/.60)
  else:w=p
  mixed=(1-w)*p0+w*p1
  cloth=over(cloth,mixed)
 result=over(cloth,headSurface(t))
 result=over(result,head.get_ahoge(t))
 return unprem(np.clip(result,0,1)),{'segment':[a,b],'t':round(float(p),4),
  'roles':used,'maxRasterCrackPixels':maxCracks}
methods=['bow_radial_blend','bow_radial_soft_visibility','all_parts_radial_blend']
qa={'schema':'KOMA_P15_106_GARMENT_SHARED_RADIAL_VDD_V1','characterId':'p0_character_001',
    'meshSHA256':MQ['meshSHA256'],'sourceAngles':[60,67.5,75],'renderAngles':angles,
    'native67p5SourceSha256':native['nativeSHA256'],
    'sourceRoleGeometry':'common 33 vertices / 48 fixed triangles per component in all three views',
    'renderedMethodNames':methods,'methods':{mode:{} for mode in methods},
    'continuousYawVisualAccepted':False,'formalArtMeshApproved':False}
for angle in angles:
 for mode in methods:
  if angle in (60,75):
   v='60' if angle==60 else '75'
   image=Image.open(R/head.TOP['views'][v]['sourcePath']).convert('RGBA')
   meta={'sourceEndpoint':True}
  else:
   array,meta=render(angle,mode)
   image=Image.fromarray(array,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
   if angle==67.5:
    # Native 67.5° garment source retained at the keyframe.
    base=np.asarray(image).copy()
    original=np.asarray(Image.open(R/native['registeredPath']).convert('RGBA'))
    base[750:,:,:]=original[750:,:,:]
    image=Image.fromarray(base,'RGBA')
  file=D/(mode+'-yaw'+f'{angle:g}'.replace('.','p')+'.png')
  image.save(file)
  qa['methods'][mode][f'{angle:g}']={'path':str(file.relative_to(R)),'sha256':sha(file),
                                      'diagnostics':meta}
 print('angle',angle,flush=True)
# Source middle keyframe is exact where the original garment can be unoccluded.
nativeImage=np.asarray(Image.open(R/native['registeredPath']).convert('RGBA'))
centerImage=np.asarray(Image.open(R/qa['methods']['bow_radial_blend']['67.5']['path']).convert('RGBA'))
y=np.indices(nativeImage.shape[:2])[0]
area=(nativeImage[:,:,3]>220)&(y>770)
qa['nativeMiddleRgbaExactFraction']=round(float(np.mean(np.all(nativeImage[area]==centerImage[area],axis=1))),6)
# All metrics have exactly the same ROI as P15-105 (same white backing and 1024 RGB).
regions={'garment':(335,655,865,1015),'bow':(500,744,790,975),
         'jewel':(595,770,701,862),'collar':(400,665,805,835),
         'head':(440,285,840,640)}
baselines=[('P15-101-head_alpha_blend',old['methods']['head_alpha_blend']),
           ('P15-105-three_key_direct',prior['methods']['three_key_direct'])]
rows=baselines+[(name,qa['methods'][name]) for name in methods]
contact=Image.new('RGB',(355*len(angles),404*len(rows)),'white');draw=ImageDraw.Draw(contact)
metrics={}
for row,(name,frames) in enumerate(rows):
 images=[]
 for col,angle in enumerate(angles):
  key=f'{angle:g}'
  rec=frames[key];file=R/(rec['path'] if 'path' in rec else rec['relativePath'])
  rgb=Image.open(file).convert('RGBA');bg=Image.new('RGBA',rgb.size,'white');bg.alpha_composite(rgb)
  images.append(np.asarray(bg.convert('RGB'),np.float32))
  crop=bg.convert('RGB').crop((365,615,845,1015)).resize((355,370),Image.Resampling.LANCZOS)
  contact.paste(crop,(col*355,row*404+26))
  draw.text((col*355+4,row*404+5),f'{name} yaw {angle:g}',fill='black')
 for key,box in regions.items():
  x0,y0,x1,y1=box
  diffs=[round(float(np.abs(images[i][y0:y1,x0:x1]-images[i-1][y0:y1,x0:x1]).mean()),4) for i in range(1,len(images))]
  metrics.setdefault(name,{})[key]={'adjacentRGBMAE':diffs,'maxAdjacentRGBMAE':max(diffs),
     'midpointAdjacentRGBMAE':max(diffs[3:5]),
     'meanAdjacentRGBMAE':round(statistics.mean(diffs),4)}
contact.save(D/'three-view-artmesh-contact.jpg',quality=93)
qa['metrics']=metrics;qa['contact']='private-assets/exports/p15-106-three-key-render/three-view-artmesh-contact.jpg'
# Explicitly record per-segment jumps and whether material mapping creates abrupt changes.
qa['segmentBoundaryMotion']={method:{key:{
   '60to67p5MAE':round(float(np.mean(region['adjacentRGBMAE'][:4])),4),
   '67p5to75MAE':round(float(np.mean(region['adjacentRGBMAE'][4:])),4)}
   for key,region in m.items() if key in ('bow','collar','jewel')}
  for method,m in metrics.items()}
(R/'evidence/p15-106-render-qa.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')
print('NATIVE_MID',qa['nativeMiddleRgbaExactFraction'])
print('METRICS',json.dumps({mode:{k:(m['maxAdjacentRGBMAE'],m['midpointAdjacentRGBMAE'])
     for k,m in values.items() if k in ('bow','collar','jewel')} for mode,values in metrics.items()},indent=2),flush=True)

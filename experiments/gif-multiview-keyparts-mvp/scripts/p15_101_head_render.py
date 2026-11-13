#!/usr/bin/env python3
"""Source-owned P0 head+hair shared indexed mesh renderer, 60°–75°.
One common head shell controls hair, forehead, near eye, ear, cheek and jaw.
Compare geometry-resolved alpha blend, eye-owner and local hair-owner strategies.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import json,numpy as np,cv2,hashlib,statistics
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-101-head-render';D.mkdir(parents=True,exist_ok=True)
M=json.loads((P/'p15-101-shared-head-mesh/head-hair-shared-mesh.json').read_text())
G=json.loads((R/'evidence/p15-101-mesh-qa.json').read_text())
TOP=json.loads((R/'evidence/p15-99-topology-qa.json').read_text())
BASE=json.loads((R/'evidence/p15-100-render-qa.json').read_text())
assert G['nonfolding'] and G['vertexCount']==len(M['vertices'])
angles=[60,61.875,63.75,65.625,67.5,69.375,71.25,73.125,75];S=512
yy,xx=np.indices((S,S),dtype=np.float32)
nodes={v:np.asarray([n['sourcePosition'][v] for n in M['vertices']],dtype=np.float32)/2 for v in ('60','75')}
triangles=M['triangles'];headOuter=M['headOuterVertexCount']
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return np.asarray(Image.open(path).convert('RGBA').resize((S,S),Image.Resampling.LANCZOS))
def signed(p):
 a,b,c=p
 return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def mesh_map(view,t):
 source=nodes[view];target=nodes['60']*(1-t)+nodes['75']*t
 mapx=np.zeros((S,S),np.float32);mapy=np.zeros((S,S),np.float32)
 assigned=np.zeros((S,S),np.uint8)
 for tri in triangles:
  src=source[tri].astype(np.float32);dst=target[tri].astype(np.float32)
  if signed(dst)<=.1:raise RuntimeError('flipped head triangle')
  x0=max(0,int(np.floor(dst[:,0].min()))-1);x1=min(S,int(np.ceil(dst[:,0].max()))+2)
  y0=max(0,int(np.floor(dst[:,1].min()))-1);y1=min(S,int(np.ceil(dst[:,1].max()))+2)
  if x1<=x0 or y1<=y0:continue
  mask=np.zeros((y1-y0,x1-x0),np.uint8)
  cv2.fillConvexPoly(mask,np.rint(dst-[x0,y0]).astype(np.int32),255)
  keep=mask>0
  if not np.any(keep):continue
  a=cv2.getAffineTransform(dst,src)
  subx=xx[y0:y1,x0:x1];suby=yy[y0:y1,x0:x1]
  mapx[y0:y1,x0:x1][keep]=(a[0,0]*subx+a[0,1]*suby+a[0,2])[keep]
  mapy[y0:y1,x0:x1][keep]=(a[1,0]*subx+a[1,1]*suby+a[1,2])[keep]
  assigned[y0:y1,x0:x1][keep]=255
 poly=np.zeros((S,S),np.uint8)
 cv2.fillPoly(poly,[np.rint(target[:headOuter]).astype(np.int32)],255)
 cover=float(np.count_nonzero(cv2.bitwise_and(poly,assigned))/max(1,np.count_nonzero(poly)))
 # Tiny subpixel cracks between triangles use image-map inpainting, never arbitrary source UV values.
 need=np.where((poly>0)&(assigned==0),255,0).astype(np.uint8)
 if need.any():
  mapx=cv2.inpaint(mapx,need,2,cv2.INPAINT_TELEA)
  mapy=cv2.inpaint(mapy,need,2,cv2.INPAINT_TELEA)
 return mapx,mapy,poly.astype(np.float32)/255,cover,int(np.count_nonzero(need))
def warp(src,maps):
 mx,my,poly,*_=maps
 rgba=src.astype(np.float32)/255
 prem=np.concatenate([rgba[:,:,:3]*rgba[:,:,3:4],rgba[:,:,3:4]],axis=2)
 w=cv2.remap(prem,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
 return np.clip(w,0,1)*poly[:,:,None]
def unprem(p):
 a=np.clip(p[:,:,3:4],0,1)
 return np.concatenate([np.clip(p[:,:,:3]/np.maximum(a,1e-6),0,1),a],axis=2)
def over(dst,front):
 a=front[:,:,3:4];return np.concatenate([front[:,:,:3]+dst[:,:,:3]*(1-a),a+dst[:,:,3:4]*(1-a)],axis=2)
def rgba(p):
 return np.uint8(np.round(np.clip(unprem(p),0,1)*255))
def prem(a):
 f=a.astype(np.float32)/255
 return np.concatenate([f[:,:,:3]*f[:,:,3:4],f[:,:,3:4]],axis=2)
def skin_blend(a,b,t):
 return np.clip((1-t)*a+t*b,0,1)
parts={}
for v in ('60','75'):
 sourceFile=R/TOP['views'][v]['sourcePath']
 src=load(sourceFile)
 # Head segment includes source image pixels under outer hair/face hull and excludes the torso.
 polys=np.zeros((S,S),np.uint8)
 cv2.fillPoly(polys,[np.rint(nodes[v][:headOuter]).astype(np.int32)],255)
 # Clip to source RGBA silhouette. Real source pixel RGB and alpha remain intact.
 head=src.copy();head[:,:,3]=(head[:,:,3].astype(np.float32)*(polys.astype(np.float32)/255)).astype(np.uint8)
 # Thin facial features source-owned, same mesh UV.
 near=load(P/f'p15-99-topology/yaw{v}/eye_near.png')
 bang=load(P/f'p15-99-topology/yaw{v}/hair_front.png')
 profile=load(P/f'p15-99-topology/yaw{v}/face_contour.png')
 profileMask=np.uint8(profile[:,:,3]>16)*255
 profileMask=cv2.dilate(profileMask,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)))
 clean=head.copy()
 clean[:,:,:3]=cv2.inpaint(cv2.cvtColor(head[:,:,:3],cv2.COLOR_RGB2BGR),
                          profileMask,4,cv2.INPAINT_TELEA)[:,:,::-1]
 # Separate upstream face undercoat is a donor only if a semantic mask reveals it.
 donor=load(P/f'p15-100-mesh-vdd/yaw{v}-undercoat.png')
 # Body and upper ahoge are excluded from head hull.
 body=src.copy();body[:,:,3]=(body[:,:,3].astype(np.float32)*(1-polys.astype(np.float32)/255)).astype(np.uint8)
 # Keep an independent strip around the top ahoge; becomes an owned layer at final render.
 ahoge=src.copy();strip=np.zeros((S,S),np.uint8);strip[:70,194:355]=255
 ahoge[:,:,3]=(ahoge[:,:,3].astype(np.float32)*(strip.astype(np.float32)/255)).astype(np.uint8)
 parts[v]={'source':src,'head':head,'near':near,'bang':bang,'donor':donor,
           'body':body,'ahoge':ahoge,'profile':profile,'clean':clean}
 for name,obj in [('head',head),('body',body)]:
  Image.fromarray(obj,'RGBA').save(D/f'yaw{v}-{name}.png')
def get_bg(t):
 # Native torso colors blend, while head/hair pixels have independent surface ownership.
 a=prem(parts['60']['body']);b=prem(parts['75']['body'])
 return skin_blend(a,b,t)
def get_ahoge(t):
 # Source-owner upper ahoge with interpolated translation only; no doubled outlines.
 v='60' if t<.5 else '75'
 aa=parts[v]['ahoge'];rootA=np.array([605,136]);rootB=np.array([595,136])
 root=rootA*(1-t)+rootB*t
 sourceRoot=rootA if v=='60' else rootB
 off=(root-sourceRoot)/2
 affine=np.array([[1,0,float(off[0])],[0,1,float(off[1])]],np.float32)
 pre=prem(aa)
 return cv2.warpAffine(pre,affine,(S,S),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
def render(t,method):
 maps={v:mesh_map(v,t) for v in ('60','75')}
 wa=warp(parts['60']['clean'] if method=='head_profile_owner' else parts['60']['head'],maps['60'])
 wb=warp(parts['75']['clean'] if method=='head_profile_owner' else parts['75']['head'],maps['75'])
 # Head image itself is a single deformation domain; source alpha and RGB are premultiplied.
 color=skin_blend(wa,wb,t)
 if method=='head_visibility_union':
  # Use union coverage while normalizing RGB by source alpha weights.
  aa=wa[:,:,3:4];ab=wb[:,:,3:4]
  norm=np.maximum((1-t)*aa+t*ab,1e-6)
  rgb=((1-t)*wa[:,:,:3]+t*wb[:,:,:3])/norm
  alpha=np.maximum(aa,ab)
  color=np.concatenate([np.clip(rgb,0,1)*alpha,alpha],axis=2)
 elif method=='head_eye_owned':
  # A single source contributes the iris and eyelashes over the geometric blend.
  v='60' if t<.5 else '75'
  e=warp(parts[v]['near'],maps[v])
  # Feather source eye opacity along segmentation borders; single texture identity.
  alpha=cv2.GaussianBlur(e[:,:,3],(0,0),.9)
  color=over(color,np.concatenate((e[:,:,:3],alpha[:,:,None]),axis=2))
 elif method=='head_hair_owned':
  # Front bangs belong to the nearest view on the shared head mesh.
  v='60' if t<.5 else '75'
  bangs=warp(parts[v]['bang'],maps[v])
  color=over(color,bangs)
 elif method=='head_profile_owner':
  v='60' if t<.5 else '75'
  contour=warp(parts[v]['profile'],maps[v])
  color=over(color,contour)
 elif method=='head_tone_mapped':
  # Restore face tone using source-owned beneath-bang donor only at the occlusion gap.
  donorA=warp(parts['60']['donor'],maps['60'])
  donorB=warp(parts['75']['donor'],maps['75'])
  b=np.clip((1-t)*wa[:,:,3:4]+t*wb[:,:,3:4],0,1)
  shade=((1-t)*donorA[:,:,:3]+t*donorB[:,:,:3])
  # Restrict donor effect to a thin face-side triangle where previously there was a seam.
  brow=np.array([680,440])*(1-t)+np.array([715,440])*t
  gx=np.exp(-(((xx-brow[0]/2)/26)**2+((yy-brow[1]/2)/70)**2))
  gate=(gx*.30)[:,:,None]
  color=np.concatenate((color[:,:,:3]*(1-gate)+shade*gate,b),axis=2)
 # Independently visible torso and ahoge, followed by one coupled head surface.
 out=get_bg(t)
 out=over(out,color)
 out=over(out,get_ahoge(t))
 return rgba(out),{'coverage60':maps['60'][3],'coverage75':maps['75'][3],
                    'meshCracks60':maps['60'][4],'meshCracks75':maps['75'][4]}
methods=['head_alpha_blend','head_eye_owned','head_hair_owned','head_visibility_union','head_tone_mapped','head_profile_owner']
qa={'schema':'KOMA_P15_101_COUPLED_HEAD_HAIR_VDD_V1',
 'mesh':'private-assets/exports/p15-101-shared-head-mesh/head-hair-shared-mesh.json',
 'meshSHA256':G['meshSha256'],'angles':angles,'methods':{m:{} for m in methods},
 'headMeshFolds':sum(q['negativeTriangleCount'] for q in G['sampledGeometry']),
 'headTexelTopologyArtistApproved':False,'continuousYawVisualAccepted':False}
for angle in angles:
 t=(angle-60)/15
 for method in methods:
  if t==0:
   img=Image.open(R/TOP['views']['60']['sourcePath']).convert('RGBA')
   diag={'source':True}
  elif t==1:
   img=Image.open(R/TOP['views']['75']['sourcePath']).convert('RGBA')
   diag={'source':True}
  else:
   array,diag=render(t,method)
   img=Image.fromarray(array,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
  p=D/(method+'-yaw'+f'{angle:g}'.replace('.','p')+'.png')
  img.save(p)
  qa['methods'][method][f'{angle:g}']={'relativePath':str(p.relative_to(R)),
   'sha256':sha(p),'diagnostics':diag}
 print('render',angle,flush=True)
# Visual comparison with P15-100 face-only result.
contact=Image.new('RGB',(380*len(angles),390*(1+len(methods))),'white')
d=ImageDraw.Draw(contact)
crop=(445,275,845,675)
metrics={}
for row,method in enumerate(['p15-100-mesh_source_blend']+methods):
 frames=[]
 for col,angle in enumerate(angles):
  p=(R/BASE['methods']['mesh_source_blend'][f'{angle:g}']['path']) if row==0 else (R/qa['methods'][method][f'{angle:g}']['relativePath'])
  art=Image.open(p).convert('RGBA')
  bg=Image.new('RGBA',art.size,'white');bg.alpha_composite(art)
  tile=bg.convert('RGB').crop(crop)
  frames.append(np.asarray(tile,np.float32))
  contact.paste(tile.resize((380,360),Image.Resampling.LANCZOS),(col*380,row*390+25))
  d.text((col*380+5,row*390+5),f'{method} yaw {angle:g}',fill='black')
 delta=[round(float(np.abs(frames[i]-frames[i-1]).mean()),4) for i in range(1,len(frames))]
 metrics[method]={'adjacentFaceRGBMAE':delta,'maxAdjacentMAE':max(delta),
  'midpointJumpMAE':max(delta[3:5]),'meanAdjacentMAE':round(statistics.mean(delta),4)}
contact.save(D/'head-hair-contact.jpg',quality=93)
qa['metrics']=metrics
qa['visualContact']='private-assets/exports/p15-101-head-render/head-hair-contact.jpg'
(R/'evidence/p15-101-render-qa.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')
print('METRICS',json.dumps({k:{z:v[z] for z in ('maxAdjacentMAE','midpointJumpMAE')} for k,v in metrics.items()},indent=2),flush=True)

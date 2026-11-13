#!/usr/bin/env python3
"""Source-owned garment ArtMesh correspondence ablation over P15-101 head animation.

Render four layer strategies: bow-only matched UV, bow union coverage, bow
single-owner, all-garment matched UV, all-garment one-view ownership.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import cv2,numpy as np,json,hashlib,statistics
import p15_101_head_render as head
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-103-render';D.mkdir(parents=True,exist_ok=True)
M=json.loads((P/'p15-103-part-mesh/garment-parts-mesh.json').read_text())
Q=json.loads((R/'evidence/p15-103-parts-qa.json').read_text())
prior=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
S=512;X,Y=head.xx,head.yy;ANGLES=head.angles
roles=M['depthOrder'][1:5]
assert roles==['shoulder.left','collar','bow','jewel']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
parts={};clean={}
for v in ('60','75'):
 folder=P/f'p15-103-parts/yaw{v}'
 parts[v]={role:head.load(folder/(role.replace('.','_')+'.png')) for role in roles}
 body=head.parts[v]['body']
 clean[v]={}
 for group,remove in [('bow',['bow','jewel']),('full',roles)]:
  mask=np.zeros((S,S),np.uint8)
  for role in remove:
   a=parts[v][role][:,:,3]
   mask=np.maximum(mask,np.uint8(a>15)*255)
  mask=cv2.dilate(mask,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9)))
  # Only source garment pixels belong to the inpainting support; body RGBA remains canonical.
  mask=np.uint8((mask>0)&(body[:,:,3]>0))*255
  color=cv2.cvtColor(body[:,:,:3],cv2.COLOR_RGB2BGR)
  filled=cv2.cvtColor(cv2.inpaint(color,mask,7,cv2.INPAINT_TELEA),cv2.COLOR_BGR2RGB)
  arr=body.copy();arr[:,:,:3]=filled
  clean[v][group]=arr
  Image.fromarray(arr,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS).save(D/f'yaw{v}-{group}-undercoat.png')
def signed(x):
 a,b,c=x
 return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def mappings(role,t,v):
 item=M['roles'][role]
 points={view:np.asarray([q['viewPosition'][view] for q in item['vertices']],np.float32)/2 for view in ('60','75')}
 source=points[v];dst=points['60']*(1-t)+points['75']*t
 mx=np.zeros((S,S),np.float32);my=np.zeros((S,S),np.float32)
 valid=np.zeros((S,S),np.uint8)
 for tri in item['triangles']:
  src=source[tri];tar=dst[tri]
  if signed(tar)<.01:raise RuntimeError(('garment triangle folded',role,t,tri))
  x0=max(0,int(np.floor(tar[:,0].min()))-1);x1=min(S,int(np.ceil(tar[:,0].max()))+2)
  y0=max(0,int(np.floor(tar[:,1].min()))-1);y1=min(S,int(np.ceil(tar[:,1].max()))+2)
  if x1<=x0 or y1<=y0:continue
  inside=np.zeros((y1-y0,x1-x0),np.uint8)
  cv2.fillConvexPoly(inside,np.rint(tar-[x0,y0]).astype(np.int32),255)
  m=inside>0
  a=cv2.getAffineTransform(tar,src)
  Xp=X[y0:y1,x0:x1];Yp=Y[y0:y1,x0:x1]
  mx[y0:y1,x0:x1][m]=(a[0,0]*Xp+a[0,1]*Yp+a[0,2])[m]
  my[y0:y1,x0:x1][m]=(a[1,0]*Xp+a[1,1]*Yp+a[1,2])[m]
  valid[y0:y1,x0:x1][m]=255
 # Some source-owned garment pixels lie outside the simple mesh rect but original viewport is canonical.
 xs=dst[:,0];ys=dst[:,1]
 support=np.zeros((S,S),np.uint8)
 cv2.fillPoly(support,[np.array([(xs[0],ys[0]),(xs[2],ys[2]),(xs[8],ys[8]),(xs[6],ys[6])],np.int32)],255)
 holes=np.uint8((support>0)&(valid==0))*255
 if np.any(holes):
  mx=cv2.inpaint(mx,holes,2,cv2.INPAINT_TELEA)
  my=cv2.inpaint(my,holes,2,cv2.INPAINT_TELEA)
 return mx,my,support.astype(np.float32)/255
def warp(src,mp):
 mx,my,mask=mp
 f=head.prem(src)
 warped=cv2.remap(f,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
 return np.clip(warped,0,1)*mask[:,:,None]
def union(a,b,t):
 # Premultiplied native sources: geometry-aligned alpha union avoids phantom pale edges.
 aa=a[:,:,3:4];bb=b[:,:,3:4]
 weight=(1-t)*aa+t*bb
 rgb=np.divide((1-t)*a[:,:,:3]+t*b[:,:,:3],np.maximum(weight,1e-6))
 alpha=np.maximum(aa,bb)
 return np.concatenate((np.clip(rgb,0,1)*alpha,alpha),axis=2)
def mix(a,b,t,mode):
 if mode=='owner':return a if t<.5 else b
 if mode=='union':return union(a,b,t)
 return head.skin_blend(a,b,t)
def render(t,method):
 mapsHead={v:head.mesh_map(v,t) for v in ('60','75')}
 garment='full' if method.startswith('all_') else 'bow'
 plainA=head.prem(clean['60'][garment]);plainB=head.prem(clean['75'][garment])
 bg=head.skin_blend(plainA,plainB,t)
 color=head.skin_blend(head.warp(head.parts['60']['head'],mapsHead['60']),
                       head.warp(head.parts['75']['head'],mapsHead['75']),t)
 # Occlude all apparel under the head silhouette.
 visible=['bow','jewel'] if garment=='bow' else roles
 for role in visible:
  maps={v:mappings(role,t,v) for v in ('60','75')}
  p60=warp(parts['60'][role],maps['60']);p75=warp(parts['75'][role],maps['75'])
  strategy='owner' if method.endswith('_owner') else 'union' if method=='bow_uv_union' else 'blend'
  overlay=mix(p60,p75,t,strategy)
  bg=head.over(bg,overlay)
 out=head.over(bg,color)
 out=head.over(out,head.get_ahoge(t))
 return head.rgba(out),{'endpoint':False,'componentRoles':visible,
                        'sam3Source':'P15-99 real eye/fringe retained in head source',
                        'geometryFolded':False}
def main():
 methods=['bow_uv_blend','bow_uv_union','bow_uv_owner','all_parts_blend','all_parts_owner']
 qa={'schema':'KOMA_P15_103_GARMENT_ARTMESH_RENDER_V1','characterId':'p0_character_001',
  'angles':ANGLES,'sourceAngles':[60,75],
  'sourceMesh':'private-assets/exports/p15-103-part-mesh/garment-parts-mesh.json',
  'meshSHA256':sha(P/'p15-103-part-mesh/garment-parts-mesh.json'),
  'sourcePixelsArtOwner':'P15-103 native source RGBA with per-part masks and normalized shared UV',
  'methods':{m:{} for m in methods},
  'fullContinuityAccepted':False,'formalArtMeshArtistApproved':False}
 for a in ANGLES:
  t=(a-60)/15
  for method in methods:
   if t<=0 or t>=1:
    k='60' if t<=0 else '75'
    im=Image.open(R/Q['views'][k]['source']).convert('RGBA');diag={'endpoint':True}
   else:
    arr,diag=render(t,method);im=Image.fromarray(arr,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
   f=D/(method+'-yaw'+f'{a:g}'.replace('.','p')+'.png')
   im.save(f);qa['methods'][method][f'{a:g}']={'sha256':sha(f),
       'relativePath':str(f.relative_to(R)),'diagnostics':diag}
  print('render',a,flush=True)
 # Quantitative comparisons per region, with matched white backing.
 regions={'face':(445,275,845,675),'collar':(400,668,798,835),
          'bow':(500,744,790,975),'jewel':(595,770,701,862),'shoulder':(230,693,521,915)}
 baselines=prior['methods']['head_alpha_blend']
 rows=['P15-101-head_alpha_blend']+methods
 contact=Image.new('RGB',(350*len(ANGLES),400*len(rows)),'white');draw=ImageDraw.Draw(contact)
 summaries={}
 for row,method in enumerate(rows):
  imgs=[]
  for col,a in enumerate(ANGLES):
   f=R/(baselines[f'{a:g}']['relativePath'] if row==0 else qa['methods'][method][f'{a:g}']['relativePath'])
   im=Image.open(f).convert('RGBA');white=Image.new('RGBA',im.size,'white');white.alpha_composite(im)
   arr=np.asarray(white.convert('RGB'),np.float32);imgs.append(arr)
   tile=white.convert('RGB').crop((360,585,830,1015)).resize((350,380),Image.Resampling.LANCZOS)
   contact.paste(tile,(350*col,row*400+18))
   draw.text((350*col+5,row*400+2),f'{method} {a:g}',fill='black')
  for name,(x0,y0,x1,y1) in regions.items():
   diffs=[round(float(np.abs(imgs[i][y0:y1,x0:x1]-imgs[i-1][y0:y1,x0:x1]).mean()),4) for i in range(1,len(imgs))]
   summaries.setdefault(method,{})[name]={'maxAdjacentMAE':max(diffs),
          'midpointAdjacentMAE':max(diffs[3:5]),
          'adjacentMAE':diffs}
 contact.save(D/'garment-contact.jpg',quality=92)
 qa['metrics']=summaries
 qa['contact']='private-assets/exports/p15-103-render/garment-contact.jpg'
 (R/'evidence/p15-103-render-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
 print('METRICS',json.dumps({k:{n:(round(v['maxAdjacentMAE'],3),round(v['midpointAdjacentMAE'],3)) for n,v in regions2.items()} for k,regions2 in summaries.items()},indent=2),flush=True)

if __name__=='__main__':
 main()

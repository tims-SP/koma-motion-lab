#!/usr/bin/env python3
"""P0 60–75 detailed garment ink mesh vs P15-103 source garment UV mesh.
Tests actual source ink ties on both independent RGBAs with constant indexed
triangle sets. Endpoint RGBA remain exact; deformation is 2D visual proxy.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import json,cv2,numpy as np,statistics
import p15_103_render as grid
import p15_101_head_render as head
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-104-detail-render';D.mkdir(parents=True,exist_ok=True)
model=json.loads((P/'p15-104-detail-mesh/garment-ink-correspondence.json').read_text())
features=json.loads((R/'evidence/p15-104-feature-qa.json').read_text())
prior=json.loads((R/'evidence/p15-103-render-qa.json').read_text())
meshQA=json.loads((R/'evidence/p15-104-mesh-qa.json').read_text())
S=head.S;X=head.xx;Y=head.yy;angles=head.angles
roles=['shoulder.left','collar','bow','jewel']
sha=lambda p:sha256(Path(p).read_bytes()).hexdigest()
def signed(t):
 a,b,c=t
 return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def detail_mapping(role,ratio,view):
 part=model['parts'][role]
 source=np.asarray(part['sourcePositions'][view],np.float32)/2
 pts60=np.asarray(part['sourcePositions']['60'],np.float32)/2
 pts75=np.asarray(part['sourcePositions']['75'],np.float32)/2
 target=pts60*(1-ratio)+pts75*ratio
 mapx=np.zeros((S,S),np.float32);mapy=np.zeros((S,S),np.float32)
 valid=np.zeros((S,S),np.uint8)
 for tri in part['triangles']:
  src=source[tri];dst=target[tri]
  if signed(dst)<.5:raise RuntimeError(('mesh folded',role,ratio,tri))
  x0=max(0,int(np.floor(dst[:,0].min()))-1);x1=min(S,int(np.ceil(dst[:,0].max()))+2)
  y0=max(0,int(np.floor(dst[:,1].min()))-1);y1=min(S,int(np.ceil(dst[:,1].max()))+2)
  if x1<=x0 or y1<=y0:continue
  mask=np.zeros((y1-y0,x1-x0),np.uint8)
  cv2.fillConvexPoly(mask,np.rint(dst-[x0,y0]).astype(np.int32),255)
  keep=mask>0
  tr=cv2.getAffineTransform(dst,src)
  XX=X[y0:y1,x0:x1];YY=Y[y0:y1,x0:x1]
  mapx[y0:y1,x0:x1][keep]=(tr[0,0]*XX+tr[0,1]*YY+tr[0,2])[keep]
  mapy[y0:y1,x0:x1][keep]=(tr[1,0]*XX+tr[1,1]*YY+tr[1,2])[keep]
  valid[y0:y1,x0:x1][keep]=255
 support=np.zeros((S,S),np.uint8)
 cv2.fillPoly(support,[np.rint(target[[0,2,8,6]]).astype(np.int32)],255)
 missing=np.uint8((support>0)&(valid==0))*255
 count=int(np.count_nonzero(missing))
 if count:
  mapx=cv2.inpaint(mapx,missing,2,cv2.INPAINT_TELEA)
  mapy=cv2.inpaint(mapy,missing,2,cv2.INPAINT_TELEA)
 return mapx,mapy,support.astype(np.float32)/255,count
def warp_detail(src,mapping):
 return grid.warp(src,mapping[:3])
def render(t,mode):
 base=head.skin_blend(head.prem(grid.clean['60']['full']),head.prem(grid.clean['75']['full']),t)
 mapsHead={v:head.mesh_map(v,t) for v in ('60','75')}
 headColor=head.skin_blend(head.warp(head.parts['60']['head'],mapsHead['60']),
                           head.warp(head.parts['75']['head'],mapsHead['75']),t)
 back=base
 diagnostics={}
 for role in roles:
  src60=grid.parts['60'][role];src75=grid.parts['75'][role]
  if mode=='ink_bow_only' and role not in ('bow','jewel'):
   ma=grid.mappings(role,t,'60');mb=grid.mappings(role,t,'75')
   aa=grid.warp(src60,ma);bb=grid.warp(src75,mb)
   diagnostics[role]={'adaptive':False}
  else:
   ma=detail_mapping(role,t,'60');mb=detail_mapping(role,t,'75')
   aa=warp_detail(src60,ma);bb=warp_detail(src75,mb)
   diagnostics[role]={'adaptive':True,'subpixelCracks':max(ma[3],mb[3])}
  effect=head.skin_blend(aa,bb,t)
  if mode=='ink_soft_owner' and role in ('bow','jewel'):
   # Eye/ink owner hysteresis to preserve a single crisp source at each side.
   fraction=np.clip((t-.30)/.40,0,1)
   smooth=fraction*fraction*(3-2*fraction)
   effect=head.skin_blend(aa,bb,smooth)
  back=head.over(back,effect)
 out=head.over(back,headColor)
 out=head.over(out,head.get_ahoge(t))
 return head.rgba(out),diagnostics
methods=['ink_all_detail_blend','ink_bow_only','ink_soft_owner']
qa={'schema':'KOMA_P15_104_DETAIL_GARMENT_RENDER_V1',
    'angles':angles,'sourceAngles':[60,75],
    'sourceMeshSHA256':sha(P/'p15-104-detail-mesh/garment-ink-correspondence.json'),
    'sourceArtMesh':'P15-103 independent garment layer/UV source',
    'featureMatches':{role:x['acceptedInteriorCorrespondences'] for role,x in meshQA['roles'].items()},
    'methods':{m:{} for m in methods},'geometryFolds':0,
    'continuousYawAccepted':False}
for a in angles:
 t=(a-60)/15
 for method in methods:
  if t<=0 or t>=1:
   view='60' if t<=0 else '75'
   img=Image.open(R/grid.Q['views'][view]['source']).convert('RGBA')
   diag={'sourceExact':True}
  else:
   arr,diag=render(t,method)
   img=Image.fromarray(arr,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
  path=D/(method+'-yaw'+f'{a:g}'.replace('.','p')+'.png')
  img.save(path)
  qa['methods'][method][f'{a:g}']={'relativePath':str(path.relative_to(R)),
     'sha256':sha(path),'diagnostics':diag}
 print('detail render',a,flush=True)
regions={'bow':(500,744,790,975),'jewel':(595,770,701,862),
         'collar':(400,668,798,835),'shoulder':(230,693,521,915)}
prior101=json.loads((R/'evidence/p15-101-render-qa.json').read_text())['methods']['head_alpha_blend']
prior103=prior['methods']['all_parts_blend']
rows=['P15-101-head_alpha_blend','P15-103-all_parts_blend']+methods
contact=Image.new('RGB',(345*len(angles),390*len(rows)),'white');pen=ImageDraw.Draw(contact)
metrics={}
for row,method in enumerate(rows):
 frames=[]
 for col,a in enumerate(angles):
  key=f'{a:g}'
  path=R/(prior101[key]['relativePath'] if row==0 else prior103[key]['relativePath'] if row==1 else qa['methods'][method][key]['relativePath'])
  rgba=Image.open(path).convert('RGBA')
  white=Image.new('RGBA',rgba.size,'white');white.alpha_composite(rgba)
  frames.append(np.asarray(white.convert('RGB'),dtype=np.float32))
  contact.paste(white.convert('RGB').crop((365,600,830,1015)).resize((345,365),Image.Resampling.LANCZOS),(345*col,390*row+25))
  pen.text((345*col+5,390*row+7),method+f' {a:g}',fill='black')
 for key,(x0,y0,x1,y1) in regions.items():
  delta=[round(float(np.abs(frames[i][y0:y1,x0:x1]-frames[i-1][y0:y1,x0:x1]).mean()),4) for i in range(1,len(frames))]
  metrics.setdefault(method,{})[key]={'adjacentMAE':delta,
    'maxAdjacentMAE':max(delta),'midpointAdjacentMAE':max(delta[3:5])}
contact.save(D/'detail-garment-contact.jpg',quality=94)
qa['metrics']=metrics
# Compare two warped source ink maps inside the same 67.5° target frame.
comparison={}
for role in roles:
 comparison[role]={}
 for desc,mapping in [('grid',grid.mappings),('detailed',detail_mapping)]:
  ma=mapping(role,.5,'60');mb=mapping(role,.5,'75')
  a=grid.warp(grid.parts['60'][role],ma) if desc=='grid' else warp_detail(grid.parts['60'][role],ma)
  b=grid.warp(grid.parts['75'][role],mb) if desc=='grid' else warp_detail(grid.parts['75'][role],mb)
  def edge(p):
   alpha=np.clip(p[:,:,3:4],0,1)
   rgb=p[:,:,:3]/np.maximum(alpha,1e-6)
   white=np.uint8(np.round(np.clip(rgb*alpha+1-alpha,0,1)*255))
   return cv2.Canny(cv2.cvtColor(white,cv2.COLOR_RGB2GRAY),45,105)>0
  edgeA=edge(a);edgeB=edge(b)
  dilA=cv2.dilate(edgeA.astype(np.uint8),np.ones((5,5),np.uint8))>0
  dilB=cv2.dilate(edgeB.astype(np.uint8),np.ones((5,5),np.uint8))>0
  match=(np.count_nonzero(edgeA&dilB)+np.count_nonzero(edgeB&dilA))
  denom=max(1,np.count_nonzero(edgeA)+np.count_nonzero(edgeB))
  comparison[role][desc]={'edgeAgreementWithin2Px':round(match/denom,5),
     'edgePixels60':int(np.count_nonzero(edgeA)),
     'edgePixels75':int(np.count_nonzero(edgeB))}
qa['inkAlignmentAt67p5']=comparison
qa['contact']='private-assets/exports/p15-104-detail-render/detail-garment-contact.jpg'
(R/'evidence/p15-104-render-qa.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')
print('METRICS',json.dumps({m:{k:round(v['maxAdjacentMAE'],3) for k,v in regions.items()} for m,regions in metrics.items()},indent=2),flush=True)
print('INK_ALIGNMENT',json.dumps(comparison,indent=2),flush=True)

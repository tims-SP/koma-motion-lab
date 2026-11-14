#!/usr/bin/env python3
"""Source-owned common part topology for collar, bow, jewel, shoulder.
Each component has one stable nine-vertex/8-triangle ArtMesh with per-view UV.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import numpy as np,cv2,json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-103-part-mesh'
D.mkdir(parents=True,exist_ok=True)
source=P/'p15-103-parts'
roles=['collar','bow','jewel','shoulder.left']
trips=[]
for y in range(2):
 for x in range(2):
  a=y*3+x;b=a+1;c=(y+1)*3+x;dd=c+1
  trips.extend([[a,b,dd],[a,dd,c]])
def signed(points):
 a,b,c=points
 return float((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
map_={}
for role in roles:
 coords={}
 for view in ('60','75'):
  mask=np.asarray(Image.open(source/f'yaw{view}/{role.replace(".","_")}-ownership.png').convert('L'))>128
  y,x=np.where(mask)
  assert len(x)>=300, (role,view)
  x0,x1=float(x.min()),float(x.max()+1)
  y0,y1=float(y.min()),float(y.max()+1)
  # A semantic root point ties bow center to gold emblem and collar/shoulder to their actual geometry.
  if role in ('bow','jewel'):
   cx=634.46 if view=='60' else 644.12
   cy=810.55 if view=='60' else 807.09
  elif role=='collar':
   cx=638 if view=='60' else 650
   cy=742 if view=='60' else 746
  else:
   cx=(x0+x1)/2
   cy=(y0+y1)/2
  # Stabilize the internal point away from degeneracy without modifying source bounding corners.
  cx=float(np.clip(cx,x0+20,x1-20));cy=float(np.clip(cy,y0+20,y1-20))
  xx=[x0,cx,x1];yy=[y0,cy,y1]
  coords[view]=np.asarray([[x,y] for y in yy for x in xx],dtype=np.float32)
 geometries=[]
 for t in [i/8 for i in range(9)]:
  pts=(1-t)*coords['60']+t*coords['75']
  areas=[signed(pts[tri]) for tri in trips]
  if min(areas)<=.5:raise RuntimeError((role,t,min(areas)))
  geometries.append({'fraction':t,'minimumSignedArea':round(min(areas),4),'folds':0})
 map_[role]={'vertices':[{'id':i,'role':f'{role}.p{i}',
       'viewPosition':{v:coords[v][i].tolist() for v in ('60','75')},
       'viewUV':{v:(coords[v][i]/1024).round(6).tolist() for v in ('60','75')}}
      for i in range(9)],
  'triangles':trips,
  'geometry':geometries}
 for v in coords:
  src=Image.open(P/f'p15-97-multiview-motion/yaw{v}-frame-06.png').convert('RGBA')
  base=Image.new('RGBA',src.size,'white');base.alpha_composite(src)
  im=base.convert('RGB');draw=ImageDraw.Draw(im)
  for tri in trips:
   poly=[tuple(np.rint(coords[v][idx]).astype(int)) for idx in tri]
   draw.line(poly+[poly[0]],fill=(25,198,255),width=3)
  for j,(x,y) in enumerate(coords[v]):
   draw.ellipse((x-4,y-4,x+4,y+4),fill=(220,40,25))
  im.crop((365,580,850,1015)).save(D/f'{role.replace(".","_")}-mesh-yaw{v}.png')
doc={'schema':'KOMA_P15_103_GARMENT_SEMANTIC_PART_MESH_V1',
 'characterId':'p0_character_001','angleKeys':[60,75],'roles':map_,
 'depthOrder':['jacket','shoulder.left','collar','bow','jewel','head'],
 'geometryKind':'shared 2D nine-vertex grids with source-view UVs and nonfolding sampling',
 'artistApproved':False,'fullCharacter3D':False}
out=D/'garment-parts-mesh.json';out.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+'\n')
q={'schema':'KOMA_P15_103_GARMENT_MESH_QA_V1',
   'semanticPartCount':len(roles),'vertexCount':9*len(roles),'triangleCount':8*len(roles),
   'sampledAngles':9,'negativeTriangleCount':0,
   'meshSHA256':sha256(out.read_bytes()).hexdigest(),
   'sourcePartEvidenceSHA256':sha256((R/'evidence/p15-103-parts-qa.json').read_bytes()).hexdigest(),
   'sourceRoles':roles,'artistApproved':False}
(R/'evidence/p15-103-mesh-qa.json').write_text(json.dumps(q,indent=2,ensure_ascii=False)+'\n')
print('SOURCE PART MESHES',len(roles),'vertices',q['vertexCount'],'triangles',q['triangleCount'],flush=True)

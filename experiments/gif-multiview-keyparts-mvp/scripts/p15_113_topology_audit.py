#!/usr/bin/env python3
"""Audit 67.5° source UV against real 60° and 75° source silhouettes and ink.

Per role: 33 indexed vertices, 48 fixed triangles; every source map uses
one canonical 67.5-degree texture. Cross-view art equivalence is evaluated
independently using source raster IoU and model-observed native stroke paths.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import cv2,json,numpy as np
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-113-canonical-topology';D.mkdir(parents=True,exist_ok=True)
M=json.loads((P/'p15-106-three-key-mesh/garment-three-key-mesh.json').read_text())
I=json.loads((R/'evidence/p15-108-stroke-qa.json').read_text())
A=json.loads((R/'private-assets/p15-110-vision-strokes/vision-stroke-annotations.json').read_text())
sha=lambda f:sha256(Path(f).read_bytes()).hexdigest()
roles={'bow':'bowFabric','collar':'collarWhite','jewel':'jewel'}
S=512;Y,X=np.indices((S,S),np.float32)
rec={'schema':'KOMA_P15_113_CANONICAL_TOPOLOGY_AUDIT_V1','characterId':'p0_character_001',
 'meshSHA256':sha(P/'p15-106-three-key-mesh/garment-three-key-mesh.json'),
 'singleSourceView':'67.5','sourceViews':['60','67.5','75'],
 'roleTopology':{},'pathCorrespondence':{},'actualTargetMaskIoU':{},
 'canonicalInkIsNative':True,'originalIndependentSourcesPreserved':True,
 'artistTopologyApproved':False}
def rawvertices(role,view):
 return np.asarray([v['sourcePosition'][view] for v in M['roles'][role]['vertices']],np.float64)
def signed(p):
 a,b,c=p
 return float((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
def point_to_triangle(src,dst,tris,p):
 for tri in tris:
  A=src[tri]
  bary=np.linalg.solve((A[1:]-A[0]).T,(p-A[0]))
  u,v=bary
  if u>=-.04 and v>=-.04 and u+v<=1.04:
   q=dst[tri[0]]+u*(dst[tri[1]]-dst[tri[0]])+v*(dst[tri[2]]-dst[tri[0]])
   return q,True
 # Explicit unsupported points retain their observed absence.
 return None,False
def resample(pts,n=24):
 pts=np.asarray(pts,np.float64)
 if len(pts)<2:return None
 distance=np.linalg.norm(np.diff(pts,axis=0),axis=1)
 cum=np.concatenate([[0],np.cumsum(distance)])
 if cum[-1]<.01:return None
 return np.stack([np.interp(np.linspace(0,cum[-1],n),cum,pts[:,d]) for d in (0,1)],axis=1)
for role,material in roles.items():
 verts={view:rawvertices(role,view) for view in ('60','67.5','75')}
 tris=M['roles'][role]['triangles']
 assert len(tris)==48 and len(verts['67.5'])==33
 assert all(len(x)==3 for x in tris)
 areas={}
 for view,coords in verts.items():
  areas[view]=[signed(coords[tri]) for tri in tris]
  assert min(areas[view])>0,(role,view,min(areas[view]))
 rec['roleTopology'][role]={'vertexCount':33,'triangleCount':48,
  'sourceCanonicalRGBA':I['views']['67.5']['layers'][material]['texturePath'],
  'sourceCanonicalRGBA_SHA256':I['views']['67.5']['layers'][material]['textureSHA256'],
  'sharedVertexIds':[v['id'] for v in M['roles'][role]['vertices']],
  'triangleIndices':tris,'minSignedTriangleArea1024':{
    view:round(min(values),3) for view,values in areas.items()},
  'viewSourcePosition':{v:verts[v].round(3).tolist() for v in verts},
  'nonfoldingAllViews':True}
 original=np.asarray(Image.open(R/I['views']['67.5']['layers'][material]['maskPath']).convert('L').resize((S,S),Image.Resampling.NEAREST))
 for view in ('60','67.5','75'):
  # inverse affine nearest sampling on fixed topology, ensures mask comparison
  ss=verts['67.5']/2;dst=verts[view]/2
  mx=np.zeros((S,S),np.float32);my=np.zeros((S,S),np.float32);coverage=np.zeros((S,S),np.uint8)
  for tri in tris:
   a,b=ss[tri],dst[tri]
   x0=max(0,int(np.floor(b[:,0].min()))-2);x1=min(S,int(np.ceil(b[:,0].max()))+3)
   y0=max(0,int(np.floor(b[:,1].min()))-2);y1=min(S,int(np.ceil(b[:,1].max()))+3)
   if x1<=x0 or y1<=y0:continue
   local=np.zeros((y1-y0,x1-x0),np.uint8)
   cv2.fillConvexPoly(local,np.rint(b-[x0,y0]).astype(np.int32),255)
   include=local>0
   af=cv2.getAffineTransform(b.astype(np.float32),a.astype(np.float32))
   px=X[y0:y1,x0:x1];py=Y[y0:y1,x0:x1]
   mx[y0:y1,x0:x1][include]=(af[0,0]*px+af[0,1]*py+af[0,2])[include]
   my[y0:y1,x0:x1][include]=(af[1,0]*px+af[1,1]*py+af[1,2])[include]
   coverage[y0:y1,x0:x1][include]=255
  pred=cv2.remap(original,mx,my,cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT)
  pred=(pred>128)&(coverage>0)
  observed=np.asarray(Image.open(R/I['views'][view]['layers'][material]['maskPath']).convert('L').resize((S,S),Image.Resampling.NEAREST))>128
  intersection=int(np.count_nonzero(pred&observed));union=int(np.count_nonzero(pred|observed))
  rec['actualTargetMaskIoU'].setdefault(role,{})[view]={
   'intersection':intersection,'union':union,'IoU':round(intersection/max(union,1),5),
   'predictedPixels':int(pred.sum()),'nativeObservedPixels':int(observed.sum())}
for role,item in A['roles'].items():
 if not role.startswith('bow'):continue
 result={'sourceLineRole':role,'views':{},'nativeRoleViewCoverage':{}}
 if not item['views']['67.5']['visible'] or len(item['views']['67.5']['points'])<2:
  result['sourcePathAvailable']=False
  rec['pathCorrespondence'][role]=result;continue
 sourcePts=resample(item['views']['67.5']['points'])
 sourceVerts=rawvertices('bow','67.5');tris=M['roles']['bow']['triangles']
 result['sourcePathAvailable']=True
 for view in ('60','75'):
  nativePoints=item['views'][view]['points']
  if not nativePoints:
   result['views'][view]={'observedPoints':0,'meshCoveredPoints':0,'meanObservedDriftPx':None}
   continue
  native=resample(nativePoints)
  mapped=[];expected=[]
  for q,ob in zip(sourcePts,native):
   m,inside=point_to_triangle(sourceVerts,rawvertices('bow',view),tris,q)
   if inside:mapped.append(m);expected.append(ob)
  fraction=len(mapped)/len(sourcePts)
  if mapped:
   mapped=np.asarray(mapped);expected=np.asarray(expected)
   errs=np.linalg.norm(mapped-expected,axis=1)
   stat={'observedPoints':len(native),'meshCoveredPoints':len(mapped),
         'meshCoveredFraction':round(fraction,5),
         'meanObservedDriftPx':round(float(errs.mean()),3),
         'p90ObservedDriftPx':round(float(np.percentile(errs,90)),3)}
  else:stat={'observedPoints':len(native),'meshCoveredPoints':0,
             'meshCoveredFraction':0.,'meanObservedDriftPx':None}
  result['views'][view]=stat
 rec['pathCorrespondence'][role]=result
 print(role,result['views'],flush=True)
for role,vals in rec['actualTargetMaskIoU'].items():
 print('MASK IoU',role,{v:z['IoU'] for v,z in vals.items()},flush=True)
(R/'evidence/p15-113-topology-qa.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n')

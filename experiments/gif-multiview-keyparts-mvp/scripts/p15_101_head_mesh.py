#!/usr/bin/env python3
"""P0 multi-view shared head/hair shell mesh with face-locked correspondences.

Uses a common indexed Delaunay head envelope and the P15-100 face control points.
This is 2D viewpoint-dependent topology, not a recovered 3D head.
References: LearnOpenCV FaceMorph, Sorkine/Alexa ARAP surface concepts.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,cv2,json,hashlib
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports';D=P/'p15-101-shared-head-mesh';D.mkdir(parents=True,exist_ok=True)
prior=json.loads((P/'p15-100-shared-face-mesh/face-shared-mesh.json').read_text())
# Author-authored per-angle semantic hair boundary correspondences. Names consistent per view.
# Outer contour in clockwise image coordinates, followed by supporting interior hair landmarks.
outer={
'60':[(565,125),(620,160),(692,196),(755,266),(786,355),(786,440),(789,521),(769,555),(738,628),(698,684),(600,704),(505,713),(401,704),(310,693),(233,665),(189,626),(166,551),(173,474),(207,402),(231,322),(276,246),(332,204),(420,160)],
'75':[(555,118),(622,164),(688,196),(748,262),(783,359),(784,437),(816,517),(798,552),(773,617),(737,664),(618,701),(535,694),(443,681),(342,689),(271,671),(199,635),(178,558),(183,469),(213,387),(236,305),(282,234),(343,193),(441,155)]}
interiorRoles=['hair.back.left','hair.back.mid','hair.back.lower',
 'hair.back.tip','hair.center.top','hair.center.mid','hair.front.crown',
 'hair.front.left','hair.front.middle','hair.front.right','hair.front.tip',
 'ear.top','ear.bottom','neck.top']
interior={
 '60':[(280,458),(365,325),(378,584),(533,666),(501,255),(530,360),
        (641,253),(576,419),(658,392),(747,413),(731,490),
        (442,418),(483,543),(562,672)],
 '75':[(281,466),(374,335),(369,599),(538,662),(509,250),(541,357),
        (654,251),(585,410),(683,390),(763,413),(757,486),
        (457,415),(507,545),(572,672)]}
faceRoles=[v['role'] for v in prior['vertices']]
roles=[f'hair.outer.{i:02d}' for i in range(len(outer['60']))]+interiorRoles+['face.'+x for x in faceRoles]
coords={}
for view in ('60','75'):
 face=np.array([p['sourcePosition'][view] for p in prior['vertices']],np.float32)
 coords[view]=np.concatenate((np.asarray(outer[view],np.float32),
           np.asarray(interior[view],np.float32),face),axis=0)
mean=(coords['60']+coords['75'])/2
# Common delaunay over the midpoint viewport; triangle IDs stay stable in both views.
sub=cv2.Subdiv2D((0,0,1024,1024))
for x,y in mean:sub.insert((float(x),float(y)))
triangleSet=set()
for coords3 in sub.getTriangleList().reshape(-1,3,2):
 idx=[]
 for point in coords3:
  diff=np.linalg.norm(mean-point,axis=1);j=int(np.argmin(diff))
  if diff[j]>.4:break
  idx.append(j)
 if len(idx)!=3 or len(set(idx))!=3:continue
 k=tuple(sorted(idx))
 center=mean[list(k)].mean(axis=0)
 if cv2.pointPolygonTest(np.asarray(mean[:len(outer['60'])],np.float32),tuple(center),False)<0:continue
 triangleSet.add(k)
def signed(p):
 a,b,c=p
 return float((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
faces=[];omitted=[]
for tri in sorted(triangleSet):
 a=signed(coords['60'][list(tri)])
 b=signed(coords['75'][list(tri)])
 if a<0 and b<0:tri=(tri[0],tri[2],tri[1]);a=-a;b=-b
 if min(a,b)<2:
  omitted.append({'indices':list(tri),'areas':[round(a,3),round(b,3)]});continue
 faces.append(tri)
sample=[i/8 for i in range(9)]
metrics=[]
for t in sample:
 points=(1-t)*coords['60']+t*coords['75']
 signedAreas=[signed(points[list(tri)]) for tri in faces]
 metrics.append({'ratio':t,'negativeTriangleCount':sum(v<=0 for v in signedAreas),
                 'minimumSignedArea':round(min(signedAreas),4)})
# Preserve negative evidence. The renderer can reject non-topology-safe triangles.
model={'schema':'KOMA_P15_101_SOURCE_HEAD_HAIR_MESH_V1','characterId':'p0_character_001',
 'vertices':[{ 'id':i,'role':r,
        'sourcePosition':{view:coords[view][i].tolist() for view in ('60','75')},
        'viewUV':{view:(coords[view][i]/1024).round(6).tolist() for view in ('60','75')}}
       for i,r in enumerate(roles)],
 'triangles':[list(t) for t in faces],'omitted':omitted,
 'headOuterVertexCount':len(outer['60']),'hairInteriorVertexCount':len(interiorRoles),
 'faceVertexCount':len(faceRoles),'source':'authored P15-101 hair/ear/neck anchors plus P15-100 face mesh',
 'geometryKind':'common indexed 2D head/hair triangulation and view-dependent UV',
 'verified3DGeometry':False,'artistApproved':False}
f=D/'head-hair-shared-mesh.json';f.write_text(json.dumps(model,indent=2,ensure_ascii=False)+'\n')
qa={'schema':'KOMA_P15_101_HEAD_HAIR_GEOMETRY_QA_V1',
 'sourceAngles':[60,75],'vertexCount':len(roles),'triangleCount':len(faces),
 'omittedTriangleCount':len(omitted),'sampledGeometry':metrics,
 'meshSha256':hashlib.sha256(f.read_bytes()).hexdigest(),
 'commonMeshStored':str(f.relative_to(R)),
 'nonfolding':all(x['negativeTriangleCount']==0 for x in metrics),
 'meshIsAnatomical3D':False,'artistApproved':False}
for view in ('60','75'):
 src=Image.open(P/f'p15-97-multiview-motion/yaw{view}-frame-06.png').convert('RGBA')
 im=Image.new('RGBA',src.size,'white');im.alpha_composite(src)
 out=im.convert('RGB');draw=ImageDraw.Draw(out)
 for tri in faces:
  poly=[tuple(np.round(coords[view][j]).astype(int)) for j in tri]
  draw.line(poly+[poly[0]],fill=(250,165,10),width=1)
 path=[tuple(map(int,p)) for p in coords[view][:len(outer['60'])]]
 draw.line(path+[path[0]],fill=(20,195,255),width=3)
 for i,(x,y) in enumerate(coords[view]):
  col=(35,210,240) if i<len(outer['60']) else (235,20,45) if i<len(outer['60'])+len(interiorRoles) else (45,95,210)
  draw.ellipse((x-3,y-3,x+3,y+3),fill=col)
 out.save(D/f'mesh-yaw{view}.png')
(R/'evidence/p15-101-mesh-qa.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')
print('MESH',len(roles),'faces',len(faces),'omitted',len(omitted),'folds',[(m['ratio'],m['negativeTriangleCount']) for m in metrics],flush=True)

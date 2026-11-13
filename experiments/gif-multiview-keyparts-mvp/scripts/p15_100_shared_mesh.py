#!/usr/bin/env python3
"""Generate common P0 face-surface triangle IDs with view-dependent UV correspondence.

Triangulation basis: OpenCV Delaunay of 60/75 mean 2D anchors, inspired by
LearnOpenCV/FaceMorph. Face polygons come from P15-99 source-owned topology.
Per-view UV remains distinct; NOT a recovered anatomical 3D mesh.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import cv2,numpy as np,hashlib,json
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports';D=P/'p15-100-shared-face-mesh'
D.mkdir(parents=True,exist_ok=True)
qaPath=R/'evidence/p15-100-mesh-qa.json'
previous=json.loads((R/'evidence/p15-99-topology-qa.json').read_text())
guides=json.loads((R/'evidence/p15-98-landmarks.json').read_text())
parts={}
for v in ('60','75'):
 polygon=np.asarray(previous['views'][v]['facePolygon'],dtype=np.float32)
 assert polygon.shape==(13,2),polygon.shape
 parts[v]=polygon
# Landmark anchors are a correspondence hypothesis; shadow/skin texels not yet artist verified.
anchorRoles=['eye.near.outer','eye.near.center','eye.near.inner',
             'eye.far.center','nose.bridge','nose.tip','mouth','cheek','chin']
roles=[f'contour.{i:02}' for i in range(13)]+anchorRoles
coords={}
for v in ('60','75'):
 lm=guides['viewLandmarks'][v]
 coords[v]=np.concatenate([parts[v],
      np.asarray([lm[name] for name in anchorRoles],dtype=np.float32)],axis=0)
# Validate that landmark interiors lie on/near the shape (their radius can still be a visual proxy).
contour=(coords['60']+coords['75'])/2
mean=contour/2
div=cv2.Subdiv2D((0,0,512,512))
for pt in mean:div.insert((float(pt[0]),float(pt[1])))
triangles=[]
for raw in div.getTriangleList():
 xy=np.asarray(raw,dtype=np.float32).reshape(3,2)
 if np.any(xy<0) or np.any(xy>=512):continue
 indices=[]
 for corner in xy:
  distances=np.linalg.norm(mean-corner,axis=1)
  j=int(np.argmin(distances))
  if distances[j]>.3:break
  indices.append(j)
 if len(indices)!=3 or len(set(indices))!=3:continue
 faceMid=contour[:13]
 center=(coords['60'][indices]+coords['75'][indices]).mean(axis=0)/2
 # A triangle belongs to the face if centroid is enclosed by the average silhouette polygon.
 if cv2.pointPolygonTest(faceMid,tuple(center),False)<0:continue
 key=tuple(sorted(indices))
 if key not in triangles:triangles.append(key)
triangles.sort()
def signed(p):
 a,b,c=p
 return float((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
verified=[]
excluded=[]
for tri in triangles:
 areas=[signed(coords[v][list(tri)]/2) for v in ('60','75')]
 if all(a<0 for a in areas):tri=(tri[0],tri[2],tri[1]);areas=[-a for a in areas]
 if min(areas)<.4:
  excluded.append({'indices':list(tri),'endpointAreas':areas})
 else:verified.append(tri)
# Exclude unstable triangles as explicit geometry gaps; never silently hide folds.
for fraction in (0,.125,.25,.375,.5,.625,.75,.875,1):
 shape=coords['60']*(1-fraction)+coords['75']*fraction
 for tri in verified:
  if signed(shape[list(tri)]/2)<.4:
   raise RuntimeError(f'Face mesh folded at t={fraction} triangle={tri}')
renderMesh={
 'schema':'KOMA_P15_100_FACE_CORRESPONDENCE_MESH_V1',
 'characterId':'p0_character_001','coordinateFrame':'1024x1024 RGBA source',
 'viewAngles':[60,75],'source':'P15-99 hand-proxy face contour & P15-98 facial anchors',
 'geometryKind':'shared indexed 2D Delaunay/ArtMesh proxy with view-dependent texture coordinates',
 'recoverable3D':False,'artistApproved':False,
 'roles':roles,
 'vertices':[{'index':i,'role':role,
   'sourcePosition':{v:coords[v][i].round(3).tolist() for v in ('60','75')},
   'canonicalUV':(contour[i]/1024).round(6).tolist(),
   'viewUV':{v:(coords[v][i]/1024).round(6).tolist() for v in ('60','75')}}
  for i,role in enumerate(roles)],
 'triangles':[list(v) for v in verified],
 'excludedTriangles':excluded}
file=D/'face-shared-mesh.json'
file.write_text(json.dumps(renderMesh,indent=2,ensure_ascii=False)+'\n')
def render_wire(v,preview):
 src=Image.open(P/f'p15-97-multiview-motion/yaw{v}-frame-06.png').convert('RGBA')
 white=Image.new('RGBA',src.size,'white');white.alpha_composite(src)
 im=white.convert('RGB')
 dr=ImageDraw.Draw(im)
 polygon=[tuple(map(int,point)) for point in coords[v][:13]]
 dr.line(polygon+[polygon[0]],fill=(0,210,255),width=3)
 for tri in verified:
  poly=[tuple(map(int,coords[v][idx])) for idx in tri]
  dr.line(poly+[poly[0]],fill=(255,190,0),width=1)
 for i,role in enumerate(roles):
  x,y=np.round(coords[v][i]).astype(int)
  dr.ellipse([x-3,y-3,x+3,y+3],fill=(255,80,38) if i>=13 else (0,210,255))
 im.save(D/f'mesh-yaw{v}.png')
 return im
render_wire('60',True);render_wire('75',True)
areas=[]
for t in [i/8 for i in range(9)]:
 points=(coords['60']*(1-t)+coords['75']*t)/2
 area=[signed(points[list(tri)]) for tri in verified]
 areas.append({'t':t,'minSignedTriangleArea':round(min(area),4),'foldedTriangleCount':sum(a<=0 for a in area)})
q={'schema':'KOMA_P15_100_SHARED_MESH_GEOMETRY_QA_V1',
  'sourceViews':['60','75'],'vertexCount':len(roles),'triangleCount':len(verified),
  'excludedTriangleCount':len(excluded),'meshJSON':'private-assets/exports/p15-100-shared-face-mesh/face-shared-mesh.json',
  'meshSHA256':hashlib.sha256(file.read_bytes()).hexdigest(),
  'meshType':'view-dependent 2D ArtMesh correspondence, not verified 3D geometry',
  'meshTrianglesNonFolded':all(x['foldedTriangleCount']==0 for x in areas),
  'signedTriangleAreas':areas,'geometryArtistApproved':False,
  'sourceLandmarkSHA256':hashlib.sha256((R/'evidence/p15-98-landmarks.json').read_bytes()).hexdigest(),
  'sourceTopologySHA256':hashlib.sha256((R/'evidence/p15-99-topology-qa.json').read_bytes()).hexdigest()}
qaPath.write_text(json.dumps(q,indent=2,ensure_ascii=False)+'\n')
print('MESH',len(roles),'triangles',len(verified),'excluded',len(excluded),
      'minarea',min(x['minSignedTriangleArea'] for x in areas),flush=True)

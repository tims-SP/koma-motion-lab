#!/usr/bin/env python3
"""Add measured native SIFT garment ink tie-points to source-owned ArtMesh.

Following shared landmark triangular morphology (e.g. LearnOpenCV FaceMorph).
Only retain feature pairs that pass mask containment, 2-view relative displacement,
and strict face orientation checks on both source views plus all nine yaw samples.
Rejected/unused features remain evidence, not a formal art sign-off.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import numpy as np,cv2,json
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports';D=P/'p15-104-detail-mesh';D.mkdir(parents=True,exist_ok=True)
base=json.loads((P/'p15-103-part-mesh/garment-parts-mesh.json').read_text())
features=json.loads((R/'evidence/p15-104-feature-qa.json').read_text())
source=json.loads((R/'evidence/p15-103-parts-qa.json').read_text())
def sha(p):return sha256(Path(p).read_bytes()).hexdigest()
def signed(a):
 p,q,r=a
 return float((q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0]))
def triangulate(left,right):
 mid=(left+right)/2
 triang=cv2.Subdiv2D((0,0,1024,1024))
 for x,y in mid:triang.insert((float(x),float(y)))
 faces=[]
 for coords in np.asarray(triang.getTriangleList(),dtype=np.float32).reshape(-1,3,2):
  indexes=[]
  for corner in coords:
   dist=np.linalg.norm(mid-corner,axis=1)
   k=int(np.argmin(dist))
   if float(dist[k])>.4:break
   indexes.append(k)
  if len(indexes)==3 and len(set(indexes))==3:faces.append(indexes)
 for face in faces:
  at=signed(left[face])
  bt=signed(right[face])
  if at<0 and bt<0:face[1],face[2]=face[2],face[1]
  elif at*bt<=0:return None
  if min(signed(left[face]),signed(right[face]))<5:return None
 return faces
detail={'schema':'KOMA_P15_104_GARMENT_INK_SHARED_MESH_V1',
 'characterId':'p0_character_001','sourceAngles':[60,75],
 'featureMethod':'SIFT mutual ratio / RANSAC + source mask and nonfolding indexed Delaunay',
 'parts':{},'modelPurpose':'per-view 2D source garment ink correspondence',
 'sourceVerifiedByArtist':False}
qa={'schema':'KOMA_P15_104_DETAIL_MESH_QA_V1','roles':{},'sourceSIFTSHA256':sha(R/'evidence/p15-104-feature-qa.json'),
 'sourceArtMeshSHA256':sha(P/'p15-103-part-mesh/garment-parts-mesh.json'),
 'sourceGeometryFolded':False,'formalTopologyApproved':False}
for role,item in base['roles'].items():
 p60=np.asarray([q['viewPosition']['60'] for q in item['vertices']],np.float32)
 p75=np.asarray([q['viewPosition']['75'] for q in item['vertices']],np.float32)
 rec=features['candidates'][role]
 masks={v:np.asarray(Image.open(P/f'p15-103-parts/yaw{v}/{role.replace(".","_")}-ownership.png').convert('L'))>128
        for v in ('60','75')}
 added=[]
 distances=[]
 candidates=sorted(rec['sourcePairs'],key=lambda r:r['descriptorDistance'])
 for match in candidates:
  a=np.asarray(match['60'],np.float32);b=np.asarray(match['75'],np.float32)
  x60,y60=np.rint(a).astype(int);x75,y75=np.rint(b).astype(int)
  if not (0<=x60<1024 and 0<=y60<1024 and 0<=x75<1024 and 0<=y75<1024):continue
  if not masks['60'][y60,x60] or not masks['75'][y75,x75]:continue
  # Reject unphysical normalized location changes relative to whole component extent.
  loA,hiA=np.min(p60,axis=0),np.max(p60,axis=0)
  loB,hiB=np.min(p75,axis=0),np.max(p75,axis=0)
  uvA=(a-loA)/np.maximum(hiA-loA,1)
  uvB=(b-loB)/np.maximum(hiB-loB,1)
  uvDiff=float(np.linalg.norm(uvA-uvB))
  if uvDiff>.33:continue
  if not (np.all(uvA>0.025) and np.all(uvA<.975) and np.all(uvB>0.025) and np.all(uvB<.975)):continue
  if min(np.linalg.norm(p60-a,axis=1))<7 or min(np.linalg.norm(p75-b,axis=1))<7:continue
  if added and (min(np.linalg.norm(np.array([s['60'] for s in added])-a,axis=1))<9 or
                min(np.linalg.norm(np.array([s['75'] for s in added])-b,axis=1))<9):continue
  trial60=np.concatenate([p60,np.array([a],np.float32)],axis=0)
  trial75=np.concatenate([p75,np.array([b],np.float32)],axis=0)
  tris=triangulate(trial60,trial75)
  if tris is None:continue
  p60,p75=trial60,trial75
  added.append({'60':a.tolist(),'75':b.tolist(),'distance':match['descriptorDistance'],
                'normalizedDistance':round(uvDiff,4)})
  distances.append(uvDiff)
 faces=triangulate(p60,p75)
 assert faces is not None
 areas=[]
 for t in [i/8 for i in range(9)]:
  pts=(1-t)*p60+t*p75
  ar=[signed(pts[tri]) for tri in faces]
  if min(ar)<=0:raise RuntimeError((role,t,min(ar)))
  areas.append({'fraction':t,'minSignedArea':round(min(ar),4),'folds':0})
 document={'sourcePositions':{
     '60':p60.round(4).tolist(),'75':p75.round(4).tolist()},
   'vertices':[{'id':i,'semanticRole':f'{role}.ink' if i>=9 else f'{role}.grid',
     'viewUV':{v:(pos[i]/1024).round(6).tolist() for v,pos in [('60',p60),('75',p75)]}}
         for i in range(len(p60))],
   'triangles':faces,'matchedFeatures':added}
 detail['parts'][role]=document
 qa['roles'][role]={'sourceFeatureCandidates':len(candidates),
     'acceptedInteriorCorrespondences':len(added),
     'vertexCount':len(p60),'triangleCount':len(faces),
     'minimumSignedArea':min(x['minSignedArea'] for x in areas),
     'sampledGeometry':areas}
 # Mark feature ties on authentic source art, cropped to independent semantic part view.
 for view,pts in [('60',p60),('75',p75)]:
  art=Image.open(P/f'p15-103-parts/yaw{view}/{role.replace(".","_")}.png').convert('RGBA')
  white=Image.new('RGBA',art.size,'white');white.alpha_composite(art)
  im=white.convert('RGB');draw=ImageDraw.Draw(im)
  for tri in faces:
   poly=[tuple(np.rint(pts[j]).astype(int)) for j in tri]
   draw.line(poly+[poly[0]],fill=(35,153,240),width=1)
  for i,(x,y) in enumerate(pts):
   c=(230,25,40) if i>=9 else (10,110,210)
   draw.ellipse((x-3,y-3,x+3,y+3),fill=c)
  a,b=np.array(pts).min(axis=0),np.array(pts).max(axis=0)
  region=(max(0,int(a[0]-25)),max(0,int(a[1]-25)),
           min(1024,int(b[0]+25)),min(1024,int(b[1]+25)))
  im.crop(region).save(D/f'{role.replace(".","_")}-yaw{view}.png')
 print(role,'accepted',len(added),'/' ,len(candidates),'vertices',len(p60),'triangles',len(faces),flush=True)
outfile=D/'garment-ink-correspondence.json'
outfile.write_text(json.dumps(detail,ensure_ascii=False,indent=2)+'\n')
qa['meshSHA256']=sha(outfile);qa['meshFile']=str(outfile.relative_to(R))
(R/'evidence/p15-104-mesh-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')

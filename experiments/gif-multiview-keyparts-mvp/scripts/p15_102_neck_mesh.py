#!/usr/bin/env python3
"""Build a common neck/collar/torso 2D ArtMesh coupled to the existing head.

Rows track visual anchors; these are source-owned 2D correspondence hypotheses.
The shoulder, collar, bow and bottom canvas share triangle IDs across views.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import json,numpy as np,cv2
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports';D=P/'p15-102-neck-shoulder-mesh';D.mkdir(parents=True,exist_ok=True)
head=json.loads((P/'p15-101-shared-head-mesh/head-hair-shared-mesh.json').read_text())
# Four rows, seven columns. Each row is ordered left-to-right; rows top-to-bottom.
# Center neckline and bow points follow real 60° and 75° art independently.
rows={
 '60':[
 [(0,630),(195,665),(390,675),(565,680),(700,682),(860,670),(1023,630)],
 [(0,747),(175,756),(358,739),(535,731),(694,743),(856,757),(1023,749)],
 [(0,882),(170,879),(355,867),(635,811),(733,870),(871,897),(1023,880)],
 [(0,1023),(170,1023),(356,1023),(622,1023),(744,1023),(878,1023),(1023,1023)]
 ],
 '75':[
 [(0,630),(197,659),(395,674),(590,679),(717,693),(869,673),(1023,630)],
 [(0,747),(163,761),(358,737),(560,736),(730,752),(862,772),(1023,749)],
 [(0,882),(177,889),(373,873),(645,808),(758,879),(883,902),(1023,880)],
 [(0,1023),(177,1023),(374,1023),(666,1023),(757,1023),(884,1023),(1023,1023)]
 ]
}
for view,points in rows.items():
 assert len(points)==4 and all(len(row)==7 for row in points)
 pts=np.asarray(points,np.float32)
 assert np.all(np.diff(pts[:,:,0],axis=1)>0)
 assert np.all(np.diff(pts[:,:,1],axis=0)>0)
tris=[]
for y in range(3):
 for x in range(6):
  a=y*7+x;b=a+1;c=(y+1)*7+x;dd=c+1
  tris.extend([[a,b,dd],[a,dd,c]])
def signed(pts):
 a,b,c=pts;return float((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
coords={v:np.asarray(rows[v],np.float32).reshape(-1,2) for v in rows}
areas=[]
for t in [i/8 for i in range(9)]:
 coord=coords['60']*(1-t)+coords['75']*t
 area=[signed(coord[tri]) for tri in tris]
 assert min(area)>0
 areas.append({'fraction':t,'minimumArea':round(min(area),4),'foldCount':sum(x<=0 for x in area)})
roles=['neck.row'+str(y)+'.'+str(x) for y in range(4) for x in range(7)]
nodes=[{'id':i,'role':role,
        'viewPosition':{v:coords[v][i].tolist() for v in coords},
        'viewUV':{v:(coords[v][i]/1024).round(6).tolist() for v in coords}}
       for i,role in enumerate(roles)]
doc={'schema':'KOMA_P15_102_NECK_SHOULDER_MESH_V1',
 'characterId':'p0_character_001','vertices':nodes,'triangles':tris,
 'sourceAngles':[60,75],'headMeshSHA256':sha256((P/'p15-101-shared-head-mesh/head-hair-shared-mesh.json').read_bytes()).hexdigest(),
 'artModel':'source-owned 2D per-view neck/collar/shoulder warp, not 3D geometry',
 'artistApproved':False}
p=D/'neck-shoulder-mesh.json';p.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+'\n')
for v in coords:
 src=Image.open(P/f'p15-97-multiview-motion/yaw{v}-frame-06.png').convert('RGBA')
 base=Image.new('RGBA',src.size,'white');base.alpha_composite(src)
 out=base.convert('RGB');dr=ImageDraw.Draw(out)
 for tri in tris:
  points=[tuple(map(int,coords[v][idx])) for idx in tri]
  dr.line(points+[points[0]],fill=(240,165,10),width=2)
 for i,(x,y) in enumerate(coords[v]):
  dr.ellipse((x-3,y-3,x+3,y+3),fill=(35,145,255))
 out.save(D/f'mesh-yaw{v}.png')
qa={'schema':'KOMA_P15_102_NECK_MESH_QA_V1','vertices':len(nodes),'triangles':len(tris),
 'nonfolding':True,'sampleAngles':areas,'meshSHA256':sha256(p.read_bytes()).hexdigest(),
 'meshPath':str(p.relative_to(R)),'headMeshLinked':True,'artistApproved':False}
(R/'evidence/p15-102-neck-mesh-qa.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')
print('neck mesh',len(nodes),'vertices',len(tris),'triangles; folded',sum(q['foldCount'] for q in areas),flush=True)

#!/usr/bin/env python3
"""Make a 45–90 degree view-dependent interpolation study with independent Codex yaw60 art."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,hashlib,json,sys
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
from flow_render import get_flow,morph
P=R/'private-assets/exports/p15-92-angle-keyart'
E=R/'evidence/p15-92-view-flow-qa.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
angles={45:P/'yaw045-reference.png',60:P/'yaw060-registered.png',75:P/'yaw075-registered.png',90:P/'yaw090-reference.png'}
keys={a:np.asarray(Image.open(p).convert('RGBA')).copy() for a,p in angles.items()}
dim=512
small={a:np.asarray(Image.fromarray(keys[a],'RGBA').resize((dim,dim),Image.Resampling.LANCZOS)).copy() for a in keys}
flow={}
for a,b in ((45,60),(60,75),(75,90)):
 flow[(a,b)]=get_flow(small[a],small[b],'dis')
yy,xx=np.indices((dim,dim),dtype=np.float32)
grid=np.stack((xx,yy),axis=2)
samples=[45,52.5,60,67.5,75,82.5,90]
frames={}
for angle in samples:
 if angle in keys:
  out=Image.fromarray(keys[angle],'RGBA')
 else:
  a,b=(45,60) if angle<60 else ((60,75) if angle<75 else (75,90))
  img=morph(small[a],small[b],*flow[(a,b)],(angle-a)/(b-a),grid,single_source=False)
  out=Image.fromarray(img,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
 name=('yaw%05.1f'%angle).replace('.','p')+'.png'
 path=P/name
 out.save(path)
 frames[str(angle)]={'path':str(path.relative_to(R)),'sha256':sha(path),'independentKeyart':angle in keys}
# Build a consistent 7-angle overview.
w=310;h=355
contact=Image.new('RGB',(w*len(samples),h),'white');d=ImageDraw.Draw(contact)
for i,ang in enumerate(samples):
 path=R/frames[str(ang)]['path']
 image=Image.open(path).convert('RGBA')
 bg=Image.new('RGBA',image.size,'white');bg.alpha_composite(image)
 thumb=bg.convert('RGB').resize((w,320),Image.Resampling.LANCZOS)
 contact.paste(thumb,(i*w,27))
 d.text((i*w+6,8),f'yaw {ang:g} deg',fill='black')
contact.save(P/'seven-angle-contact.jpg',quality=93)
q={'schema':'KOMA-P15-92-INDEPENDENT_KEYVIEW_FLOW_QA_V1','sourceAngles':[45,60,75,90],
   'independentSourceHashes':{str(a):sha(p) for a,p in angles.items()},
   'interpolation':'OpenCV DIS bidirectional optical flow between independent raster keyviews',
   'interpolationOnlyAngles':[52.5,67.5,82.5],
   'frames':frames,'contact':'private-assets/exports/p15-92-angle-keyart/seven-angle-contact.jpg',
   'modelYawTargets':[60,75],'actualGeometricYawConfirmed':False,
   'formalKeyframeAccepted':False,'formalArtMeshAccepted':False,
   'visualGate':'VIEW_CONTINUITY_PREVIEW_REQUIRES_ART_REVIEW'}
E.write_text(json.dumps(q,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'frames':len(frames),'independentSources':len(angles),'interpolatedViews':len(samples)-len(angles),
 'contact':q['contact'],'status':q['visualGate']},indent=2))

#!/usr/bin/env python3
"""Explicit semantic occlusion topology renderer: 60°→75° independent keyart.
Compare per-layer view ownership against P15-98 full-frame anchor blending.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json,statistics
import numpy as np,cv2
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports'
D=P/'p15-99-vdd-review';D.mkdir(exist_ok=True)
A=P/'p15-99-topology'
ref=json.loads((R/'evidence/p15-98-landmarks.json').read_text())
base=json.loads((R/'evidence/p15-98-anchor-vdd-qa.json').read_text())
topology=json.loads((R/'evidence/p15-99-topology-qa.json').read_text())
source={'60':P/'p15-97-multiview-motion/yaw60-frame-06.png',
        '75':P/'p15-97-multiview-motion/yaw75-frame-06.png'}
assert all(topology['views'][v]['pixelExactReconstruction'] for v in source)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
N=512;Y,X=np.indices((N,N),dtype=np.float32);GRID=np.stack((X,Y),axis=2)
roles=topology['occlusionOrder']
data={}
for view in source:
 d=A/f'yaw{view}'
 parts={}
 for role in roles:
  im=Image.open(d/(role.replace('.','_')+'.png')).convert('RGBA')
  parts[role]=np.asarray(im.resize((N,N),Image.Resampling.LANCZOS)).copy()
 # Synthetic semantic hidden-face underpaint, strictly a donor not part of source-owned pixel decomposition.
 model=Image.open(R/topology['views'][view]['modelUnderpaint']).convert('RGBA')
 polygon=Image.new('L',(1024,1024),0)
 ImageDraw.Draw(polygon).polygon(topology['views'][view]['facePolygon'],fill=255)
 area=np.asarray(polygon.resize((N,N),Image.Resampling.BILINEAR),dtype=np.float32)/255
 draw=np.asarray(model.resize((N,N),Image.Resampling.LANCZOS)).copy()
 draw[:,:,3]=np.uint8(np.round(np.asarray(draw[:,:,3],dtype=np.float32)*area))
 parts['face.underpaint']=draw
 data[view]=parts
angles=[60,61.875,63.75,65.625,67.5,69.375,71.25,73.125,75]
rolesWithHidden=['other.rear','face.underpaint']+roles[1:]
qa={'schema':'KOMA_P15_99_EXPLICIT_OCCLUSION_TOPOLOGY_VDD_V1',
  'sourceYaw':[60,75],'angles':angles,'sampledHeadMotion':'P15-97 6px hair-tip offset',
  'semantics':'source-owned split layers with separate model underdraw and explicit near/far eye visibility',
  'maskSource':'actual SAM3 near eye, far eye and front hair + visually authored skin/contour proxy',
  'layerDepthOrder':rolesWithHidden,
  'roleVisibility':{'eye.far':{'60':1,'75':0},'eye.near':{'60':1,'75':1}},
  'hiddenFaceSource':{v:topology['views'][v]['modelUnderpaint'] for v in source},
  'artistApproved':False,'continuousYawAccepted':False,
  'methods':{},'geometry':{},'sourceSHA256':{v:sha(f) for v,f in source.items()}}
def keypoints(v):
 f=ref['viewLandmarks'][v]
 features=ref['correspondenceRoles']
 can=ref['fixedCanvasAnchors']
 coords=[f[k] for k in features]+[can[k] for k in can]
 return np.asarray(coords,dtype=np.float32)/2
coordsA=keypoints('60');coordsB=keypoints('75')
def inv_map(src,tgt):
 sigma=67
 pair= tgt[:,None,:]-tgt[None,:,:]
 ker=np.exp(-np.sum(pair*pair,axis=2)/(2*sigma*sigma))
 coeff=np.linalg.solve(ker+np.eye(len(src),dtype=np.float32)*.025,src-tgt)
 positions=GRID.reshape(-1,2)
 field=np.empty_like(positions)
 for start in range(0,len(positions),12000):
  sub=positions[start:start+12000]
  diff=sub[:,None,:]-tgt[None,:,:]
  phi=np.exp(-np.sum(diff*diff,axis=2)/(2*sigma*sigma))
  field[start:start+12000]=phi@coeff
 return (GRID+np.clip(field.reshape(N,N,2),-65,65)).astype(np.float32)
def warp(arr,coords):
 # Keep alpha premultiplied so source pixels have valid subpixel edges.
 f=arr.astype(np.float32)/255
 prem=np.concatenate((f[:,:,:3]*f[:,:,3:4],f[:,:,3:4]),axis=2)
 w=cv2.remap(prem,coords[:,:,0],coords[:,:,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
 return np.clip(w,0,1)
def over(dst,src):
 a=src[:,:,3:4]
 return np.concatenate((src[:,:,:3]+dst[:,:,:3]*(1-a),a+dst[:,:,3:4]*(1-a)),axis=2)
def blend(a,b,t):
 return np.clip(a*(1-t)+b*t,0,1)
def to_rgba(prem):
 al=np.clip(prem[:,:,3:4],0,1)
 rgb=np.clip(prem[:,:,:3]/np.maximum(al,1e-6),0,1)
 return np.uint8(np.round(np.concatenate((rgb,al),axis=2)*255))
def render(t,method,maps):
 a,b=maps
 alphaA={role:warp(data['60'][role],a) for role in rolesWithHidden}
 alphaB={role:warp(data['75'][role],b) for role in rolesWithHidden}
 result=np.zeros((N,N,4),dtype=np.float32)
 # Combined source-owned rear hair / clothing can retain limited cross-fade.
 result=over(result,(alphaA['other.rear'] if t<.5 else alphaB['other.rear']) if method=='topology_rear_owner' else blend(alphaA['other.rear'],alphaB['other.rear'],t))
 # Hidden face underpainting is chosen with the face identity, behind the owned visible skin.
 faceView='60' if t<.5 else '75'
 result=over(result,alphaA['face.underpaint'] if faceView=='60' else alphaB['face.underpaint'])
 if method=='topology_blended_skin':
  face=blend(alphaA['face.skin'],alphaB['face.skin'],t)
 else:
  face=alphaA['face.skin'] if faceView=='60' else alphaB['face.skin']
 result=over(result,face)
 # Profile line and nose contour come from one view to prevent doubled jaw ink.
 result=over(result,alphaA['face.contour'] if faceView=='60' else alphaB['face.contour'])
 # The source 60° far eye occludes behind the foreground bangs, then disappears in profile.
 farVis=np.clip((0.62-t)/0.62,0,1)
 if method=='topology_staged':farVis=np.clip((0.45-t)/0.45,0,1)
 far=alphaA['eye.far']*farVis
 result=over(result,far)
 nearView='60' if t<(.5 if method!='topology_staged' else .625) else '75'
 result=over(result,alphaA['eye.near'] if nearView=='60' else alphaB['eye.near'])
 hairView='60' if t<(.5 if method!='topology_staged' else .375) else '75'
 result=over(result,alphaA['hair.front'] if hairView=='60' else alphaB['hair.front'])
 # Final foreground identity accent is source-owned gold hairclip.
 result=over(result,alphaA['hair.clip'] if t<.5 else alphaB['hair.clip'])
 return to_rgba(result)
methods=['topology_nearest','topology_blended_skin','topology_staged','topology_rear_owner']
for method in methods:qa['methods'][method]={}
for angle in angles:
 t=(angle-60)/15
 existing={method:D/(method+'-yaw'+f'{angle:g}'.replace('.','p')+'.png') for method in methods}
 if all(f.is_file() for f in existing.values()):
  for method,f in existing.items():
   qa['methods'][method][f'{angle:g}']={'file':str(f.relative_to(R)),'sha256':sha(f),'keyviewExact':t in (0,1)}
  print('reuse',angle,flush=True)
  continue
 if t<=0:matA=GRID;matB=None
 elif t>=1:matA=None;matB=GRID
 else:
  middle=coordsA*(1-t)+coordsB*t
  matA=inv_map(coordsA,middle);matB=inv_map(coordsB,middle)
 for method in methods:
  if t==0:full=Image.open(source['60']).convert('RGBA')
  elif t==1:full=Image.open(source['75']).convert('RGBA')
  else:
   sample=render(t,method,(matA,matB))
   full=Image.fromarray(sample,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
  f=D/(method+'-yaw'+f'{angle:g}'.replace('.','p')+'.png')
  full.save(f)
  qa['methods'][method][f'{angle:g}']={'file':str(f.relative_to(R)),
     'sha256':sha(f),'keyviewExact':t in (0,1)}
 print('angle',angle,'done',flush=True)
# Side-by-side actual original baseline and compositing approaches.
comp=Image.new('RGB',(370*len(angles),405*(1+len(methods))),'white');draw=ImageDraw.Draw(comp)
def baseline_path(angle):
 return R/base['methodFrames']['landmark_blend'][f'{angle:g}']['relativePath'] if angle in (60,63.75,67.5,71.25,75) else None
for row,name in enumerate(['P15-98-anchor-blend']+methods):
 qframes=[]
 for col,angle in enumerate(angles):
  path=baseline_path(angle) if row==0 else R/qa['methods'][name][f'{angle:g}']['file']
  if path is None:continue
  im=Image.open(path).convert('RGBA')
  white=Image.new('RGBA',im.size,'white');white.alpha_composite(im)
  crop=white.convert('RGB').crop((480,290,835,645))
  qframes.append((angle,np.asarray(crop,dtype=np.float32)))
  tile=crop.resize((370,370),Image.Resampling.LANCZOS)
  comp.paste(tile,(col*370,row*405+26))
  draw.text((col*370+5,row*405+6),f'{name} {angle:g}',fill='black')
 if row>0:
  diffs=[]
  for i in range(1,len(qframes)):
   diffs.append(round(float(np.abs(qframes[i][1]-qframes[i-1][1]).mean()),4))
  qa.setdefault('metrics',{})[name]={'adjacentFaceMAE':diffs,'maxAdjacentMAE':max(diffs),
   'meanAdjacentMAE':round(statistics.mean(diffs),4),'midpointJumpMAE':max(diffs[3:5])}
comp.save(D/'topology-vdd-contact.jpg',quality=93)
qa['contact']='private-assets/exports/p15-99-vdd-review/topology-vdd-contact.jpg'
(R/'evidence/p15-99-topology-vdd-qa.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')
print('METRICS',json.dumps(qa['metrics'],indent=2))

#!/usr/bin/env python3
"""P0 source-owned 60/67.5/75 garment layer composition using genuine inferred art.

Transparent AI-drawn collar and bow interiors are composited strictly BEHIND
native visible source-owned bow and golden jewel. Original garment source
textures, head, hair, and yaw keyframes remain intact. Test two compositors:
premultiplied layer interpolation and source-owner brooch.

Measured occlusion coverage is structural evidence. Aesthetic acceptance
requires direct full-frame preview; source-hidden material is inferred.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import json,cv2,numpy as np,statistics
import p15_101_head_render as head
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-111-layered-render';D.mkdir(parents=True,exist_ok=True)
srcQA=json.loads((R/'evidence/p15-111-source-qa.json').read_text())
roleQA=json.loads((R/'evidence/p15-108-stroke-qa.json').read_text())
comp=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
old=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
sha=lambda f:sha256(Path(f).read_bytes()).hexdigest()
S=512;Y,X=np.indices((S,S),np.float32);angles=head.angles
views=['60','67.5','75']
def load(file):
 return np.asarray(Image.open(file).convert('RGBA').resize((S,S),Image.Resampling.LANCZOS))
def prem(img):
 a=img.astype(np.float32)/255
 return np.concatenate([a[:,:,:3]*a[:,:,3:4],a[:,:,3:4]],axis=2)
def unprem(p):
 alpha=np.clip(p[:,:,3:4],0,1)
 rgb=np.clip(p[:,:,:3]/np.maximum(alpha,1e-6),0,1)
 return np.uint8(np.round(np.concatenate((rgb,alpha),axis=2)*255))
def over(back,front):
 alpha=np.clip(front[:,:,3:4],0,1)
 return np.concatenate([front[:,:,:3]+back[:,:,:3]*(1-alpha),
                        alpha+back[:,:,3:4]*(1-alpha)],axis=-1)
def face(t):
 maps={view:head.mesh_map(view,t) for view in ('60','75')}
 return head.skin_blend(head.warp(head.parts['60']['head'],maps['60']),
                        head.warp(head.parts['75']['head'],maps['75']),t)
def subview(a):
 z=float(a)
 return str(int(z)) if z.is_integer() else str(a)
layers={}
for view in views:
 record=roleQA['views'][view]['layers']
 hidden=srcQA['layers'][view]
 images={}
 for part in ('background','goldTrim','collarWhite','bowFabric','jewel'):
  images[part]=prem(load(R/record[part]['texturePath']))
 for role in ('collar','bow'):
  images[role+'Under']=prem(load(R/hidden[role]['hiddenOnlyPath']))
 layers[view]=images
def segment(angle):
 if angle<=67.5:return '60','67.5',float((angle-60)/7.5)
 return '67.5','75',float((angle-67.5)/7.5)
centers={'60':np.array([634.46,810.55],np.float32)/2,
         '67.5':np.array([639.29,808.82],np.float32)/2,
         '75':np.array([644.12,807.09],np.float32)/2}
def translate(layer,dx,dy):
 matrix=np.float32([[1,0,dx],[0,1,dy]])
 return cv2.warpAffine(layer,matrix,(S,S),flags=cv2.INTER_LINEAR,
             borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
def layered(angle,mode):
 a,b,t=segment(angle)
 def blend(name):
  return np.clip((1-t)*layers[a][name]+t*layers[b][name],0,1)
 bg=np.zeros((S,S,4),np.float32)
 for role in ('background','goldTrim','collarUnder','collarWhite','bowUnder'):
  bg=over(bg,blend(role))
 if mode=='layered_full':
  bg=over(bg,blend('bowFabric'))
  bg=over(bg,blend('jewel'))
 elif mode in ('layered_jewel_owner','layered_bow_owner'):
  if mode=='layered_bow_owner':
   view=a if t<.5 else b
   ownerCenter=centers[view];destCenter=centers[a]*(1-t)+centers[b]*t
   bg=over(bg,translate(layers[view]['bowFabric'],*(destCenter-ownerCenter)))
  else:
   bg=over(bg,blend('bowFabric'))
  sourceView=a if t<.5 else b
  ownerCenter=centers[sourceView];destCenter=centers[a]*(1-t)+centers[b]*t
  bg=over(bg,translate(layers[sourceView]['jewel'],*(destCenter-ownerCenter)))
 else:raise ValueError(mode)
 tHead=(angle-60)/15
 result=over(bg,face(tHead))
 result=over(result,head.get_ahoge(tHead))
 return unprem(np.clip(result,0,1)),{'segment':[a,b],'t':round(t,5),
   'collarArtwork':'registered inferred collar under native fabric',
   'bowArtwork':'registered inferred bow under native golden jewel',
   'sourceNativeJewel':mode!='layered_full'}
methods=['layered_full','layered_jewel_owner','layered_bow_owner']
q={'schema':'KOMA_P15_111_SOURCE_HIDDEN_GARMENT_LAYER_RENDER_V1',
 'character':'p0_character_001','sourceAngles':[60,67.5,75],
 'renderAngles':angles,'sourceArtSHA256':sha(R/'evidence/p15-111-source-qa.json'),
 'layerCountPerView':7,'hiddenOriginalGenuineModelImages':6,
 'method':'source-owned separate image layers, independent depth and correspondence',
 'drawingOrder':['background','goldTrim','collarUnder','collarWhite','bowUnder','bowFabric','jewel','headHair'],
 'inferredArtGroundTruth':False,'visualApproved':False,
 'methods':{m:{} for m in methods},'hiddenCoverage':{
  view:{role:record['hiddenCoverageFraction'] for role,record in z.items()}
  for view,z in srcQA['layers'].items()}}
for angle in angles:
 for mode in methods:
  if angle in (60,67.5,75):
   p=R/comp['methods']['companion_direct_native_keys'][f'{angle:g}']['relativePath']
   image=Image.open(p).convert('RGBA')
   meta={'exactFullCharacterSource':True}
  else:
   frame,meta=layered(angle,mode)
   image=Image.fromarray(frame,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
  dest=D/(mode+'-yaw'+f'{angle:g}'.replace('.','p')+'.png')
  image.save(dest)
  q['methods'][mode][f'{angle:g}']={'path':str(dest.relative_to(R)),'sha256':sha(dest),'diagnostics':meta}
 print('FRAME',angle,flush=True)
methodsRef={'P15-101-original':{k:v['relativePath'] for k,v in old['methods']['head_alpha_blend'].items()},
 'P15-107-three-native':{k:v['relativePath'] for k,v in comp['methods']['companion_direct_native_keys'].items()}}
methodsRef.update({m:{k:rec['path'] for k,rec in frames.items()} for m,frames in q['methods'].items()})
regions={'bow':(500,744,790,975),'jewel':(595,770,701,862),
 'collar':(400,665,805,835),'garment':(335,655,865,1015),
 'head':(440,285,840,640)}
contact=Image.new('RGB',(335*len(angles),377*len(methodsRef)),'white')
draw=ImageDraw.Draw(contact)
for row,(method,frames) in enumerate(methodsRef.items()):
 rgb=[]
 for col,angle in enumerate(angles):
  image=Image.open(R/frames[f'{angle:g}']).convert('RGBA')
  white=Image.new('RGBA',image.size,'white');white.alpha_composite(image)
  rgb.append(np.asarray(white.convert('RGB'),np.float32))
  contact.paste(white.convert('RGB').crop((365,615,845,1015)).resize((335,353),Image.Resampling.LANCZOS),(col*335,row*377+23))
  draw.text((col*335+4,row*377+4),method+f' {angle:g}',fill='black')
 for roi,(x0,y0,x1,y1) in regions.items():
  dif=[round(float(np.abs(rgb[i][y0:y1,x0:x1]-rgb[i-1][y0:y1,x0:x1]).mean()),4)
       for i in range(1,len(rgb))]
  q.setdefault('metrics',{}).setdefault(method,{})[roi]={
   'adjacentRGBMAE':dif,'maxAdjacentRGBMAE':max(dif),
   'interiorMaxRGBMAE':max(dif[1:7]),
   'meanAdjacentRGBMAE':round(statistics.mean(dif),4)}
contact.save(D/'hidden-material-layer-contact.jpg',quality=93)
q['contact']=str((D/'hidden-material-layer-contact.jpg').relative_to(R))
(R/'evidence/p15-111-render-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print('METRICS',json.dumps({mode:{k:v['maxAdjacentRGBMAE'] for k,v in rec.items() if k in ('bow','collar','jewel')}
 for mode,rec in q['metrics'].items()},indent=2),flush=True)

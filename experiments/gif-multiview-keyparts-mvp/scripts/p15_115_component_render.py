#!/usr/bin/env python3
"""P0 P15-115: canonical bow/jewel and piecewise trim, native collar + underpaint.

Every visible ribbon and jewel pixel comes from the same original 67.5-degree
native art at every yaw. Native right gold trim is explicitly retained at
75-degree occlusion. Compare source-target silhouette matte vs raw canonical
material, and continuous native garment background vs source-owner background.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import json,cv2,numpy as np,statistics
import p15_101_head_render as head
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-115-component-render';D.mkdir(exist_ok=True,parents=True)
reg=json.loads((R/'evidence/p15-115-source-qa.json').read_text())
collar=json.loads((R/'evidence/p15-114-source-qa.json').read_text())
layers=json.loads((R/'evidence/p15-108-stroke-qa.json').read_text())
hidden=json.loads((R/'evidence/p15-111-source-qa.json').read_text())
ref101=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
ref107=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
ref114=json.loads((R/'evidence/p15-114-render-qa.json').read_text())
sha=lambda p:sha256(Path(p).read_bytes()).hexdigest()
S=512;angles=ref107['angles'];keys=('60','67.5','75')
def im(file,mode='RGBA',method=Image.Resampling.LANCZOS):
 return np.asarray(Image.open(file).convert(mode).resize((S,S),method))
def pre(image):
 f=image.astype(np.float32)/255
 return np.concatenate((f[:,:,:3]*f[:,:,3:4],f[:,:,3:4]),axis=-1)
def unpre(p):
 a=np.clip(p[:,:,3:4],0,1)
 return np.uint8(np.round(np.concatenate((np.clip(p[:,:,:3]/np.maximum(a,1e-6),0,1),a),axis=-1)*255))
def over(b,a):
 alpha=np.clip(a[:,:,3:4],0,1)
 return np.concatenate((a[:,:,:3]+b[:,:,:3]*(1-alpha),alpha+b[:,:,3:4]*(1-alpha)),axis=-1)
def seg(a):
 if a<=67.5:return '60','67.5',float((a-60)/7.5)
 return '67.5','75',float((a-67.5)/7.5)
brooch={'60':np.array([634.46,810.55],np.float32)/2,
 '67.5':np.array([639.29,808.82],np.float32)/2,
 '75':np.array([644.12,807.09],np.float32)/2}
def shift(preArr,dx,dy):
 return cv2.warpAffine(preArr,np.float32([[1,0,dx],[0,1,dy]]),(S,S),flags=cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
def interpolate_mat(Wa,Wb,t):
 return ((1-t)*np.asarray(Wa,np.float32)+t*np.asarray(Wb,np.float32)).astype(np.float32)
def warp(source,W):
 return cv2.warpAffine(source,W,(S,S),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,
                       borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
def dist_mat(mask):
 m=np.uint8(mask>.5)
 return cv2.distanceTransform(np.uint8(m==0),cv2.DIST_L2,3)-cv2.distanceTransform(m,cv2.DIST_L2,3)
base={}
matte={}
nativeRight={}
for view in keys:
 z=layers['views'][view]['layers']
 base[view]=pre(im(R/z['background']['texturePath']))
 nativeRight[view]=pre(im(R/reg['registered']['goldTrimRight'][view]['registeredPath']))
 matte[view]={}
 for role in ('bowFabric','jewel','goldTrimLeft','goldTrimRight','collarWhite'):
  name='goldTrim' if role.startswith('goldTrim') else role
  binary=im(R/z[name]['maskPath'],'L',Image.Resampling.NEAREST)>128
  if role=='goldTrimLeft':binary[:,342:]=False
  if role=='goldTrimRight':binary[:,:342]=False
  matte[view][role]=binary.astype(np.float32)
art={}
for role in ('bowFabric','jewel','goldTrimLeft','goldTrimRight'):
 canon=im(R/reg['registered'][role]['67.5']['registeredPath'])
 art[role]=pre(canon)
art['collarWhite']=pre(im(R/collar['views']['67.5']['canonicalCollarPath']))
art['collarUnder']=pre(im(R/hidden['layers']['67.5']['collar']['hiddenOnlyPath']))
art['bowUnder']=pre(im(R/hidden['layers']['67.5']['bow']['hiddenOnlyPath']))
def interpolated(role,angle,masked=False):
 a,b,t=seg(angle)
 if role in ('collarWhite','collarUnder'):
  wa=collar['views'][a]['inverseMap512'];wb=collar['views'][b]['inverseMap512']
 else:
  meshRole='bowFabric' if role=='bowUnder' else role
  wa=reg['registered'][meshRole][a]['inverseAffine512']
  wb=reg['registered'][meshRole][b]['inverseAffine512']
 W=interpolate_mat(wa,wb,t)
 output=warp(art[role],W)
 if masked and role in ('bowFabric','jewel','goldTrimLeft','collarWhite'):
  key='collarWhite' if role=='collarWhite' else role
  d0=dist_mat(matte[a][key]);d1=dist_mat(matte[b][key])
  # Signed-distance target silhouette, aligned to the native material labels.
  shape=np.clip((.55-((1-t)*d0+t*d1))/1.5,0,1)
  output*=shape[:,:,None]
 return output
def background(angle,mode):
 a,b,t=seg(angle)
 if mode=='owner_body':
  owner=a if t<.5 else b
  delta=(1-t)*brooch[a]+t*brooch[b]-brooch[owner]
  return shift(base[owner],float(delta[0]),float(delta[1])),owner
 # Align native source backgrounds on the observed brooch anchor before mixing.
 point=(1-t)*brooch[a]+t*brooch[b]
 A=shift(base[a],*(point-brooch[a]))
 B=shift(base[b],*(point-brooch[b]))
 return (1-t)*A+t*B,'native_pair'
def gold_right(angle):
 a,b,t=seg(angle)
 if a!='67.5':return interpolated('goldTrimRight',angle),{'rightOwner':'67.5 canonical'}
 # The thin 75° right lapel trim is a different visible segment. Use the
 # native source, aligned at the brooch, with an explicitly recorded handoff.
 canonical=warp(art['goldTrimRight'],interpolate_mat(
   reg['registered']['goldTrimRight'][a]['inverseAffine512'],
   reg['registered']['goldTrimRight'][b]['inverseAffine512'],t))
 owner=shift(nativeRight['75'],*((1-t)*brooch[a]+t*brooch[b]-brooch['75']))
 weight=t*t*(3-2*t)
 return (1-weight)*canonical+weight*owner,{'rightOwner':'canonical-to-native75','rightOwnerBlend':round(weight,4)}
def face(angle):
 t=(angle-60)/15
 maps={v:head.mesh_map(v,t) for v in ('60','75')}
 return head.skin_blend(head.warp(head.parts['60']['head'],maps['60']),
                        head.warp(head.parts['75']['head'],maps['75']),t)
def render(angle,mode):
 masked=(mode=='target_matte')
 torso,torsoOwner=background(angle,'owner_body' if mode=='owner_body' else 'blend_body')
 result=torso
 for role in ('goldTrimLeft','goldTrimRight','collarUnder','collarWhite','bowUnder','bowFabric','jewel'):
  if role=='goldTrimRight':part,ownership=gold_right(angle)
  else:part=interpolated(role,angle,masked=masked)
  result=over(result,part)
 result=over(over(result,face(angle)),head.get_ahoge((angle-60)/15))
 return unpre(np.clip(result,0,1)),{'torsoSource':torsoOwner,
  'bowSource':'registered native 67.5 single texture',
  'jewelSource':'registered native 67.5 single texture',
  'goldLeftSource':'registered native 67.5',
  **ownership,'targetSilhouetteMatte':masked}
methods=['registered_full','target_matte','owner_body']
q={'schema':'KOMA_P15_115_NATIVE_PART_SOURCE_CORRESPONDENCE_V1',
 'characterId':'p0_character_001','sourceViews':[60,67.5,75],
 'angles':angles,'sourceRegistrySHA256':sha(R/'evidence/p15-115-source-qa.json'),
 'collarRegistrySHA256':sha(R/'evidence/p15-114-source-qa.json'),
 'canonicalView':'67.5','sourceArtPreserved':True,
 'roles':reg['roles'],'methods':{m:{} for m in methods},
 'sourceExceptions':{'goldTrimRight75':'physical source-native after correspondence mask failure'},
 'fullYawVisualApproved':False}
for angle in angles:
 for method in methods:
  pixels,metadata=render(angle,method)
  path=D/(method+'-yaw'+f'{angle:g}'.replace('.','p')+'.png')
  Image.fromarray(pixels,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS).save(path)
  q['methods'][method][f'{angle:g}']={'path':str(path.relative_to(R)),
     'sha256':sha(path),'ownerAudit':metadata}
 print('FRAME',angle,flush=True)
references={
 'P15-101-original':{k:r['relativePath'] for k,r in ref101['methods']['head_alpha_blend'].items()},
 'P15-107-native':{k:r['relativePath'] for k,r in ref107['methods']['companion_direct_native_keys'].items()},
 'P15-114-collar':{k:r['path'] for k,r in ref114['methods']['source_collar_continuous'].items()},
 **{m:{k:r['path'] for k,r in frames.items()} for m,frames in q['methods'].items()}}
zones={'bow':(500,744,790,975),'collar':(400,665,805,835),
 'jewel':(595,770,701,862),'goldTrim':(405,775,805,1015),
 'garment':(335,655,865,1015)}
contact=Image.new('RGB',(340*len(angles),380*len(references)),'white')
draw=ImageDraw.Draw(contact)
for row,(method,files) in enumerate(references.items()):
 images=[]
 for col,angle in enumerate(angles):
  img=Image.open(R/files[f'{angle:g}']).convert('RGBA')
  white=Image.new('RGBA',img.size,'white');white.alpha_composite(img)
  images.append(np.asarray(white.convert('RGB'),np.float32))
  contact.paste(white.convert('RGB').crop((365,615,845,1015)).resize((340,354),Image.Resampling.LANCZOS),(col*340,row*380+26))
  draw.text((col*340+4,row*380+5),method+f' {angle:g}',fill='black')
 for zone,(x0,y0,x1,y1) in zones.items():
  dif=[round(float(np.abs(images[i][y0:y1,x0:x1]-images[i-1][y0:y1,x0:x1]).mean()),4)
       for i in range(1,len(images))]
  q.setdefault('metrics',{}).setdefault(method,{})[zone]={
   'adjacentRGBMAE':dif,'maxAdjacentRGBMAE':max(dif),
   'meanAdjacentRGBMAE':round(statistics.mean(dif),4),
   'interiorMaxRGBMAE':max(dif[1:7])}
contact.save(D/'component-yaw-contact.jpg',quality=93)
q['contact']=str((D/'component-yaw-contact.jpg').relative_to(R))
(R/'evidence/p15-115-render-qa.json').write_text(json.dumps(q,indent=2,ensure_ascii=False)+'\n')
print('METRICS',json.dumps({m:{k:v['maxAdjacentRGBMAE'] for k,v in z.items() if k in ('bow','collar','goldTrim')}
 for m,z in q['metrics'].items()},indent=2),flush=True)

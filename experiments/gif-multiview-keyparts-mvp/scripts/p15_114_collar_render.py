#!/usr/bin/env python3
"""P15-114 continuous collar from the same observed native 67.5° ink.

Replace only the collar layer; other genuine 60/67.5/75 physical parts
retain their own source ownership. Two ablations:
- source_collar_continuous: a single source collar on interpolated ECC maps
- source_collar_silhouette: same drawing, source-native silhouette SDF support

Both use the original P15-101 head ArtMesh and P15-111 hidden underpaint.
Neither synthesizes new unseen source folds. All native images remain intact.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import numpy as np,cv2,json,statistics
import p15_101_head_render as head
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-114-collar-render';D.mkdir(parents=True,exist_ok=True)
Reg=json.loads((R/'evidence/p15-114-source-qa.json').read_text())
O=json.loads((R/'evidence/p15-108-stroke-qa.json').read_text())
H=json.loads((R/'evidence/p15-111-source-qa.json').read_text())
P107=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
P101=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
P113=json.loads((R/'evidence/p15-113-render-qa.json').read_text())
S=512;X,Y=np.meshgrid(np.arange(S,dtype=np.float32),np.arange(S,dtype=np.float32))
angles=P107['angles'];views=('60','67.5','75')
sha=lambda f:sha256(Path(f).read_bytes()).hexdigest()
def rgba(file):
 return np.asarray(Image.open(file).convert('RGBA').resize((S,S),Image.Resampling.LANCZOS))
def pre(im):
 f=im.astype(np.float32)/255
 return np.concatenate((f[:,:,:3]*f[:,:,3:4],f[:,:,3:4]),axis=2)
def unpack(p):
 a=np.clip(p[:,:,3:4],0,1)
 rgb=np.clip(p[:,:,:3]/np.maximum(a,1e-6),0,1)
 return np.uint8(np.round(np.concatenate((rgb,a),axis=2)*255))
def over(back,front):
 a=np.clip(front[:,:,3:4],0,1)
 return np.concatenate((front[:,:,:3]+back[:,:,:3]*(1-a),a+back[:,:,3:4]*(1-a)),axis=2)
def segment(angle):
 if angle<=67.5:return ('60','67.5',float((angle-60)/7.5))
 return ('67.5','75',float((angle-67.5)/7.5))
def distance(mask):
 binary=np.uint8(mask>0.5)
 return cv2.distanceTransform(1-binary,cv2.DIST_L2,3)-cv2.distanceTransform(binary,cv2.DIST_L2,3)
def shifted(img,dx,dy,nearest=False):
 mat=np.float32([[1,0,dx],[0,1,dy]])
 return cv2.warpAffine(img,mat,(S,S),flags=cv2.INTER_NEAREST if nearest else cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
brooch={'60':np.array([634.46,810.55],np.float32)/2,
 '67.5':np.array([639.29,808.82],np.float32)/2,
 '75':np.array([644.12,807.09],np.float32)/2}
art={}
for v in views:
 entry=O['views'][v]['layers']
 item={}
 for part in ('background','goldTrim','bowFabric','jewel'):
  item[part]=pre(rgba(R/entry[part]['texturePath']))
 for part in ('bow','collar'):
  item[part+'Under']=pre(rgba(R/H['layers'][v][part]['hiddenOnlyPath']))
 item['nativeMask']=np.asarray(Image.open(R/entry['collarWhite']['maskPath']).convert('L').resize((S,S),Image.Resampling.NEAREST),np.float32)/255
 art[v]=item
canonical=pre(rgba(R/Reg['views']['67.5']['canonicalCollarPath']))
def collar_frame(angle,with_mask):
 a,b,t=segment(angle)
 # Source 67.5 target-to-source affine at both native endpoints (ECC convention).
 invA=np.asarray(Reg['views'][a]['inverseMap512'],np.float32)
 invB=np.asarray(Reg['views'][b]['inverseMap512'],np.float32)
 inverse=(1-t)*invA+t*invB
 pixel=cv2.warpAffine(canonical,inverse,(S,S),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,
                      borderMode=cv2.BORDER_CONSTANT)
 diag={'sourceTargetInverseAffine':inverse.round(6).tolist(),
       'canonicalTextureSHA256':Reg['canonicalSourceSHA256']}
 if with_mask:
  point=brooch[a]*(1-t)+brooch[b]*t
  ma=shifted(art[a]['nativeMask'],*(point-brooch[a]))
  mb=shifted(art[b]['nativeMask'],*(point-brooch[b]))
  sdf=(1-t)*distance(ma)+t*distance(mb)
  area=np.clip((0.55-sdf)/1.5,0,1)
  pixel=pixel*area[:,:,None]
  diag['silhouetteSource']='interpolated signed-distance matte from original 60/67.5/75 owner masks'
 else:diag['silhouetteSource']='single canonical 67.5° source geometry'
 return pixel,diag
def face(angle):
 t=(angle-60)/15
 maps={v:head.mesh_map(v,t) for v in ('60','75')}
 return head.skin_blend(head.warp(head.parts['60']['head'],maps['60']),
                        head.warp(head.parts['75']['head'],maps['75']),t)
def render(angle,mode):
 a,b,t=segment(angle)
 c=brooch[a]*(1-t)+brooch[b]*t
 def blend(role):
  pa=shifted(art[a][role],*(c-brooch[a]))
  pb=shifted(art[b][role],*(c-brooch[b]))
  return np.clip((1-t)*pa+t*pb,0,1)
 cloth=np.zeros((S,S,4),np.float32)
 for role in ('background','goldTrim','collarUnder'):
  cloth=over(cloth,blend(role))
 collar,info=collar_frame(angle,mode=='source_collar_silhouette')
 cloth=over(cloth,collar)
 for role in ('bowUnder','bowFabric','jewel'):
  cloth=over(cloth,blend(role))
 cloth=over(over(cloth,face(angle)),head.get_ahoge((angle-60)/15))
 return unpack(np.clip(cloth,0,1)),info
methods=['source_collar_continuous','source_collar_silhouette']
q={'schema':'KOMA_P15_114_CORRESPONDING_NATIVE_COLLAR_YAW_V1','character':'p0_character_001',
 'nativeSourceAngles':[60,67.5,75],'renderedAngles':angles,'methods':{m:{} for m in methods},
 'singleSourceCollarAngle':67.5,'sourceRegistrationSHA256':sha(R/'evidence/p15-114-source-qa.json'),
 'canonicalTextureSHA256':Reg['canonicalSourceSHA256'],
 'bodyArt':'P15-108 source-owner garment layers with P15-111 hidden textile',
 'headArt':'P15-101 VDD head and ahoge',
 'nativeOriginalSourceRGBAUnchanged':True,
 'fullVisualApproved':False}
for angle in angles:
 for mode in methods:
  artOut,data=render(angle,mode)
  path=D/(mode+'-yaw'+f'{angle:g}'.replace('.','p')+'.png')
  Image.fromarray(artOut,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS).save(path)
  q['methods'][mode][f'{angle:g}']={'path':str(path.relative_to(R)),'sha256':sha(path),'diagnostics':data}
 print('FRAME',angle,flush=True)
refs={
 'P15-101-original':{k:r['relativePath'] for k,r in P101['methods']['head_alpha_blend'].items()},
 'P15-107-native':{k:r['relativePath'] for k,r in P107['methods']['companion_direct_native_keys'].items()},
 'P15-113-singleSource':{k:r['path'] for k,r in P113['methods']['canonical_full'].items()},
 **{m:{k:r['path'] for k,r in frames.items()} for m,frames in q['methods'].items()}}
regions={'bow':(500,744,790,975),'collar':(400,665,805,835),
 'jewel':(595,770,701,862),'head':(440,285,840,640),'garment':(335,655,865,1015)}
contact=Image.new('RGB',(345*len(angles),382*len(refs)),'white');pen=ImageDraw.Draw(contact)
for row,(method,files) in enumerate(refs.items()):
 samples=[]
 for col,angle in enumerate(angles):
  image=Image.open(R/files[f'{angle:g}']).convert('RGBA')
  bg=Image.new('RGBA',image.size,'white');bg.alpha_composite(image)
  samples.append(np.asarray(bg.convert('RGB'),np.float32))
  contact.paste(bg.convert('RGB').crop((365,615,845,1015)).resize((345,357),Image.Resampling.LANCZOS),(col*345,row*382+25))
  pen.text((col*345+3,row*382+4),method+f' {angle:g}',fill='black')
 for roi,(x0,y0,x1,y1) in regions.items():
  diff=[round(float(np.abs(samples[i][y0:y1,x0:x1]-samples[i-1][y0:y1,x0:x1]).mean()),4) for i in range(1,len(samples))]
  q.setdefault('metrics',{}).setdefault(method,{})[roi]={
   'maxAdjacentRGBMAE':max(diff),'interiorMaxRGBMAE':max(diff[1:7]),
   'meanAdjacentRGBMAE':round(statistics.mean(diff),4),'adjacentRGBMAE':diff}
contact.save(D/'single-source-collar-yaw-contact.jpg',quality=94)
q['contact']=str((D/'single-source-collar-yaw-contact.jpg').relative_to(R))
(R/'evidence/p15-114-render-qa.json').write_text(json.dumps(q,indent=2,ensure_ascii=False)+'\n')
print('METRICS',json.dumps({method:{k:z['maxAdjacentRGBMAE'] for k,z in val.items() if k in ('bow','collar','jewel')} for method,val in q['metrics'].items()},indent=2),flush=True)

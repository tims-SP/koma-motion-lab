#!/usr/bin/env python3
"""P15-112 bow geometry and disocclusion with source-owned visible ink.

Use the four source-grounded P15-110 matched ribbon contours to deform both
key art images into a common target. The bow has one SDF-morphed silhouette,
and only one source owns high-contrast ink at a time. Visible foreground and
hidden material have independent depth owners. Three actual implementations
are compared against P15-101, 107, and 111.

This validates actual rendered pixels rather than assuming inferred underpaint
or machine stroke IDs provide final artistic correspondence.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import cv2,json,numpy as np,statistics
import p15_101_head_render as head
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-112-visibility-vdd';D.mkdir(parents=True,exist_ok=True)
V=json.loads((R/'evidence/p15-110-vision-qa.json').read_text())
Annotations=json.loads((R/'private-assets/p15-110-vision-strokes/vision-stroke-annotations.json').read_text())
Hidden=json.loads((R/'evidence/p15-111-source-qa.json').read_text())
Owners=json.loads((R/'evidence/p15-108-stroke-qa.json').read_text())
Base107=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
Base111=json.loads((R/'evidence/p15-111-render-qa.json').read_text())
Base101=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
S=512;Y,X=np.indices((S,S),np.float32)
views=['60','67.5','75'];angles=Base107['angles']
centers={'60':np.array([634.46,810.55],np.float32)/2,
         '67.5':np.array([639.29,808.82],np.float32)/2,
         '75':np.array([644.12,807.09],np.float32)/2}
sha=lambda f:sha256(Path(f).read_bytes()).hexdigest()
def load(file):
 return np.asarray(Image.open(file).convert('RGBA').resize((S,S),Image.Resampling.LANCZOS))
def mask(file):
 return np.asarray(Image.open(file).convert('L').resize((S,S),Image.Resampling.NEAREST))
def prem(img):
 f=img.astype(np.float32)/255
 return np.concatenate((f[:,:,:3]*f[:,:,3:4],f[:,:,3:4]),axis=2)
def unprem(p):
 a=np.clip(p[:,:,3:4],0,1)
 rgb=np.clip(p[:,:,:3]/np.maximum(a,1e-6),0,1)
 return np.uint8(np.round(np.concatenate((rgb,a),axis=2)*255))
def over(back,fg):
 a=np.clip(fg[:,:,3:4],0,1)
 return np.concatenate((fg[:,:,:3]+back[:,:,:3]*(1-a),a+back[:,:,3:4]*(1-a)),axis=2)
def shift(pre,dx,dy):
 mat=np.float32([[1,0,dx],[0,1,dy]])
 return cv2.warpAffine(pre,mat,(S,S),flags=cv2.INTER_LINEAR,
                       borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
def segment(a):
 if a<=67.5:return '60','67.5',float((a-60)/7.5)
 return '67.5','75',float((a-67.5)/7.5)
def path_points(role,view,n=12):
 raw=np.asarray(Annotations['roles'][role]['views'][view]['points'],np.float32)/2
 lengths=np.linalg.norm(np.diff(raw,axis=0),axis=1)
 cum=np.concatenate([[0],np.cumsum(lengths)])
 return np.stack([np.interp(np.linspace(0,cum[-1],n),cum,raw[:,d]) for d in (0,1)],axis=1).astype(np.float32)
def signed_distance(alpha):
 silhouette=np.uint8(alpha>.1)
 # closed mask eliminates isolated source-ink holes but does not change the saved source.
 silhouette=cv2.morphologyEx(silhouette,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
 outside=cv2.distanceTransform(1-silhouette,cv2.DIST_L2,3)
 inside=cv2.distanceTransform(silhouette,cv2.DIST_L2,3)
 return outside-inside
def field(source,destination,rigid,scale=18):
 # A globally rigid translation provides the natural default; local measured
 # path displacement affects pixels only near the corresponding visible bow.
 impulse=np.zeros((S,S),np.float32)
 sx=np.zeros((S,S),np.float32);sy=np.zeros((S,S),np.float32)
 for p,q in zip(source,destination):
  x,y=np.rint(q).astype(int)
  if not(4<=x<S-4 and 4<=y<S-4):continue
  diff=p-q-rigid
  cv2.circle(impulse,(x,y),2,1,-1)
  cv2.circle(sx,(x,y),2,float(diff[0]),-1)
  cv2.circle(sy,(x,y),2,float(diff[1]),-1)
 ww=cv2.GaussianBlur(impulse,(0,0),scale)
 dx=cv2.GaussianBlur(sx,(0,0),scale)/np.maximum(ww,1e-7)
 dy=cv2.GaussianBlur(sy,(0,0),scale)/np.maximum(ww,1e-7)
 strength=np.clip(ww/.06,0,1)
 dx=np.clip(dx*strength+rigid[0],-29,29)
 dy=np.clip(dy*strength+rigid[1],-29,29)
 mx=(X+dx).astype(np.float32);my=(Y+dy).astype(np.float32)
 # Mapping is target pixel -> source sample.
 detX=np.gradient(mx,axis=1);detY=np.gradient(mx,axis=0)
 jac=detX*np.gradient(my,axis=0)-detY*np.gradient(my,axis=1)
 return mx,my,{'minJacobian':float(np.min(jac[170:505,205:430])),
                'negativeJacobianPixels':int(np.count_nonzero(jac[170:505,205:430]<=0)),
                'meanSourceDeltaPx':float(np.sqrt(dx**2+dy**2).mean())}
def warp(pre,m):
 return cv2.remap(pre,m[0],m[1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
def face(t):
 maps={v:head.mesh_map(v,t) for v in ('60','75')}
 return head.skin_blend(head.warp(head.parts['60']['head'],maps['60']),
                        head.warp(head.parts['75']['head'],maps['75']),t)
def base_layers(view):
 img=load(R/V['sourceImages'][view]['path'])
 entries=Owners['views'][view]['layers']
 red=mask(R/entries['bowFabric']['maskPath'])>127
 gem=mask(R/entries['jewel']['maskPath'])>127
 bowHull=cv2.dilate(np.uint8(red),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)))>0
 gemHull=cv2.dilate(np.uint8(gem),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3)))>0
 # Keep stray material color from expanding beyond actual source-connected garment.
 sourceAlpha=img[:,:,3]>5
 bowHull&=sourceAlpha;gemHull&=sourceAlpha
 silhouette=bowHull|gemHull
 # Derive an undercoat using source-owned neighbors. Imagegen collar pixels are
 # layered underneath any disappearing bow pixels; native art is not mutated.
 under=np.asarray(img).copy()
 underMask=np.uint8(silhouette)*255
 under[:,:,:3]=cv2.inpaint(img[:,:,:3],underMask,5,cv2.INPAINT_TELEA)
 under[:,:,3]=cv2.inpaint(img[:,:,3],underMask,7,cv2.INPAINT_TELEA)
 underWhite=load(R/Hidden['layers'][view]['collar']['hiddenOnlyPath'])
 underBow=load(R/Hidden['layers'][view]['bow']['hiddenOnlyPath'])
 # Source bow separated and extended at the brooch with inferred red fabric.
 redImg=img.copy();redImg[:,:,3]=np.uint8(redImg[:,:,3]*bowHull)
 gemImg=img.copy();gemImg[:,:,3]=np.uint8(gemImg[:,:,3]*gemHull)
 sourceBow=over(prem(underBow),prem(redImg))
 sourceBack=over(prem(under),prem(underWhite))
 # Native source coordinates remain exact on disk; this is an inbetween model.
 return {'original':prem(img),'back':sourceBack,'bow':sourceBow,
         'jewel':prem(gemImg),'bowPixels':int(bowHull.sum()),
         'gemPixels':int(gemHull.sum())}
parts={view:base_layers(view) for view in views}
def prepare(angle):
 a,b,t=segment(angle)
 targetCenter=centers[a]*(1-t)+centers[b]*t
 anchorA=[];anchorB=[]
 for role in V['experimentAcceptedRoles']:
  p=path_points(role,a);q=path_points(role,b)
  direct=np.linalg.norm((p-centers[a])-(q-centers[b]),axis=1).mean()
  reverse=np.linalg.norm((p-centers[a])-(q[::-1]-centers[b]),axis=1).mean()
  if reverse<direct:q=q[::-1]
  anchorA.extend(p);anchorB.extend(q)
 anchorA=np.asarray(anchorA,np.float32);anchorB=np.asarray(anchorB,np.float32)
 anchorDst=anchorA*(1-t)+anchorB*t
 mA=field(anchorA,anchorDst,centers[a]-targetCenter)
 mB=field(anchorB,anchorDst,centers[b]-targetCenter)
 A=warp(parts[a]['bow'],mA);B=warp(parts[b]['bow'],mB)
 gemA=shift(parts[a]['jewel'],*(targetCenter-centers[a]))
 gemB=shift(parts[b]['jewel'],*(targetCenter-centers[b]))
 baseA=shift(parts[a]['back'],*(targetCenter-centers[a]))
 baseB=shift(parts[b]['back'],*(targetCenter-centers[b]))
 return a,b,t,(A,B),(gemA,gemB),(baseA,baseB),(mA[2],mB[2])
def shape_with_texture(A,B,t,mode):
 sd=(1-t)*signed_distance(A[:,:,3])+t*signed_distance(B[:,:,3])
 alpha=np.clip((.55-sd)/1.40,0,1)
 def RGB(a):return np.clip(a[:,:,:3]/np.maximum(a[:,:,3:4],.003),0,1)
 AA=RGB(A);BB=RGB(B)
 # A single source owns detailed ink. Blended shape remains continuous.
 ownerA=(t<=.5)
 if mode=='visible_blend':
  rgb=(1-t)*AA+t*BB
 else:
  chosen=AA if ownerA else BB
  fallback=BB if ownerA else AA
  valid=A[:,:,3:4] if ownerA else B[:,:,3:4]
  rgb=np.where(valid>.05,chosen,fallback)
  if mode=='edge_guard':
   # Gradually blend only texture interiors, never divergent dark outlines.
   # Source-native ink differences beyond a threshold retain nearest-owner color.
   lumA=.2126*AA[:,:,0]+.7152*AA[:,:,1]+.0722*AA[:,:,2]
   lumB=.2126*BB[:,:,0]+.7152*BB[:,:,1]+.0722*BB[:,:,2]
   contrast=np.abs(lumA-lumB)
   blend=np.clip((.15-contrast)/.1,0,1)[:,:,None]
   rgb=np.clip(rgb*(1-blend)+((1-t)*AA+t*BB)*blend,0,1)
 return np.concatenate((rgb*alpha[:,:,None],alpha[:,:,None]),axis=2)
def render(angle,mode):
 a,b,t,bows,gem,base,geoq=prepare(angle)
 bg=(1-t)*base[0]+t*base[1]
 if mode=='visible_blend':
  bow=shape_with_texture(*bows,t,'visible_blend')
  jewel=(1-t)*gem[0]+t*gem[1]
 elif mode=='single_ink_owner':
  bow=shape_with_texture(*bows,t,'single_ink_owner')
  jewel=gem[0] if t<.5 else gem[1]
 elif mode=='edge_guard':
  bow=shape_with_texture(*bows,t,'edge_guard')
  jewel=gem[0] if t<.5 else gem[1]
 else:raise ValueError(mode)
 garment=over(over(bg,bow),jewel)
 headT=(angle-60)/15
 result=over(over(garment,face(headT)),head.get_ahoge(headT))
 return unprem(np.clip(result,0,1)),{
  'sourceSegment':[a,b],'relativeYawPosition':round(t,5),
  'negativeWarpJacobianSamples':sum(x['negativeJacobianPixels'] for x in geoq),
  'minJacobian':round(min(x['minJacobian'] for x in geoq),5),
  'sourceBowPixelCounts':[parts[a]['bowPixels'],parts[b]['bowPixels']],
  'generatedHiddenCollarUnderpaint':True,'generatedHiddenBowUnderpaint':True}
methods=['visible_blend','single_ink_owner','edge_guard']
qa={'schema':'KOMA_P15_112_VIEW_GEOMETRY_VISIBILITY_VDD_V1',
 'character':'p0_character_001','sourceAngles':[60,67.5,75],
 'angles':angles,'models':methods,'sourceVisionSHA256':sha(R/'evidence/p15-110-vision-qa.json'),
 'sourceHiddenSHA256':sha(R/'evidence/p15-111-source-qa.json'),
 'nativeSourceImageHashes':{v:z['sha256'] for v,z in V['sourceImages'].items()},
 'geometry':'source-observed ribbon paths, per-segment Gaussian displacement with rigid anchor translation',
 'visibility':'single SDF ribbon shape, own ink, native jewel owner, source-hidden collar/bow underpaint',
 'artistVisualAccepted':False,'newMaterialArtInferred':True,'methods':{m:{} for m in methods}}
for angle in angles:
 for mode in methods:
  if angle in (60,67.5,75):
   ref=Base107['methods']['companion_direct_native_keys'][f'{angle:g}']
   image=Image.open(R/ref['relativePath']).convert('RGBA')
   diagnostics={'nativeKeyframeExact':True}
  else:
   rgba,diagnostics=render(angle,mode)
   image=Image.fromarray(rgba,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
  path=D/(mode+'-yaw'+f'{angle:g}'.replace('.','p')+'.png')
  image.save(path)
  qa['methods'][mode][f'{angle:g}']={'path':str(path.relative_to(R)),
     'sha256':sha(path),'diagnostics':diagnostics}
 print('FRAME',angle,flush=True)
refs={
 'P15-101-original':{k:r['relativePath'] for k,r in Base101['methods']['head_alpha_blend'].items()},
 'P15-107-native':{k:r['relativePath'] for k,r in Base107['methods']['companion_direct_native_keys'].items()},
 'P15-111-layered':{k:r['path'] for k,r in Base111['methods']['layered_full'].items()},
 **{m:{k:r['path'] for k,r in vals.items()} for m,vals in qa['methods'].items()}}
regions={'bow':(500,744,790,975),'jewel':(595,770,701,862),
 'collar':(400,665,805,835),'garment':(335,655,865,1015),'head':(440,285,840,640)}
sheet=Image.new('RGB',(346*len(angles),390*len(refs)),'white');draw=ImageDraw.Draw(sheet)
for row,(mode,frames) in enumerate(refs.items()):
 array=[]
 for col,angle in enumerate(angles):
  image=Image.open(R/frames[f'{angle:g}']).convert('RGBA')
  bg=Image.new('RGBA',image.size,'white');bg.alpha_composite(image)
  array.append(np.asarray(bg.convert('RGB'),np.float32))
  sheet.paste(bg.convert('RGB').crop((365,615,845,1015)).resize((346,364),Image.Resampling.LANCZOS),(col*346,row*390+26))
  draw.text((col*346+5,row*390+4),mode+f' {angle:g}',fill='black')
 for region,(x0,y0,x1,y1) in regions.items():
  dif=[round(float(np.abs(array[j][y0:y1,x0:x1]-array[j-1][y0:y1,x0:x1]).mean()),4)
       for j in range(1,len(array))]
  qa.setdefault('metrics',{}).setdefault(mode,{})[region]={
   'adjacentRGBMAE':dif,'maxAdjacentRGBMAE':max(dif),
   'meanAdjacentRGBMAE':round(statistics.mean(dif),4),
   'interiorMaxRGBMAE':max(dif[1:7])}
sheet.save(D/'visibility-geometry-contact.jpg',quality=94)
qa['contact']=str((D/'visibility-geometry-contact.jpg').relative_to(R))
(R/'evidence/p15-112-render-qa.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')
print('METRICS',json.dumps({m:{k:round(v['maxAdjacentRGBMAE'],3) for k,v in val.items()
 if k in ('bow','collar','jewel')} for m,val in qa['metrics'].items()},indent=2),flush=True)

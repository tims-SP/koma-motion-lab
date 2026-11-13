#!/usr/bin/env python3
"""P15-108: source-owned stroke identities and layered-occlusion ablation.

Actual original 60/67.5/75 companion garment PNGs are retained. For
inbetweens, segment-local bidirectional DIS warps align source candidate
ink masks. Per-ID signed-distance interpolation draws a *single* dark
contour after inpainting source strokes from the color fill. Collar lines
are under bow lines, gemstone owns top pixels; role clipping prevents
ink crossing garment components. A complete ink-owner alternative
preserves source linework but may switch discontinuously at segment midpoints.

This is an *experimental* source-owned rendering, not a certified artistic
stroke correspondence solution or a 360-degree rotation implementation.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import json,cv2,numpy as np,statistics
import p15_101_head_render as head
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-108-stroke-render';D.mkdir(parents=True,exist_ok=True)
Q=json.loads((R/'evidence/p15-108-stroke-qa.json').read_text())
S=json.loads((R/'evidence/p15-108-source-qa.json').read_text())
R107=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
R101=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
sha=lambda f:sha256(Path(f).read_bytes()).hexdigest()
W=512;Y,X=np.indices((W,W),np.float32)
angles=head.angles;views=['60','67.5','75']
def load(path,kind='RGBA'):
 return np.asarray(Image.open(path).convert(kind).resize((W,W),Image.Resampling.LANCZOS if kind=='RGBA' else Image.Resampling.NEAREST))
def prem(a):
 a=a.astype(np.float32)/255.
 return np.concatenate((a[:,:,:3]*a[:,:,3:4],a[:,:,3:4]),axis=2)
def unprem(p):
 alpha=np.clip(p[:,:,3:4],0,1)
 color=np.clip(p[:,:,:3]/np.maximum(alpha,1e-6),0,1)
 return np.uint8(np.round(np.concatenate((color,alpha),axis=2)*255))
def over(dst,src):
 a=np.clip(src[:,:,3:4],0,1)
 return np.concatenate((src[:,:,:3]+dst[:,:,:3]*(1-a),a+dst[:,:,3:4]*(1-a)),axis=2)
def visible(img):
 p=prem(img)
 return np.uint8(np.round(np.clip(p[:,:,:3]+1-p[:,:,3:4],0,1)*255))
def warp(img,f,amount):
 mx=(X-f[:,:,0]*amount).astype(np.float32)
 my=(Y-f[:,:,1]*amount).astype(np.float32)
 return cv2.remap(img,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
def sdf(mask):
 binary=np.uint8(mask>127)
 outside=cv2.distanceTransform(1-binary,cv2.DIST_L2,3)
 inside=cv2.distanceTransform(binary,cv2.DIST_L2,3)
 return outside-inside
def flow(a,b):
 dis=cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
 dis.setFinestScale(0);dis.setVariationalRefinementIterations(4)
 f=dis.calc(cv2.cvtColor(visible(a),cv2.COLOR_RGB2GRAY),
            cv2.cvtColor(visible(b),cv2.COLOR_RGB2GRAY),None)
 return cv2.GaussianBlur(np.clip(f,-24,24),(0,0),1.1)
data={}
for view in views:
 rec=Q['views'][view]
 source=load(R/rec['source'])
 masks={}
 for role,entry in rec['strokeRegions'].items():
  masks[role]=load(R/entry['maskPath'],'L')
 clipMasks={}
 for role in ('bowFabric','collarWhite','jewel'):
  clipMasks[role]=load(R/rec['layers'][role]['maskPath'],'L')
 lineMask=np.zeros((W,W),np.uint8)
 for m in masks.values():lineMask=np.maximum(lineMask,m)
 # Inpaint narrow ink only, no changes to artist-source files.
 mask=cv2.dilate(np.uint8(lineMask>127)*255,np.ones((3,3),np.uint8))
 # Fill gem independently then composite as foreground, so the emblem has one owner.
 jewelMask=cv2.dilate(np.uint8(clipMasks['jewel']>127)*255,np.ones((5,5),np.uint8))
 paintMask=np.maximum(mask,jewelMask)
 paintMask=np.uint8((paintMask>0)&(source[:,:,3]>12))*255
 color=cv2.cvtColor(source[:,:,:3],cv2.COLOR_RGB2BGR)
 filled=cv2.cvtColor(cv2.inpaint(color,paintMask,4,cv2.INPAINT_TELEA),cv2.COLOR_BGR2RGB)
 clean=source.copy();clean[:,:,:3]=filled
 # Source pixels are untouched; this is only an experimental inbetween underpainting.
 out=D/f'yaw{view.replace(".","p")}-undercoat.png'
 Image.fromarray(clean,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS).save(out)
 jewelLayer=source.copy();jewelLayer[:,:,3]=np.uint8(source[:,:,3].astype(np.float32)*clipMasks['jewel']/255)
 # Average representative source ink RGB and use each category's real local color.
 palette={}
 for role,ink in masks.items():
  idx=(ink>127)&(source[:,:,3]>127)
  palette[role]=np.median(source[idx,:3],axis=0).astype(np.float32) if idx.sum()>1 else np.asarray([86,43,65] if role.startswith('bow') else [91,82,102],np.float32)
 data[view]={'source':source,'undercoat':prem(clean),
   'ink':masks,'sdf':{k:sdf(v) for k,v in masks.items()},
   'roleMasks':clipMasks,'palette':palette,'jewelPrem':prem(jewelLayer)}
paths={}
for a,b in [('60','67.5'),('67.5','75')]:
 paths[(a,b)]=(flow(data[a]['source'],data[b]['source']),
               flow(data[b]['source'],data[a]['source']))
 print('FLOW',a,b,round(float(np.linalg.norm(paths[(a,b)][0],axis=2).mean()),3),flush=True)
def segment(angle):
 if angle<=67.5:return ('60','67.5',float((angle-60)/7.5))
 return ('67.5','75',float((angle-67.5)/7.5))
def headSurface(angle):
 t=(angle-60)/15
 maps={v:head.mesh_map(v,t) for v in ('60','75')}
 return head.skin_blend(head.warp(head.parts['60']['head'],maps['60']),
                        head.warp(head.parts['75']['head'],maps['75']),t)
def choose_jewel(a,b,t,fa,fb):
 # Source-owned top of ribbon brooch. Its pixels have one owner at a time.
 picked=a if t<.5 else b
 f=fa if t<.5 else fb
 distance=t if t<.5 else 1-t
 return warp(data[picked]['jewelPrem'],f,distance)
def synth(angle,mode):
 a,b,t=segment(angle)
 fa,fb=paths[(a,b)]
 A=warp(data[a]['undercoat'],fa,t)
 B=warp(data[b]['undercoat'],fb,1-t)
 base=np.clip((1-t)*A+t*B,0,1)
 if mode=='single_bow_owner':
  # Complete bow source owned by one view, with original texture, crease
  # and silhouette. Source keyframe angle transitions may still show jumps.
  owner=a if t<.5 else b
  flowUse=fa if t<.5 else fb
  amount=t if t<.5 else 1-t
  originalPrem=prem(data[owner]['source'])
  mask=np.float32(data[owner]['roleMasks']['bowFabric'])/255
  src=originalPrem*mask[:,:,None]
  bow=warp(src,flowUse,amount)
  base=over(base,bow)
 else:
  IDs=[role for role in Q['roleIDs'] if role.startswith('collar')]+[
     role for role in Q['roleIDs'] if role.startswith('bow')]
  diagnostics={}
  for role in IDs:
   ma=data[a]['ink'][role];mb=data[b]['ink'][role]
   la=int(np.count_nonzero(ma>127));lb=int(np.count_nonzero(mb>127))
   if la==0 and lb==0:continue
   if la==0 or lb==0:
    inp=warp(np.float32(ma if la else mb)/255,fa if la else fb,t if la else 1-t)
    opacity=inp*((1-t) if la else t)
   else:
    da=warp(data[a]['sdf'][role],fa,t)
    db=warp(data[b]['sdf'][role],fb,1-t)
    # Signed-distance blending produces a single candidate ink geometry.
    signed=np.clip((1-t)*da+t*db,-25,25)
    opacity=np.clip((.6-signed)/1.5,0,1)
   surface='bowFabric' if role.startswith('bow') else 'collarWhite'
   support=warp(np.float32(data[a]['roleMasks'][surface])/255,fa,t)*(1-t)+warp(
             np.float32(data[b]['roleMasks'][surface])/255,fb,1-t)*t
   # A stroke is only allowed inside its source-owned garment material.
   opacity*=np.clip(support*1.35,0,1)
   color=(1-t)*data[a]['palette'][role]+t*data[b]['palette'][role]
   alpha=np.clip(opacity*.78,0,1)[:,:,None]
   front=np.concatenate((alpha*(color/255),alpha),axis=2)
   base=over(base,front)
 # The gemstone draws last above both collar and bow crease regions.
 jewel=choose_jewel(a,b,t,fa,fb)
 base=over(base,jewel)
 result=over(base,headSurface(angle))
 result=over(result,head.get_ahoge((angle-60)/15))
 return unprem(np.clip(result,0,1))
methods=['sdf_role_ink_native_keys','sdf_role_ink_original_keys','single_bow_owner']
qa={'schema':'KOMA_P15_108_SOURCE_STROKE_SDF_VDD_V1',
 'characterId':'p0_character_001','sourceAngles':[60,67.5,75],
 'renderedAngles':angles,'sourceStrokeQASHA256':sha(R/'evidence/p15-108-stroke-qa.json'),
 'sourceNativeSHA256':{v:Q['views'][v]['sourceSHA256'] for v in views},
 'method':'per-region signed distance ink correspondence after bidirectional source optical flow',
 'depthRules':['collarInk','bowInk','goldJewel','headHair'],
 'artisticStrokeIDsApproved':False,'continuousYawVisualAccepted':False,
 'methods':{m:{} for m in methods}}
for angle in angles:
 for mode in methods:
  if angle in (60,67.5,75):
   if angle in (60,75) and mode=='sdf_role_ink_original_keys':
    view=str(int(angle))
    im=Image.open(R/head.TOP['views'][view]['sourcePath']).convert('RGBA')
    srcType='ORIGINAL_P0_CHARACTER_SOURCE'
   else:
    # Native garment + source-owned P15-101 head composite (not a bare garment PNG).
    # Reuse the previously verified full-character frame at all three keys.
    original=R/R107['methods']['companion_direct_native_keys'][f'{angle:g}']['relativePath']
    im=Image.open(original).convert('RGBA')
    srcType='NATIVE_COMPANION_FULL_CHARACTER'
  else:
   im=Image.fromarray(synth(angle,mode),'RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
   srcType='SYNTHETIC_INBETWEEN'
  outfile=D/(mode+'-yaw'+f'{angle:g}'.replace('.','p')+'.png')
  im.save(outfile)
  qa['methods'][mode][f'{angle:g}']={
     'path':str(outfile.relative_to(R)),'sha256':sha(outfile),'sourceKind':srcType}
 print('FRAME',angle,flush=True)
regions={'bow':(500,744,790,975),'jewel':(595,770,701,862),
 'collar':(400,665,805,835),'garment':(335,655,865,1015),'head':(440,285,840,640)}
baselines={
 'P15-101-original':{k:r['relativePath'] for k,r in R101['methods']['head_alpha_blend'].items()},
 'P15-107-three-native':{k:r['relativePath'] for k,r in R107['methods']['companion_direct_native_keys'].items()}}
allframes={**baselines,**{m:{k:r['path'] for k,r in frames.items()} for m,frames in qa['methods'].items()}}
contact=Image.new('RGB',(343*len(angles),390*len(allframes)),'white');draw=ImageDraw.Draw(contact)
for row,(name,refs) in enumerate(allframes.items()):
 frames=[]
 for col,angle in enumerate(angles):
  frame=Image.open(R/refs[f'{angle:g}']).convert('RGBA')
  white=Image.new('RGBA',frame.size,'white');white.alpha_composite(frame)
  frames.append(np.asarray(white.convert('RGB'),np.float32))
  crop=white.convert('RGB').crop((365,615,845,1015)).resize((343,364),Image.Resampling.LANCZOS)
  contact.paste(crop,(343*col,390*row+25))
  draw.text((343*col+4,390*row+5),name+f' {angle:g}',fill='black')
 for role,(x0,y0,x1,y1) in regions.items():
  diffs=[round(float(np.abs(frames[i][y0:y1,x0:x1]-frames[i-1][y0:y1,x0:x1]).mean()),4) for i in range(1,len(frames))]
  qa.setdefault('metrics',{}).setdefault(name,{})[role]={
   'adjacentRGBMAE':diffs,'maxAdjacentRGBMAE':max(diffs),
   'interiorMaxRGBMAE':max(diffs[1:7]),
   'meanAdjacentRGBMAE':round(statistics.mean(diffs),4)}
contact.save(D/'stroke-sdf-occlusion-contact.jpg',quality=93)
qa['contact']=str((D/'stroke-sdf-occlusion-contact.jpg').relative_to(R))
(R/'evidence/p15-108-render-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
print('METRICS',json.dumps({m:{k:(v['maxAdjacentRGBMAE'],v['interiorMaxRGBMAE'])
 for k,v in vals.items() if k in ('bow','jewel','collar')} for m,vals in qa['metrics'].items()},indent=2),flush=True)

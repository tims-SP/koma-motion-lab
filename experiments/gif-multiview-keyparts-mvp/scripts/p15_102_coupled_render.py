#!/usr/bin/env python3
"""P0 60°–75° eye/profile/head-neck correspondence experiment.

Reuses P15-101 validated head/UV warp, and adds a common lower-body ArtMesh.
Tests near-eye ownership with original source pixels on inpainted hidden eye
undercoat, and view-dependent single-source nose/jaw lines. No GAN denoising.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import json,statistics
import numpy as np,cv2
import p15_101_head_render as head
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports';D=P/'p15-102-neck-eye-profile';D.mkdir(parents=True,exist_ok=True)
M=json.loads((P/'p15-102-neck-shoulder-mesh/neck-shoulder-mesh.json').read_text())
mq=json.loads((R/'evidence/p15-102-neck-mesh-qa.json').read_text())
prior=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
top=head.TOP
assert mq['nonfolding'] and len(M['triangles'])==36
S=head.S;X=head.xx;Y=head.yy
coords={v:np.asarray([p['viewPosition'][v] for p in M['vertices']],np.float32)/2 for v in ('60','75')}
def sha(p):return sha256(Path(p).read_bytes()).hexdigest()
def signed(p):
 a,b,c=p;return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def body_mapping(view,t):
 src=coords[view];dest=coords['60']*(1-t)+coords['75']*t
 mx=np.zeros((S,S),np.float32);my=np.zeros((S,S),np.float32)
 valid=np.zeros((S,S),np.uint8)
 for tri in M['triangles']:
  s=src[tri].astype(np.float32);q=dest[tri].astype(np.float32)
  assert signed(q)>0
  x0=max(0,int(np.floor(q[:,0].min()))-1)
  x1=min(S,int(np.ceil(q[:,0].max()))+2)
  y0=max(0,int(np.floor(q[:,1].min()))-1)
  y1=min(S,int(np.ceil(q[:,1].max()))+2)
  if x1<=x0 or y1<=y0:continue
  inside=np.zeros((y1-y0,x1-x0),np.uint8)
  cv2.fillConvexPoly(inside,np.rint(q-[x0,y0]).astype(np.int32),255)
  mask=inside>0
  warp=cv2.getAffineTransform(q,s)
  xx=X[y0:y1,x0:x1];yy=Y[y0:y1,x0:x1]
  mx[y0:y1,x0:x1][mask]=(warp[0,0]*xx+warp[0,1]*yy+warp[0,2])[mask]
  my[y0:y1,x0:x1][mask]=(warp[1,0]*xx+warp[1,1]*yy+warp[1,2])[mask]
  valid[y0:y1,x0:x1][mask]=255
 hull=np.zeros((S,S),np.uint8)
 cv2.fillPoly(hull,[np.rint(dest[[0,6,13,20,27,21,14,7]]).astype(np.int32)],255)
 missing=np.where((hull>0)&(valid==0),255,0).astype(np.uint8)
 if np.any(missing):
  mx=cv2.inpaint(mx,missing,2,cv2.INPAINT_TELEA)
  my=cv2.inpaint(my,missing,2,cv2.INPAINT_TELEA)
 return mx,my,hull.astype(np.float32)/255,float((hull*valid).sum()/max(1,hull.sum()*255)),int(np.count_nonzero(missing))
def body_warp(arr,maps):
 x,y,mask,*_=maps
 f=head.prem(arr)
 out=cv2.remap(f,x,y,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
 return np.clip(out,0,1)*mask[:,:,None]
def smooth(v):
 v=np.clip(v,0,1)
 return v*v*(3-2*v)
def roi_ink_mask(src,view):
 # Dark silhouette line within 2D authored nose/profile boundary proxy.
 whole=Image.new('L',(1024,1024),0)
 pts=top['views'][view]['faceProfileContour']
 ImageDraw.Draw(whole).line([tuple(map(int,p)) for p in pts],fill=255,width=13,joint='curve')
 near=np.asarray(whole.resize((S,S),Image.Resampling.LANCZOS))>40
 gray=cv2.cvtColor(src[:,:,:3],cv2.COLOR_RGB2GRAY)
 opaque=(src[:,:,3]>80)
 dark=gray<145
 return (near&opaque&dark).astype(np.uint8)*255
tex={}
for view in ('60','75'):
 p=head.parts[view]
 color=p['head'][:,:,:3].copy()
 eye=(p['near'][:,:,3]>10).astype(np.uint8)*255
 eye=cv2.dilate(eye,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9)))
 ink=roi_ink_mask(p['source'],view)
 ink=cv2.dilate(ink,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)))
 # Restore source skin texture underneath the actual source eye and near-side profile ink.
 clean_eye=p['head'].copy()
 clean_eye[:,:,:3]=cv2.cvtColor(cv2.inpaint(cv2.cvtColor(color,cv2.COLOR_RGB2BGR),
                                         eye,5,cv2.INPAINT_TELEA),cv2.COLOR_BGR2RGB)
 union=cv2.max(eye,ink)
 clean_all=p['head'].copy()
 clean_all[:,:,:3]=cv2.cvtColor(cv2.inpaint(cv2.cvtColor(color,cv2.COLOR_RGB2BGR),
                                         union,5,cv2.INPAINT_TELEA),cv2.COLOR_BGR2RGB)
 profile=p['source'].copy()
 profile[:,:,3]=np.uint8(np.round(p['source'][:,:,3].astype(np.float32)*ink.astype(np.float32)/255))
 tex[view]={'eye_clean':clean_eye,'eye_profile_clean':clean_all,
            'profile_layer':profile,'eye_layer':p['near'],
            'eyeMaskPixels':int(np.count_nonzero(eye)),
            'profileMaskPixels':int(np.count_nonzero(ink))}
 for name,arr in [('eye-clean-undercoat',clean_eye),('eye-profile-undercoat',clean_all),('profile-line',profile)]:
  Image.fromarray(arr,'RGBA').save(D/f'yaw{view}-{name}.png')
def main():
 methods=['neck_mesh','neck_eye_owner','neck_eye_dissolve','neck_eye_profile']
 angles=head.angles
 def render(t,method):
  faceMaps={v:head.mesh_map(v,t) for v in ('60','75')}
  bodyMaps={v:body_mapping(v,t) for v in ('60','75')}
  # Base upper torso source: use matched collar/bow mesh, with 8px feather across top row.
  baseBg=head.get_bg(t)
  aa=body_warp(head.parts['60']['body'],bodyMaps['60'])
  bb=body_warp(head.parts['75']['body'],bodyMaps['75'])
  warped=head.skin_blend(aa,bb,t)
  gate=cv2.GaussianBlur(bodyMaps['60'][2].astype(np.float32),(0,0),4.0)
  gate=np.clip(gate,0,1)[:,:,None]
  background=(1-gate)*baseBg+gate*warped
  # Same head warp as P15-101; selective eye/ink removal before sampling.
  if method=='neck_mesh':
   a=head.warp(head.parts['60']['head'],faceMaps['60'])
   b=head.warp(head.parts['75']['head'],faceMaps['75'])
  else:
   key='eye_profile_clean' if method=='neck_eye_profile' else 'eye_clean'
   a=head.warp(tex['60'][key],faceMaps['60'])
   b=head.warp(tex['75'][key],faceMaps['75'])
  combined=head.skin_blend(a,b,t)
  if method!='neck_mesh':
   eyeA=head.warp(tex['60']['eye_layer'],faceMaps['60'])
   eyeB=head.warp(tex['75']['eye_layer'],faceMaps['75'])
   if method=='neck_eye_dissolve':
    # No double-eye outside short crossfade; preserve source eyelash textures.
    owner=smooth((t-.43)/.14)
    overlay=head.skin_blend(eyeA,eyeB,owner)
   else:
    overlay=eyeA if t<.5 else eyeB
   combined=head.over(combined,overlay)
  if method=='neck_eye_profile':
   outlineA=head.warp(tex['60']['profile_layer'],faceMaps['60'])
   outlineB=head.warp(tex['75']['profile_layer'],faceMaps['75'])
   combined=head.over(combined,outlineA if t<.5 else outlineB)
  out=head.over(background,combined)
  out=head.over(out,head.get_ahoge(t))
  return head.rgba(out),{'headCoverage':min(faceMaps['60'][3],faceMaps['75'][3]),
    'bodyCoverage':min(bodyMaps['60'][3],bodyMaps['75'][3]),
    'bodyMeshCracks':max(bodyMaps['60'][4],bodyMaps['75'][4]),
    'eyeRestoredFromNativeSource':method!='neck_mesh'}
 qa={'schema':'KOMA_P15_102_NECK_EYE_PROFILE_VDD_V1','angles':angles,
     'headMeshSHA256':head.G['meshSha256'],'bodyMeshSHA256':mq['meshSHA256'],
     'textureRole':'real source RGBA with eye/profile-source-owned layers',
     'eyeMasks':{v:tex[v]['eyeMaskPixels'] for v in tex},
     'profileMasks':{v:tex[v]['profileMaskPixels'] for v in tex},
     'methods':{m:{} for m in methods},'fullVisualAccepted':False}
 for ang in angles:
  t=(ang-60)/15
  faceMasks=[]
  for method in methods:
   if t==0 or t==1:
    view='60' if t==0 else '75'
    im=Image.open(R/top['views'][view]['sourcePath']).convert('RGBA')
    diag={'source':True}
   else:
    arr,diag=render(t,method)
    im=Image.fromarray(arr,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
   f=D/(method+'-yaw'+f'{ang:g}'.replace('.','p')+'.png')
   im.save(f)
   qa['methods'][method][f'{ang:g}']={'sha256':sha(f),'relativePath':str(f.relative_to(R)),
     'diagnostics':diag}
  print('rendered yaw',ang,flush=True)
 # Diagnostic ROIs use identical canvas ranges, check real artifacts instead of trusting scalar alone.
 rois={'face':(445,275,845,675),'eye':(550,388,785,510),'nose_jaw':(675,455,825,665),'neck_collar':(380,665,800,925)}
 baseline=prior['methods']['head_alpha_blend']
 summary={}
 contact=Image.new('RGB',(385*len(angles),382*(1+len(methods))),'white')
 dr=ImageDraw.Draw(contact)
 for row,method in enumerate(['p15-101-head_alpha_blend']+methods):
  pictures=[]
  for col,ang in enumerate(angles):
   key=f'{ang:g}'
   f=R/(baseline[key]['relativePath'] if row==0 else qa['methods'][method][key]['relativePath'])
   im=Image.open(f).convert('RGBA')
   white=Image.new('RGBA',im.size,'white');white.alpha_composite(im)
   rgb=np.asarray(white.convert('RGB'),np.float32);pictures.append(rgb)
   tile=white.convert('RGB').crop(rois['face']).resize((385,355),Image.Resampling.LANCZOS)
   contact.paste(tile,(385*col,382*row+24))
   dr.text((385*col+5,382*row+5),method+f' {ang:g}',fill='black')
  for name,box in rois.items():
   x0,y0,x1,y1=box
   diffs=[round(float(np.abs(pictures[i][y0:y1,x0:x1]-pictures[i-1][y0:y1,x0:x1]).mean()),4) for i in range(1,len(pictures))]
   summary.setdefault(method,{})[name]={'adjacentRGBMAE':diffs,
     'maxAdjacentRGBMAE':max(diffs),'midpointAdjacentRGBMAE':max(diffs[3:5])}
 contact.save(D/'neck-eye-profile-contact.jpg',quality=94)
 qa['metrics']=summary
 qa['contact']='private-assets/exports/p15-102-neck-eye-profile/neck-eye-profile-contact.jpg'
 (R/'evidence/p15-102-render-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
 print('KEY_METRICS',json.dumps({k:{n:(v[n]['maxAdjacentRGBMAE'],v[n]['midpointAdjacentRGBMAE']) for n in ('face','eye','neck_collar')} for k,v in summary.items()},indent=2),flush=True)

if __name__=='__main__':
 main()

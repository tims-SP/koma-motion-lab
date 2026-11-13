#!/usr/bin/env python3
"""Align real source gold bow emblems with measured garment anchors.
Keep the emblem from one source as a source-owned ArtMesh layer instead of
mixing two different ink outlines. Evaluate static and neck-meshed torso.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import json,numpy as np,cv2,hashlib,statistics
import p15_101_head_render as head
import p15_102_coupled_render as neck
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-102-neck-eye-profile';D.mkdir(exist_ok=True)
angles=head.angles;S=head.S
prior=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
sourcePaths={v:R/head.TOP['views'][v]['sourcePath'] for v in ('60','75')}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def gold_layers(v):
 body=head.parts[v]['body'].copy()
 full=head.parts[v]['source']
 src=full[:,:,:3]
 hsv=cv2.cvtColor(src,cv2.COLOR_RGB2HSV)
 h,w=hsv.shape[:2]
 golden=cv2.inRange(hsv,np.array([10,45,55],np.uint8),np.array([35,255,255],np.uint8))
 allow=np.zeros((h,w),np.uint8)
 allow[385:438,297:357]=255
 golden=cv2.bitwise_and(golden,allow)
 n,l,stats,cent=cv2.connectedComponentsWithStats(golden,8)
 center=np.array([635,811] if v=='60' else [645,808],np.float32)/2
 choices=[]
 for i in range(1,n):
  area=int(stats[i,cv2.CC_STAT_AREA]);dist=float(np.linalg.norm(cent[i]-center))
  if area>=24 and dist<28:choices.append((area/(1+dist/10),i,area,dist))
 if not choices:raise RuntimeError('No gold emblem source island '+v)
 choices.sort(reverse=True)
 selected=choices[0][1]
 gold=np.where(l==selected,255,0).astype(np.uint8)
 gold=cv2.dilate(gold,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9)))
 gold=cv2.GaussianBlur(gold,(0,0),.8)
 pixels=gold>5
 yy,xx=np.where(pixels)
 foreground=np.zeros_like(body)
 foreground[:,:,:3]=full[:,:,:3]
 foreground[:,:,3]=np.uint8(np.round(body[:,:,3].astype(np.float32)*gold/255))
 # Backdrop is original garment with gold emblem removed before cross-view mixing.
 cut=np.uint8(gold>8)*255
 cut=cv2.dilate(cut,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)))
 clean=body.copy()
 clean[:,:,:3]=cv2.cvtColor(cv2.inpaint(cv2.cvtColor(body[:,:,:3],cv2.COLOR_RGB2BGR),
                                      cut,6,cv2.INPAINT_TELEA),cv2.COLOR_BGR2RGB)
 meta={'centerMeasured':(cent[selected]*2).round(2).tolist(),
       'sourceBlobArea':choices[0][2],
       'sourceDistanceFromExpected':round(choices[0][3]*2,3),
       'mattePixels':int(len(xx)),
       'matteBBox':[int(xx.min()*2),int(yy.min()*2),int((xx.max()+1)*2),int((yy.max()+1)*2)]}
 for name,im in [('emblem',foreground),('clean-torso',clean)]:
  Image.fromarray(im,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS).save(D/f'yaw{v}-{name}.png')
 return foreground,clean,meta
gold={};bodyClean={};goldDiag={}
for v in ('60','75'):
 gold[v],bodyClean[v],goldDiag[v]=gold_layers(v)
print('SOURCES',json.dumps(goldDiag),flush=True)
def rgba2(p):return head.rgba(p)
def draw(t,method):
 faceMaps={v:head.mesh_map(v,t) for v in ('60','75')}
 bodyMaps={v:neck.body_mapping(v,t) for v in ('60','75')}
 alphaBlend=head.skin_blend(head.warp(head.parts['60']['head'],faceMaps['60']),
                            head.warp(head.parts['75']['head'],faceMaps['75']),t)
 if method=='gold_owner_static':
  bg=head.skin_blend(head.prem(bodyClean['60']),head.prem(bodyClean['75']),t)
 else:
  bg=head.skin_blend(neck.body_warp(bodyClean['60'],bodyMaps['60']),
                     neck.body_warp(bodyClean['75'],bodyMaps['75']),t)
  # Shape valid only inside new torso mesh, preserve untouched source above it.
  g=cv2.GaussianBlur(bodyMaps['60'][2],(0,0),4)[:,:,None]
  bg=bg*g+head.get_bg(t)*(1-g)
 result=head.over(bg,alphaBlend)
 goldA=neck.body_warp(gold['60'],bodyMaps['60'])
 goldB=neck.body_warp(gold['75'],bodyMaps['75'])
 if method=='gold_crossfade_mesh':
  weight=neck.smooth((t-.42)/.16)
  item=head.skin_blend(goldA,goldB,weight)
 else:
  item=goldA if t<.5 else goldB
 result=head.over(result,item)
 result=head.over(result,head.get_ahoge(t))
 return rgba2(result),{'headMeshCoverage':min(faceMaps['60'][3],faceMaps['75'][3]),
  'neckMeshCoverage':min(bodyMaps['60'][3],bodyMaps['75'][3]),
  'jewelSourceOwned':True,
  'emblemOwner':'blend' if method=='gold_crossfade_mesh' else '60' if t<.5 else '75'}
methods=['gold_owner_static','gold_owner_mesh','gold_crossfade_mesh']
qa={'schema':'KOMA_P15_102_SOURCE_OWNED_GOLD_JEWEL_QA_V1',
    'sourceRealEmblemLandmarks':goldDiag,'angles':angles,
    'headMeshSHA256':head.G['meshSha256'],
    'neckMeshSHA256':neck.mq['meshSHA256'],
    'methods':{m:{} for m in methods},'visualAcceptance':False}
for angle in angles:
 t=(angle-60)/15
 for method in methods:
  if t==0 or t==1:
   v='60' if t==0 else '75'
   im=Image.open(sourcePaths[v]).convert('RGBA');diag={'source':True}
  else:
   arr,diag=draw(t,method);im=Image.fromarray(arr,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
  file=D/(f'{method}-yaw'+f'{angle:g}'.replace('.','p')+'.png')
  im.save(file)
  qa['methods'][method][f'{angle:g}']={'sha256':sha(file),
    'relativePath':str(file.relative_to(R)),'diagnostics':diag}
 print('emblem yaw',angle,flush=True)
# Inspect nose/eye/neck/jewel without conflating numeric motion in other regions.
rois={'face':(445,275,845,675),'eye':(550,388,785,510),
      'neck_collar':(380,665,800,925),'jewel':(600,775,710,875)}
baseline=json.loads((R/'evidence/p15-101-render-qa.json').read_text())['methods']['head_alpha_blend']
summary={}
board=Image.new('RGB',(385*9,425*(1+len(methods))),'white');pen=ImageDraw.Draw(board)
for row,method in enumerate(['P15-101-head_alpha_blend']+methods):
 pictures=[]
 for col,angle in enumerate(angles):
  path=R/(baseline[f'{angle:g}']['relativePath'] if row==0 else qa['methods'][method][f'{angle:g}']['relativePath'])
  art=Image.open(path).convert('RGBA');white=Image.new('RGBA',art.size,'white');white.alpha_composite(art)
  arr=np.asarray(white.convert('RGB'),dtype=np.float32);pictures.append(arr)
  board.paste(white.convert('RGB').crop((365,585,835,1010)).resize((385,390),Image.Resampling.LANCZOS),(385*col,425*row+24))
  pen.text((385*col+5,425*row+5),method+f' {angle:g}',fill='black')
 for key,(x0,y0,x1,y1) in rois.items():
  diffs=[round(float(np.abs(pictures[i][y0:y1,x0:x1]-pictures[i-1][y0:y1,x0:x1]).mean()),4) for i in range(1,len(pictures))]
  summary.setdefault(method,{})[key]={'adjacentRGBMAE':diffs,
     'maxAdjacentRGBMAE':max(diffs),'midpointAdjacentRGBMAE':max(diffs[3:5])}
board.save(D/'jewel-ownership-contact.jpg',quality=93)
qa['metrics']=summary;qa['contact']='private-assets/exports/p15-102-neck-eye-profile/jewel-ownership-contact.jpg'
(R/'evidence/p15-102-jewel-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
print('METRICS',json.dumps({m:{k:(x['maxAdjacentRGBMAE'],x['midpointAdjacentRGBMAE']) for k,x in a.items()} for m,a in summary.items()},indent=2),flush=True)

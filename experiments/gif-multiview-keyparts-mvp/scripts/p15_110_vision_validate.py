#!/usr/bin/env python3
"""Validate model-observed source bow/collar stroke IDs against native pixel data.

Raw multimodal Codex annotations are immutable inputs. Per-role acceptance
requires all three visible source paths, confidence, source ink edge proximity,
and normalized correspondence plausibility. Every rejection carries reasons.
No geometry is artist-certified by this program.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import hashlib,json,cv2,numpy as np
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-110-vision-validated';D.mkdir(parents=True,exist_ok=True)
raw=R/'private-assets/p15-110-vision-strokes/vision-stroke-annotations.json'
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
a=json.loads(raw.read_text())
assert a['schema']=='P15_110_VISION_ANNOTATION_V1'
assert a['angles']==['60','67.5','75']
sources={
 '60':P/'p15-107-source-patches/yaw60-registered.png',
 '67.5':P/'p15-105-middle-art/yaw067p5-garment-registered.png',
 '75':P/'p15-107-source-patches/yaw75-registered.png'}
centers={'60':np.array([634.46,810.55]),'67.5':np.array([639.29,808.82]),'75':np.array([644.12,807.09])}
angles=list(sources)
native={}
for view,src in sources.items():
 data=np.asarray(Image.open(src).convert('RGBA'))
 alpha=data[:,:,3]/255.
 white=np.uint8(np.round(data[:,:,:3]*alpha[:,:,None]+255*(1-alpha[:,:,None])))
 grey=cv2.cvtColor(white,cv2.COLOR_RGB2GRAY)
 edges=cv2.Canny(grey,35,100)
 edges=cv2.dilate(edges,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3)))
 distance=cv2.distanceTransform(np.uint8(edges==0),cv2.DIST_L2,3)
 native[view]={'rgba':data,'white':white,'edgeDistance':distance}
roles={}
for role,entry in a['roles'].items():
 status={'sourceView':{},'modelCrossViewConfidence':float(entry.get('cross_view_identity_confidence',0)),
 'crossViewAcceptedForExperiment':False,'reasons':[]}
 paths=[]
 for view in angles:
  item=entry['views'][view]
  rawpoints=item.get('points',[])
  points=np.asarray(rawpoints,dtype=np.float64).reshape(-1,2)
  declared=bool(item.get('visible',False))
  visible=float(item.get('visible_fraction',0))
  confidence=float(item.get('confidence',0))
  bounds=bool(np.isfinite(points).all() and np.all(points>=0) and np.all(points<1024))
  enough=len(points)>=3
  lengths=np.linalg.norm(np.diff(points,axis=0),axis=1) if len(points)>1 else np.array([])
  pathlength=float(lengths.sum())
  unique=float(np.min(lengths)) if len(lengths) else 0
  dists=[]
  opaque=[]
  if bounds:
   for x,y in points:
    xx=int(round(x));yy=int(round(y))
    xx=max(0,min(1023,xx));yy=max(0,min(1023,yy))
    dists.append(float(native[view]['edgeDistance'][yy,xx]))
    opaque.append(int(native[view]['rgba'][yy,xx,3]>90))
  edgeFrac=float(np.mean(np.asarray(dists)<=9)) if dists else 0.
  alphaFrac=float(np.mean(opaque)) if opaque else 0.
  rec={'declaredVisible':declared,'visibleFraction':visible,'modelConfidence':confidence,
       'sourcePointCount':len(points),'points':points.round(3).tolist(),
       'sourceBounds':bounds,'pathLength':round(pathlength,4),
       'minStep':round(unique,3),'edgeWithin9pxFraction':round(edgeFrac,4),
       'sourceAlphaFraction':round(alphaFrac,4),
       'medianSourceEdgeDistancePx':round(float(np.median(dists)),3) if dists else None,
       'occludedBy':item.get('occluded_by')}
  good=(declared and visible>=.55 and confidence>=.66 and enough and bounds and
        pathlength>=10 and edgeFrac>=.6 and alphaFrac>=.6)
  rec['passesViewGate']=bool(good)
  status['sourceView'][view]=rec
  paths.append(points if good else None)
 if not all(x is not None for x in paths):
  status['reasons'].append('missing source-observed view path or insufficient source-edge support')
 else:
  # Reparameterize at 24 arclength samples to compare source-view material lines.
  def norm(pts):
   lengths=np.linalg.norm(np.diff(pts,axis=0),axis=1)
   d=np.concatenate([[0],np.cumsum(lengths)])
   if d[-1]<1:return None
   pos=np.linspace(0,d[-1],24)
   return np.stack([np.interp(pos,d,pts[:,axis]) for axis in range(2)],axis=1)
  path24=[norm(p) for p in paths]
  ratios=[float(np.linalg.norm(np.diff(p,axis=0),axis=1).sum()) for p in paths]
  ratio=max(ratios)/max(.01,min(ratios))
  status['sourceLengthRatio']=round(ratio,3)
  meanShifts=[];flipped=[]
  for left,right,a0,a1 in zip(path24,path24[1:],angles,angles[1:]):
   centeredLeft=left-centers[a0][None,:]
   centeredRight=right-centers[a1][None,:]
   front=float(np.linalg.norm(centeredLeft-centeredRight,axis=1).mean())
   backward=float(np.linalg.norm(centeredLeft-centeredRight[::-1],axis=1).mean())
   meanShifts.append(round(min(front,backward),3))
   flipped.append(backward<front)
  status['normalizedPairwiseDriftPx']=meanShifts
  status['reversePairDirections']=flipped
  if ratio>3.3:status['reasons'].append('source path length ratio > 3.3')
  if max(meanShifts)>84:status['reasons'].append('large cross-view source path drift')
 if status['modelCrossViewConfidence']<.73:
  status['reasons'].append('vision model identity confidence < .73')
 status['crossViewAcceptedForExperiment']=not status['reasons']
 roles[role]=status
 print('ROLE',role,'accepted',status['crossViewAcceptedForExperiment'],
       'edge',[x['edgeWithin9pxFraction'] for x in status['sourceView'].values()],
       'reasons',status['reasons'],flush=True)
# Real source drawing overlays, with one role identity color and observed point order.
colors=[(248,38,43),(35,156,239),(190,61,224),(45,188,111),
        (232,149,34),(159,40,102),(38,134,213),(221,91,26),(124,90,216)]
for view in angles:
 canvas=Image.fromarray(native[view]['white'],'RGB')
 paint=ImageDraw.Draw(canvas)
 for j,(role,state) in enumerate(roles.items()):
  pts=np.array(state['sourceView'][view]['points']).reshape(-1,2)
  if len(pts)<2:continue
  col=colors[j%len(colors)]
  thickness=3 if state['crossViewAcceptedForExperiment'] else 2
  paint.line([tuple(p) for p in pts],fill=col,width=thickness)
  x,y=pts[0]
  paint.ellipse((x-4,y-4,x+4,y+4),fill=col)
  paint.text((x+5,y-13),str(j)+('✓' if state['crossViewAcceptedForExperiment'] else ''),fill=col)
 canvas.crop((385,625,845,1024)).resize((690,599),Image.Resampling.LANCZOS).save(
   D/f'yaw{view.replace(".","p")}-model-paths.jpg',quality=94)
payload={'schema':'KOMA_P15_110_VISION_CORRESPONDENCE_QA_V1',
 'characterId':'p0_character_001','sourceAngles':[60,67.5,75],
 'annotationSHA256':sha(raw),'annotationSource':'Codex gpt-6.1-sol image vision, 7 native/cropped source images',
 'sourceImages':{view:{'path':str(src.relative_to(R)),'sha256':sha(src)} for view,src in sources.items()},
 'roleNames':list(roles),'roles':roles,
 'experimentAcceptedRoles':[name for name,q in roles.items() if q['crossViewAcceptedForExperiment']],
 'sourceImageVisualGate':'source-edge distance, alpha support, material-length and model confidence',
 'artistStrokeIDsApproved':False,
 'full360YawAccepted':False}
out=R/'evidence/p15-110-vision-qa.json'
out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
print('ACCEPTED',len(payload['experimentAcceptedRoles']),'/',len(roles),payload['experimentAcceptedRoles'])

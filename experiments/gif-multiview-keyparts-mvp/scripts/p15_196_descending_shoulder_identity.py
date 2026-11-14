#!/usr/bin/env python3
"""P15-196 correct semantic identity of the ahoge descending shoulder.

P15-194's exit shoulder search window overlapped the outer-arc apex and
selected unrelated curvature peaks. This audit constrains the exit feature
to the descending branch after the apex, then reparameterizes the same
source centerline/width/donor coordinates and compares 13-yaw renders.
"""
import json,hashlib
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw
from p15_129_ahoge_ownership import keyframes,KEYS,top_components
from p15_184_alpha_aware_temporal_sweep import ANGLES,build_sequence,local_metrics
from p15_187_full_skeleton_vdd import source_geometry,render_strand,normalized
from p15_194_multifeature_correspondence import FEATURE_U,FEATURE_NAMES
from p15_195_width_curvature_regularization import regularize
from p15_189_root_emergence_audit import interpolate_crossing,color_seam
from p15_166_crown_silhouette import crown_edge
from p15_134_underpaint_probe import P,compose
ROOT=Path(__file__).resolve().parents[1]
OUT=P/'exports/p15-196-descending-shoulder-identity'
E=ROOT/'evidence/p15-196-descending-shoulder-identity-qa.json'
N=160
def curve_curvature(curve):
 p=np.asarray(curve,np.float32);d=np.gradient(p,axis=0);dd=np.gradient(d,axis=0)
 return np.abs(d[:,0]*dd[:,1]-d[:,1]*dd[:,0])/np.maximum(np.linalg.norm(d,axis=1)**3,1.e-5)
def smooth1(x,sigma):
 x=np.asarray(x,np.float32)
 return cv2.GaussianBlur(x.reshape(1,-1),(0,0),sigma).reshape(-1)
def semantic_indices(g):
 p=g['curve'];c=smooth1(curve_curvature(p),3);n=len(p)
 apex=int(np.argmin(smooth1(p[:,1],2)))
 # Entry: rising branch before apex; exit: descending branch after apex.
 elo=max(8,int(.08*n));ehi=min(apex-8,int(.32*n))
 xlo=max(apex+12,int(.76*n));xhi=min(n-8,int(.96*n))
 entry=int(elo+np.argmax(c[elo:ehi]))
 exit=int(xlo+np.argmax(c[xlo:xhi]))
 ids=np.array([0,entry,apex,exit,n-1],np.int32)
 if not np.all(np.diff(ids)>0):raise ValueError(f'feature ordering failed {ids}')
 return ids,c,{'entryWindow':[elo,ehi],'apexIndex':apex,'exitWindow':[xlo,xhi]}
def reparameterize(g,ids):
 new=np.interp(np.arange(N,dtype=np.float32),FEATURE_U*(N-1),ids.astype(np.float32))
 xy=np.column_stack([np.interp(new,np.arange(N),g['curve'][:,j]) for j in (0,1)]).astype(np.float32)
 width=np.interp(new,np.arange(N),g['width']).astype(np.float32)
 xy[0]=g['curve'][0];xy[-1]=g['curve'][-1]
 out=dict(g);out.update(curve=xy,width=width,normal=normalized(xy))
 return out
def geom(gs,a,b,t):
 xy=(1-t)*gs[a]['curve']+t*gs[b]['curve'];w=(1-t)*gs[a]['width']+t*gs[b]['width']
 return {'curve':xy,'width':w,'normal':normalized(xy)}
def evaluate(save=True):
 src=keyframes();dis,crowns=build_sequence(src)
 raw={a:source_geometry(src[a],a) for a in KEYS}
 corrected={};landmarks={}
 for a in KEYS:
  ids,c,windows=semantic_indices(raw[a]);corrected[a]=reparameterize(raw[a],ids)
  landmarks[f'{a:g}']={'indices':ids.tolist(),'coordinates':raw[a]['curve'][ids].round(4).tolist(),
   'normalizedArcPositions':(ids/(N-1)).round(5).tolist(),
   'curvatureAtFeatures':c[ids].round(6).tolist(),
   'widthAtFeatures':raw[a]['width'][ids].round(4).tolist(),
   'windows':windows,'exitShoulderBranch':'descending-after-apex',
   'sourceRGBAHash':hashlib.sha256(src[a].tobytes()).hexdigest()}
 variants={'P15_194_old_feature_linear':{a:None for a in KEYS},
          'P15_196_corrected_feature_linear':corrected,
          'P15_196_corrected_light_smooth':{a:regularize(corrected[a],1.5,3) for a in KEYS}}
 metrics={};details={};renders={}
 dis_local,dis_global=local_metrics(dis)
 for name,gs in variants.items():
  seq=[];report={};cross={};seams={}
  for i,angle in enumerate(ANGLES):
   if angle in KEYS:
    frame=src[angle].copy();shape=raw[angle]
   else:
    a,b=(90.,112.5) if angle<112.5 else (112.5,135.)
    t=(angle-a)/(b-a)
    if name=='P15_194_old_feature_linear':
     from p15_194_multifeature_correspondence import parameterize
     old={k:parameterize(raw[k])[0] for k in KEYS}
     shape=geom(old,a,b,t)
     left,right=old[a],old[b]
    else:
     shape=geom(gs,a,b,t);left,right=gs[a],gs[b]
    strand,meta=render_strand(shape,left,right,t)
    frame=compose(strand,crowns[i]);frame[125:]=dis[i][125:]
   edge=crown_edge(crowns[i],9)
   point,tangent,seg=interpolate_crossing(shape['curve'],edge)
   has=point is not None
   if not has:point=shape['curve'][0];tangent=np.array([0.,-1.],np.float32)
   cross[f'{angle:g}']=point
   seams[f'{angle:g}']=color_seam(frame,crowns[i],point,tangent)['rootContactColorDeltaRGB']
   if angle not in KEYS:
    report[f'{angle:g}']={'actualCrownCrossing':has,'connectedComponents':top_components(frame),
      'deepBodyExact':bool(np.array_equal(frame[125:],dis[i][125:])),
      'rootCrossing':point.round(4).tolist(),'seam':seams[f'{angle:g}'],
      'featureCoordinates':np.stack([shape['curve'][int(round(u*(N-1)))] for u in FEATURE_U]).round(4).tolist(),
      'visibleStrandPixels':meta['visibleStrandPixels']}
   seq.append(frame)
  local,global_=local_metrics(seq)
  steps=[float(np.linalg.norm(cross[f'{b:g}']-cross[f'{a:g}'])) for a,b in zip(ANGLES,ANGLES[1:])]
  seam_steps=[abs(seams[f'{b:g}']-seams[f'{a:g}']) for a,b in zip(ANGLES,ANGLES[1:])]
  metrics[name]={'maxAdjacentLocalRGBMAE':max(local),'maxAdjacentGlobalRGBMAE':max(global_),
   'maxAdjacentDISLocalRGBMAE':max(dis_local),'maxAdjacentDISGlobalRGBMAE':max(dis_global),
   'maxAdjacentRootCrossingStepPixels':round(max(steps),4),
   'middleRootCrossingStepsPixels':[round(x,4) for x in steps[5:7]],
   'maxAdjacentSeamChange':round(max(seam_steps),4),
   'allNativeKeysExact':all(np.array_equal(seq[ANGLES.index(a)],src[a]) for a in KEYS),
   'allMidframesHaveCrownCrossing':all(x['actualCrownCrossing'] for x in report.values()),
   'allMidframesSingleComponent':all(x['connectedComponents']==1 for x in report.values()),
   'allDeepBodyExact':all(x['deepBodyExact'] for x in report.values())}
  details[name]=report;renders[name]=seq
 # Candidate requires geometry and temporal improvement against previous accepted candidate.
 base=metrics['P15_194_old_feature_linear'];cand=metrics['P15_196_corrected_light_smooth']
 qa={'schema':'KOMA_P15_196_DESCENDING_SHOULDER_IDENTITY_V1','characterId':'p0_character_001',
  'sourceAngles':list(KEYS),'renderAngles':list(ANGLES),'featureNames':list(FEATURE_NAMES),
  'sharedFeatureCoordinates':FEATURE_U.tolist(),'sourceLandmarks':landmarks,
  'methods':metrics,'details':details,'selectedDiagnosticMethod':'P15_196_corrected_light_smooth',
  'finding':'P15-194 exit shoulder search selected curvature maxima from a window overlapping the outer-arc apex. The corrected detector constrains the exit shoulder to the descending branch after the apex (76%-96% source arc). This produces semantically ordered and visually distinct features. Promotion is still gated by temporal metrics and full-resolution review.',
  'productionRendererUpdated':False,'visualAccepted':False,
  'review':'private-assets/exports/p15-196-descending-shoulder-identity/index.html'}
 qa['gate']={'allFeatureIndicesOrdered':all(all(x<y for x,y in zip(v['indices'],v['indices'][1:])) for v in landmarks.values()),
  'exitShouldersOnDescendingBranch':all(v['indices'][3]>v['indices'][2] and v['windows']['exitWindow'][0]>v['indices'][2] for v in landmarks.values()),
  'allNativeKeysExact':cand['allNativeKeysExact'],'allDeepBodyExact':cand['allDeepBodyExact'],
  'allMidframesSingleComponent':cand['allMidframesSingleComponent'],
  'allMidframesHaveCrownCrossing':cand['allMidframesHaveCrownCrossing'],
  'localTemporalImproved':cand['maxAdjacentLocalRGBMAE']<base['maxAdjacentLocalRGBMAE'],
  'globalTemporalBeatsDIS':cand['maxAdjacentGlobalRGBMAE']<=max(dis_global),
  'rootAndSeamNotWorse':cand['maxAdjacentRootCrossingStepPixels']<=base['maxAdjacentRootCrossingStepPixels'] and cand['maxAdjacentSeamChange']<=base['maxAdjacentSeamChange'],
  'visualAccepted':False,'semanticFeatureCorrespondenceApproved':False,'passes':False}
 if save:
  OUT.mkdir(parents=True,exist_ok=True)
  board=Image.new('RGB',(205*len(ANGLES),185*4),(35,42,54));pen=ImageDraw.Draw(board)
  for row,(name,seq) in enumerate([('DIS',dis),*renders.items()]):
   folder=OUT/name;folder.mkdir(exist_ok=True)
   for col,(angle,frame) in enumerate(zip(ANGLES,seq)):
    Image.fromarray(frame,'RGBA').save(folder/(f'yaw{angle:06.2f}'.replace('.','p')+'.png'))
    tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
    board.paste(tile.crop((110,0,380,135)).resize((198,150),Image.Resampling.LANCZOS).convert('RGB'),(col*205,row*185+25))
    pen.text((col*205+3,row*185+3),f'{name} {angle:g}',fill='white')
  board.save(OUT/'corrected-shoulder-13-yaw.jpg',quality=95)
  # Feature point audit at native key angles.
  strips=Image.new('RGB',(360*3,220),(35,42,54))
  for col,a in enumerate(KEYS):
   tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(src[a],'RGBA'))
   draw=ImageDraw.Draw(tile)
   for j,(x,y) in enumerate(landmarks[f'{a:g}']['coordinates']):
    draw.ellipse((x-4,y-4,x+4,y+4),fill=(255,210,40,255));draw.text((x+5,y-5),str(j),fill='white')
   strips.paste(tile.crop((110,0,380,145)).resize((350,188),Image.Resampling.LANCZOS).convert('RGB'),(col*360,25))
  strips.save(OUT/'corrected-native-feature-points.jpg',quality=95)
  (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P15-196 descending shoulder identity</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Corrected source feature identities</h2><p>0 root, 1 entry shoulder, 2 outer apex, 3 descending-branch shoulder, 4 tip.</p><img src="corrected-native-feature-points.jpg"><h2>13-yaw comparison</h2><img src="corrected-shoulder-13-yaw.jpg"><pre>'+json.dumps(qa['gate'],indent=2)+'</pre>')
  E.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
 return qa
if __name__=='__main__':
 q=evaluate();print(json.dumps({'landmarks':q['sourceLandmarks'],'metrics':q['methods'],'gate':q['gate']},indent=2))

#!/usr/bin/env python3
"""P15-194 multi-feature semantic correspondence for the 3 native ahoge keys.

Extract root, outer-arc apex, free tip, two stable curvature shoulders and
local width profile from each native source-owned strand. Reparameterize
geometry and donor texture together against shared feature coordinates and
compare against raw arc-length linear VDD on 13 yaw frames.
"""
import json,hashlib
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_129_ahoge_ownership import keyframes,KEYS,top_components
from p15_184_alpha_aware_temporal_sweep import ANGLES,build_sequence,local_metrics
from p15_187_full_skeleton_vdd import source_geometry,render_strand,normalized
from p15_189_root_emergence_audit import color_seam,interpolate_crossing
from p15_166_crown_silhouette import crown_edge
from p15_134_underpaint_probe import P,compose
ROOT=Path(__file__).resolve().parents[1]
OUT=P/'exports/p15-194-multifeature-correspondence'
E=ROOT/'evidence/p15-194-multifeature-correspondence-qa.json'
N=160
# Shared semantic coordinates: root, entry shoulder, outer arc apex,
# exit shoulder, free tip. Curvature shoulders are selected in separate
# arc windows to avoid choosing the same local maximum twice.
FEATURE_U=np.array([0.,.25,.5,.75,1.],np.float32)
FEATURE_NAMES=('root','entry_shoulder','outer_arc_apex','exit_shoulder','free_tip')
def curvature(curve):
    p=np.asarray(curve,np.float32)
    d1=np.gradient(p,axis=0);d2=np.gradient(d1,axis=0)
    cross=np.abs(d1[:,0]*d2[:,1]-d1[:,1]*d2[:,0])
    return cross/np.maximum(np.linalg.norm(d1,axis=1)**3,1.e-5)
def smooth(x,sigma=3.):
    return cv2.GaussianBlur(np.asarray(x,np.float32).reshape(1,-1),(1,0),sigma).reshape(-1)
def feature_indices(curve):
    c=smooth(curvature(curve),3)
    # Suppress skeleton raster spikes; constrain shoulders to their own
    # monotonic portions of the root-to-tip arc.
    n=len(curve)
    apex=int(np.argmin(smooth(curve[:,1],2.)))
    apex=int(np.clip(apex,35,125))
    left_lo=max(8,int(.12*n));left_hi=min(apex-10,int(.42*n))
    right_lo=max(apex+10,int(.58*n));right_hi=min(n-8,int(.9*n))
    left=int(left_lo+np.argmax(c[left_lo:left_hi]))
    right=int(right_lo+np.argmax(c[right_lo:right_hi]))
    ids=np.array([0,left,apex,right,n-1],np.int32)
    # Guarantee monotonicity; if curvature extrema collide with apex,
    # use the nearest interior point and retain the raw feature evidence.
    for i in range(1,len(ids)-1):
        ids[i]=max(ids[i],ids[i-1]+5)
    ids[-1]=n-1
    return ids,c
def parameterize(g):
    ids,curv=feature_indices(g['curve'])
    old=np.arange(N,dtype=np.float32)
    new=np.interp(old,FEATURE_U*(N-1),ids.astype(np.float32)).astype(np.float32)
    xy=np.column_stack([np.interp(new,np.arange(N),g['curve'][:,k]) for k in (0,1)]).astype(np.float32)
    width=np.interp(new,np.arange(N),g['width']).astype(np.float32)
    # The feature coordinates are shared; endpoints stay exact.
    xy[0]=g['curve'][0];xy[-1]=g['curve'][-1]
    result=dict(g);result.update(curve=xy,width=width,normal=normalized(xy))
    return result,ids,curv
def arc_geom(gs,a,b,t):
    xy=gs[a]['curve']*(1-t)+gs[b]['curve']*t
    w=gs[a]['width']*(1-t)+gs[b]['width']*t
    return {'curve':xy.astype(np.float32),'width':w.astype(np.float32),'normal':normalized(xy)}
def run(save=True):
    src=keyframes();base,crowns=build_sequence(src)
    raw={a:source_geometry(src[a],a) for a in KEYS}
    aligned={};feature_data={}
    for a in KEYS:
        aligned[a],ids,curv=parameterize(raw[a])
        p=raw[a]['curve']
        feature_data[f'{a:g}']={
          'indices':ids.tolist(),
          'coordinates':p[ids].round(4).tolist(),
          'normalizedArcPositions':(ids/(N-1)).round(5).tolist(),
          'curvatureAtFeatures':curv[ids].round(6).tolist(),
          'featureNames':list(FEATURE_NAMES),
          'widthAtFeatures':raw[a]['width'][ids].round(3).tolist(),
          'widthPercentiles':np.percentile(raw[a]['width'],[10,50,90]).round(3).tolist(),
          'sourceSHA256':hashlib.sha256(src[a].tobytes()).hexdigest()}
    methods=('arc_linear','multi_feature_linear')
    outputs={};details={};metrics={}
    dis_local,dis_global=local_metrics(base)
    for method in methods:
        frames=[];report={};crossings={};feature_trajectory={}
        gs=raw if method=='arc_linear' else aligned
        for i,angle in enumerate(ANGLES):
            if angle in KEYS:
                frames.append(src[angle].copy())
                native_edge=crown_edge(crowns[i],9)
                native_cross,_,_=interpolate_crossing(raw[angle]['curve'],native_edge)
                if native_cross is None:raise RuntimeError(f'missing native root/crown crossing at {angle}')
                crossings[f'{angle:g}']=native_cross
                feature_trajectory[f'{angle:g}']=np.asarray(feature_data[f'{angle:g}']['coordinates'])
                continue
            a,b=(90.,112.5) if angle<112.5 else (112.5,135.)
            t=(angle-a)/(b-a)
            shape=arc_geom(gs,a,b,t)
            strand,render_meta=render_strand(shape,gs[a],gs[b],t)
            image=compose(strand,crowns[i])
            image[125:]=base[i][125:]
            edge=crown_edge(crowns[i],9)
            # Measure actual crown crossing for geometric continuity.
            cross,tangent,seg=interpolate_crossing(shape['curve'],edge)
            actual_crossing=cross is not None
            if cross is None:
                signed=np.asarray([float(pt[1]-edge[int(np.clip(round(float(pt[0])),0,442))]) for pt in shape['curve']])
                nearest=int(np.argmin(np.abs(signed)))
                cross=shape['curve'][nearest].copy()
                tangent=shape['curve'][min(nearest+2,N-1)]-shape['curve'][max(nearest-2,0)]
                tangent=tangent/max(float(np.linalg.norm(tangent)),1.e-6)
            crossings[f'{angle:g}']=cross
            # The 5 shared semantic points are evaluated in the interpolated
            # medial geometry, not re-detected from a noisy raster skeleton.
            points=np.stack([shape['curve'][int(round(u*(N-1)))] for u in FEATURE_U])
            feature_trajectory[f'{angle:g}']=points
            report[f'{angle:g}']={
              'featureCoordinates':points.round(4).tolist(),
              'rootCrownCrossing':cross.round(4).tolist(),
              'crossingTangent':tangent.round(5).tolist(),
              'crossingSegment':int(seg) if actual_crossing else None,
              'actualCrownCrossingFound':actual_crossing,
              'featureWidths':[float(shape['width'][int(round(u*(N-1)))]) for u in FEATURE_U],
              'connectedComponents':top_components(image),
              'deepBodyExact':bool(np.array_equal(image[125:],base[i][125:])),
              'visibleStrandPixels':render_meta['visibleStrandPixels'],
              'colorSeam':color_seam(image,crowns[i],cross,tangent)['rootContactColorDeltaRGB']}
            frames.append(image)
        local,global_e=local_metrics(frames)
        adjacent_cross=[float(np.linalg.norm(crossings[f'{b:g}']-crossings[f'{a:g}'])) for a,b in zip(ANGLES,ANGLES[1:])]
        # Feature motion per yaw step; report each semantic landmark separately.
        feature_steps=np.stack([
          np.linalg.norm(feature_trajectory[f'{b:g}']-feature_trajectory[f'{a:g}'],axis=1)
          for a,b in zip(ANGLES,ANGLES[1:])])
        metrics[method]={
          'maxAdjacentLocalRGBMAE':max(local),'maxAdjacentGlobalRGBMAE':max(global_e),
          'maxAdjacentDISLocalRGBMAE':max(dis_local),'maxAdjacentDISGlobalRGBMAE':max(dis_global),
          'maxAdjacentRootCrossingStepPixels':round(max(adjacent_cross),4),
          'middleRootCrossingStepsPixels':[round(x,4) for x in adjacent_cross[5:7]],
          'maxAdjacentFeatureStepByName':{n:round(float(feature_steps[:,j].max()),4) for j,n in enumerate(FEATURE_NAMES)},
          'meanFeatureStepPixels':round(float(feature_steps.mean()),4),
          'allNativeKeysExact':all(np.array_equal(frames[ANGLES.index(k)],src[k]) for k in KEYS),
          'allMidframesSingleComponent':all(v['connectedComponents']==1 for v in report.values()),
          'allMidframesHaveActualCrownCrossing':all(v['actualCrownCrossingFound'] for v in report.values()),
          'allDeepBodyExact':all(v['deepBodyExact'] for v in report.values())}
        outputs[method]=frames;details[method]=report
    # No score-only promotion: multi-feature must improve both root crossing
    # continuity and local temporal error to displace the arc baseline.
    chosen='multi_feature_linear' if (
      metrics['multi_feature_linear']['maxAdjacentRootCrossingStepPixels']<metrics['arc_linear']['maxAdjacentRootCrossingStepPixels']
      and metrics['multi_feature_linear']['maxAdjacentLocalRGBMAE']<=metrics['arc_linear']['maxAdjacentLocalRGBMAE']) else 'arc_linear'
    m=metrics[chosen]
    q={'schema':'KOMA_P15_194_MULTIFEATURE_CORRESPONDENCE_V1',
      'characterId':'p0_character_001','sourceAngles':list(KEYS),'renderAngles':list(ANGLES),
      'featureNames':list(FEATURE_NAMES),'sharedFeatureCoordinates':FEATURE_U.tolist(),
      'sourceFeatureLandmarks':feature_data,'methods':metrics,'details':details,
      'selectedDiagnosticMethod':chosen,
      'method':'Source-owned medial curve multi-feature correspondence: root, two windowed curvature shoulders, minimum-y outer-arc apex, free tip; jointly reparameterize centerline, width and donor texture at shared u={0,.25,.5,.75,1}.',
      'productionRendererUpdated':False,'visualAccepted':False,
      'review':'private-assets/exports/p15-194-multifeature-correspondence/index.html'}
    q['gate']={
      'allFiveFeaturesOrderedInAllKeys':all(all(x<y for x,y in zip(v['indices'],v['indices'][1:])) for v in feature_data.values()),
      'allNativeKeysExact':all(v['allNativeKeysExact'] for v in metrics.values()),
      'allMidframesSingleComponent':all(v['allMidframesSingleComponent'] for v in metrics.values()),
      'allMidframesHaveActualCrownCrossing':all(v['allMidframesHaveActualCrownCrossing'] for v in metrics.values()),
      'allDeepBodyExact':all(v['allDeepBodyExact'] for v in metrics.values()),
      'rootCrossingImprovedOverArc':m['maxAdjacentRootCrossingStepPixels']<metrics['arc_linear']['maxAdjacentRootCrossingStepPixels'],
      'localTemporalBeatsArc':m['maxAdjacentLocalRGBMAE']<=metrics['arc_linear']['maxAdjacentLocalRGBMAE'],
      'globalTemporalBeatsDIS':m['maxAdjacentGlobalRGBMAE']<=max(dis_global),
      'visualAccepted':False,'semanticFeatureCorrespondenceApproved':False,'passes':False}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(205*len(ANGLES),190*3),(35,42,54));draw=ImageDraw.Draw(board)
        for row,(name,seq) in enumerate([('whole_frame_DIS',base),*outputs.items()]):
            folder=OUT/name;folder.mkdir(exist_ok=True)
            for col,(angle,image) in enumerate(zip(ANGLES,seq)):
                Image.fromarray(image,'RGBA').save(folder/(f'yaw{angle:06.2f}'.replace('.','p')+'.png'))
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(image,'RGBA'))
                board.paste(tile.crop((110,0,380,135)).resize((198,150),Image.Resampling.LANCZOS).convert('RGB'),(col*205,row*190+28))
                draw.text((col*205+3,row*190+4),f'{name} {angle:g}',fill='white')
        board.save(OUT/'multifeature-13-yaw.jpg',quality=95)
        # Native feature overlay makes the point identities auditable.
        overlays=Image.new('RGB',(360*3,220),(35,42,54))
        for col,a in enumerate(KEYS):
            tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(src[a],'RGBA'))
            pen=ImageDraw.Draw(tile);f=feature_data[f'{a:g}']['coordinates']
            for j,(x,y) in enumerate(f):
                rr=4;pen.ellipse((x-rr,y-rr,x+rr,y+rr),fill=(255,210,40,255))
                pen.text((x+5,y-5),str(j),fill=(255,255,255,255))
            overlays.paste(tile.crop((110,0,380,145)).resize((350,188),Image.Resampling.LANCZOS).convert('RGB'),(col*360,25))
        overlays.save(OUT/'native-five-feature-landmarks.jpg',quality=95)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P15-194 multi-feature correspondence</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Native semantic feature landmarks</h2><p>0 root, 1 entry curvature shoulder, 2 outer-arc apex, 3 exit curvature shoulder, 4 free tip.</p><img src="native-five-feature-landmarks.jpg"><h2>13-yaw comparison</h2><img src="multifeature-13-yaw.jpg"><pre>'+json.dumps(q['gate'],indent=2)+'</pre>')
        E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':
 q=run();print(json.dumps({'selected':q['selectedDiagnosticMethod'],'metrics':q['methods'],'gate':q['gate']},indent=2))

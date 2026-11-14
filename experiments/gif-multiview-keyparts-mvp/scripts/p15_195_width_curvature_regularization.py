#!/usr/bin/env python3
"""P15-195: curvature and width-profile regularization of native 3-key strands.

Compare the accepted P15-194 five-landmark linear baseline with source-local
smoothed centerlines and distance-transform widths. Smooth in source local
coordinates, preserve root/tip, keep the original three source raster keys,
and score local/global temporal error, scalp contact and mask continuity.
"""
import json,hashlib
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw
from p15_129_ahoge_ownership import keyframes,KEYS,top_components
from p15_184_alpha_aware_temporal_sweep import ANGLES,build_sequence,local_metrics
from p15_187_full_skeleton_vdd import source_geometry,render_strand,normalized
from p15_194_multifeature_correspondence import parameterize,feature_indices,curvature,FEATURE_U,FEATURE_NAMES
from p15_189_root_emergence_audit import interpolate_crossing,color_seam
from p15_166_crown_silhouette import crown_edge
from p15_134_underpaint_probe import P,compose
ROOT=Path(__file__).resolve().parents[1]
OUT=P/'exports/p15-195-width-curvature-regularization'
E=ROOT/'evidence/p15-195-width-curvature-regularization-qa.json'
N=160
METHODS={'feature_linear':(0.,0.),'width_s3':(0.,3.),'width_s6':(0.,6.),
         'curve_s1p5_width_s3':(1.5,3.),'curve_s3_width_s6':(3.,6.)}
def blur_1d(vals,sigma):
    arr=np.asarray(vals,np.float32)
    if sigma<=0:return arr.copy()
    if arr.ndim==1:
        return cv2.GaussianBlur(arr.reshape(1,-1),(0,0),sigma).reshape(-1)
    return np.column_stack([blur_1d(arr[:,j],sigma) for j in range(arr.shape[1])])
def regularize(source,curve_sigma,width_sigma):
    out=dict(source)
    xy=blur_1d(source['curve'],curve_sigma)
    w=blur_1d(source['width'],width_sigma)
    # Source endpoint IDs and tip taper are exact.
    xy[0]=source['curve'][0];xy[-1]=source['curve'][-1]
    w[0]=source['width'][0];w[-1]=source['width'][-1]
    out.update(curve=xy,width=np.clip(w,1.5,18.),normal=normalized(xy))
    return out
def interval(a):
    left,right=(90.,112.5) if a<112.5 else (112.5,135.)
    return left,right,(a-left)/(right-left)
def shape_at(gs,angle):
    left,right,t=interval(angle)
    xy=(1-t)*gs[left]['curve']+t*gs[right]['curve']
    w=(1-t)*gs[left]['width']+t*gs[right]['width']
    return {'curve':xy,'width':w,'normal':normalized(xy)},left,right,t
def evaluate(save=True):
    source=keyframes();baseline,crowns=build_sequence(source)
    keys={a:parameterize(source_geometry(source[a],a))[0] for a in KEYS}
    features={}
    for a in KEYS:
        geom=source_geometry(source[a],a)
        idx,score=feature_indices(geom['curve'])
        apex=int(idx[2]);exit_idx=int(idx[3])
        features[f'{a:g}']={
          'landmarkIndices':idx.tolist(),'exitShoulder':[float(v) for v in geom['curve'][exit_idx]],
          'exitShoulderWidth':round(float(geom['width'][exit_idx]),4),
          'exitShoulderCurvature':round(float(score[exit_idx]),5),
          'apex':[float(v) for v in geom['curve'][apex]],
          'sourceRGBAHash':hashlib.sha256(source[a].tobytes()).hexdigest()}
    dis_local,dis_global=local_metrics(baseline)
    methods={};details={};outputs={}
    for name,(cs,ws) in METHODS.items():
        gs={a:regularize(keys[a],cs,ws) for a in KEYS}
        seq=[];info={};crossings={};seams={};visible_areas={}
        for i,a in enumerate(ANGLES):
            if a in KEYS:
                seq.append(source[a].copy())
                edge=crown_edge(crowns[i],9)
                pt,tangent,_=interpolate_crossing(source_geometry(source[a],a)['curve'],edge)
                if pt is None:raise ValueError('native crown crossing missing')
                crossings[f'{a:g}']=pt
                seams[f'{a:g}']=color_seam(source[a],crowns[i],pt,tangent)['rootContactColorDeltaRGB']
                continue
            shape,left,right,t=shape_at(gs,float(a))
            strand,metadata=render_strand(shape,gs[left],gs[right],t)
            frame=compose(strand,crowns[i])
            frame[125:]=baseline[i][125:]
            edge=crown_edge(crowns[i],9)
            point,tangent,_=interpolate_crossing(shape['curve'],edge)
            has_cross=point is not None
            if not has_cross:
                # Missing crown crossing is an explicit failure, not replaced
                # by an invented interpolated crossing coordinate.
                point=shape['curve'][0];tangent=np.array([0.,-1.],np.float32)
            crossings[f'{a:g}']=point
            seams[f'{a:g}']=color_seam(frame,crowns[i],point,tangent)['rootContactColorDeltaRGB']
            info[f'{a:g}']={
                'hasCrownCrossing':has_cross,'sourceKeysExact':True,
                'belowY125Exact':bool(np.array_equal(frame[125:],baseline[i][125:])),
                'singleComponent':top_components(frame)==1,
                'tipCoordinate':shape['curve'][-1].round(4).tolist(),
                'rootCrossing':point.round(4).tolist(),
                'colorSeam':seams[f'{a:g}'],
                'visibleStrandPixels':metadata['visibleStrandPixels'],
                'maxWidth':round(float(np.max(shape['width'])),4),
                'curvatureMax':round(float(np.max(blur_1d(curvature(shape['curve']),2))),5)}
            visible_areas[f'{a:g}']=metadata['visibleStrandPixels']
            seq.append(frame)
        local,global_e=local_metrics(seq)
        csteps=[float(np.linalg.norm(crossings[f'{b:g}']-crossings[f'{a:g}'])) for a,b in zip(ANGLES,ANGLES[1:])]
        seamsteps=[abs(seams[f'{b:g}']-seams[f'{a:g}']) for a,b in zip(ANGLES,ANGLES[1:])]
        methods[name]={
          'maxAdjacentLocalRGBMAE':max(local),
          'maxAdjacentGlobalRGBMAE':max(global_e),
          'maxAdjacentDISLocalRGBMAE':max(dis_local),
          'maxAdjacentDISGlobalRGBMAE':max(dis_global),
          'maxAdjacentRootCrossingStepPixels':round(max(csteps),4),
          'middleRootCrossingStepPixels':[round(x,4) for x in csteps[5:7]],
          'maxAdjacentColorSeamChange':round(max(seamsteps),4),
          'middleSeamChanges':[round(x,4) for x in seamsteps[5:7]],
          'intermediateAreaMinMax':[min(visible_areas.values()),max(visible_areas.values())],
          'allNativeKeysExact':all(np.array_equal(seq[ANGLES.index(a)],source[a]) for a in KEYS),
          'allMidframesHaveCrownCrossing':all(v['hasCrownCrossing'] for v in info.values()),
          'allMidframesSingleComponent':all(v['singleComponent'] for v in info.values()),
          'allDeepBodyExact':all(v['belowY125Exact'] for v in info.values())}
        outputs[name]=seq;details[name]=info
    baseline_m=methods['feature_linear']
    eligible=[name for name,m in methods.items() if (
        m['allMidframesHaveCrownCrossing'] and m['allMidframesSingleComponent'] and
        m['maxAdjacentRootCrossingStepPixels']<=baseline_m['maxAdjacentRootCrossingStepPixels'] and
        m['maxAdjacentLocalRGBMAE']<=baseline_m['maxAdjacentLocalRGBMAE'] and
        m['maxAdjacentColorSeamChange']<=baseline_m['maxAdjacentColorSeamChange'])]
    chosen=min(eligible,key=lambda n:(methods[n]['maxAdjacentGlobalRGBMAE'],methods[n]['maxAdjacentLocalRGBMAE']))
    m=methods[chosen]
    qa={'schema':'KOMA_P15_195_WIDTH_CURVATURE_REGULARIZATION_V1',
        'characterId':'p0_character_001','sourceAngles':list(KEYS),'renderAngles':list(ANGLES),
        'sourceFeatureEvidence':features,'methods':methods,'details':details,
        'selectedDiagnosticMethod':chosen,
        'selectionRule':'Require source-key, alpha-region, root-crossing, single-component and seam continuity gates. Among candidates that do not worsen local MAE, crossing displacement or maximum seam change, minimize global RGB MAE.',
        'productionRendererUpdated':False,'visualAccepted':False,
        'review':'private-assets/exports/p15-195-width-curvature-regularization/index.html'}
    qa['gate']={'allNativeKeysExact':all(v['allNativeKeysExact'] for v in methods.values()),
        'allDeepBodyExact':all(v['allDeepBodyExact'] for v in methods.values()),
        'allMidframesSingleComponent':all(v['allMidframesSingleComponent'] for v in methods.values()),
        'allMidframesHaveCrownCrossing':all(v['allMidframesHaveCrownCrossing'] for v in methods.values()),
        'localTemporalBetterThanP15194':m['maxAdjacentLocalRGBMAE']<baseline_m['maxAdjacentLocalRGBMAE'],
        'globalTemporalBeatsDIS':m['maxAdjacentGlobalRGBMAE']<=max(dis_global),
        'rootAndSeamNotWorse':m['maxAdjacentRootCrossingStepPixels']<=baseline_m['maxAdjacentRootCrossingStepPixels'] and m['maxAdjacentColorSeamChange']<=baseline_m['maxAdjacentColorSeamChange'],
        'sourceShoulderSemanticIdentityApproved':False,'visualAccepted':False,'passes':False}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(205*len(ANGLES),182*(len(METHODS)+1)),(35,42,54));pen=ImageDraw.Draw(board)
        for row,(name,seq) in enumerate([('DIS_reference',baseline),*outputs.items()]):
            folder=OUT/name;folder.mkdir(exist_ok=True)
            for col,(angle,img) in enumerate(zip(ANGLES,seq)):
                Image.fromarray(img,'RGBA').save(folder/(f'yaw{angle:06.2f}'.replace('.','p')+'.png'))
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(img,'RGBA'))
                board.paste(tile.crop((110,0,380,135)).resize((198,149),Image.Resampling.LANCZOS).convert('RGB'),(col*205,row*182+26))
                pen.text((col*205+4,row*182+4),f'{name} {angle:g}',fill='white')
        board.save(OUT/'width-curvature-13-yaw.jpg',quality=95)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P15-195 source width and curvature regularization</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Source width and curvature regularization</h2><p>5-feature source geometry with local width smoothing and low-curvature deformation, compared over 13 yaw views. Native keys remain exact.</p><img src="width-curvature-13-yaw.jpg">')
        E.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    return qa
if __name__=='__main__':
    q=evaluate()
    print(json.dumps({'selected':q['selectedDiagnosticMethod'],'methods':q['methods'],'gate':q['gate']},indent=2))

#!/usr/bin/env python3
"""P15-193: 3-key root-contact landmark parameterization and 13-yaw VDD.

Reparameterize each native strand's medial line at the measured crown
emergence. Shared u landmarks: embedded root u=0, emergence u=0.20,
free tip u=1. The donor texture, width and curve are resampled together.
Compare normalized arc linear, root-landmark linear, root-landmark PCHIP.
Native keyframes and material below row 125 stay pixel exact.
"""
import json,hashlib,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from p15_129_ahoge_ownership import keyframes,KEYS,top_components
from p15_184_alpha_aware_temporal_sweep import ANGLES,build_sequence,local_metrics
from p15_187_full_skeleton_vdd import source_geometry,geometry_at,render_strand,normalized
from p15_185_keyview_geometry_correspondence import pchip_three
from p15_189_root_emergence_audit import interpolate_crossing,color_seam
from p15_166_crown_silhouette import crown_edge
from p15_134_underpaint_probe import P,compose
ROOT=Path(__file__).resolve().parents[1]
OUT=P/'exports/p15-193-landmark-parameter-vdd'
E=ROOT/'evidence/p15-193-landmark-parameter-vdd-qa.json'
METHODS=('arc_linear','landmark_linear','landmark_pchip')
N=160
LANDMARK_NODE=32
def parameterize(source,edge):
    curve=source['curve']
    point,tangent,j=interpolate_crossing(curve,edge)
    if point is None:raise ValueError('missing source emergence')
    # P15-189 uses first segment where medial line exits the crown.
    k=float(j-1)
    c0=curve[j-1];c1=curve[j]
    frac=float(np.clip(np.linalg.norm(point-c0)/max(np.linalg.norm(c1-c0),1.e-6),0,1))
    k+=frac
    u=np.arange(N,dtype=np.float32)
    old=np.interp(u,[0,LANDMARK_NODE,N-1],[0,k,N-1]).astype(np.float32)
    # Joint resampling is required: the texture donor's nodes must retain
    # the same semantic longitudinal coordinate as the interpolated ribbon.
    xy=np.column_stack([np.interp(old,np.arange(N),curve[:,dim]) for dim in (0,1)]).astype(np.float32)
    width=np.interp(old,np.arange(N),source['width']).astype(np.float32)
    xy[0]=curve[0];xy[-1]=curve[-1]
    out=dict(source)
    out.update(curve=xy,width=width,normal=normalized(xy))
    return out,{'originalCrossingSegment':int(j),'sourceCrossingFractionalNode':round(k,4),
                'newCrossingNode':LANDMARK_NODE,'sourceCrossing':point.round(4).tolist(),
                'newCrossingControl':xy[LANDMARK_NODE].round(4).tolist(),
                'landmarkResidualPixels':round(float(np.linalg.norm(xy[LANDMARK_NODE]-point)),4),
                'freeTipExact':bool(np.array_equal(xy[-1],curve[-1]))}
def geometry(gs,angle,method):
    a,b=(90.,112.5) if angle<112.5 else (112.5,135.)
    t=(angle-a)/(b-a)
    if method.endswith('linear'):
        xy=gs[a]['curve']*(1-t)+gs[b]['curve']*t
        w=gs[a]['width']*(1-t)+gs[b]['width']*t
    else:
        xy=pchip_three(np.stack([gs[k]['curve'] for k in KEYS]),angle).astype(np.float32)
        w=pchip_three(np.stack([gs[k]['width'] for k in KEYS]),angle).astype(np.float32)
    return {'curve':xy.astype(np.float32),'normal':normalized(xy),'width':np.clip(w,1.5,18).astype(np.float32)},a,b,t

def run(save=True):
    src=keyframes()
    base,crowns=build_sequence(src)
    original={a:source_geometry(src[a],a) for a in KEYS}
    registered={};landmarks={};native_cross={}
    for a in KEYS:
        edge=crown_edge(crowns[ANGLES.index(a)],9)
        registered[a],landmarks[f'{a:g}']=parameterize(original[a],edge)
        native_cross[a]=np.asarray(landmarks[f'{a:g}']['sourceCrossing'],np.float32)
    outputs={};perframe={};metrics={}
    dis_local,dis_global=local_metrics(base)
    for method in METHODS:
        gs=original if method=='arc_linear' else registered
        output=[];reports={};crossings={}
        for i,angle in enumerate(ANGLES):
            if angle in KEYS:
                output.append(src[angle].copy())
                crossings[f'{angle:g}']=native_cross[angle]
                continue
            shape,left,right,t=geometry(gs,float(angle),method)
            strand,st=render_strand(shape,gs[left],gs[right],t)
            img=compose(strand,crowns[i])
            img[125:]=base[i][125:]
            edge=crown_edge(crowns[i],9)
            crossing,tangent,j=interpolate_crossing(shape['curve'],edge)
            if crossing is None:raise ValueError(f'{method}: no crossing at {angle}')
            crossings[f'{angle:g}']=crossing
            target=(1-t)*native_cross[left]+t*native_cross[right]
            reports[f'{angle:g}']={
              'rootCrossing':crossing.round(4).tolist(),
              'rootCrossingTarget':target.round(4).tolist(),
              'rootCrossingTargetResidual':round(float(np.linalg.norm(crossing-target)),4),
              'crossingTangent':tangent.round(4).tolist(),
              'freeTip':shape['curve'][-1].round(4).tolist(),
              'sourceTipInterpolationExact':bool(np.allclose(shape['curve'][-1],gs[left]['curve'][-1]*(1-t)+gs[right]['curve'][-1]*t)) if method.endswith('linear') else True,
              'singleConnectedStrand':top_components(img)==1,
              'deepBodyExact':bool(np.array_equal(img[125:],base[i][125:])),
              'visibleStrandPixels':st['visibleStrandPixels'],
              'colorSeam':color_seam(img,crowns[i],crossing,tangent)['rootContactColorDeltaRGB']}
            output.append(img)
        local,global_e=local_metrics(output)
        steps=[round(float(np.linalg.norm(crossings[f'{a:g}']-crossings[f'{b:g}'])),4) for a,b in zip(ANGLES,ANGLES[1:])]
        target_errors=[v['rootCrossingTargetResidual'] for v in reports.values()]
        metrics[method]={
          'maxAdjacentLocalRGBMAE':max(local),'maxAdjacentGlobalRGBMAE':max(global_e),
          'maxAdjacentDISLocalRGBMAE':max(dis_local),'maxAdjacentDISGlobalRGBMAE':max(dis_global),
          'maxAdjacentRootCrossingStepPixels':max(steps),
          'middleRootCrossingStepsPixels':[steps[5],steps[6]],
          'meanRootCrossingTargetResidual':round(float(np.mean(target_errors)),4),
          'maxRootCrossingTargetResidual':max(target_errors),
          'allNativeKeysExact':all(np.array_equal(output[ANGLES.index(a)],src[a]) for a in KEYS),
          'allDeepBodyExact':all(v['deepBodyExact'] for v in reports.values()),
          'allMidframesSingleComponent':all(v['singleConnectedStrand'] for v in reports.values()),
          'allFreeTipsSourceInterpolated':all(v['sourceTipInterpolationExact'] for v in reports.values())}
        outputs[method]=output;perframe[method]=reports
    # Prefer a method that improves root matching and temporal quality over
    # the existing raw arc baseline; no forced acceptance otherwise.
    candidates=[m for m in METHODS if m!='arc_linear' and
       metrics[m]['maxAdjacentRootCrossingStepPixels']<=metrics['arc_linear']['maxAdjacentRootCrossingStepPixels'] and
       metrics[m]['maxAdjacentLocalRGBMAE']<=metrics['arc_linear']['maxAdjacentLocalRGBMAE']]
    chosen=min(candidates,key=lambda m:metrics[m]['maxAdjacentLocalRGBMAE']) if candidates else 'arc_linear'
    m=metrics[chosen]
    q={'schema':'KOMA_P15_193_ROOT_LANDMARK_PARAMETER_VDD_V1',
       'characterId':'p0_character_001','sourceAngles':list(KEYS),
       'renderAngles':list(ANGLES),'methods':metrics,'details':perframe,
       'sourceLandmarks':landmarks,'landmarkNode':LANDMARK_NODE,
       'selectedDiagnosticMethod':chosen,
       'method':'Native-source root/crown crossing aligned to shared u=0.2; root and free tip are u=0,1. Jointly resample 160-point medial centerline, source donor sampling normals and variable width, then compare linear and PCHIP geometry.',
       'nativeKeyframeSHA256':{f'{a:g}':hashlib.sha256(src[a].tobytes()).hexdigest() for a in KEYS},
       'productionRendererUpdated':False,'visualAccepted':False,
       'review':'private-assets/exports/p15-193-landmark-parameter-vdd/index.html'}
    q['gate']={'allNativeKeysExact':all(v['allNativeKeysExact'] for v in metrics.values()),
       'allDeepBodyExact':all(v['allDeepBodyExact'] for v in metrics.values()),
       'allMidframesSingleComponent':all(v['allMidframesSingleComponent'] for v in metrics.values()),
       'allSourceLandmarksWithinPixel':all(v['landmarkResidualPixels']<1 for v in landmarks.values()),
       'crossingImprovedOverArc':m['maxAdjacentRootCrossingStepPixels']<metrics['arc_linear']['maxAdjacentRootCrossingStepPixels'],
       'localTemporalBeatsDIS':m['maxAdjacentLocalRGBMAE']<=max(dis_local),
       'globalTemporalBeatsDIS':m['maxAdjacentGlobalRGBMAE']<=max(dis_global),
       'visualAccepted':False,'semanticCorrespondenceApproved':False,'passes':False}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(205*len(ANGLES),187*(len(METHODS)+1)),(35,42,54));draw=ImageDraw.Draw(board)
        for row,(name,images) in enumerate([('whole_frame_DIS',base),*outputs.items()]):
            folder=OUT/name;folder.mkdir(exist_ok=True)
            for col,(a,image) in enumerate(zip(ANGLES,images)):
                Image.fromarray(image,'RGBA').save(folder/(f'yaw{a:06.2f}'.replace('.','p')+'.png'))
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(image,'RGBA'))
                board.paste(tile.crop((110,0,380,135)).resize((198,150),Image.Resampling.LANCZOS).convert('RGB'),
                  (col*205,row*187+27))
                draw.text((col*205+3,row*187+4),f'{name} {a:g}',fill='white')
        board.save(OUT/'three-key-landmark-13-yaw.jpg',quality=95)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P15-193 three-key landmark VDD</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Source root-contact normalized VDD</h2><p>Three independently authored source keyframes remain unchanged. Compare raw arc linear against root-contact shared-u linear and PCHIP; 13 yaw views.</p><img src="three-key-landmark-13-yaw.jpg">')
        E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':
    q=run()
    print(json.dumps({'chosen':q['selectedDiagnosticMethod'],'metrics':q['methods'],'gate':q['gate']},indent=2))

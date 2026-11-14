#!/usr/bin/env python3
"""P15-190: source-crossing anchored, root-local geometric registration.

Align each interpolated crown intersection to a linear interpolation of the
three measured native crossings. Apply a smooth displacement to the first
portion of the source-owned medial curve; leave the tip and source keyviews
unchanged. Compare root crossing, image-space seam and temporal baselines.
"""
import json,math
from pathlib import Path
import numpy as np
import cv2
from PIL import Image,ImageDraw
from p15_187_full_skeleton_vdd import (keyframes,KEYS,ANGLES,source_geometry,geometry_at,
    render_strand,build_sequence,local_metrics)
from p15_189_root_emergence_audit import interpolate_crossing,color_seam
from p15_166_crown_silhouette import crown_edge
from p15_134_underpaint_probe import P,compose
from p15_129_ahoge_ownership import top_components
ROOT=Path(__file__).resolve().parents[1]
OUT=P/'exports/p15-190-root-registration'
E=ROOT/'evidence/p15-190-root-registration-qa.json'
METHODS={'baseline':0,'anchor_24':24,'anchor_40':40,'anchor_64':64}
H=W=443

def align_root(shape,edge,target,extent):
    original=shape['curve']
    adjusted=original.copy()
    current,_,_=interpolate_crossing(original,edge)
    if current is None:raise ValueError('source curve lacks crown crossing')
    shift=np.asarray(target,np.float32)-current
    # Root-only displacement, smooth ease-out. Iteratively recompute crossing
    # because the scalp boundary has nonconstant y(x).
    n=min(extent,len(original))
    weights=np.zeros(len(original),np.float32)
    weights[:n]=(1-np.arange(n,dtype=np.float32)/n)**2
    for _ in range(4):
        crossing,_,_=interpolate_crossing(adjusted,edge)
        if crossing is None:break
        error=np.asarray(target,np.float32)-crossing
        adjusted+=weights[:,None]*error
    out=shape.copy();out['curve']=adjusted
    tangent=np.gradient(adjusted,axis=0)
    tangent/=np.maximum(np.linalg.norm(tangent,axis=1,keepdims=True),1.e-5)
    out['normal']=np.column_stack([-tangent[:,1],tangent[:,0]]).astype(np.float32)
    crossing,_,_=interpolate_crossing(adjusted,edge)
    return out,{'targetCrossing':np.asarray(target).round(4).tolist(),
       'originalCrossing':current.round(4).tolist(),
       'registeredCrossing':crossing.round(4).tolist() if crossing is not None else None,
       'rootDisplacement':(adjusted[0]-original[0]).round(4).tolist(),
       'tipExact':bool(np.array_equal(adjusted[-1],original[-1])),
       'targetResidualPixels':round(float(np.linalg.norm(crossing-target)),4) if crossing is not None else None}

def evaluate(save=True):
    src=keyframes();base,crowns=build_sequence(src)
    geom={a:source_geometry(src[a],a) for a in KEYS}
    key_cross={}
    for a in KEYS:
        i=ANGLES.index(a)
        edge=crown_edge(crowns[i],9)
        p,t,j=interpolate_crossing(geom[a]['curve'],edge)
        if p is None:raise ValueError(f'source key {a} no crossing')
        key_cross[a]=p
    variants={};details={};metrics={}
    reference=json.loads((ROOT/'evidence/p15-189-root-emergence-audit-qa.json').read_text())
    for mode,extent in METHODS.items():
        frames=[];per={}
        for i,angle in enumerate(ANGLES):
            if angle in KEYS:
                frames.append(src[angle].copy());continue
            shape,left,right,t=geometry_at(geom,float(angle),'linear_centerline')
            edge=crown_edge(crowns[i],9)
            target=(1-t)*key_cross[left]+t*key_cross[right]
            if extent:
                shape,registration=align_root(shape,edge,target,extent)
            else:
                p,_,_=interpolate_crossing(shape['curve'],edge)
                registration={'targetCrossing':target.round(4).tolist(),
                  'originalCrossing':p.round(4).tolist(),
                  'registeredCrossing':p.round(4).tolist(),
                  'rootDisplacement':[0.,0.],'tipExact':True,
                  'targetResidualPixels':round(float(np.linalg.norm(p-target)),4)}
            strand,_=render_strand(shape,geom[left],geom[right],t)
            frame=compose(strand,crowns[i])
            frame[125:]=base[i][125:]
            frames.append(frame)
            cross,tangent,_=interpolate_crossing(shape['curve'],edge)
            per[f'{angle:g}']={**registration,
              'crossing':cross.round(4).tolist(),
              'tangent':tangent.round(5).tolist(),
              'colorSeam':color_seam(frame,crowns[i],cross,tangent)['rootContactColorDeltaRGB'],
              'topConnectedComponents':top_components(frame),
              'bodyBelow125Exact':bool(np.array_equal(frame[125:],base[i][125:]))}
        variants[mode]=frames;details[mode]=per
        local,global_e=local_metrics(frames)
        # Compare native keyviews and generated midframes using one consistent
        # crossing extractor so middle-key jumps are not hidden.
        all_cross={k:np.asarray(v['crossing'],np.float32) for k,v in per.items()}
        all_cross.update({f'{a:g}':key_cross[a] for a in KEYS})
        steps=[float(np.linalg.norm(all_cross[f'{b:g}']-all_cross[f'{a:g}'])) for a,b in zip(ANGLES,ANGLES[1:])]
        seam={**{k:v['colorSeam'] for k,v in per.items()},
              **{f'{a:g}':reference['diagnostics'][f'{a:g}']['rootContactColorDeltaRGB'] for a in KEYS}}
        seam_steps=[abs(seam[f'{b:g}']-seam[f'{a:g}']) for a,b in zip(ANGLES,ANGLES[1:])]
        metrics[mode]={
            'maxAdjacentCrossingDisplacementPixels':round(max(steps),4),
            'middleCrossingSteps':[round(steps[5],4),round(steps[6],4)],
            'maxAdjacentColorSeamChange':round(max(seam_steps),4),
            'middleColorSeamChanges':[round(seam_steps[5],4),round(seam_steps[6],4)],
            'maxRootTargetResidualPixels':max(v['targetResidualPixels'] for v in per.values()),
            'maxAdjacentLocalRGBMAE':max(local),'maxAdjacentGlobalRGBMAE':max(global_e),
            'allNativeKeysExact':all(np.array_equal(frames[ANGLES.index(a)],src[a]) for a in KEYS),
            'allBodyBelow125Exact':all(v['bodyBelow125Exact'] for v in per.values()),
            'allConnected':all(v['topConnectedComponents']==1 for v in per.values()),
            'allFreeTipsExact':all(v['tipExact'] for v in per.values())}
    chosen=min(METHODS,key=lambda name:(
        metrics[name]['maxAdjacentCrossingDisplacementPixels'],
        metrics[name]['maxAdjacentLocalRGBMAE']))
    q={'schema':'KOMA_P15_190_ROOT_REGISTRATION_V1','characterId':'p0_character_001',
       'sourceAngles':list(KEYS),'renderAngles':list(ANGLES),
       'sourceKeyCrossings':{f'{a:g}':p.round(4).tolist() for a,p in key_cross.items()},
       'methods':metrics,'details':details,'selectedByCrossingContinuity':chosen,
       'referenceMaxAdjacentCrossingDisplacementPixels':reference['metrics']['maxAdjacentCrossingDisplacementPixels'],
       'referenceLocalRGBMAE':reference['metrics']['referenceLocalRGBMAE'],
       'referenceGlobalRGBMAE':reference['metrics']['referenceGlobalRGBMAE'],
       'sourceKeysModified':False,'productionRendererUpdated':False,'visualAccepted':False,
       'review':'private-assets/exports/p15-190-root-registration/index.html'}
    m=metrics[chosen]
    q['gate']={'allSourceKeysExact':all(v['allNativeKeysExact'] for v in metrics.values()),
      'allBodyBelow125Exact':all(v['allBodyBelow125Exact'] for v in metrics.values()),
      'allFreeTipsExact':all(v['allFreeTipsExact'] for v in metrics.values()),
      'allMidframesConnected':all(v['allConnected'] for v in metrics.values()),
      'crossingBetterThanReference':m['maxAdjacentCrossingDisplacementPixels']<q['referenceMaxAdjacentCrossingDisplacementPixels'],
      'localTemporalBeatsDIS':m['maxAdjacentLocalRGBMAE']<=7.9475,
      'globalTemporalBeatsDIS':m['maxAdjacentGlobalRGBMAE']<=6.6299,
      'colorSeamContinuityAccepted':False,
      'visualAccepted':False,'passes':False}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(205*len(ANGLES),188*len(variants)),(35,42,54));d=ImageDraw.Draw(board)
        for row,(name,frames) in enumerate(variants.items()):
            folder=OUT/name;folder.mkdir(exist_ok=True)
            for col,(a,img) in enumerate(zip(ANGLES,frames)):
                Image.fromarray(img,'RGBA').save(folder/(f'yaw{a:06.2f}'.replace('.','p')+'.png'))
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(img,'RGBA'))
                board.paste(tile.crop((110,0,380,135)).resize((200,155),Image.Resampling.LANCZOS).convert('RGB'),
                            (col*205,row*188+27))
                d.text((col*205+4,row*188+4),f'{name} {a:g}',fill='white')
        board.save(OUT/'13-yaw-root-registration.jpg',quality=95)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P15-190 root registration</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Root crossing registered to three source keyviews</h2><p>Near-root deformation has quadratic falloff. Native keyviews and free tips stay exact.</p><img src="13-yaw-root-registration.jpg">')
        E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':
 q=evaluate()
 print(json.dumps({'selected':q['selectedByCrossingContinuity'],'metrics':q['methods'],'gate':q['gate']},indent=2))

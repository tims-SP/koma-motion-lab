#!/usr/bin/env python3
"""P15-185: 3-keyview shape-preserving geometry interpolation.

PCHIP is implemented for three equally spaced keys following the
Fritsch-Butland / PCHIP derivative rule. Compare coordinate-wise linear
and Hermite-PCHIP interpolation of corresponding 160-point source curves,
with the P15-183 source-valid texture and root-only contact geometry.
Native source keyviews are copied, never re-rendered.
"""
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw
from p15_129_ahoge_ownership import keyframes,KEYS,top_components
from p15_134_underpaint_probe import P,compose
from p15_184_alpha_aware_temporal_sweep import build_sequence,donor_for_mix,local_metrics,ANGLES
import p15_181_curve_correspondence as curves
from p15_182_free_tip_root_tangent import root_extension
ROOT=Path(__file__).resolve().parents[1]
OUT=P/'exports/p15-185-keyview-geometry-correspondence'
E=ROOT/'evidence/p15-185-keyview-geometry-correspondence-qa.json'
METHODS=('linear','pchip')
MID=tuple(a for a in ANGLES if a not in KEYS)

def pchip_three(values,angle):
    """Shape-preserving cubic Hermite for three equal-spacing abscissae.

    Applies the standard PCHIP slopes elementwise to multidimensional
    control point values; never extrapolates outside [90, 135].
    """
    arr=np.asarray(values,np.float64)
    assert arr.shape[0]==3
    h=22.5
    d0=(arr[1]-arr[0])/h;d1=(arr[2]-arr[1])/h
    same=(d0*d1)>0
    middle=np.where(same,2*d0*d1/np.where(same,d0+d1,1),0.)
    edge0=(3*d0-d1)/2
    edge1=(3*d1-d0)/2
    edge0=np.where(np.sign(edge0)!=np.sign(d0),0.,edge0)
    edge1=np.where(np.sign(edge1)!=np.sign(d1),0.,edge1)
    edge0=np.where((np.sign(d0)!=np.sign(d1))&(np.abs(edge0)>3*np.abs(d0)),3*d0,edge0)
    edge1=np.where((np.sign(d0)!=np.sign(d1))&(np.abs(edge1)>3*np.abs(d1)),3*d1,edge1)
    j=0 if angle<=112.5 else 1
    t=float((angle-(90 if j==0 else 112.5))/h)
    y0,y1=arr[j],arr[j+1]
    m0,m1=(edge0,middle) if j==0 else (middle,edge1)
    return (2*t**3-3*t**2+1)*y0+(t**3-2*t**2+t)*h*m0+(-2*t**3+3*t**2)*y1+(t**3-t**2)*h*m1

def target_shape(shape_keys,angle,method):
    a,b=(90.,112.5) if angle<112.5 else (112.5,135.)
    t=(angle-a)/(b-a)
    if method=='linear':
        target=curves.interp_curve(shape_keys[a],shape_keys[b],t)
    else:
        points=pchip_three(np.stack([shape_keys[k]['curve'] for k in KEYS]),angle).astype(np.float32)
        width=float(pchip_three(np.array([shape_keys[k]['width'] for k in KEYS]),angle))
        tangent=np.gradient(points,axis=0)
        tangent/=np.maximum(np.linalg.norm(tangent,axis=1,keepdims=True),1e-5)
        normal=np.column_stack([-tangent[:,1],tangent[:,0]])
        if np.median(normal[:,1])<0:normal=-normal
        target={'curve':points,'width':float(np.clip(width,2,16)),'normal':normal}
    return target,a,b,t

def shape_metrics(shape_keys,method):
    # Include both sides of the middle key to measure jumps of the underlying
    # continuous deformation before pixel rasterization.
    check=np.arange(90.,135.0001,0.75)
    features=[]
    for a in check:
        if a in KEYS: c=shape_keys[a]['curve'];w=shape_keys[a]['width']
        else:
            t,_,_,_=target_shape(shape_keys,float(a),method);c=t['curve'];w=t['width']
        features.append(np.concatenate([c.reshape(-1),[float(w)]],axis=0))
    feature=np.asarray(features)
    delta=np.linalg.norm(feature[1:,:-1]-feature[:-1,:-1],axis=1)/curves.N**.5
    i=np.argmin(abs(check-112.5))
    left=feature[i]-feature[i-1];right=feature[i+1]-feature[i]
    derivative_jump=float(np.linalg.norm(right-left)/curves.N**.5)
    return {'maxAdjacentCurveRMSStep':round(float(delta.max()),5),
            'meanAdjacentCurveRMSStep':round(float(delta.mean()),5),
            'middleKeyDerivativeJump':round(derivative_jump,5),
            'widthMin':round(float(feature[:,-1].min()),4),
            'widthMax':round(float(feature[:,-1].max()),4)}

def evaluate(save=True):
    sources=keyframes();source_frames,crown_frames=build_sequence(sources)
    shapes={a:curves.source_curve(sources[a]) for a in KEYS}
    for a in KEYS:shapes[a]['texture']=donor_for_mix(sources[a],shapes[a],.8)
    results={};details={};metrics={}
    for method in METHODS:
        frames=[];diag={}
        for i,a in enumerate(ANGLES):
            if a in KEYS:frames.append(sources[a].copy());continue
            target,left,right,t=target_shape(shapes,a,method)
            strand_target,root_info=root_extension(target,crown_frames[i],8)
            # Existing 2-key source color blending, only geometry changes.
            strand,info=curves.render_curve(strand_target,shapes[left],shapes[right],t)
            out=compose(crown_frames[i],strand);out[125:]=source_frames[i][125:]
            frames.append(out)
            mask=(strand[:120,:,3]>64)&(strand[:120,:,3]<245)
            gray=cv2.cvtColor(strand[:120,:,:3],cv2.COLOR_RGB2GRAY)
            diag[f'{a:g}']={**root_info,**info,
                'darkEdgePixels':int((mask&(gray<85)).sum()),
                'topConnectedComponents':top_components(out),
                'deepBodyExact':bool(np.array_equal(out[125:],source_frames[i][125:])),
                'sourceInterval':[left,right]}
        local,global_errors=local_metrics(frames)
        metrics[method]={**shape_metrics(shapes,method),
            'maxAdjacentLocalRGBMAE':max(local),
            'maxAdjacentGlobalRGBMAE':max(global_errors),
            'totalDarkEdgePixels':sum(x['darkEdgePixels'] for x in diag.values()),
            'allNativeKeysExact':all(np.array_equal(frames[ANGLES.index(a)],sources[a]) for a in KEYS),
            'allDeepBodyExact':all(d['deepBodyExact'] for d in diag.values()),
            'singleConnectedStrand':all(d['topConnectedComponents']==1 for d in diag.values()),
            'freeTipPreserved':all(d['freeTipPreserved'] for d in diag.values())}
        details[method]=diag;results[method]=frames
    baseline_local,baseline_global=local_metrics(source_frames)
    p=metrics['pchip'];l=metrics['linear']
    qa={'schema':'KOMA_P15_185_KEYVIEW_GEOMETRY_CORRESPONDENCE_V1',
        'characterId':'p0_character_001','angles':list(ANGLES),
        'sourceAngles':list(KEYS),'method':'Fritsch-Butland PCHIP 3-keyview per-coordinate Hermite with source curve control points',
        'reference':'https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.PchipInterpolator.html',
        'metrics':metrics,'intermediateDetails':details,
        'baselineMaxAdjacentLocalRGBMAE':max(baseline_local),
        'baselineMaxAdjacentGlobalRGBMAE':max(baseline_global),
        'preferredGeometry':'pchip' if p['middleKeyDerivativeJump']<=l['middleKeyDerivativeJump'] else 'linear',
        'productionRendererUpdated':False,'visualAccepted':False,
        'review':'private-assets/exports/p15-185-keyview-geometry-correspondence/index.html'}
    qa['gate']={'sourceKeyviewsExact':all(v['allNativeKeysExact'] for v in metrics.values()),
        'bodyExact':all(v['allDeepBodyExact'] for v in metrics.values()),
        'strandConnected':all(v['singleConnectedStrand'] for v in metrics.values()),
        'tipPreserved':all(v['freeTipPreserved'] for v in metrics.values()),
        'derivativeJumpReduced':p['middleKeyDerivativeJump']<l['middleKeyDerivativeJump'],
        'pchipLocalTemporalBeatsLinear':p['maxAdjacentLocalRGBMAE']<=l['maxAdjacentLocalRGBMAE'],
        'pchipLocalTemporalBeatsDIS':p['maxAdjacentLocalRGBMAE']<=qa['baselineMaxAdjacentLocalRGBMAE'],
        'visualAccepted':False,'passes':False}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(205*len(ANGLES),190*3),(35,42,54));pen=ImageDraw.Draw(board)
        for row,(method,frames) in enumerate([('whole_frame_DIS',source_frames),*results.items()]):
            folder=OUT/method;folder.mkdir(exist_ok=True)
            for col,(a,img) in enumerate(zip(ANGLES,frames)):
                Image.fromarray(img,'RGBA').save(folder/(f'yaw{a:06.2f}'.replace('.','p')+'.png'))
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(img,'RGBA'))
                board.paste(tile.crop((110,0,380,135)).resize((200,158),Image.Resampling.LANCZOS).convert('RGB'),
                    (col*205,row*190+26))
                pen.text((col*205+4,row*190+4),f'{method} {a:g}',fill='white')
        board.save(OUT/'geometry-13-yaw.jpg',quality=95)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P15-185 PCHIP geometry correspondence</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Shape-preserving keyview geometry interpolation</h2><p>Linear and PCHIP interpolate 160 corresponding source curve points and strand width across three native yaw keys. All native keyframes remain exact; visual and local temporal gates are evaluated separately.</p><img src="geometry-13-yaw.jpg">')
        E.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    return qa
if __name__=='__main__':
    q=evaluate();print(json.dumps({'gate':q['gate'],'metrics':q['metrics']},indent=2))

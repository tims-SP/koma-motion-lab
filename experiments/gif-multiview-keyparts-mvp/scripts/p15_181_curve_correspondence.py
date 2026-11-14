#!/usr/bin/env python3
"""P15-181: normalized centerline correspondence and single-strand rendering.

The source loop is clipped at the crown ownership boundary (y=54); its lower
contour is therefore a crop edge, not the opposite side of a hair ribbon.
Use the upper contour as a centerline, estimate source stroke width from
visible alpha area / centerline length, and interpolate one curve + width.
Texture is sampled from both source views in the same curve/normal coordinates.
"""
import json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_129_ahoge_ownership import keyframes,KEYS,ANGLES,top_components
from p15_128_keyart_registration import frame_interp,jumps
from p15_134_underpaint_probe import P,compose
from p15_153_source_topology import extract
from p15_168_root_occlusion import crown_edge
from p15_128_keyart_registration import frame_interp as interp_rgba

ROOT=Path(__file__).resolve().parents[1]
OUT=P/'exports/p15-181-curve-correspondence'
E=ROOT/'evidence/p15-181-curve-correspondence-qa.json'
N=160;H=W=443
MID=tuple(a for a in ANGLES if a not in KEYS)

def resample(points,n=N):
    p=np.asarray(points,np.float32)
    arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
    target=np.linspace(0,arc[-1],n)
    return np.column_stack([np.interp(target,arc,p[:,0]),np.interp(target,arc,p[:,1])]).astype(np.float32)

def source_curve(frame):
    layer=extract(frame)[0]['loop_visible']
    mask=layer[...,3]>24
    contours,_=cv2.findContours(np.uint8(mask),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    contour=max(contours,key=cv2.contourArea).reshape(-1,2)
    li=int(np.argmin(contour[:,0]));ri=int(np.argmax(contour[:,0]))
    def path(i,j,step):
        ids=[];k=i
        while True:
            ids.append(k)
            if k==j:break
            k=(k+step)%len(contour)
            if len(ids)>len(contour)+1:raise RuntimeError('contour path failure')
        return contour[ids].astype(np.float32)
    a=path(li,ri,1);b=path(li,ri,-1)
    # The crop boundary at y=54 is not the second side of the strand.
    center=a if a[:,1].mean()<b[:,1].mean() else b
    curve=resample(center)
    # Keep the source arc in left-to-right direction.
    if curve[0,0]>curve[-1,0]:curve=curve[::-1]
    length=float(np.linalg.norm(np.diff(curve,axis=0),axis=1).sum())
    width=float(mask.sum()/max(length,1))
    width=float(np.clip(width,3.0,12.0))
    tangent=np.gradient(curve,axis=0)
    tangent/=np.maximum(np.linalg.norm(tangent,axis=1,keepdims=True),1e-5)
    normal=np.column_stack([-tangent[:,1],tangent[:,0]])
    # Choose normal direction toward the clipped crown (downward) consistently.
    if np.median(normal[:,1])<0:normal=-normal
    return {'curve':curve,'normal':normal,'width':width,'length':length,
            'area':int(mask.sum()),'texture':frame[...,:3].copy(),
            'sourceMask':mask}

def interp_curve(a,b,t):
    curve=(1-t)*a['curve']+t*b['curve']
    tangent=np.gradient(curve,axis=0)
    tangent/=np.maximum(np.linalg.norm(tangent,axis=1,keepdims=True),1e-5)
    normal=np.column_stack([-tangent[:,1],tangent[:,0]])
    if np.median(normal[:,1])<0:normal=-normal
    width=(1-t)*a['width']+t*b['width']
    return {'curve':curve,'normal':normal,'width':float(width)}

def extend_to_crown(target,crown):
    curve=target['curve'].copy()
    edge=crown_edge(crown,9)
    tangent=np.gradient(curve,axis=0)
    tangent/=np.maximum(np.linalg.norm(tangent,axis=1,keepdims=True),1e-5)
    # Continue the actual strand tangent until it meets the scalp silhouette.
    for at_start in (True,False):
        idx=0 if at_start else -1
        direction=-tangent[idx] if at_start else tangent[idx]
        endpoint=curve[idx].copy()
        hit=endpoint.copy()
        for distance in np.linspace(0,90,181):
            candidate=endpoint+direction*distance
            x=int(np.clip(round(float(candidate[0])),0,W-1))
            if candidate[1]>=edge[x]-1:
                hit=candidate;break
        displacement=hit-endpoint
        count=18
        weights=np.linspace(1,0,count)**2
        if at_start:curve[:count]+=weights[:,None]*displacement
        else:curve[-count:]+=weights[::-1,None]*displacement
    tangent=np.gradient(curve,axis=0)
    tangent/=np.maximum(np.linalg.norm(tangent,axis=1,keepdims=True),1e-5)
    normal=np.column_stack([-tangent[:,1],tangent[:,0]])
    if np.median(normal[:,1])<0:normal=-normal
    return {'curve':curve,'normal':normal,'width':target['width']}

def render_curve(target,a,b,t):
    # Draw a single continuous centerline at 4x resolution for stable AA.
    scale=4;mask_hi=np.zeros((H*scale,W*scale),np.uint8)
    c=np.round(target['curve']*scale).astype(np.int32)
    for i in range(len(c)-1):
        w=(1-t)*a['width']+t*b['width']
        cv2.line(mask_hi,tuple(c[i]),tuple(c[i+1]),255,
                 max(1,int(round(w*scale))),cv2.LINE_AA)
    alpha=cv2.resize(mask_hi,(W,H),interpolation=cv2.INTER_AREA)
    yy,xx=np.indices((H,W),dtype=np.float32)
    points=np.column_stack([xx[alpha>8],yy[alpha>8]])
    delta=points[:,None,:]-target['curve'][None,:,:]
    ids=np.argmin(np.sum(delta*delta,axis=2),axis=1).astype(np.int32)
    offsets=points-target['curve'][ids]
    signed=np.sum(offsets*target['normal'][ids],axis=1)
    target_half=max(target['width']/2,.5)
    def sample(src,curve,normal,source_width):
        factor=np.clip(source_width/(2*target_half),.55,1.8)
        xy=curve[ids]+normal[ids]*(source_width*.30+signed*np.clip(source_width/max(target['width'],1),.55,1.8))[:,None]
        return cv2.remap(src,xy[:,0].astype(np.float32).reshape(1,-1),
                         xy[:,1].astype(np.float32).reshape(1,-1),cv2.INTER_CUBIC,
                         borderMode=cv2.BORDER_REPLICATE).reshape(-1,3)
    ca=sample(a['texture'],a['curve'],a['normal'],a['width'])
    cb=sample(b['texture'],b['curve'],b['normal'],b['width'])
    rgb=np.zeros((H,W,3),np.uint8)
    rgb[alpha>8]=np.uint8(np.clip(np.rint(ca*(1-t)+cb*t),0,255))
    out=np.dstack([rgb,alpha]);out[alpha==0]=0
    return out,{'curveLength':round(float(np.linalg.norm(np.diff(target['curve'],axis=0),axis=1).sum()),3),
      'targetStrokeWidth':round(float(target['width']),3),'loopPixels':int((alpha>64).sum()),
      'curveStart':target['curve'][0].round(2).tolist(),
      'curveEnd':target['curve'][-1].round(2).tolist()}

def render(save=True):
    sources=keyframes();curves={a:source_curve(sources[a]) for a in KEYS}
    baseline=frame_interp(sources[90.],sources[112.5],sources[135.])
    tags={90.:'yaw090',112.5:'yaw112p5',135.:'yaw135'}
    crown_layers={a:np.asarray(Image.open(P/f'exports/p15-178-ai-rootless-crown/local/{tags[a]}/crown-motion-underpaint.png').convert('RGBA')).copy() for a in KEYS}
    crown_frames=frame_interp(crown_layers[90.],crown_layers[112.5],crown_layers[135.])
    outputs=[];details={}
    for i,angle in enumerate(ANGLES):
        if angle in KEYS:
            outputs.append(sources[angle].copy());continue
        left,right=(90.,112.5) if angle<112.5 else (112.5,135.)
        t=(angle-left)/(right-left)
        target=interp_curve(curves[left],curves[right],t)
        core_loop,core_info=render_curve(target,curves[left],curves[right],t)
        base=baseline[i].copy();bg=crown_frames[i].copy()
        target=extend_to_crown(target,bg)
        loop,info=render_curve(target,curves[left],curves[right],t)
        info['coreLoopPixels']=core_info['loopPixels']
        info['rootExtensionPixels']=max(0,info['loopPixels']-core_info['loopPixels'])
        frame=compose(bg,loop);frame[125:]=base[125:]
        outputs.append(frame)
        info.update({'leftKey':left,'rightKey':right,'t':round(float(t),5),
          'belowY125Exact':bool(np.array_equal(frame[125:],base[125:])),
          'topConnectedComponents':top_components(frame)})
        details[f'{angle:g}']=info
    area={a:curves[a]['area'] for a in KEYS};ratios={}
    for angle in MID:
        left,right=(90.,112.5) if angle<112.5 else (112.5,135.)
        t=(angle-left)/(right-left)
        expected=(1-t)*area[left]+t*area[right]
        ratios[f'{angle:g}']=round(details[f'{angle:g}']['coreLoopPixels']/expected,4)
    metrics={'maxAdjacentRGBMAE':max(jumps(outputs)),
      'baselineMaxAdjacentRGBMAE':max(jumps(baseline)),
      'adjacentRGBMAE':jumps(outputs),'baselineAdjacentRGBMAE':jumps(baseline),
      'topConnectedComponents':[top_components(f) for f in outputs],
      'nativeKeyframesPixelExact':all(np.array_equal(outputs[ANGLES.index(a)],sources[a]) for a in KEYS),
      'belowY125Exact':all(details[f'{a:g}']['belowY125Exact'] for a in MID),
      'midframesSingleComponent':all(details[f'{a:g}']['topConnectedComponents']==1 for a in MID)}
    q={'schema':'KOMA_P15_181_CURVE_CORRESPONDENCE_V2','characterId':'p0_character_001',
      'sourceAngles':list(KEYS),'renderAngles':list(ANGLES),'intermediateAngles':list(MID),
      'curveSamples':N,'sourceCurveGeometry':{f'{a:g}':{'start':curves[a]['curve'][0].round(3).tolist(),
       'end':curves[a]['curve'][-1].round(3).tolist(),'length':curves[a]['length'],
       'visibleArea':curves[a]['area'],'estimatedStrokeWidth':curves[a]['width']} for a in KEYS},
      'intermediateDiagnostics':details,'loopAreaRatios':ratios,'metrics':metrics,
      'areaMetricDefinition':'Core loop area excludes added root-extension pixels; root extension is reported separately because source keyview extraction clips the loop at y=54.',
      'productionRendererUpdated':False,'visualAccepted':False,
      'review':'private-assets/exports/p15-181-curve-correspondence/index.html'}
    q['gate']={'nativeKeyframesPixelExact':metrics['nativeKeyframesPixelExact'],
      'deepBodyExact':metrics['belowY125Exact'],
      'allMidframesSingleComponent':metrics['midframesSingleComponent'],
      'loopAreaWithin25Percent':all(.75<=v<=1.25 for v in ratios.values()),
      'temporalNoWorseThanBaseline':metrics['maxAdjacentRGBMAE']<=metrics['baselineMaxAdjacentRGBMAE'],
      'temporalRegressionRecorded':metrics['maxAdjacentRGBMAE']>metrics['baselineMaxAdjacentRGBMAE'],
      'passes':False}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        for name,frames in (('whole_frame_DIS',baseline),('curve_correspondence',outputs)):
            folder=OUT/name;folder.mkdir(exist_ok=True)
            for a,im in zip(ANGLES,frames):Image.fromarray(im,'RGBA').save(folder/(f'yaw{a:06.2f}'.replace('.','p')+'.png'))
        board=Image.new('RGB',(300*len(ANGLES),330*2),(35,42,54));d=ImageDraw.Draw(board)
        zoom=Image.new('RGB',(300*len(ANGLES),210*2),(35,42,54));dz=ImageDraw.Draw(zoom)
        for row,(name,frames) in enumerate((('whole_frame_DIS',baseline),('curve_correspondence',outputs))):
            for col,(a,im) in enumerate(zip(ANGLES,frames)):
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(im,'RGBA'))
                board.paste(tile.convert('RGB').resize((292,292),Image.Resampling.LANCZOS),(col*300,row*330+28))
                d.text((col*300+5,row*330+5),f'{name} {a:g}',fill='white')
                zoom.paste(tile.crop((120,0,370,135)).resize((292,158),Image.Resampling.NEAREST).convert('RGB'),(col*300,row*210+26))
                dz.text((col*300+5,row*210+5),f'{name} {a:g}',fill='white')
        board.save(OUT/'full-yaw-comparison.jpg',quality=94);zoom.save(OUT/'loop-closeups.jpg',quality=95)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P15-181 curve correspondence</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Normalized centerline correspondence</h2><p>One source-derived centerline and estimated stroke width are interpolated across views. Both source textures are sampled in the same normalized curve coordinates; one strand is rendered at each intermediate yaw.</p><img src="loop-closeups.jpg"><h2>Full view</h2><img src="full-yaw-comparison.jpg">')
        E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':
 q=render();print(json.dumps({'gate':q['gate'],'metrics':q['metrics'],'areaRatios':q['loopAreaRatios']},indent=2))

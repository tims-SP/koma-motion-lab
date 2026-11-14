#!/usr/bin/env python3
"""P15-182: root-connected, free-tip ahoge curve VDD.

P15-167 source topology establishes one scalp contact on the left and one
visible free tip at right. Retain the latter free, extend only the left root,
and compare original texture mapping with source-aware texture donors.
Native keyframes and all material below y125 remain unchanged.
"""
import json,hashlib
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
import p15_181_curve_correspondence as parent
from p15_129_ahoge_ownership import keyframes,KEYS,ANGLES,top_components
from p15_128_keyart_registration import frame_interp,jumps
from p15_134_underpaint_probe import P,compose,background_rgb
from p15_168_root_occlusion import crown_edge
from p15_167_endpoint_pair import ROOT_AND_TIP

ROOT=Path(__file__).resolve().parents[1]
OUT=P/'exports/p15-182-root-free-tip'
E=ROOT/'evidence/p15-182-root-free-tip-qa.json'
MID=tuple(a for a in ANGLES if a not in KEYS)

def root_extension(target,crown,reach):
    """Only root (left endpoint) is attached to scalp. Right endpoint is free."""
    curve=target['curve'].copy()
    edge=crown_edge(crown,9)
    tangent=np.gradient(curve,axis=0)
    tangent/=np.maximum(np.linalg.norm(tangent,axis=1,keepdims=True),1e-5)
    origin=curve[0].copy()
    direction=-tangent[0]
    goal=origin.copy()
    for distance in np.linspace(0,90,181):
        candidate=origin+direction*distance
        x=int(np.clip(round(float(candidate[0])),0,parent.W-1))
        if candidate[1]>=edge[x]-1:
            goal=candidate;break
    count=reach
    weights=np.linspace(1,0,count)**2
    curve[:count]+=weights[:,None]*(goal-origin)
    tangent=np.gradient(curve,axis=0)
    tangent/=np.maximum(np.linalg.norm(tangent,axis=1,keepdims=True),1e-5)
    normal=np.column_stack([-tangent[:,1],tangent[:,0]])
    if np.median(normal[:,1])<0:normal=-normal
    result={'curve':curve,'normal':normal,'width':target['width']}
    return result,{'rootExtensionDistance':round(float(np.linalg.norm(goal-origin)),3),
                   'freeTipPreserved':bool(np.array_equal(curve[-1],target['curve'][-1])),
                   'freeTip':curve[-1].round(3).tolist(),
                   'crownEdgeAtRoot':round(float(edge[int(np.clip(round(float(goal[0])),0,parent.W-1))]),3)}

def evaluate(save=True):
    src=keyframes();curves={a:parent.source_curve(src[a]) for a in KEYS}
    baseline=frame_interp(src[90.],src[112.5],src[135.])
    tags={90.:'yaw090',112.5:'yaw112p5',135.:'yaw135'}
    crowns={}
    for a in KEYS:
        with Image.open(P/f'exports/p15-178-ai-rootless-crown/local/{tags[a]}/crown-motion-underpaint.png') as im:
            crowns[a]=np.asarray(im.convert('RGBA')).copy()
    crown_frames=frame_interp(crowns[90.],crowns[112.5],crowns[135.])
    variants={}
    diagnostics={}
    for reach in (8,14,20,28):
        name=f'root_tangent_{reach:02d}'
        frames=[];details={}
        for i,angle in enumerate(ANGLES):
            if angle in KEYS:
                frames.append(src[angle].copy());continue
            left,right=(90.,112.5) if angle<112.5 else (112.5,135.)
            t=(angle-left)/(right-left)
            base=baseline[i].copy()
            target=parent.interp_curve(curves[left],curves[right],t)
            core,core_info=parent.render_curve(target,curves[left],curves[right],t)
            target,root_info=root_extension(target,crown_frames[i],reach)
            strand,info=parent.render_curve(target,curves[left],curves[right],t)
            # Underpaint is separate from the single source-derived strand.
            out=compose(crown_frames[i],strand)
            out[125:]=base[125:]
            frames.append(out)
            details[f'{angle:g}']={**info,**root_info,
                'coreArea':core_info['loopPixels'],
                'rootAddedArea':int(info['loopPixels']-core_info['loopPixels']),
                'sourceRoot':ROOT_AND_TIP[left]['root'],
                'sourceFreeTip':ROOT_AND_TIP[left]['tip'],
                'topComponents':top_components(out),
                'belowY125Exact':bool(np.array_equal(out[125:],base[125:]))}
        variants[name]=frames
        diagnostics[name]=details
    metrics={}
    for name,frames in variants.items():
        mae=jumps(frames)
        details=diagnostics[name]
        ratios={}
        for a in MID:
            left,right=(90.,112.5) if a<112.5 else (112.5,135.)
            t=(a-left)/(right-left)
            expected=(1-t)*curves[left]['area']+t*curves[right]['area']
            ratios[f'{a:g}']=round(details[f'{a:g}']['coreArea']/expected,4)
        metrics[name]={
            'maxAdjacentRGBMAE':max(mae),
            'adjacentRGBMAE':mae,
            'loopAreaRatios':ratios,
            'midframesSingleComponent':all(details[f'{a:g}']['topComponents']==1 for a in MID),
            'allFreeTipsPreserved':all(details[f'{a:g}']['freeTipPreserved'] for a in MID),
            'allDeepBodyExact':all(details[f'{a:g}']['belowY125Exact'] for a in MID),
            'allKeyframesExact':all(np.array_equal(frames[ANGLES.index(a)],src[a]) for a in KEYS),
            'areaWithin25Percent':all(.75<=v<=1.25 for v in ratios.values())}
    baseline_max=max(jumps(baseline))
    selected=min(metrics,key=lambda k:metrics[k]['maxAdjacentRGBMAE'])
    q={'schema':'KOMA_P15_182_ROOT_FREE_TIP_V1','characterId':'p0_character_001',
      'sourceAngles':list(KEYS),'renderAngles':list(ANGLES),
      'sourceTopology':'Left/root endpoint joins crown; right endpoint is visible free tip',
      'methods':metrics,'details':diagnostics,'bestTemporalCandidate':selected,
      'reference':{'maxAdjacentRGBMAE':baseline_max,'adjacentRGBMAE':jumps(baseline)},
      'productionRendererUpdated':False,'visualAccepted':False,
      'review':'private-assets/exports/p15-182-root-free-tip/index.html'}
    q['gate']={
      'allNativeKeysExact':all(v['allKeyframesExact'] for v in metrics.values()),
      'allDeepBodyExact':all(v['allDeepBodyExact'] for v in metrics.values()),
      'freeTipIdentityPreserved':all(v['allFreeTipsPreserved'] for v in metrics.values()),
      'singleLoop':metrics[selected]['midframesSingleComponent'],
      'areaWithin25Percent':metrics[selected]['areaWithin25Percent'],
      'betterThanP15181':metrics[selected]['maxAdjacentRGBMAE']<12.3552,
      'beatsWholeFrameReference':metrics[selected]['maxAdjacentRGBMAE']<=baseline_max,
      'rootContactVisuallyAccepted':False,
      'passes':False}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(300*len(ANGLES),215*(len(variants)+1)),(35,42,54));d=ImageDraw.Draw(board)
        for row,(name,frames) in enumerate([('baseline',baseline),*variants.items()]):
            folder=OUT/name;folder.mkdir(exist_ok=True)
            for col,(a,im) in enumerate(zip(ANGLES,frames)):
                Image.fromarray(im,'RGBA').save(folder/(f"yaw{a:06.2f}".replace('.','p')+'.png'))
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(im,'RGBA'))
                crop=tile.crop((120,0,370,135)).resize((292,170),Image.Resampling.NEAREST)
                board.paste(crop.convert('RGB'),(col*300,row*215+30))
                d.text((col*300+6,row*215+7),f'{name} {a:g}',fill='white')
        board.save(OUT/'root-curve-comparison.jpg',quality=95)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P15-182 root free-tip curve</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Single-root, free-tip curve correspondence</h2><p>Only the root is connected to the scalp; the right tip remains free. Four source-curve root tangent profiles are compared with the whole-frame DIS baseline.</p><img src="root-curve-comparison.jpg">')
        E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':
    q=evaluate()
    print(json.dumps({'selected':q['bestTemporalCandidate'],'gate':q['gate'],'methods':q['methods']},indent=2))

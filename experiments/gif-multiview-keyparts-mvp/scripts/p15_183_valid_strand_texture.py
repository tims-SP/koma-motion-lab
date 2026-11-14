#!/usr/bin/env python3
"""P15-183 source-valid strand texture sampling for the root/free-tip curve.

Only the source-owned ahoge alpha-positive domain provides color donors.
Construct compact inpainted or alpha-normalized RGB texture fields before
sampling the existing P15-182 curve coordinates. Geometry and source keys
are immutable. Compare per-frame color stability and alpha-edge dark pixels.
"""
import json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
import p15_181_curve_correspondence as curve
from p15_182_free_tip_root_tangent import root_extension
from p15_129_ahoge_ownership import keyframes,KEYS,ANGLES,top_components
from p15_128_keyart_registration import frame_interp,jumps
from p15_134_underpaint_probe import P,compose

ROOT=Path(__file__).resolve().parents[1]
OUT=P/'exports/p15-183-valid-strand-texture'
E=ROOT/'evidence/p15-183-valid-strand-texture-qa.json'
MID=tuple(a for a in ANGLES if a not in KEYS)
MODES=('native','nearest_valid','alpha_normalized','valid_mix_50','valid_mix_75')
H=W=443

def donor_texture(source,curve_data,mode):
    if mode=='native': return source[...,:3].copy()
    if mode.startswith('valid_mix_'):
        t={'valid_mix_50':.5,'valid_mix_75':.75}[mode]
        original=source[...,:3].astype(np.float32)
        valid=donor_texture(source,curve_data,'nearest_valid').astype(np.float32)
        return np.uint8(np.clip(np.rint((1-t)*original+t*valid),0,255))
    mask=curve_data['sourceMask']
    ys,xs=np.where(mask)
    pad=12;x0=max(0,int(xs.min())-pad);x1=min(W,int(xs.max())+pad+1)
    y0=max(0,int(ys.min())-pad);y1=min(H,int(ys.max())+pad+1)
    rgb=source[y0:y1,x0:x1,:3].copy()
    alpha=source[y0:y1,x0:x1,3].astype(np.float32)/255.
    valid=alpha>=.32
    if mode=='nearest_valid':
        # The black/transparent source RGB outside the strand is not color.
        # Fill those pixels from the strand's real painting before remap.
        repaired=cv2.inpaint(cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR),
                             np.uint8(~valid)*255,5,cv2.INPAINT_TELEA)
        fixed=cv2.cvtColor(repaired,cv2.COLOR_BGR2RGB)
        fixed[valid]=rgb[valid]
    elif mode=='alpha_normalized':
        # Locally alpha-normalize the source RGB, keeping interior pixels exact.
        weights=np.where(valid,alpha,0).astype(np.float32)
        numerator=cv2.GaussianBlur(rgb.astype(np.float32)*weights[...,None],(0,0),2.3)
        denominator=cv2.GaussianBlur(weights,(0,0),2.3)
        normalized=np.uint8(np.clip(np.rint(numerator/np.maximum(denominator[...,None],.0001)),0,255))
        fixed=normalized
        fixed[valid]=rgb[valid]
    else:raise ValueError(mode)
    output=source[...,:3].copy()
    output[y0:y1,x0:x1]=fixed
    return output

def edge_metrics(frame,crown):
    # Evaluate strand color independent of the underpaint background.
    top=frame[:120,:,:3]
    alpha=frame[:120,:,3]
    region=(alpha>64)&(alpha<245)
    if region.sum()==0:return {'edgePixelCount':0,'darkEdgePixels':0,'darkEdgeRatio':0.}
    gray=cv2.cvtColor(top,cv2.COLOR_RGB2GRAY)
    dark=region&(gray<85)
    return {'edgePixelCount':int(region.sum()),'darkEdgePixels':int(dark.sum()),
            'darkEdgeRatio':round(float(dark.sum()/region.sum()),5)}

def evaluate(save=True):
    sources=keyframes();base_curves={a:curve.source_curve(sources[a]) for a in KEYS}
    baseline=frame_interp(sources[90.],sources[112.5],sources[135.])
    tags={90.:'yaw090',112.5:'yaw112p5',135.:'yaw135'}
    crowns={}
    for a in KEYS:
        with Image.open(P/f'exports/p15-178-ai-rootless-crown/local/{tags[a]}/crown-motion-underpaint.png') as im:
            crowns[a]=np.asarray(im.convert('RGBA')).copy()
    interpolated_crowns=frame_interp(crowns[90.],crowns[112.5],crowns[135.])
    sequences={};details={}
    for mode in MODES:
        curves={}
        for a in KEYS:
            curves[a]=base_curves[a].copy()
            curves[a]['texture']=donor_texture(sources[a],base_curves[a],mode)
        frames=[];reports={}
        for i,a in enumerate(ANGLES):
            if a in KEYS:
                frames.append(sources[a].copy());continue
            left,right=(90.,112.5) if a<112.5 else (112.5,135.)
            t=(a-left)/(right-left)
            interpolated=curve.interp_curve(curves[left],curves[right],t)
            core,core_diag=curve.render_curve(interpolated,curves[left],curves[right],t)
            target,root_diag=root_extension(interpolated,interpolated_crowns[i],8)
            strand,strand_diag=curve.render_curve(target,curves[left],curves[right],t)
            frame=compose(interpolated_crowns[i],strand)
            frame[125:]=baseline[i][125:]
            frames.append(frame)
            reports[f'{a:g}']={**root_diag,**strand_diag,**edge_metrics(strand,interpolated_crowns[i]),
                'coreArea':core_diag['loopPixels'],
                'belowY125Exact':bool(np.array_equal(frame[125:],baseline[i][125:])),
                'topConnectedComponents':top_components(frame)}
        sequences[mode]=frames;details[mode]=reports
    metrics={}
    for mode,frames in sequences.items():
        series=jumps(frames)
        metrics[mode]={
            'maxAdjacentRGBMAE':max(series),
            'adjacentRGBMAE':series,
            'meanDarkEdgeRatio':round(float(np.mean([d['darkEdgeRatio'] for d in details[mode].values()])),5),
            'totalDarkEdgePixels':sum(d['darkEdgePixels'] for d in details[mode].values()),
            'allSourceKeysExact':all(np.array_equal(frames[ANGLES.index(a)],sources[a]) for a in KEYS),
            'allDeepBodyExact':all(d['belowY125Exact'] for d in details[mode].values()),
            'singleConnectedStrand':all(d['topConnectedComponents']==1 for d in details[mode].values()),
            'freeTipPreserved':all(d['freeTipPreserved'] for d in details[mode].values())}
    winner=min((m for m in MODES if metrics[m]['totalDarkEdgePixels']<=25),
               key=lambda m:metrics[m]['maxAdjacentRGBMAE'])
    q={'schema':'KOMA_P15_183_VALID_STRAND_TEXTURE_V1','characterId':'p0_character_001',
       'renderAngles':list(ANGLES),'sourceAngles':list(KEYS),
       'modes':metrics,'intermediateDetails':details,
       'selectedDiagnosticMethod':winner,
       'priorMaxAdjacentRGBMAE':12.2739,'wholeFrameBaselineMaxAdjacentRGBMAE':12.0984,
       'selectionRule':'Among candidates with at most 25 dark antialias edge pixels, minimize adjacent RGB MAE',
       'productionRendererUpdated':False,'visualAccepted':False,
       'review':'private-assets/exports/p15-183-valid-strand-texture/index.html'}
    q['gate']={'allSourceKeysExact':all(m['allSourceKeysExact'] for m in metrics.values()),
       'allDeepBodyExact':all(m['allDeepBodyExact'] for m in metrics.values()),
       'freeTipPreserved':all(m['freeTipPreserved'] for m in metrics.values()),
       'singleConnectedStrand':all(m['singleConnectedStrand'] for m in metrics.values()),
       'textureDarkEdgeReduced':metrics[winner]['totalDarkEdgePixels']<metrics['native']['totalDarkEdgePixels'],
       'temporalBetterThanP15182':metrics[winner]['maxAdjacentRGBMAE']<q['priorMaxAdjacentRGBMAE'],
       'temporalBeatsWholeFrameBaseline':metrics[winner]['maxAdjacentRGBMAE']<=q['wholeFrameBaselineMaxAdjacentRGBMAE'],
       'visualAccepted':False,'passes':False}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(300*len(ANGLES),215*(len(MODES)+1)),(35,42,54));pen=ImageDraw.Draw(board)
        for row,(mode,frames) in enumerate([('whole_frame_DIS',baseline),*sequences.items()]):
            folder=OUT/mode;folder.mkdir(parents=True,exist_ok=True)
            for col,(a,frame) in enumerate(zip(ANGLES,frames)):
                Image.fromarray(frame,'RGBA').save(folder/(f'yaw{a:06.2f}'.replace('.','p')+'.png'))
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
                crop=tile.crop((120,0,370,135)).resize((292,170),Image.Resampling.NEAREST)
                board.paste(crop.convert('RGB'),(col*300,row*215+30))
                pen.text((col*300+6,row*215+7),f'{mode} {a:g}',fill='white')
        board.save(OUT/'texture-comparison.jpg',quality=96)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P15-183 source-valid strand texture</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Source-valid strand texture reconstruction</h2><p>Compare native RGB, nearest valid inpaint, and alpha-normalized RGB as the donor for one root-connected, free-tip curve. Source keyframes remain exact.</p><img src="texture-comparison.jpg">')
        E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':
    q=evaluate()
    print(json.dumps({'gate':q['gate'],'methods':q['modes']},indent=2))

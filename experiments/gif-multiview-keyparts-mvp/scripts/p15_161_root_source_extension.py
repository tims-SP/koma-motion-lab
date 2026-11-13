#!/usr/bin/env python3
"""Root-aware extraction from whole canonical keys, with reversible source ownership.

P15-160 extended an already-cropped layer. This study extracts actual pixels
from the full source keyframe below y54, checks root continuity, and probes
five-angle deformation. Estimated dark-line segmentation is not painted art.
"""
import json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_129_ahoge_ownership import keyframes,ANGLES,KEYS,top_components
from p15_153_source_topology import extract,ROOT
from p15_159_curve_controls import control_points,inverse_deform
from p15_128_keyart_registration import frame_interp,jumps
from p15_134_underpaint_probe import P,compose
OUT=P/'exports/p15-161-root-source-extension'
E=ROOT/'evidence/p15-161-root-source-extension-qa.json'
CUT=54

def extract_extended(source,root_xy,band=17,dark_threshold=0.80):
    visible=extract(source)[0]['loop_visible'][...,3]>24
    yy,xx=np.indices(visible.shape)
    rx,ry=map(float,root_xy)
    # Full original source, not the cropped alpha layer. Take bounded darker
    # ink near the presumed attachment, with a small bridge to the upper loop.
    rgb=source[...,:3].astype(np.float32)
    grey=cv2.cvtColor(rgb.astype('uint8'),cv2.COLOR_RGB2GRAY).astype(np.float32)
    blur=cv2.GaussianBlur(grey,(0,0),5)
    near=(abs(xx-rx)<=band)&(yy>=CUT)&(yy<=ry+8)
    darker=grey<blur*dark_threshold
    ink=near&darker&(source[...,3]>24)
    # Retain ink components touching the cropped upper part by local dilation;
    # extend only within the near-root window, with a 1px gap tolerance.
    active=visible.copy()
    for _ in range(35):
        grown=cv2.dilate(active.astype('uint8'),np.ones((3,3),np.uint8))>0
        nxt=active|(grown&ink)
        if np.array_equal(nxt,active):break
        active=nxt
    extension=active&~visible
    material=source.copy();material[~active]=0
    remaining=source.copy();remaining[active]=0
    recovered=remaining.copy();recovered[active]=material[active]
    assert np.array_equal(recovered,source)
    return material,remaining,{
        'visibleLoopPixels':int(visible.sum()),'extendedRootPixels':int(extension.sum()),
        'extensionBelowCutPixels':int((extension&(yy>=CUT)).sum()),
        'sourceRecompositionExact':True,'roiBandHalfWidth':band,
        'darkLineThresholdRatio':dark_threshold,
        'extensionBBox':([int(xx[extension].min()),int(yy[extension].min()),int(xx[extension].max()),int(yy[extension].max())] if extension.any() else None)}

def evaluate(save=True):
    sources=keyframes()
    native={k:extract(sources[k])[0]['loop_visible'] for k in KEYS}
    controls={k:control_points(native[k],k) for k in KEYS}
    base=frame_interp(sources[90.],sources[112.5],sources[135.])
    groups={}
    render_sets={'reference':base}
    for band,ratio in ((13,.75),(19,.85)):
        name=f'root_band_{band}'
        extended={}
        rest={}
        reports={}
        for k in KEYS:
            part,remaining,info=extract_extended(sources[k],controls[k][0],band,ratio)
            extended[k]=part;rest[k]=remaining;reports[f'{k:g}']=info
        images=[]
        for i,angle in enumerate(ANGLES):
            if angle in KEYS:
                images.append(sources[angle].copy());continue
            a,b=(90.,112.5) if angle<112.5 else (112.5,135.)
            t=(angle-a)/(b-a)
            target=controls[a]*(1-t)+controls[b]*t
            owner=a if t<=.5 else b
            moved=inverse_deform(extended[owner],controls[owner],target)
            # Protect baseline full-body material. Remove only the upper-loop
            # silhouette from the baseline inbetween, then overlay source-owned
            # extended material. The lower attachment remains test-only.
            backdrop=base[i].copy()
            backdrop[:CUT]=0
            images.append(compose(backdrop,moved))
        render_sets[name]=images
        groups[name]=reports
    metrics={}
    for name,imgs in render_sets.items():
        metrics[name]={
            'maxAdjacentRGBMAE':max(jumps(imgs)),
            'topConnectedComponents':[top_components(x) for x in imgs],
            'nativeKeyframesPixelExact':all(np.array_equal(imgs[ANGLES.index(k)],sources[k]) for k in KEYS),
            'midframeAlphaHolesBelowCrown':{f'{a:g}':int(((base[ANGLES.index(a)][CUT:95,:,3]>128)&
                (imgs[ANGLES.index(a)][CUT:95,:,3]<48)).sum()) for a in (101.25,123.75)}}
    qa={'schema':'KOMA_P15_161_SOURCE_ROOT_EXTENSION_V1',
        'characterId':'p0_character_001','sourceAngles':list(KEYS),'samples':list(ANGLES),
        'cutoffY':CUT,'rootCandidateSources':groups,'methods':metrics,
        'sourceMaterialPreserved':True,'artistVerifiedRootOutline':False,
        'hiddenCrownUnderpaintValidated':False,'visualAccepted':False,
        'selectedForProduction':False,
        'review':'private-assets/exports/p15-161-root-source-extension/index.html',
        'next':'Replace line-ratio segmentation with source-painted semantic root and hidden crown material, then retest both midway view connectivity.'}
    qa['gate']={
        'materialRootPixelsThreshold':20,
        'realSourceRootPixelsRecovered':any(any(x['extensionBelowCutPixels']>=20 for x in g.values()) for g in groups.values()),
        'allViewRootPixelsRecovered':any(all(x['extensionBelowCutPixels']>=20 for x in g.values()) for g in groups.values()),
        'allMidviewsConnected':any(all(v['topConnectedComponents'][i]==1 for i in (1,3)) for name,v in metrics.items() if name!='reference'),
        'passes':False,
        'reason':'No view-complete root was extracted from whole source art; at most three extra 112.5-degree pixels were found and intermediate loops remain broken. Source-derived line masks are not artist-verified root material.'}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        for name in groups:
            for k in KEYS:
                folder=OUT/name/('yaw'+f'{k:g}'.replace('.','p'));folder.mkdir(parents=True,exist_ok=True)
                layer,under,_=extract_extended(sources[k],controls[k][0],
                    int(name.rsplit('_',1)[-1]),.75 if name.endswith('13') else .85)
                Image.fromarray(layer,'RGBA').save(folder/'source-loop-root-candidate.png')
                Image.fromarray(under,'RGBA').save(folder/'source-remainder.png')
        board=Image.new('RGB',(310*5,355*len(render_sets)),(35,42,53))
        detail=Image.new('RGB',(310*5,210*len(render_sets)),(35,42,53))
        d=ImageDraw.Draw(board);dd=ImageDraw.Draw(detail)
        for row,(name,images) in enumerate(render_sets.items()):
            folder=OUT/name;folder.mkdir(parents=True,exist_ok=True)
            for col,(ang,frame) in enumerate(zip(ANGLES,images)):
                Image.fromarray(frame,'RGBA').save(folder/(f'yaw{ang:06.2f}'.replace('.','p')+'.png'))
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
                board.paste(tile.resize((304,304),Image.Resampling.LANCZOS).convert('RGB'),(col*310,row*355+28))
                d.text((col*310+6,row*355+6),f'{name} {ang:g}',fill='white')
                detail.paste(tile.crop((135,0,360,115)).resize((304,180),Image.Resampling.NEAREST).convert('RGB'),(col*310,row*210+26))
                dd.text((col*310+6,row*210+5),f'{name} {ang:g}',fill='white')
        board.save(OUT/'full-comparison.jpg',quality=94)
        detail.save(OUT/'root-closeup.jpg',quality=95)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 source root extraction</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Source root extraction at true crown attachment</h2><p>Root candidates are extracted from whole 90/112.5/135° canonical artwork; this proves recoverable source pixels but does not verify physical part identity or painter-authored underpaint.</p><img src="root-closeup.jpg"><img src="full-comparison.jpg">')
        E.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    return qa
if __name__=='__main__':
 q=evaluate()
 print(json.dumps({'roots':q['rootCandidateSources'],'methods':q['methods'],'gate':q['gate']},indent=2))

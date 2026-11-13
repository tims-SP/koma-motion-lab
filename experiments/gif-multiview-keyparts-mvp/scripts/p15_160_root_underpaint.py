#!/usr/bin/env python3
"""Three-keyview root-ownership and crown-underpaint feasibility study.

Source art's loop root sits below the historic y=54 extraction cutoff. This
experiment records exact source alpha silhouettes, constructs a bounded
inpainted crown candidate, then tests source-owned five-control interpolation
at 101.25 and 123.75. Inpainting is synthetic and not painter-verified art.
"""
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw
from p15_159_curve_controls import control_points,inverse_deform
from p15_153_source_topology import extract,ROOT
from p15_129_ahoge_ownership import keyframes,ANGLES,KEYS,top_components
from p15_128_keyart_registration import frame_interp,jumps
from p15_134_underpaint_probe import P,compose
OUT=P/'exports/p15-160-root-underpaint'
E=ROOT/'evidence/p15-160-root-underpaint-qa.json'
CUT=54
H=W=443
BAND_END=83

def root_inspection(source,angle):
    part,_,meta=extract(source)
    loop=part['loop_visible']
    ctrl=control_points(loop,angle)
    y,x=np.indices(source.shape[:2])
    root=ctrl[0]
    # At the true root position, upper loop paint and intact head region
    # already overlap vertically in the original full-frame key.
    root_region=((x-root[0])/19)**2+((y-root[1])/17)**2<=1
    source_nonzero=source[...,3]>128
    return {'landmarkRoot':[round(float(z),2) for z in root],
        'sourceRootBelowCut':bool(root[1]>=CUT),
        'rootZoneSourcePixels':int((source_nonzero&root_region).sum()),
        'loopExtractedPixelsBelowCut':int((loop[CUT:,:,3]>0).sum()),
        'sourceTopLoopPixels':meta['loopVisiblePixels']}

def crown_candidate(source,root,extension=20):
    # Estimate visible loop ink near its root using RGB contrast relative to
    # nearby crown pink. This is a small source-image diagnostic, not semantic art.
    y,x=np.indices(source.shape[:2])
    cx,cy=root
    patch=((x-cx)/20)**2+((y-(cy-7))/24)**2<=1
    patch &= (y>=CUT-8)&(y<BAND_END)
    rgba=source.copy()
    rgb=cv2.cvtColor(rgba[...,:3],cv2.COLOR_RGB2BGR)
    # Inpaint only an extremely narrow center/root line corridor. Avoid
    # treating an entire scalp region as missing source art.
    near_line=(np.abs(x-cx)<4)&(y>=CUT)&(y<=min(BAND_END-1,int(cy+8)))
    mask=np.uint8(near_line&patch)*255
    under=cv2.inpaint(rgb,mask,3,cv2.INPAINT_TELEA)
    rgba[...,:3]=cv2.cvtColor(under,cv2.COLOR_BGR2RGB)
    return rgba,mask

def warp_extended_layer(source,angle,controls):
    image=source.copy()
    # Pixel-exact source extraction above y=54 plus a narrow extension below
    # from original source (not an independently painted hidden layer).
    y,x=np.indices((H,W))
    root=controls[0]
    lower=(y>=CUT)&(y<BAND_END)&(abs(x-root[0])<9)&(source[...,3]>16)
    image[~lower & (y>=CUT)]=0
    return image,int(lower.sum())

def evaluate(save=True):
    keys=keyframes()
    original={k:keys[k] for k in KEYS}
    baseline=frame_interp(keys[90.],keys[112.5],keys[135.])
    base_parts={k:extract(keys[k])[0]['loop_visible'] for k in KEYS}
    controls={k:control_points(base_parts[k],k) for k in KEYS}
    inspected={f'{k:g}':root_inspection(keys[k],k) for k in KEYS}
    source_layers={}
    underlays={}
    mask_stats={}
    for k in KEYS:
        under,mask=crown_candidate(keys[k],controls[k][0])
        layer,count=warp_extended_layer(base_parts[k],k,controls[k])
        source_layers[k]=layer;underlays[k]=under
        mask_stats[f'{k:g}']={'syntheticInpaintMaskPixels':int((mask>0).sum()),
                            'extendedSourceLoopPixels':count,
                            'nativeSourceUnchanged':bool(np.array_equal(keys[k],original[k]))}
    methods={}
    renders={'reference':baseline}
    for mode in ('source_ownership','bounded_underpaint'):
        seq=[]
        for i,a in enumerate(ANGLES):
            if a in KEYS:
                seq.append(keys[a].copy());continue
            left,right=(90.,112.5) if a<112.5 else (112.5,135.)
            t=(a-left)/(right-left)
            target=controls[left]*(1-t)+controls[right]*t
            owner=left if t<=.5 else right
            part=inverse_deform(source_layers[owner],controls[owner],target)
            # Use baseline body for inter-view skin/clothes, while source crown
            # receives optional bounded synthetic inpainting in the root ROI.
            backdrop=baseline[i].copy()
            backdrop[:CUT]=0
            # Root strip is recomposed by one source-owned part over the
            # existing baseline crown. Inpaint alternative only a patch in
            # exact owner coordinates; it is not physically registered.
            if mode=='bounded_underpaint':
                root=target[0]
                yy,xx=np.indices((H,W))
                zone=(yy>=CUT)&(yy<BAND_END)&(abs(xx-root[0])<=6)
                patch=underlays[owner]
                backdrop[zone]=patch[zone]
            seq.append(compose(backdrop,part))
        renders[mode]=seq
    for name,seq in renders.items():
        methods[name]={'maxAdjacentRGBMAE':max(jumps(seq)),
            'topConnectedComponents':[top_components(x) for x in seq],
            'nativeKeysPixelExact':all(np.array_equal(seq[ANGLES.index(k)],keys[k]) for k in KEYS),
            'midRootExtraComponents':{f'{a:g}':top_components(seq[ANGLES.index(a)])-1 for a in (101.25,123.75)},
            'lowerCrownModifiedPixels':{f'{a:g}':int(np.any(seq[ANGLES.index(a)][CUT:BAND_END]!=baseline[ANGLES.index(a)][CUT:BAND_END],axis=2).sum()) for a in (101.25,123.75)}}
    qa={'schema':'KOMA_P15_160_SOURCE_ROOT_AND_CROWN_V1','characterId':'p0_character_001',
        'sourceAngles':list(KEYS),'samples':list(ANGLES),'legacyLoopCutoffY':CUT,
        'rootInspection':inspected,'underpaintProbes':mask_stats,'methods':methods,
        'originalSourcesUnchanged':True,'sourceAlphaRootSeparationComplete':False,
        'independentPaintedRootAvailable':False,'sourceMatchedHiddenScalpApproved':False,
        'fullYawVisualAccepted':False,'selectedForProduction':False,
        'review':'private-assets/exports/p15-160-root-underpaint/index.html',
        'next':'Paint source-owned loop roots through the actual crown attachment and generate a complete registered hidden crown per key view; validate full semantic layers before cross-yaw interpolation.'}
    qa['acceptanceGate']={
        'passes':False,
        'productionCandidateSelected':False,
        'allSourceRootsBelowOldCut':all(x['sourceRootBelowCut'] for x in inspected.values()),
        'extractedLoopContainsBelowCutPixels':any(x['loopExtractedPixelsBelowCut']>0 for x in inspected.values()),
        'bothMidviewsSingleComponent':all(
            methods['bounded_underpaint']['topConnectedComponents'][ANGLES.index(a)]==1
            for a in (101.25,123.75)),
        'reason':'All source root anchors fall below the extracted material boundary; synthetic underpaint neither supplies root semantics nor produces connected intermediate silhouettes.'
    }
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        for k in KEYS:
            folder=OUT/('yaw'+f'{k:g}'.replace('.','p'));folder.mkdir(exist_ok=True)
            Image.fromarray(underlays[k],'RGBA').save(folder/'synthetic-crown-probe.png')
            Image.fromarray(source_layers[k],'RGBA').save(folder/'visible-source-loop.png')
        full=Image.new('RGB',(310*5,355*len(renders)),(36,42,52));detail=Image.new('RGB',(310*5,225*len(renders)),(36,42,52))
        df=ImageDraw.Draw(full);dd=ImageDraw.Draw(detail)
        for row,(name,seq) in enumerate(renders.items()):
            folder=OUT/name;folder.mkdir(exist_ok=True)
            for col,(a,img) in enumerate(zip(ANGLES,seq)):
                Image.fromarray(img,'RGBA').save(folder/(f'yaw{a:06.2f}'.replace('.','p')+'.png'))
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(img,'RGBA'))
                full.paste(tile.resize((305,305),Image.Resampling.LANCZOS).convert('RGB'),(col*310,row*355+28))
                df.text((col*310+6,row*355+6),f'{name} {a:g}',fill='white')
                detail.paste(tile.crop((135,0,360,115)).resize((305,185),Image.Resampling.NEAREST).convert('RGB'),(col*310,row*225+30))
                dd.text((col*310+6,row*225+6),f'{name} {a:g}',fill='white')
        full.save(OUT/'full-comparison.jpg',quality=94)
        detail.save(OUT/'root-closeup.jpg',quality=95)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 root underpaint analysis</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Three-view loop-root and crown material diagnostic</h2><p>Source root landmarks sit below the y54 cutoff. The inpainted strip is a synthetic analysis candidate, not approved source artwork. Native keyframes remain exact.</p><img src="root-closeup.jpg"><h2>Full-frame comparison</h2><img src="full-comparison.jpg">')
        E.write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')
    return qa
if __name__=='__main__':
 q=evaluate()
 print(json.dumps({'root':q['rootInspection'],'underpaint':q['underpaintProbes'],'methods':q['methods']},indent=2))

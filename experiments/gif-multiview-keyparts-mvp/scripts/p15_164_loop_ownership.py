#!/usr/bin/env python3
"""Canonical loop ownership and head-underpaint reconstruction study.

Source-visible upper hair is assigned to one movable layer. A local, bounded
inpaint is tested only for the crown attachment; it is not approved artwork.
Full keyviews remain byte-identical.
"""
import json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_163_canonical_registration import OUT as PREVIOUS,ROOT,P
from p15_153_source_topology import extract
from p15_129_ahoge_ownership import keyframes,ANGLES,KEYS,top_components
from p15_128_keyart_registration import frame_interp,jumps
from p15_158_loop_correspondence import similarity,anchors,warp
from p15_134_underpaint_probe import compose
OUT=P/'exports/p15-164-loop-ownership'
E=ROOT/'evidence/p15-164-loop-ownership-qa.json'
H=W=443
CUT=54
def owned_key(source):
    part,head,info=extract(source)
    assert info['recompositionExact']
    return part['loop_visible'],head,info
def prepare_underpaint(source,part,root_xy):
    y,x=np.indices((H,W))
    base=source.copy()
    # Treat above-crown detached material as transparent scene background;
    # only the attached ink in the crown band is a candidate inpaint target.
    mask=(part[...,3]>24)
    base[mask]=0
    rootx,rooty=root_xy
    ink=(source[...,3]>64)&(y>=CUT)&(y<=min(90,int(rooty+13)))&(abs(x-rootx)<=7)
    # Underlying crown color estimate may be applied only inside native head.
    crown_mask=np.uint8(ink)*255
    rgb=cv2.cvtColor(source[...,:3],cv2.COLOR_RGB2BGR)
    repaired=cv2.inpaint(rgb,crown_mask,3,cv2.INPAINT_TELEA)
    repaired=cv2.cvtColor(repaired,cv2.COLOR_BGR2RGB)
    base[ink,:3]=repaired[ink]
    return base,{'erasedVisiblePixels':int(mask.sum()),'syntheticCrownPixels':int(ink.sum()),
                 'sourceBelowY91Unmodified':bool(np.array_equal(base[91:],source[91:])),
                 'sourceAlphaBelowY54Unmodified':bool(np.array_equal(base[CUT:,:,3],source[CUT:,:,3]))}
def render():
    src=keyframes()
    ref=frame_interp(src[90.],src[112.5],src[135.])
    # Filename conventions in P15-163 are yaw090 / yaw112p5 / yaw135.
    tags={90.:'yaw090',112.5:'yaw112p5',135.:'yaw135'}
    aligned={k:np.asarray(Image.open(PREVIOUS/tags[k]/'aligned.png').convert('RGBA')) for k in KEYS}
    sourceparts={};under={};details={}
    for k in KEYS:
        part,_,meta=owned_key(src[k])
        under[k],diag=prepare_underpaint(src[k],part,anchors(k)[0])
        sourceparts[k]=part
        # Verify the exact source partition before any inpainted root variant.
        original_part,plain_head,_=owned_key(src[k])
        reconstructed=plain_head.copy()
        owned=original_part[...,3]>24
        reconstructed[owned]=original_part[owned]
        assert np.array_equal(reconstructed,src[k])
        details[f'{k:g}']={**diag,'sourceVisibleLoopPixels':meta['loopVisiblePixels'],
           'sourcePartitionExact':meta['recompositionExact'],
           'sourceHeadExactBeforeInpaint':bool(np.array_equal(reconstructed,src[k]))}
    sequences={'reference':ref}
    for mode in ('source_owned','registered_owned'):
        seq=[]
        for i,a in enumerate(ANGLES):
            if a in KEYS:
                seq.append(src[a].copy());continue
            start,end=(90.,112.5) if a<112.5 else (112.5,135.)
            t=(a-start)/(end-start);owner=start if t<=.5 else end
            dest=anchors(start)*(1-t)+anchors(end)*t
            part=sourceparts[owner] if mode=='source_owned' else aligned[owner]
            transformed=warp(part,similarity(anchors(owner),dest))
            # Work on the baseline frame, erasing ONLY the old upper loop.
            # Head/face/garment at and below CUT remains intact.
            base=ref[i].copy()
            base[:CUT]=0
            if mode=='registered_owned':
                # A bounded crown underpainting probe around the interpolated root.
                y,x=np.indices((H,W));root=dest[0]
                region=(y>=CUT)&(y<86)&(abs(x-root[0])<7)
                patch=under[owner]
                base[region,:3]=patch[region,:3]
            seq.append(compose(base,transformed))
        sequences[mode]=seq
    metrics={}
    for mode,frames in sequences.items():
        metrics[mode]={'maxAdjacentRGBMAE':max(jumps(frames)),
          'topConnectedComponents':[top_components(f) for f in frames],
          'keyframesPixelExact':all(np.array_equal(frames[ANGLES.index(k)],src[k]) for k in KEYS),
          'crownAlphaIntact':all(np.array_equal(frames[i][CUT:,:,3],ref[i][CUT:,:,3]) for i in (1,3))}
    q={'schema':'KOMA_P15_164_LOOP_PIXEL_OWNERSHIP_V1','characterId':'p0_character_001',
       'sourceAngles':list(KEYS),'samples':list(ANGLES),'sourceDetails':details,
       'methods':metrics,'sourceKeyArtUnchanged':True,
       'actualScalpPaintingApproved':False,'physicalRootIdentityVerified':False,
       'continuousVisualAccepted':False,'productionSelected':False,
       'review':'private-assets/exports/p15-164-loop-ownership/index.html'}
    q['gate']={'keyviewsExact':all(v['keyframesPixelExact'] for v in metrics.values()),
       'sourceVisiblePixelsErased':all(x['erasedVisiblePixels']>800 for x in details.values()),
       'sourceCrownAlphaPreserved':all(metrics[m]['crownAlphaIntact'] for m in ('source_owned','registered_owned')),
       'bothIntermediateConnected':any(all(metrics[m]['topConnectedComponents'][i]==1 for i in (1,3)) for m in ('source_owned','registered_owned')),
       'beatsReference':any(metrics[m]['maxAdjacentRGBMAE']<=metrics['reference']['maxAdjacentRGBMAE'] for m in ('source_owned','registered_owned')),
       'passes':False}
    return q,sequences,under,sourceparts
def evaluate(save=True):
    q,sequences,under,parts=render()
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(310*5,347*3),(36,43,54));zoom=Image.new('RGB',(310*5,221*3),(36,43,54))
        draw=ImageDraw.Draw(board);dz=ImageDraw.Draw(zoom)
        for row,(label,frames) in enumerate(sequences.items()):
            folder=OUT/label;folder.mkdir(parents=True,exist_ok=True)
            for col,(angle,frame) in enumerate(zip(ANGLES,frames)):
                Image.fromarray(frame,'RGBA').save(folder/(f'yaw{angle:06.2f}'.replace('.','p')+'.png'))
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
                board.paste(tile.resize((302,302),Image.Resampling.LANCZOS).convert('RGB'),(col*310,row*347+31))
                zoom.paste(tile.crop((135,0,360,115)).resize((302,185),Image.Resampling.NEAREST).convert('RGB'),(col*310,row*221+28))
                draw.text((col*310+5,row*347+6),f'{label} {angle:g}',fill='white')
                dz.text((col*310+5,row*221+6),f'{label} {angle:g}',fill='white')
        board.save(OUT/'full-comparison.jpg',quality=94)
        zoom.save(OUT/'root-closeup.jpg',quality=95)
        for a in KEYS:
            tags={90.:'yaw090',112.5:'yaw112p5',135.:'yaw135'}
            directory=OUT/tags[a];directory.mkdir(exist_ok=True)
            Image.fromarray(parts[a],'RGBA').save(directory/'source-visible-loop.png')
            Image.fromarray(under[a],'RGBA').save(directory/'crown-underpaint-probe.png')
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 loop ownership & crown</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Canonical loop ownership and bounded crown underpaint</h2><p>Original source, source-owned loop, and aligned loop with synthetic crown probe. All original keys remain unchanged. Check 101.25° and 123.75° root and residual ink.</p><img src="root-closeup.jpg"><img src="full-comparison.jpg">')
        E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':print(json.dumps(evaluate(),ensure_ascii=False,indent=2))

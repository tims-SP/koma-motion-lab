#!/usr/bin/env python3
"""Interpolate source-owned crown underpainting independently from the ahoge.

Compare separately interpolated crown layers (P15-167 lossless source
ownership + synthetic root underpainting) with the existing whole-frame
optical-flow reference and independently transformed visible loop.
Source keys, body pixels and mask provenance are retained unchanged.
"""
import json,hashlib
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_167_endpoint_pair import pair,ROOT_AND_TIP,ROOT,P
from p15_168_root_occlusion import root_tip_at,crown_edge
from p15_129_ahoge_ownership import keyframes,KEYS,ANGLES,top_components
from p15_128_keyart_registration import frame_interp,jumps
from p15_158_loop_correspondence import similarity,warp
from p15_134_underpaint_probe import compose
OUT=P/'exports/p15-171-paired-layer-flow';E=ROOT/'evidence/p15-171-paired-layer-flow-qa.json'
H=W=443
def prepare_layers():
    native=keyframes(); hair={};head={};ownership={};checks={}
    for angle in KEYS:
        part,bg,mask,meta=pair(native[angle],angle)
        rebuilt=bg.copy();rebuilt[mask]=part[mask]
        assert np.array_equal(rebuilt,native[angle])
        hair[angle]=part;head[angle]=bg;ownership[angle]=mask
        checks[f'{angle:g}']={
            'rootPixels':meta['rootSourcePixels'],
            'underpaintPixels':meta['inpaintedCrownPixels'],
            'sourceSHA256':hashlib.sha256(native[angle].tobytes()).hexdigest(),
            'pairedReassemblyExact':True}
    return native,hair,head,ownership,checks
def independent_loop(part,angle):
    root,tip,owner=root_tip_at(angle)
    return warp(part[owner],similarity(
        np.float32([ROOT_AND_TIP[owner]['root'],ROOT_AND_TIP[owner]['tip']]),
        np.float32([root,tip]))),root
def source_owned_crown(baseline_bg,crown,root,mode):
    """The new crown must never replace nonhair imagery below y125."""
    alpha=crown[...,3]>32
    edge=crown_edge(baseline_bg,9)
    yy,xx=np.indices((H,W))
    # In the upper root band, use an independently interpolated crown;
    # original non-hair and deep anatomy are preserved.
    inside=(yy>=edge[None,:]-2)&(yy<110)&(xx>120)&(xx<390)&(baseline_bg[...,3]>16)
    # Only where the source interpolation covers a valid head surface.
    if mode=='paired_crown':
        feather=np.clip((110-yy)/20,0,1).astype(np.float32)
    elif mode=='paired_root':
        feather=np.clip((110-yy)/20,0,1).astype(np.float32)
        feather*=np.exp(-.5*((xx-root[0])/28)**2).astype(np.float32)
    elif mode=='paired_root_soft':
        feather=np.clip((110-yy)/20,0,1).astype(np.float32)
        feather*=np.exp(-.5*((xx-root[0])/16)**2).astype(np.float32)
        feather*=.65
    else:raise ValueError(mode)
    w=feather*inside*alpha
    out=baseline_bg.copy()
    out[...,:3]=np.uint8(np.clip(np.round(baseline_bg[...,:3]*(1-w[...,None])+
                                          crown[...,:3]*w[...,None]),0,255))
    out[...,3]=baseline_bg[...,3]
    return out,int((w>1e-3).sum())
def render_mid(full_frame,flow_crown,loop,root,mode):
    background,edited=source_owned_crown(full_frame,flow_crown,root,mode)
    edge=crown_edge(full_frame,9)
    yy,xx=np.indices((H,W))
    air=(yy<edge[None,:]-2)&(xx>=120)&(xx<=390)
    background[air]=0
    # Keep the loop on one side of the crown, with original root underpaint
    # visible in the paired interpolated background.
    moving=loop.copy()
    if mode=='paired_root_soft':
        depth=np.clip((edge[None,:]+6-yy)/11,0,1)
        moving[...,3]=np.uint8(np.round(moving[...,3]*depth))
        moving[moving[...,3]==0]=0
    else:
        moving[yy>=edge[None,:]+2]=0
    moving[(xx<120)|(xx>390)]=0
    out=compose(background,moving)
    out[125:]=full_frame[125:]
    return out,{'pairedCrownRGBEditedPixels':edited,
        'foregroundLoopPixels':int((moving[...,3]>64).sum()),
        'sourceBelowY125Exact':bool(np.array_equal(out[125:],full_frame[125:])),
        'sourceCrownAlphaChangedPixels':int((out[55:110,:,3]!=full_frame[55:110,:,3]).sum())}
def evaluate(save=True):
    source,hair,crowns,mattes,pairs=prepare_layers()
    reference=frame_interp(source[90.],source[112.5],source[135.])
    # Treat the registered underpainting as a distinct view-dependent layer.
    crown_frames=frame_interp(crowns[90.],crowns[112.5],crowns[135.])
    seqs={'reference':reference};checks={}
    for mode in ('paired_crown','paired_root','paired_root_soft'):
        frames=[];info={}
        for i,angle in enumerate(ANGLES):
            if angle in KEYS:
                frames.append(source[angle].copy());continue
            part,root=independent_loop(hair,angle)
            frame,details=render_mid(reference[i],crown_frames[i],part,root,mode)
            frames.append(frame);info[f'{angle:g}']=details
        seqs[mode]=frames;checks[mode]=info
    metrics={}
    for mode,frames in seqs.items():
        metrics[mode]={'maxAdjacentRGBMAE':max(jumps(frames)),
            'adjacentRGBMAE':jumps(frames),
            'topConnectedComponents':[top_components(f) for f in frames],
            'sourceKeysPixelExact':all(np.array_equal(frames[ANGLES.index(k)],source[k]) for k in KEYS),
            'bodyBelowY125Exact':all(np.array_equal(frames[i][125:],reference[i][125:]) for i in (1,3))}
    result={'schema':'KOMA_P15_171_PAIRED_LAYER_FLOW_V1',
       'characterId':'p0_character_001','sourceAngles':list(KEYS),'renderAngles':list(ANGLES),
       'keyviewPairs':pairs,'methods':metrics,'midframeChecks':checks,
       'materialMethod':'independent DIS crown-background interpolation with source-owned ahoge root and free-tip transform',
       'artistApprovedUnderpaint':False,'artistApprovedHairAttachment':False,
       'continuousVisualAccepted':False,'canonicalRendererUpdated':False,
       'review':'private-assets/exports/p15-171-paired-layer-flow/index.html'}
    result['gate']={
       'sourcePairsExact':all(v['pairedReassemblyExact'] for v in pairs.values()),
       'nativeKeysExact':all(v['sourceKeysPixelExact'] for v in metrics.values()),
       'deepBodyExact':all(v['bodyBelowY125Exact'] for v in metrics.values()),
       'midviewConnected':any(all(metrics[name]['topConnectedComponents'][i]==1 for i in (1,3)) for name in checks),
       'beatsReference':any(metrics[name]['maxAdjacentRGBMAE']<=metrics['reference']['maxAdjacentRGBMAE'] for name in checks),
       'artistApproval':False,'passes':False}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        for key in KEYS:
            folder=OUT/('yaw'+f'{key:g}'.replace('.','p'));folder.mkdir(exist_ok=True)
            Image.fromarray(hair[key],'RGBA').save(folder/'source-owned-loop.png')
            Image.fromarray(crowns[key],'RGBA').save(folder/'paired-crown.png')
            Image.fromarray(np.uint8(mattes[key])*255,'L').save(folder/'ownership.png')
        panel=Image.new('RGB',(311*5,228*len(seqs)),(35,42,53))
        draw=ImageDraw.Draw(panel)
        for row,(mode,frames) in enumerate(seqs.items()):
            folder=OUT/mode;folder.mkdir(exist_ok=True)
            for col,(yaw,frame) in enumerate(zip(ANGLES,frames)):
                Image.fromarray(frame,'RGBA').save(folder/(f'yaw{yaw:06.2f}'.replace('.','p')+'.png'))
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
                panel.paste(tile.crop((125,0,365,140)).resize((304,188),Image.Resampling.NEAREST).convert('RGB'),(col*311,row*228+30))
                draw.text((col*311+6,row*228+7),f'{mode} {yaw:g}',fill='white')
        panel.save(OUT/'root-paired-comparison.jpg',quality=96)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 paired layer interpolation</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Independent crown and ahoge interpolation</h2><p>Three painter-source keyviews with reversible loop/crown ownership. Comparing separate crown flow, root-local blending and soft occlusion. The hidden crown pixels are synthetic and require source-art visual acceptance.</p><img src="root-paired-comparison.jpg">')
        E.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result
if __name__=='__main__':
    q=evaluate();print(json.dumps({'methods':q['methods'],'checks':q['midframeChecks'],'gate':q['gate']},indent=2))

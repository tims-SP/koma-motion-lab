#!/usr/bin/env python3
"""Independent loop compositing across two rear-yaw midframes.

Rebuilds a clean source-owned upper-loop plane and tests three root
occlusion variants while preserving source keyviews exactly.
All inpaint and junction bridges are experimental render material.
"""
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw
from p15_167_endpoint_pair import ROOT_AND_TIP,pair,ROOT,P
from p15_129_ahoge_ownership import keyframes,KEYS,ANGLES,top_components
from p15_166_crown_silhouette import crown_edge
from p15_128_keyart_registration import frame_interp,jumps
from p15_158_loop_correspondence import similarity,warp
from p15_134_underpaint_probe import compose
OUT=P/'exports/p15-168-root-occlusion'
E=ROOT/'evidence/p15-168-root-occlusion-qa.json'
H=W=443

def root_tip_at(a):
    left,right=(90.,112.5) if a<112.5 else (112.5,135.)
    t=(a-left)/(right-left)
    root=np.array(ROOT_AND_TIP[left]['root'],np.float32)*(1-t)+np.array(ROOT_AND_TIP[right]['root'],np.float32)*t
    tip=np.array(ROOT_AND_TIP[left]['tip'],np.float32)*(1-t)+np.array(ROOT_AND_TIP[right]['tip'],np.float32)*t
    owner=left if t<=.5 else right
    return root,tip,owner

def clean_background(frame,edge,root,mode):
    yy,xx=np.indices((H,W))
    # Source top pixels belong to the currently interpolated loop, and
    # will be replaced with a single source-owned hair layer.
    air=(yy<np.minimum(edge[None,:]-2,125))&(xx>=120)&(xx<=390)
    bg=frame.copy();bg[air]=0
    # Confine synthetic crown inpainting to the root-centered ink corridor,
    # retaining original head alpha. This is NOT a final painted texture.
    if mode!='upper_only':
        x0,y0=root
        region=(yy>=edge[None,:]+3)&(yy<edge[None,:]+15)&(abs(xx-x0)<9)
        region&=(yy<104)&(frame[...,3]>=245)
        image=cv2.cvtColor(bg[...,:3],cv2.COLOR_RGB2BGR)
        restored=cv2.inpaint(image,np.uint8(region)*255,3,cv2.INPAINT_TELEA)
        result=cv2.cvtColor(restored,cv2.COLOR_BGR2RGB)
        bg[region,:3]=result[region]
    return bg,air

def candidate(frame,original_part,source_root,source_tip,target_root,target_tip,mode):
    shifted=warp(original_part,similarity(np.float32([source_root,source_tip]),
                                          np.float32([target_root,target_tip])))
    edge=crown_edge(frame,9)
    bg,air=clean_background(frame,edge,target_root,mode)
    yy,xx=np.indices((H,W))
    alpha=shifted[...,3].copy()
    if mode=='upper_only':
        shifted[~air]=0
    elif mode=='root_front':
        # Blend the source root into existing crown, then suppress it beneath
        # the scalp. The root remains one source-owned material.
        depth=np.clip((edge[None,:]+8-yy)/12,0,1)
        shifted[...,3]=np.uint8(np.round(alpha*depth))
        shifted[(xx<120)|(xx>390)]=0
        shifted[shifted[...,3]==0]=0
    elif mode=='crown_front':
        # Crown owns all y >= crown edge, but retain the hair root within a
        # narrow band above it; this tests the visible root contact.
        boundary=edge[None,:]+2
        shifted[yy>=boundary]=0
        shifted[(xx<120)|(xx>390)]=0
    else:raise ValueError(mode)
    result=compose(bg,shifted)
    # Preserve the entire original source-owned head and garment from y125.
    result[125:]=frame[125:]
    # Alpha below the crown stays fully source owned, not dropped by erasure.
    root_px=int((shifted[...,3]>64).sum())
    head=(yy>=edge[None,:]+16)&(xx>=120)&(xx<390)
    changed=int(np.count_nonzero(result[head]!=frame[head]))
    return result,{'visibleHairPixels':root_px,'headFarBelowCrownChangedChannels':changed,
        'nativeBelowY125Exact':bool(np.array_equal(result[125:],frame[125:])),
        'rootDistanceToCrown':round(float(target_root[1]-edge[int(round(target_root[0]))]),3),
        'foregroundAlphaPixelsInCrownBand':int(((shifted[...,3]>64)&(yy>=edge[None,:]-2)&(yy<=edge[None,:]+8)).sum())}

def evaluate(save=True):
    keys=keyframes()
    strands={a:pair(keys[a],a)[0] for a in KEYS}
    ref=frame_interp(keys[90.],keys[112.5],keys[135.])
    sequences={'reference':ref}
    diagnostics={}
    for mode in ('upper_only','root_front','crown_front'):
        seq=[];details={}
        for i,angle in enumerate(ANGLES):
            if angle in KEYS:
                seq.append(keys[angle].copy());continue
            root,tip,owner=root_tip_at(angle)
            result,diag=candidate(ref[i],strands[owner],ROOT_AND_TIP[owner]['root'],
                                   ROOT_AND_TIP[owner]['tip'],root,tip,mode)
            seq.append(result);details[f'{angle:g}']=diag
        sequences[mode]=seq;diagnostics[mode]=details
    metrics={}
    for mode,seq in sequences.items():
        metrics[mode]={'maxAdjacentRGBMAE':max(jumps(seq)),
            'adjacentRGBMAE':jumps(seq),
            'topConnectedComponents':[top_components(a) for a in seq],
            'originalKeyviewsPixelExact':all(np.array_equal(seq[ANGLES.index(a)],keys[a]) for a in KEYS)}
    q={'schema':'KOMA_P15_168_ROOT_OCCLUSION_V1','characterId':'p0_character_001',
       'sourceAngles':list(KEYS),'renderAngles':list(ANGLES),
       'variants':metrics,'midframeDiagnostics':diagnostics,
       'sourcePartSelection':'P15-167 source-native hair ownership and source-verified contact/free-tip proposals',
       'syntheticCrownUnderpaintOnly':True,
       'painterApprovedUnderpaint':False,'physicalRootConnected':False,
       'fullYawVisualAccepted':False,'productionRendererUpdated':False,
       'review':'private-assets/exports/p15-168-root-occlusion/index.html'}
    q['gate']={'originalKeyviewsPixelExact':all(x['originalKeyviewsPixelExact'] for x in metrics.values()),
       'bothMidframesConnected':any(all(metrics[k]['topConnectedComponents'][i]==1 for i in (1,3)) for k in diagnostics),
       'zeroChangedPixelsBelowY125':all(all(d['nativeBelowY125Exact'] for d in v.values()) for v in diagnostics.values()),
       'beatsCurrentBaseline':any(metrics[k]['maxAdjacentRGBMAE']<=metrics['reference']['maxAdjacentRGBMAE'] for k in diagnostics),
       'visualApproval':False,'passes':False}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        panel=Image.new('RGB',(312*5,240*len(sequences)),(36,42,54));full=Image.new('RGB',(312*5,352*len(sequences)),(36,42,54))
        draw=ImageDraw.Draw(panel);df=ImageDraw.Draw(full)
        for row,(mode,seq) in enumerate(sequences.items()):
            directory=OUT/mode;directory.mkdir(exist_ok=True)
            for col,(angle,arr) in enumerate(zip(ANGLES,seq)):
                Image.fromarray(arr,'RGBA').save(directory/(f'yaw{angle:06.2f}'.replace('.','p')+'.png'))
                image=Image.new('RGBA',(443,443),(49,61,78,255));image.alpha_composite(Image.fromarray(arr,'RGBA'))
                panel.paste(image.crop((120,0,370,140)).resize((305,192),Image.Resampling.NEAREST).convert('RGB'),
                            (312*col,240*row+30))
                full.paste(image.resize((305,305),Image.Resampling.LANCZOS).convert('RGB'),
                           (312*col,352*row+30))
                draw.text((312*col+6,240*row+6),f'{mode} {angle:g}',fill='white')
                df.text((312*col+6,352*row+6),f'{mode} {angle:g}',fill='white')
        panel.save(OUT/'root-closeup.jpg',quality=95)
        full.save(OUT/'full-comparison.jpg',quality=94)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 root occlusion comparison</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>P0 root and crown occlusion</h2><p>Three intermediate-frame ownership approaches; native keys remain pixel exact. Synthetic crown strips are experimental. Source artwork is preserved separately.</p><img src="root-closeup.jpg"><img src="full-comparison.jpg">')
        E.write_text(json.dumps(q,indent=2,ensure_ascii=False)+'\n')
    return q

if __name__=='__main__':
    q=evaluate()
    print(json.dumps({'variants':q['variants'],'diagnostics':q['midframeDiagnostics'],'gate':q['gate']},indent=2))

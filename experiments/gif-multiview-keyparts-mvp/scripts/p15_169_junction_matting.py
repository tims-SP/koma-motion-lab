#!/usr/bin/env python3
"""Root-junction matte repair for two intermediate source-owned loop renders.

Use P15-167 native contact/free-tip anchors with P15-168 crown-front
occlusion. Evaluate feathered scalp RGB reconstruction only in a bounded
opaque crown region, plus a source-aligned root anti-alias edge.
Native keyviews and geometry outside upper 125 rows remain pixel-exact.
"""
import json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_168_root_occlusion import (candidate,root_tip_at,ROOT_AND_TIP,ROOT,P,
                                     crown_edge)
from p15_167_endpoint_pair import pair
from p15_129_ahoge_ownership import keyframes,KEYS,ANGLES,top_components
from p15_128_keyart_registration import frame_interp,jumps
OUT=P/'exports/p15-169-junction-matting'
E=ROOT/'evidence/p15-169-junction-matting-qa.json'
H=W=443
def render_mid(reference,part,source_root,source_tip,root,tip,mode):
    base,info=candidate(reference,part,source_root,source_tip,root,tip,'crown_front')
    if mode=='crown_front':
        return base,{**info,'editedPixels':0,'maxCrownRGBChange':0,
                     'belowY125Exact':bool(np.array_equal(base[125:],reference[125:]))}
    edge=crown_edge(reference,9)
    yy,xx=np.indices((H,W))
    rootx=float(root[0])
    # The original interpolated loop's ghost stroke lives around the root
    # inside the opaque crown. Limit diagnostics to a narrow, source-owned
    # crown strip; preserve original alpha and all other content.
    halfwidth={'junction_06':6,'junction_10':10,'junction_14':14}[mode]
    target=((yy>=edge[None,:]+2)&(yy<=edge[None,:]+16)&(yy<108)
            &(abs(xx-rootx)<halfwidth)&(reference[...,3]>=245))
    target=cv2.morphologyEx(target.astype('uint8'),cv2.MORPH_ELLIPSE,
                           np.ones((3,3),np.uint8)).astype(bool)
    # Inpaint using only already opaque crown pixels. Restore source
    # background RGB where inpainting would sample transparent air.
    safe=reference.copy()
    rgb=cv2.cvtColor(safe[...,:3],cv2.COLOR_RGB2BGR)
    repaired=cv2.cvtColor(cv2.inpaint(rgb,(target*255).astype('uint8'),3,
                                      cv2.INPAINT_TELEA),cv2.COLOR_BGR2RGB)
    matte=cv2.GaussianBlur(target.astype(np.float32),(0,0),1.2)
    matte=np.clip(matte*.85,0,1)
    result=base.copy()
    original=result[...,:3].astype(np.float32)
    result[...,:3]=np.uint8(np.clip(np.round(original*(1-matte[...,None])+
                        repaired.astype(np.float32)*matte[...,None]),0,255))
    result[...,3]=base[...,3]
    result[125:]=reference[125:]
    diff=np.any(result!=base,axis=2)
    change=np.abs(result[...,:3].astype(np.int16)-base[...,:3].astype(np.int16))
    return result,{**info,'editedPixels':int(diff.sum()),
                   'maxCrownRGBChange':int(change.max()),
                   'belowY125Exact':bool(np.array_equal(result[125:],reference[125:])),
                   'scalpAlphaIdenticalToBase':bool(np.array_equal(result[...,3],base[...,3])),
                   'editBBox':box(diff)}
def box(mask):
    ys,xs=np.where(mask)
    return [int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())] if len(xs) else []
def run(save=True):
    original=keyframes()
    parts={a:pair(original[a],a)[0] for a in KEYS}
    baseline=frame_interp(original[90.],original[112.5],original[135.])
    sequences={'reference':baseline}
    notes={}
    for mode in ('crown_front','junction_06','junction_10','junction_14'):
        frames=[];details={}
        for i,angle in enumerate(ANGLES):
            if angle in KEYS:
                frames.append(original[angle].copy());continue
            root,tip,owner=root_tip_at(angle)
            image,meta=render_mid(baseline[i],parts[owner],ROOT_AND_TIP[owner]['root'],
                 ROOT_AND_TIP[owner]['tip'],root,tip,mode)
            frames.append(image);details[f'{angle:g}']=meta
        sequences[mode]=frames;notes[mode]=details
    metrics={}
    for name,frames in sequences.items():
        metrics[name]={'maxAdjacentRGBMAE':max(jumps(frames)),
                       'adjacentRGBMAE':jumps(frames),
                       'topConnectedComponents':[top_components(f) for f in frames],
                       'nativeKeyviewsPixelExact':all(np.array_equal(frames[ANGLES.index(a)],original[a]) for a in KEYS),
                       'deepBodyPixelExact':all(np.array_equal(frames[i][125:],baseline[i][125:]) for i in (1,3))}
    q={'schema':'KOMA_P15_169_ROOT_JUNCTION_MATTING_V1','characterId':'p0_character_001',
       'sourceAngles':list(KEYS),'samples':list(ANGLES),
       'methods':metrics,'localMaterialChecks':notes,
       'method':'Opaque-crown bounded inpaint with soft RGB matte; independent registered source loop; original RGBA keys',
       'nativeArtUnchanged':True,'hiddenCrownPaintArtistApproved':False,
       'rootAttachmentArtistApproved':False,'fullYawVisualAccepted':False,
       'canonicalRendererUpdated':False,
       'review':'private-assets/exports/p15-169-junction-matting/index.html'}
    q['gate']={'nativeKeyviewsExact':all(v['nativeKeyviewsPixelExact'] for v in metrics.values()),
       'deepBodyExact':all(v['deepBodyPixelExact'] for v in metrics.values()),
       'bothMidviewsTopologicallyConnected':all(metrics[m]['topConnectedComponents'][i]==1 for m in notes for i in (1,3)),
       'alphaRetained':all(v.get('scalpAlphaIdenticalToBase',True) for m in notes for v in notes[m].values()),
       'noMotionRegression':any(metrics[m]['maxAdjacentRGBMAE']<=metrics['reference']['maxAdjacentRGBMAE'] for m in notes),
       'visualApproval':False,'passes':False}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        image=Image.new('RGB',(311*5,230*len(sequences)),(35,42,53))
        pen=ImageDraw.Draw(image)
        for row,(name,frames) in enumerate(sequences.items()):
            folder=OUT/name;folder.mkdir(exist_ok=True)
            for col,(angle,frame) in enumerate(zip(ANGLES,frames)):
                Image.fromarray(frame,'RGBA').save(folder/(f'yaw{angle:06.2f}'.replace('.','p')+'.png'))
                bg=Image.new('RGBA',(443,443),(49,61,78,255))
                bg.alpha_composite(Image.fromarray(frame,'RGBA'))
                image.paste(bg.crop((125,0,365,140)).resize((304,194),Image.Resampling.NEAREST).convert('RGB'),
                            (col*311,row*230+27))
                pen.text((col*311+5,row*230+6),f'{name} {angle:g}',fill='white')
        image.save(OUT/'junction-closeup.jpg',quality=95)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 root junction matte</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Intermediate-yaw root junction matte evaluation</h2><p>All source keyviews are preserved; candidate scalp restoration is bounded to opaque crown pixels. Fine line continuity and source-matched underpaint remain subject to visual review.</p><img src="junction-closeup.jpg">')
        E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':
    q=run()
    print(json.dumps({'methods':q['methods'],'checks':q['localMaterialChecks'],'gate':q['gate']},indent=2))

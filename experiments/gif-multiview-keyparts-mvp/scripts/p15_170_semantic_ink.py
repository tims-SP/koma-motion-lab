#!/usr/bin/env python3
"""Source-root ink ownership experiment using line-response masks.

Preserve the verified P15-168 crown-front silhouette. Classify locally dark
source-root strokes by morphological blackhat inside opaque native crown,
excluding the current foreground hair mask. Compare bounded correction modes.
All native source artwork and the renderer baseline are retained unchanged.
"""
import json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_168_root_occlusion import candidate,root_tip_at,ROOT_AND_TIP,ROOT,P,crown_edge
from p15_167_endpoint_pair import pair
from p15_129_ahoge_ownership import keyframes,KEYS,ANGLES,top_components
from p15_128_keyart_registration import frame_interp,jumps
from p15_158_loop_correspondence import similarity,warp
OUT=P/'exports/p15-170-semantic-ink'; E=ROOT/'evidence/p15-170-semantic-ink-qa.json'
H=W=443
def root_mask(frame,root,existing_loop,contrast=14,halfwidth=15):
    yy,xx=np.indices((H,W))
    edge=crown_edge(frame,9)
    rootx=float(root[0])
    zone=(yy>=edge[None,:]-1)&(yy<=edge[None,:]+20)&(yy<115)&(abs(xx-rootx)<=halfwidth)
    zone&=frame[...,3]>=245
    gray=cv2.cvtColor(frame[...,:3],cv2.COLOR_RGB2GRAY)
    blackhat=cv2.morphologyEx(gray,cv2.MORPH_BLACKHAT,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9)))
    dark=(blackhat>=contrast)&zone
    # Current donor loop must retain its own native ink identity.
    protect=cv2.dilate(np.uint8(existing_loop[...,3]>64),np.ones((3,3),np.uint8))>0
    dark&=~protect
    return dark, zone,blackhat
def repair(frame,part,root,tip,source_root,source_tip,method):
    base,info=candidate(frame,part,source_root,source_tip,root,tip,'crown_front')
    donor=warp(part,similarity(np.float32([source_root,source_tip]),np.float32([root,tip])))
    threshold={'ink_10':10,'ink_18':18,'ink_26':26}[method]
    mask,zone,response=root_mask(frame,root,donor,threshold)
    # A 1px soft fringe avoids replacing unrelated broad shading pixels.
    m=cv2.dilate(np.uint8(mask),np.ones((2,2),np.uint8))>0
    rgb=cv2.cvtColor(frame[...,:3],cv2.COLOR_RGB2BGR)
    paint=cv2.cvtColor(cv2.inpaint(rgb,np.uint8(m)*255,2,cv2.INPAINT_TELEA),
                       cv2.COLOR_BGR2RGB)
    w=cv2.GaussianBlur(np.float32(m),(0,0),.65)
    w=np.clip(w*.9,0,1)
    out=base.copy()
    out[...,:3]=np.uint8(np.round(np.clip(
      out[...,:3].astype(np.float32)*(1-w[...,None])+paint.astype(np.float32)*w[...,None],0,255)))
    out[...,3]=base[...,3]
    out[125:]=frame[125:]
    delta=np.any(out!=base,axis=2)
    y,x=np.where(delta)
    return out,{**info,'semanticInkPixels':int(mask.sum()),
      'editPixels':int(delta.sum()),
      'editBBox':[int(x.min()),int(y.min()),int(x.max()),int(y.max())] if len(x) else [],
      'sourceAlphaExact':bool(np.array_equal(out[...,3],base[...,3])),
      'sourceBodyY125Exact':bool(np.array_equal(out[125:],frame[125:])),
      'maxRGBChange':int(np.abs(out[...,:3].astype(np.int16)-base[...,:3].astype(np.int16)).max())}
def run(save=True):
    source=keyframes()
    parts={a:pair(source[a],a)[0] for a in KEYS}
    reference=frame_interp(source[90.],source[112.5],source[135.])
    sequences={'reference':reference}; details={}
    for method in ('crown_front','ink_10','ink_18','ink_26'):
        seq=[];part_details={}
        for i,angle in enumerate(ANGLES):
            if angle in KEYS:seq.append(source[angle].copy());continue
            root,tip,owner=root_tip_at(angle)
            if method=='crown_front':
                result,info=candidate(reference[i],parts[owner],ROOT_AND_TIP[owner]['root'],
                     ROOT_AND_TIP[owner]['tip'],root,tip,'crown_front')
            else:
                result,info=repair(reference[i],parts[owner],root,tip,
                     ROOT_AND_TIP[owner]['root'],ROOT_AND_TIP[owner]['tip'],method)
            seq.append(result);part_details[f'{angle:g}']=info
        sequences[method]=seq;details[method]=part_details
    metrics={}
    for method,seq in sequences.items():
        metrics[method]={'maxAdjacentRGBMAE':max(jumps(seq)),
          'adjacentRGBMAE':jumps(seq),
          'topConnectedComponents':[top_components(im) for im in seq],
          'nativeKeysExact':all(np.array_equal(seq[ANGLES.index(a)],source[a]) for a in KEYS),
          'belowY125Exact':all(np.array_equal(seq[i][125:],reference[i][125:]) for i in (1,3))}
    q={'schema':'KOMA_P15_170_SEMANTIC_INK_V1','characterId':'p0_character_001',
       'keyAngles':list(KEYS),'renderAngles':list(ANGLES),
       'methods':metrics,'pixelDiagnostics':details,
       'model':'Local morphological blackhat source-ink ownership outside protected donor loop',
       'originalArtPreserved':True,'painterApprovedSourceLineOwnership':False,
       'painterApprovedRootlessCrown':False,'continuousYawVisuallyAccepted':False,
       'productionRendererUpdated':False,
       'review':'private-assets/exports/p15-170-semantic-ink/index.html'}
    q['gate']={'allKeyviewsExact':all(v['nativeKeysExact'] for v in metrics.values()),
      'bodyExact':all(v['belowY125Exact'] for v in metrics.values()),
      'allMidviewsConnected':all(metrics[method]['topConnectedComponents'][i]==1
                                 for method in details for i in (1,3)),
      'alphaExactToCrownFront':all(v.get('sourceAlphaExact',True) for method in details for v in details[method].values()),
      'beatsBaseline':any(metrics[method]['maxAdjacentRGBMAE']<=metrics['reference']['maxAdjacentRGBMAE']
                          for method in details),
      'artistApproved':False,'passes':False}
    if save:
      OUT.mkdir(exist_ok=True,parents=True)
      board=Image.new('RGB',(311*5,234*len(sequences)),(36,42,54));d=ImageDraw.Draw(board)
      for row,(name,seq) in enumerate(sequences.items()):
        folder=OUT/name;folder.mkdir(exist_ok=True)
        for col,(angle,arr) in enumerate(zip(ANGLES,seq)):
          Image.fromarray(arr,'RGBA').save(folder/(f'yaw{angle:06.2f}'.replace('.','p')+'.png'))
          tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(arr,'RGBA'))
          board.paste(tile.crop((125,0,365,140)).resize((304,193),Image.Resampling.NEAREST).convert('RGB'),(col*311,row*234+28))
          d.text((col*311+6,row*234+6),f'{name} {angle:g}',fill='white')
      board.save(OUT/'semantic-ink-closeup.jpg',quality=95)
      (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 source root ink ownership</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Intermediate yaw source-ink ownership</h2><p>Root-local morphological ink candidate against a protected foreground loop. Native keys and below-neck pixels are identical to source. Synthetic paint is an exploratory material only.</p><img src="semantic-ink-closeup.jpg">')
      E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':
    q=run()
    print(json.dumps({'metrics':q['methods'],'details':q['pixelDiagnostics'],'gate':q['gate']},indent=2))

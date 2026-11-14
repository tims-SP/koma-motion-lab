#!/usr/bin/env python3
"""Separate free-standing loop from crown using the crown's broad spatial support.

The reference intermediate render is preserved below a per-column crown edge.
Three alternative opening radii are compared, with the independently aligned
loop composited behind the retained crown surface.
"""
import json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_163_canonical_registration import OUT as ALIGNED,P,ROOT
from p15_129_ahoge_ownership import keyframes,ANGLES,KEYS,top_components
from p15_128_keyart_registration import frame_interp,jumps
from p15_158_loop_correspondence import anchors,similarity,warp
from p15_134_underpaint_probe import compose,background_rgb
OUT=P/'exports/p15-166-crown-silhouette';E=ROOT/'evidence/p15-166-crown-silhouette-qa.json'
TAGS={90.:'yaw090',112.5:'yaw112p5',135.:'yaw135'}
H=W=443
def open_head_core(frame,radius):
    alpha=np.uint8(frame[...,3]>32)
    # Suppress slim free-standing hair while retaining the broad head mass.
    size=radius*2+1
    element=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(size,size))
    eroded=cv2.erode(alpha,element)
    count,labels,stats,_=cv2.connectedComponentsWithStats(eroded,8)
    candidates=[i for i in range(1,count) if stats[i,cv2.CC_STAT_AREA]>1000]
    if not candidates:raise ValueError('No head core extracted')
    main=max(candidates,key=lambda i:stats[i,cv2.CC_STAT_AREA])
    mask=np.uint8(labels==main)
    recovered=cv2.dilate(mask,element)
    return recovered>0
def crown_edge(frame,radius):
    core=open_head_core(frame,radius)
    # Per-column first contact on the head, ignoring front-side slim hair.
    edge=np.full(W,85.,dtype=np.float32)
    good=[]
    for x in range(105,390):
        rows=np.flatnonzero(core[20:145,x])
        if len(rows):
            edge[x]=float(rows.min()+20);good.append(x)
    if len(good)<80:raise ValueError('Insufficient crown columns')
    low,high=min(good),max(good)
    edge[:low]=edge[low];edge[high+1:]=edge[high]
    gaps=[x for x in range(low,high+1) if x not in set(good)]
    if gaps:edge[gaps]=np.interp(gaps,good,edge[good])
    edge=cv2.GaussianBlur(edge.reshape(1,-1),(0,0),7).reshape(-1)
    # Make a two pixel safety margin so crown ink is not erased.
    edge-=2
    edge=np.clip(edge,35,140)
    return edge
def separate(frame,radius):
    edge=crown_edge(frame,radius)
    yy,xx=np.indices((H,W))
    air=(yy<edge[None,:])&(xx>=105)&(xx<=390)
    back=frame.copy()
    back[air]=0
    crown=frame.copy();crown[air]=0
    return back,crown,air,edge
def composite_mid(frame,part,angle,radius,fade=1):
    bg,crown,air,edge=separate(frame,radius)
    # Only the registered donor loop owns free-standing top material.
    # Material that reaches below the edge is painted behind the crown.
    yy,xx=np.indices((H,W))
    keep=yy<edge[None,:]
    loop=part.copy()
    loop[~keep]=0
    loop[(xx<105)|(xx>390)]=0
    output=compose(bg,loop)
    return output,{'erasedUpperAlphaPixels':int((air&(frame[...,3]>32)).sum()),
                   'newLoopOpaquePixels':int((loop[...,3]>64).sum()),
                   'preservedCrownPixels':bool(np.array_equal(output[~air],frame[~air])),
                   'crownAlphaChangedPixels':int(np.count_nonzero(output[~air,3]!=frame[~air,3])),
                   'crownEdgeRangeY':[round(float(edge[135:360].min()),2),round(float(edge[135:360].max()),2)]},edge

def evaluate(save=True):
    sources=keyframes()
    baseline=frame_interp(sources[90.],sources[112.5],sources[135.])
    aligned={k:np.asarray(Image.open(ALIGNED/TAGS[k]/'aligned.png').convert('RGBA')) for k in KEYS}
    sequences={'reference':baseline};notes={}
    for radius in (5,9,13):
        name=f'crown_{radius:02d}'
        seq=[];details={}
        for i,a in enumerate(ANGLES):
            if a in KEYS:seq.append(sources[a].copy());continue
            start,end=(90.,112.5) if a<112.5 else (112.5,135.)
            t=(a-start)/(end-start)
            owner=start if t<=.5 else end
            target=anchors(start)*(1-t)+anchors(end)*t
            moved=warp(aligned[owner],similarity(anchors(owner),target))
            candidate,info,edge=composite_mid(baseline[i],moved,a,radius)
            seq.append(candidate);details[f'{a:g}']=info
        sequences[name]=seq;notes[name]=details
    outcomes={}
    for name,frames in sequences.items():
        outcomes[name]={'maxAdjacentRGBMAE':max(jumps(frames)),
                        'topComponents':[top_components(x) for x in frames],
                        'nativeKeysPixelExact':all(np.array_equal(frames[ANGLES.index(k)],sources[k]) for k in KEYS)}
    report={'schema':'KOMA_P15_166_CROWN_SILHOUETTE_V1',
       'characterId':'p0_character_001','sourceAngles':list(KEYS),'samples':list(ANGLES),
       'methods':outcomes,'crownBoundaries':notes,
       'sourceUnmodified':True,'originalRootlessCrownPaintApproved':False,
       'physicallyMatchedHairRootsApproved':False,'continuousVisualAccepted':False,
       'productionSelected':False,
       'review':'private-assets/exports/p15-166-crown-silhouette/index.html'}
    report['gate']={
      'crownPixelsPreserved':all(all(x['preservedCrownPixels'] for x in m.values()) for m in notes.values()),
      'allFiveFrameSourceKeysExact':all(x['nativeKeysPixelExact'] for x in outcomes.values()),
      'allMidviewLoopsConnected':any(all(outcomes[k]['topComponents'][i]==1 for i in (1,3)) for k in notes),
      'candidateImprovesMotion':any(outcomes[k]['maxAdjacentRGBMAE']<=outcomes['reference']['maxAdjacentRGBMAE'] for k in notes),
      'visualAccepted':False,'passes':False}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(310*5,212*len(sequences)),(35,42,53));d=ImageDraw.Draw(board)
        for row,(name,frames) in enumerate(sequences.items()):
            folder=OUT/name;folder.mkdir(exist_ok=True)
            for col,(angle,img) in enumerate(zip(ANGLES,frames)):
                Image.fromarray(img,'RGBA').save(folder/(f'yaw{angle:06.2f}'.replace('.','p')+'.png'))
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(img,'RGBA'))
                crop=tile.crop((135,0,360,125)).resize((303,180),Image.Resampling.NEAREST)
                board.paste(crop.convert('RGB'),(310*col,212*row+26))
                d.text((310*col+7,212*row+6),f'{name} {angle:g}',fill='white')
        board.save(OUT/'comparison.jpg',quality=95)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 crown silhouette ownership</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>90–135° crown silhouette and source-owned loop</h2><p>Head-edge ownership from morphological head core at three kernel radii. Donor loop rests behind retained crown surface; source keys remain intact. Painter-registered hidden root material is a separate art requirement.</p><img src="comparison.jpg">')
        E.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report
if __name__=='__main__':
    q=evaluate()
    print(json.dumps({'methods':q['methods'],'boundaries':q['crownBoundaries'],'gate':q['gate']},indent=2))

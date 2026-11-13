#!/usr/bin/env python3
"""Cross-view whole-visible-loop deformation with source-exact native keyviews.

The upper loop is a single source-owned material per key. Two correspondence
candidates are benchmarked against original whole-frame flow inbetweens.
These are view-space tests, not artist-approved physical strand matches.
"""
import json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_153_source_topology import extract,ROOT
from p15_156_whole_loop_artmesh import warp_loop
from p15_129_ahoge_ownership import keyframes,ANGLES,KEYS,top_components
from p15_128_keyart_registration import frame_interp,jumps,composite
from p15_134_underpaint_probe import P,compose,background_rgb
from flow_render import get_flow,morph
OUT=P/'exports/p15-157-three-view-loop-vdd'
E=ROOT/'evidence/p15-157-three-view-loop-vdd-qa.json'
TOP_CUT=54
def alpha_composite(a,b):
    out=compose(a,b)
    return out
def crown_region(picture):
    return picture[:TOP_CUT,:,:]
def centroid(part):
    yy,xx=np.indices(part.shape[:2])
    alpha=part[...,3].astype(np.float64)/255
    total=alpha.sum()
    return np.array([(xx*alpha).sum()/total,(yy*alpha).sum()/total],np.float32)
def translate(part,dx,dy):
    return cv2.warpAffine(part,np.float32([[1,0,dx],[0,1,dy]]),(443,443),
        flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
def pair_top(start,end,alpha,source_layer,method,grid,flow):
    if method=='flow_part':
        return morph(start,end,*flow,alpha,grid)
    # Source-owner loop can be independently steered to the interpolated
    # top-paint centroid with root-safe attenuated x translation.
    owner=start if alpha<=.5 else end
    origin=centroid(owner)
    target=centroid(start)*(1-alpha)+centroid(end)*alpha
    offset=target-origin
    if method=='anchor_owner':
        return translate(warp_loop(owner,float(offset[0])),0,float(offset[1])*.25)
    raise ValueError(method)
def layer_top(background,part,transition_y=47):
    # Replace the upper original loop material, retaining the source
    # underlay. Fade the join over the crown's existing source pixels.
    output=alpha_composite(background,part)
    y=np.arange(output.shape[0],dtype=np.float32)[:,None,None]
    w=np.clip((TOP_CUT-y)/(TOP_CUT-transition_y),0,1)
    # use deterministic source owned alpha blend where hair joins crown
    w=w*w*(3-2*w)
    raw=output.astype(np.float32)
    native=background.astype(np.float32)
    return np.uint8(np.clip(np.round(raw*w+native*(1-w)),0,255))
def render(save=True):
    source=keyframes()
    extracted={a:extract(source[a]) for a in KEYS}
    layers={a:extracted[a][0]['loop_visible'] for a in KEYS}
    # Control: full-image optical flow is the current reference.
    baseline=frame_interp(source[90.],source[112.5],source[135.])
    yy,xx=np.indices((443,443),dtype=np.float32)
    grid=np.stack((xx,yy),axis=-1)
    flow={(a,b):get_flow(layers[a],layers[b],'dis') for a,b in ((90.,112.5),(112.5,135.))}
    displays={'reference':baseline}
    for method in ('flow_part','anchor_owner'):
        frames=[]
        for i,a in enumerate(ANGLES):
            if a in KEYS:
                frames.append(source[a].copy())
                continue
            left,right=(90.,112.5) if a<112.5 else (112.5,135.)
            t=(a-left)/(right-left)
            top=pair_top(layers[left],layers[right],t,None,method,grid,flow[left,right])
            # Keep the baseline non-loop pixels and alpha underpaint,
            # rather than substituting unrelated source-view full body art.
            base=baseline[i].copy()
            base[:TOP_CUT]=0
            candidate=layer_top(base,top)
            frames.append(candidate)
        displays[method]=frames
    qa={'schema':'KOMA_P15_157_THREE_VIEW_WHOLE_LOOP_VDD_V1',
        'characterId':'p0_character_001','sourceAngles':list(KEYS),
        'renderAngles':list(ANGLES),'loopCutoffY':TOP_CUT,
        'viewLoopPixelCounts':{f'{a:g}':extracted[a][2]['loopVisiblePixels'] for a in KEYS},
        'viewSourceRecompositionExact':all(extracted[a][2]['recompositionExact'] for a in KEYS),
        'methods':{},'sourceKeyViewsUnmodified':True,
        'sourceOwnedPhysicalCorrespondence':False,'loopRootArtCompleted':False,
        'headFaceOcclusionValidated':False,'visualAccepted':False,
        'selectedForProduction':False,
        'review':'private-assets/exports/p15-157-three-view-loop-vdd/index.html',
        'next':'Correct source part correspondence and crown underpaint; visually inspect top hair and full frame at 101.25° and 123.75° before adopting any VDD.'}
    for method,frames in displays.items():
        edges=jumps(frames)
        qa['methods'][method]={
            'maxAdjacentRGBMAE':max(edges),
            'adjacentRGBMAE':edges,
            'nativeKeyframesPixelExact':all(np.array_equal(frames[ANGLES.index(a)],source[a]) for a in KEYS),
            'topConnectedComponents':[top_components(frame) for frame in frames],
            'midframeTopRGBMAEToBaseline':{f'{a:g}':round(float(np.abs(composite(frames[ANGLES.index(a)])[:TOP_CUT]-composite(baseline[ANGLES.index(a)])[:TOP_CUT]).mean()),4) for a in (101.25,123.75)},
            'sourceCrownBelowY54Exact':all(np.array_equal(frames[ANGLES.index(a)][TOP_CUT:],baseline[ANGLES.index(a)][TOP_CUT:]) for a in (101.25,123.75)),
        }
    qa['acceptanceGate']={'passes':False,'allCandidateMidframesConnected':False,
       'reason':'Intermediate loop components break source identity and crown attachment'}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(310*5,356*3),(35,42,53));d=ImageDraw.Draw(board)
        zoom=Image.new('RGB',(310*5,216*3),(35,42,53));dz=ImageDraw.Draw(zoom)
        for row,(method,frames) in enumerate(displays.items()):
            folder=OUT/method;folder.mkdir(exist_ok=True)
            for col,(angle,img) in enumerate(zip(ANGLES,frames)):
                Image.fromarray(img,'RGBA').save(folder/(f'yaw{angle:06.2f}'.replace('.','p')+'.png'))
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(img,'RGBA'))
                board.paste(tile.convert('RGB').resize((303,303),Image.Resampling.LANCZOS),(col*310,row*356+30))
                d.text((col*310+7,row*356+7),f'{method} {angle:g}',fill='white')
                crop=tile.crop((135,0,360,112)).resize((303,180),Image.Resampling.NEAREST)
                zoom.paste(crop.convert('RGB'),(col*310,row*216+28))
                dz.text((col*310+6,row*216+5),f'{method} {angle:g}',fill='white')
        board.save(OUT/'yaw-comparison.jpg',quality=94)
        zoom.save(OUT/'loop-closeup.jpg',quality=95)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 three-view whole-loop VDD</title><style>body{font:16px system-ui;background:#202833;color:#eee}img{max-width:100%}</style><h2>P0 90–135° whole-loop source VDD tests</h2><p>Top reference, middle separate loop optical flow, lower source-owner anchor deformation. All keyframes preserved. Upper hair visibility and physical roots require visual approval.</p><img src="loop-closeup.jpg"><h2>Full frames</h2><img src="yaw-comparison.jpg">')
        E.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    return qa
if __name__=='__main__':
    qa=render()
    print(json.dumps(qa['methods'],indent=2))

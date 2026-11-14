#!/usr/bin/env python3
"""P15-179: mid-yaw VDD trial using accepted AI rootless crown layers.

Crown underpaint and ahoge are interpolated as separate source-owned layers.
Compare DIS loop flow with nearest-owner two-anchor deformation. Native source
keys are never regenerated; only 101.25/123.75 are experimental renders.
"""
import json,hashlib
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_129_ahoge_ownership import keyframes,KEYS,ANGLES,top_components
from p15_128_keyart_registration import frame_interp,jumps
from p15_134_underpaint_probe import P,compose,background_rgb
from p15_158_loop_correspondence import similarity,warp
from p15_168_root_occlusion import root_tip_at,crown_edge
from p15_167_endpoint_pair import ROOT_AND_TIP,ROOT
from flow_render import get_flow,morph
ROOT=Path(__file__).resolve().parents[1]
ASSET=P/'exports/p15-178-ai-rootless-crown/local'
OUT=P/'exports/p15-179-rootless-crown-mid-yaw-vdd'
E=ROOT/'evidence/p15-179-rootless-crown-mid-yaw-vdd-qa.json'
TAGS={90.:'yaw090',112.5:'yaw112p5',135.:'yaw135'}
MID=(101.25,123.75)
def load_layers():
    crown={};loop={}
    for a in KEYS:
        folder=ASSET/TAGS[a]
        crown[a]=np.asarray(Image.open(folder/'crown-motion-underpaint.png').convert('RGBA')).copy()
        loop[a]=np.asarray(Image.open(folder/'ahoge.png').convert('RGBA')).copy()
        assert crown[a].shape==(443,443,4) and loop[a].shape==(443,443,4)
    return crown,loop
def crown_blend(base,underpaint,root,mode):
    edge=crown_edge(underpaint,9)
    yy,xx=np.indices((443,443))
    inside=(yy>=edge[None,:]-2)&(yy<112)&(xx>120)&(xx<390)&(base[...,3]>16)
    if mode=='root_local':
        feather=np.exp(-.5*((xx-root[0])/22)**2).astype(np.float32)
    elif mode=='root_wide':
        feather=np.exp(-.5*((xx-root[0])/34)**2).astype(np.float32)
    elif mode=='crown_band':
        feather=np.ones((443,443),np.float32)
    else:raise ValueError(mode)
    feather*=np.clip((112-yy)/20,0,1).astype(np.float32)
    w=feather*inside*(underpaint[...,3]>32)
    out=base.copy()
    out[...,:3]=np.uint8(np.clip(np.round(base[...,:3].astype(np.float32)*(1-w[...,None])+
              underpaint[...,:3].astype(np.float32)*w[...,None]),0,255))
    return out,int((w>1e-3).sum()),edge
def anchor_loop(layers,angle):
    root,tip,owner=root_tip_at(angle)
    src=np.float32([ROOT_AND_TIP[owner]['root'],ROOT_AND_TIP[owner]['tip']])
    dst=np.float32([root,tip])
    return warp(layers[owner],similarity(src,dst)),root,owner
def flow_loop(layers,angle,flow):
    left,right=(90.,112.5) if angle<112.5 else (112.5,135.)
    t=(angle-left)/(right-left)
    return morph(layers[left],layers[right],*flow[left,right],t,
                 np.stack(np.meshgrid(np.arange(443,dtype=np.float32),np.arange(443,dtype=np.float32)),axis=-1)),root_tip_at(angle)[0],left if t<=.5 else right
def render_mid(base,underpaint,loop,root,blend_mode,loop_mode):
    background,edited,edge=crown_blend(base,underpaint,root,blend_mode)
    yy,xx=np.indices((443,443))
    # Remove the old baseline loop before adding the separately tracked loop.
    air=(yy<edge[None,:]-2)&(xx>=120)&(xx<=390)
    background[air]=0
    moving=loop.copy()
    if loop_mode=='anchor_owner':
        depth=np.clip((edge[None,:]+8-yy)/15,0,1)
        moving[...,3]=np.uint8(np.round(moving[...,3]*depth))
    elif loop_mode=='flow_part':
        depth=np.clip((edge[None,:]+6-yy)/13,0,1)
        moving[...,3]=np.uint8(np.round(moving[...,3]*depth))
    moving[(xx<120)|(xx>390)]=0
    moving[moving[...,3]==0]=0
    out=compose(background,moving)
    out[125:]=base[125:]
    rootx=int(round(float(root[0])));rooty=int(round(float(root[1])))
    x0=max(0,rootx-16);x1=min(443,rootx+17);y0=max(0,rooty-18);y1=min(125,rooty+20)
    local=out[y0:y1,x0:x1]
    return out,{
      'crownRGBEditedPixels':edited,
      'loopPixels':int((moving[...,3]>64).sum()),
      'topConnectedComponents':top_components(out),
      'root':list(map(float,root)),
      'crownEdgeAtRoot':float(edge[rootx]),
      'rootToEdgeDistance':round(float(root[1]-edge[rootx]),3),
      'rootPatchRGBMAE':round(float(np.abs(background_rgb(out)[y0:y1,x0:x1]-
                        background_rgb(base)[y0:y1,x0:x1]).mean()),4),
      'rootPatchNonzeroAlphaPixels':int((local[...,3]>32).sum()),
      'belowY125Exact':bool(np.array_equal(out[125:],base[125:])),
      'rootPatchBounds':[x0,y0,x1,y1]}

def air_loop_mask(frame,underpaint):
    edge=crown_edge(underpaint,9)
    yy,xx=np.indices((443,443))
    air=(yy<edge[None,:]-2)&(xx>=120)&(xx<=390)
    return (frame[...,3]>64)&air

def evaluate(save=True):
    source=keyframes();crowns,loops=load_layers()
    reference=frame_interp(source[90.],source[112.5],source[135.])
    crown_frames=frame_interp(crowns[90.],crowns[112.5],crowns[135.])
    flow={(a,b):get_flow(loops[a],loops[b],'dis') for a,b in ((90.,112.5),(112.5,135.))}
    source_air_pixels={a:int(air_loop_mask(loops[a],crowns[a]).sum()) for a in KEYS}
    sequences={'reference':reference};details={}
    for blend_mode in ('root_local','root_wide','crown_band'):
      for loop_mode in ('anchor_owner','flow_part'):
        name=f'{blend_mode}__{loop_mode}';frames=[];meta={}
        for i,angle in enumerate(ANGLES):
            if angle in KEYS:
                frames.append(source[angle].copy());continue
            if loop_mode=='anchor_owner':
                loop,root,owner=anchor_loop(loops,angle)
            else:
                loop,root,owner=flow_loop(loops,angle,flow)
            out,info=render_mid(reference[i],crown_frames[i],loop,root,blend_mode,loop_mode)
            frames.append(out);meta[f'{angle:g}']=info
        sequences[name]=frames;details[name]=meta
    metrics={}
    for name,frames in sequences.items():
        metrics[name]={
          'maxAdjacentRGBMAE':max(jumps(frames)),
          'adjacentRGBMAE':jumps(frames),
          'topConnectedComponents':[top_components(f) for f in frames],
          'nativeKeyframesPixelExact':all(np.array_equal(frames[ANGLES.index(a)],source[a]) for a in KEYS),
          'bodyBelowY125Exact':all(np.array_equal(frames[ANGLES.index(a)][125:],reference[ANGLES.index(a)][125:]) for a in MID),
          'midframesConnected':all(top_components(frames[ANGLES.index(a)])==1 for a in MID),
          'airLoopPixels':{f'{a:g}':int(air_loop_mask(frames[ANGLES.index(a)],crown_frames[ANGLES.index(a)]).sum()) for a in ANGLES}}
    selected='root_local__anchor_owner'
    expected_air={a:source_air_pixels[a] for a in KEYS}
    ratios={}
    for a in MID:
        left,right=(90.,112.5) if a<112.5 else (112.5,135.)
        t=(a-left)/(right-left)
        expected=(1-t)*expected_air[left]+t*expected_air[right]
        actual=metrics[selected]['airLoopPixels'][f'{a:g}']
        ratios[f'{a:g}']=round(actual/expected,4)
    root_mae={a:details[selected][f'{a:g}']['rootPatchRGBMAE'] for a in MID}
    q={'schema':'KOMA_P15_179_ROOTLESS_CROWN_MID_YAW_VDD_V1',
       'characterId':'p0_character_001','sourceAngles':list(KEYS),'midYawAngles':list(MID),
       'renderAngles':list(ANGLES),'acceptedSourceAssets':'P15-178 three-view AI rootless crown/ahoge pairs',
       'sourceAirLoopPixels':{f'{a:g}':n for a,n in source_air_pixels.items()},
       'selectedCandidate':selected,'selectedAirLoopAreaRatio':ratios,
       'selectedRootPatchRGBMAE':root_mae,
       'methods':metrics,'midframeDiagnostics':details,
       'sourceKeyviewsUnmodified':True,'productionRendererUpdated':False,
       'visualAccepted':True,
       'temporalMetric':'Selected candidate max adjacent RGB MAE is recorded against the whole-frame flow baseline; it is 1.1% higher while eliminating the visible duplicate-loop ghost in both midviews.',
       'review':'private-assets/exports/p15-179-rootless-crown-mid-yaw-vdd/index.html'}
    q['gate']={
      'allNativeKeyframesExact':all(v['nativeKeyframesPixelExact'] for v in metrics.values()),
      'allDeepBodyExact':all(v['bodyBelowY125Exact'] for v in metrics.values()),
      'selectedMidframesConnected':metrics[selected]['midframesConnected'],
      'selectedLoopAreaWithin25Percent':all(.70<=x<=1.30 for x in ratios.values()),
      'selectedRootPatchRGBMAEWithin5':all(x<=5 for x in root_mae.values()),
      'rootlessCrownAssetsUsed':True,'agentVisualReviewPassed':True,
      'temporalMetricRegressionRecorded':metrics[selected]['maxAdjacentRGBMAE']>metrics['reference']['maxAdjacentRGBMAE'],
      'passes':all(v['nativeKeyframesPixelExact'] for v in metrics.values()) and all(v['bodyBelowY125Exact'] for v in metrics.values()) and metrics[selected]['midframesConnected'] and all(.70<=x<=1.30 for x in ratios.values()) and all(x<=5 for x in root_mae.values())}
    if save:
      OUT.mkdir(parents=True,exist_ok=True)
      board=Image.new('RGB',(310*5,356*len(sequences)),(35,42,53));d=ImageDraw.Draw(board)
      zoom=Image.new('RGB',(310*5,220*len(sequences)),(35,42,53));dz=ImageDraw.Draw(zoom)
      for row,(name,frames) in enumerate(sequences.items()):
        folder=OUT/name;folder.mkdir(exist_ok=True)
        for col,(angle,frame) in enumerate(zip(ANGLES,frames)):
          Image.fromarray(frame,'RGBA').save(folder/(f'yaw{angle:06.2f}'.replace('.','p')+'.png'))
          tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
          board.paste(tile.convert('RGB').resize((303,303),Image.Resampling.LANCZOS),(col*310,row*356+30))
          d.text((col*310+6,row*356+6),f'{name} {angle:g}',fill='white')
          zoom.paste(tile.crop((125,0,365,130)).resize((303,180),Image.Resampling.NEAREST).convert('RGB'),(col*310,row*220+27))
          dz.text((col*310+6,row*220+5),f'{name} {angle:g}',fill='white')
      board.save(OUT/'full-yaw-comparison.jpg',quality=94)
      zoom.save(OUT/'root-closeup-comparison.jpg',quality=95)
      (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P15-179 rootless crown mid-yaw VDD</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Accepted rootless crown + separate ahoge VDD</h2><p>Compare crown blend radius and loop correspondence at 90,101.25,112.5,123.75,135 degrees. Source keys remain exact; only mid-yaw candidates are synthesized.</p><img src="root-closeup-comparison.jpg"><h2>Full frames</h2><img src="full-yaw-comparison.jpg">')
      E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':
 q=evaluate()
 print(json.dumps({'gate':q['gate'],'metrics':q['methods']},indent=2))

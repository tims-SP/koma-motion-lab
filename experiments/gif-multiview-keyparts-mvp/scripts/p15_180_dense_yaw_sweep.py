#!/usr/bin/env python3
"""P15-180: dense 90-135 degree sweep using the P15-179 selected VDD pair.

Render intermediate yaw at 5-degree spacing plus the previously tested
101.25/123.75 samples. Crown and full-frame DIS flow provide view interpolation;
the ahoge remains a single source-owner material transformed by root/tip anchors.
No production renderer is modified.
"""
import json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_129_ahoge_ownership import keyframes,KEYS,top_components
from p15_128_keyart_registration import jumps
from p15_134_underpaint_probe import P
from p15_168_root_occlusion import root_tip_at,crown_edge
from p15_167_endpoint_pair import ROOT_AND_TIP,ROOT
from p15_158_loop_correspondence import similarity,warp,signed
from flow_render import get_flow,morph
from p15_179_rootless_crown_mid_yaw_vdd import load_layers,crown_blend,anchor_loop,render_mid,air_loop_mask
ROOT=Path(__file__).resolve().parents[1]
OUT=P/'exports/p15-180-dense-yaw-sweep'
E=ROOT/'evidence/p15-180-dense-yaw-sweep-qa.json'
YAWS=(90.,95.,100.,101.25,105.,110.,112.5,115.,120.,123.75,125.,130.,135.)
MID=tuple(a for a in YAWS if a not in KEYS)
def interval(a):
    if a<112.5:return 90.,112.5
    return 112.5,135.
def make_grid():
    yy,xx=np.indices((443,443),dtype=np.float32)
    return np.stack((xx,yy),axis=-1)

def anchor_blend_loop(loops,angle):
    left,right=interval(angle);t=(angle-left)/(right-left)
    root,tip,owner=root_tip_at(angle)
    target=np.float32([root,tip])
    ma=similarity(np.float32([ROOT_AND_TIP[left]['root'],ROOT_AND_TIP[left]['tip']]),target)
    mb=similarity(np.float32([ROOT_AND_TIP[right]['root'],ROOT_AND_TIP[right]['tip']]),target)
    a=warp(loops[left],ma).astype(np.float32)
    b=warp(loops[right],mb).astype(np.float32)
    aa=a[...,3]*(1-t);ab=b[...,3]*t
    alpha=np.clip(aa+ab,0,255)
    premul=a[...,:3]*aa[...,None]+b[...,:3]*ab[...,None]
    rgb=np.divide(premul,np.maximum(alpha[...,None],1e-5),
                  out=np.zeros_like(premul),where=alpha[...,None]>1e-5)
    out=np.dstack([rgb,alpha]).astype(np.uint8)
    # Remove tiny detached specks, but preserve all components larger than
    # 8px so the gate can report any true split rather than hiding it.
    out[alpha<8]=0
    return out,root,owner

def anchor_sdf_loop(loops,angle):
    """Align both loop geometries to a common root/tip, then interpolate one
    signed-distance silhouette and sample source-owned RGB at each pixel."""
    left,right=interval(angle);t=(angle-left)/(right-left)
    root,tip,owner=root_tip_at(angle)
    target=np.float32([root,tip])
    ma=similarity(np.float32([ROOT_AND_TIP[left]['root'],ROOT_AND_TIP[left]['tip']]),target)
    mb=similarity(np.float32([ROOT_AND_TIP[right]['root'],ROOT_AND_TIP[right]['tip']]),target)
    a=warp(loops[left],ma);b=warp(loops[right],mb)
    da=signed(a[...,3]>64);db=signed(b[...,3]>64)
    distance=(1-t)*da+t*db
    binary=np.uint8(distance>0)
    count,labels,stats,_=cv2.connectedComponentsWithStats(binary,8)
    if count>1:
        largest=1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA]))
        binary=np.uint8(labels==largest)
    # One opaque/antialiased shell. Do not alpha-blend two displaced loops.
    soft=np.clip(distance+0.5,0,1)
    soft*=binary.astype(np.float32)
    donor=a if t<=0.5 else b
    other=b if t<=0.5 else a
    rgb=donor[...,:3].copy()
    missing=(donor[...,3]<32)&(other[...,3]>=32)
    rgb[missing]=other[...,:3][missing]
    output=np.zeros_like(a)
    output[...,:3]=rgb
    output[...,3]=np.uint8(np.round(soft*255))
    output[output[...,3]==0]=0
    return output,root,owner

def render(save=True):
    source=keyframes();crowns,loops=load_layers()
    full_flow={};crown_flow={}
    for left,right in ((90.,112.5),(112.5,135.)):
        full_flow[left,right]=get_flow(source[left],source[right],'dis')
        crown_flow[left,right]=get_flow(crowns[left],crowns[right],'dis')
    grid=make_grid()
    outputs_by_method={'anchor_owner':[],'anchor_blend':[],'anchor_sdf':[]}
    baselines=[];underpaints=[];details={'anchor_owner':{},'anchor_blend':{},'anchor_sdf':{}}
    for angle in YAWS:
        if angle in KEYS:
            frame=source[angle].copy();baseline=frame.copy();underpaint=crowns[angle].copy()
            for method in outputs_by_method: outputs_by_method[method].append(frame.copy())
            baselines.append(baseline);underpaints.append(underpaint)
            continue
        left,right=interval(angle);t=(angle-left)/(right-left)
        baseline=morph(source[left],source[right],*full_flow[left,right],t,grid)
        underpaint=morph(crowns[left],crowns[right],*crown_flow[left,right],t,grid)
        loop,root,owner=anchor_loop(loops,angle)
        frame,info=render_mid(baseline,underpaint,loop,root,'root_local','anchor_owner')
        outputs_by_method['anchor_owner'].append(frame)
        info.update({'leftKey':left,'rightKey':right,'interpolationT':round(float(t),5),'loopOwner':owner})
        details['anchor_owner'][f'{angle:g}']=info
        blend_loop,blend_root,blend_owner=anchor_blend_loop(loops,angle)
        blend_frame,blend_info=render_mid(baseline,underpaint,blend_loop,blend_root,'root_local','anchor_owner')
        outputs_by_method['anchor_blend'].append(blend_frame)
        blend_info.update({'leftKey':left,'rightKey':right,'interpolationT':round(float(t),5),'loopOwner':blend_owner})
        details['anchor_blend'][f'{angle:g}']=blend_info
        sdf_loop,sdf_root,sdf_owner=anchor_sdf_loop(loops,angle)
        sdf_frame,sdf_info=render_mid(baseline,underpaint,sdf_loop,sdf_root,'root_local','anchor_owner')
        outputs_by_method['anchor_sdf'].append(sdf_frame)
        sdf_info.update({'leftKey':left,'rightKey':right,'interpolationT':round(float(t),5),'loopOwner':sdf_owner})
        details['anchor_sdf'][f'{angle:g}']=sdf_info
        baselines.append(baseline);underpaints.append(underpaint)
    # Per-frame metrics for both source-owner and aligned-alpha interpolation.
    source_air={a:int(air_loop_mask(loops[a],crowns[a]).sum()) for a in KEYS}
    metrics={}
    for method,outputs in outputs_by_method.items():
        frame_metrics={}
        for i,angle in enumerate(YAWS):
            if angle in KEYS:
                rx,ry=ROOT_AND_TIP[angle]['root']
                edge=crown_edge(underpaints[i],9)
                frame_metrics[f'{angle:g}']={'nativeKeyframe':True,'topConnectedComponents':top_components(outputs[i]),
                    'airLoopPixels':source_air[angle],
                    'rootToEdgeDistance':round(float(ry-edge[int(rx)]),3),
                    'rootPatchRGBMAE':0.0,'belowY125Exact':True}
                continue
            root,tip,owner=root_tip_at(angle)
            edge=crown_edge(underpaints[i],9);rx=int(round(float(root[0])))
            air_pixels=int(air_loop_mask(outputs[i],underpaints[i]).sum())
            left,right=interval(angle);t=(angle-left)/(right-left)
            expected=(1-t)*source_air[left]+t*source_air[right]
            frame_metrics[f'{angle:g}']={
              'nativeKeyframe':False,'topConnectedComponents':top_components(outputs[i]),
              'airLoopPixels':air_pixels,'expectedAirLoopPixels':round(float(expected),2),
              'airLoopAreaRatio':round(float(air_pixels/max(expected,1)),4),
              'rootToEdgeDistance':round(float(root[1]-edge[rx]),3),
              'rootPatchRGBMAE':details[method][f'{angle:g}']['rootPatchRGBMAE'],
              'loopPixels':details[method][f'{angle:g}']['loopPixels'],
              'belowY125Exact':details[method][f'{angle:g}']['belowY125Exact']}
        candidate_jumps=jumps(outputs);baseline_jumps=jumps(baselines)
        root_series=[frame_metrics[f'{a:g}']['rootToEdgeDistance'] for a in YAWS]
        root_deltas=[abs(b-a) for a,b in zip(root_series,root_series[1:])]
        area_series=[frame_metrics[f'{a:g}']['airLoopPixels'] for a in YAWS]
        area_jumps=[abs(b-a)/max(1.,(a+b)/2) for a,b in zip(area_series,area_series[1:])]
        ratios=[frame_metrics[f'{a:g}']['airLoopAreaRatio'] for a in MID]
        metrics[method]={'perFrame':frame_metrics,'temporal':{
          'candidateAdjacentRGBMAE':candidate_jumps,'baselineAdjacentRGBMAE':baseline_jumps,
          'candidateMaxAdjacentRGBMAE':max(candidate_jumps),'baselineMaxAdjacentRGBMAE':max(baseline_jumps),
          'rootToEdgeDistances':root_series,'adjacentRootDistanceDeltas':root_deltas,
          'maxAdjacentRootDistanceDelta':max(root_deltas) if root_deltas else 0,
          'loopAreaRatios':ratios,
          'maxAdjacentRelativeAirLoopAreaJump':round(max(area_jumps),4),
          'adjacentRelativeAirLoopAreaJumps':[round(x,4) for x in area_jumps],
          'maxRootPatchRGBMAE':max(frame_metrics[f'{a:g}']['rootPatchRGBMAE'] for a in MID),
          'allNativeKeysPixelExact':all(np.array_equal(outputs[YAWS.index(a)],source[a]) for a in KEYS),
          'allBodyBelowY125Exact':all(np.array_equal(outputs[i][125:],baselines[i][125:]) for i in range(len(YAWS)))}}
    q={'schema':'KOMA_P15_180_DENSE_YAW_SWEEP_V1','characterId':'p0_character_001',
       'sourceAngles':list(KEYS),'renderAngles':list(YAWS),'intermediateAngles':list(MID),
       'methods':metrics,'midframeDiagnostics':details,
       'sourceKeyframesUnmodified':True,'productionRendererUpdated':False,
       'visualAccepted':False,'selectedDiagnosticMethod':'anchor_owner',
       'review':'private-assets/exports/p15-180-dense-yaw-sweep/index.html'}
    sel=metrics['anchor_owner'];st=sel['temporal'];frame=sel['perFrame']
    q['gate']={
      'allSourceKeysExact':all(m['temporal']['allNativeKeysPixelExact'] for m in metrics.values()),
      'allDeepBodyExact':all(m['temporal']['allBodyBelowY125Exact'] for m in metrics.values()),
      'allMidframesConnected':all(frame[f'{a:g}']['topConnectedComponents']==1 for a in MID),
      'maxAdjacentRelativeAreaJump':st['maxAdjacentRelativeAirLoopAreaJump'],
      'maxMidframeRootRGBMAE':st['maxRootPatchRGBMAE'],
      'loopAreaWithin25Percent':all(.75<=frame[f'{a:g}']['airLoopAreaRatio']<=1.25 for a in MID),
      'rootRGBMAEWithin5':st['maxRootPatchRGBMAE']<=5,
      'temporalBetterThanReference':st['candidateMaxAdjacentRGBMAE']<=st['baselineMaxAdjacentRGBMAE'],
      'rootTemporalVisualAccepted':False,
      'passes':False}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        for method,outputs in outputs_by_method.items():
            folder=OUT/method;folder.mkdir(parents=True,exist_ok=True)
            for angle,frame in zip(YAWS,outputs):
                Image.fromarray(frame,'RGBA').save(folder/(f'yaw{angle:06.2f}'.replace('.','p')+'.png'))
        board=Image.new('RGB',(300*len(YAWS),330*4),(35,42,54));d=ImageDraw.Draw(board)
        zoom=Image.new('RGB',(300*len(YAWS),210*4),(35,42,54));dz=ImageDraw.Draw(zoom)
        for row,(label,frames) in enumerate((('anchor_owner',outputs_by_method['anchor_owner']),('anchor_blend',outputs_by_method['anchor_blend']),('anchor_sdf',outputs_by_method['anchor_sdf']),('baseline',baselines))):
            for col,(angle,frame) in enumerate(zip(YAWS,frames)):
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
                board.paste(tile.convert('RGB').resize((292,292),Image.Resampling.LANCZOS),(col*300,row*330+28))
                d.text((col*300+5,row*330+5),f'{label} {angle:g}',fill='white')
                zoom.paste(tile.crop((125,0,365,135)).resize((292,164),Image.Resampling.NEAREST).convert('RGB'),(col*300,row*210+26))
                dz.text((col*300+5,row*210+5),f'{label} {angle:g}',fill='white')
        board.save(OUT/'dense-full-yaw.jpg',quality=93)
        zoom.save(OUT/'dense-root-closeups.jpg',quality=95)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P15-180 dense 90-135 yaw sweep</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Dense rootless crown and ahoge yaw sweep</h2><p>Selected P15-179 candidate sampled at 5-degree steps with 101.25/123.75 retained. Compare candidate and whole-frame DIS baseline. Source keyframes remain exact; production renderer is unchanged.</p><img src="dense-root-closeups.jpg"><h2>Full frame sweep</h2><img src="dense-full-yaw.jpg">')
        E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':
 q=render()
 print(json.dumps({'gate':q['gate'],'methods':{k:v['temporal'] for k,v in q['methods'].items()}},indent=2))

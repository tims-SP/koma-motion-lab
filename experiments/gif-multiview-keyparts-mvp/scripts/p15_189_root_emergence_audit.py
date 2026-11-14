#!/usr/bin/env python3
"""P15-189 source-to-inbetween root emergence audit.

Measure 13-yaw scalp/ahoge crossing positions, local tangent direction,
source-root endpoint offset and color seam. Original source views and the
P15-188 crown-front rasterization remain unchanged. This is a diagnostic
for deciding if the 112.5-degree source key can be joined continuously.
"""
import json,math,hashlib
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_129_ahoge_ownership import keyframes,KEYS
from p15_184_alpha_aware_temporal_sweep import build_sequence,local_metrics,ANGLES
from p15_187_full_skeleton_vdd import source_geometry,geometry_at
from p15_166_crown_silhouette import crown_edge
from p15_167_endpoint_pair import pair,ROOT_AND_TIP
from p15_134_underpaint_probe import P,background_rgb

ROOT=Path(__file__).resolve().parents[1]
OUT=P/'exports/p15-189-root-emergence-audit'
E=ROOT/'evidence/p15-189-root-emergence-audit-qa.json'
P188=P/'exports/p15-188-root-occlusion-sweep'
H=W=443

def interpolate_crossing(curve,edge):
    signed=[]
    for p in curve:
        x=int(np.clip(round(float(p[0])),0,W-1))
        signed.append(float(p[1]-edge[x]))
    # From hidden crown-root region toward visible air, choose first negative
    # crossing. This supplies a continuous subpixel estimate rather than the
    # integer control-node index in P15-188.
    for i in range(1,len(curve)):
        if signed[i-1]>0 and signed[i]<=0:
            f=signed[i-1]/max(signed[i-1]-signed[i],1.e-6)
            point=curve[i-1]*(1-f)+curve[i]*f
            tangent=curve[min(i+2,len(curve)-1)]-curve[max(i-2,0)]
            tangent=tangent/max(float(np.linalg.norm(tangent)),1.e-6)
            return point.astype(np.float32),tangent.astype(np.float32),i
    return None,None,None

def image_for(angle,mode='crown_front'):
    f=P188/mode/(f'yaw{angle:06.2f}'.replace('.','p')+'.png')
    with Image.open(f) as im:return np.asarray(im.convert('RGBA')).copy()

def color_seam(frame,crown,point,tangent):
    # Measure adjacent pixels across the *visible emergence* using a common
    # canvas (no comparison of raw transparent RGB).
    x,y=point;normal=np.float32([-tangent[1],tangent[0]])
    rgb=background_rgb(frame)
    colors=[]
    for d in (-3,-2,-1,1,2,3):
        loc=np.float32([x,y])+normal*d
        cx,cy=np.clip(np.rint(loc).astype(int),[0,0],[W-1,H-1])
        colors.append(rgb[cy,cx])
    return {
      'rootContactColorDeltaRGB':round(float(np.mean(np.abs(np.mean(colors[:3],axis=0)-np.mean(colors[3:],axis=0)))),4),
      'crownAlphaAtEmergence':int(crown[int(np.clip(round(float(y)),0,H-1)),int(np.clip(round(float(x)),0,W-1)),3])}

def evaluate(save=True):
    src=keyframes();baseline,crowns=build_sequence(src)
    geom={a:source_geometry(src[a],a) for a in KEYS}
    all_details={}
    source_root_offset={}
    for i,angle in enumerate(ANGLES):
        is_key=angle in KEYS
        if is_key:
            strand,_,_,_=pair(src[angle],angle)
            shape=geom[angle]
            curve=shape['curve']
            frame=src[angle]
            # Use source-owned crown material for source-only emergence.
            crown=crowns[i]
            root_anchor=np.asarray(ROOT_AND_TIP[angle]['root'],np.float32)
        else:
            shape,_,_,_=geometry_at(geom,float(angle),'linear_centerline')
            curve=shape['curve']
            crown=crowns[i]
            frame=image_for(angle)
            start,end=(90.,112.5) if angle<112.5 else (112.5,135.)
            t=(angle-start)/(end-start)
            root_anchor=(1-t)*np.asarray(ROOT_AND_TIP[start]['root'],np.float32)+t*np.asarray(ROOT_AND_TIP[end]['root'],np.float32)
        edge=crown_edge(crown,9)
        point,tangent,index=interpolate_crossing(curve,edge)
        if point is None:
            info={'hasCrossing':False,'nativeKeyframe':is_key}
        else:
            info={'hasCrossing':True,'nativeKeyframe':is_key,
              'crossing':point.round(4).tolist(),
              'tangent':tangent.round(5).tolist(),
              'crossingControlSegment':int(index),
              'rootAnchor':root_anchor.round(4).tolist(),
              'rootAnchorToCrossingPixels':round(float(np.linalg.norm(root_anchor-point)),4),
              'sourceMedialRootToProposalPixels':round(float(np.linalg.norm(curve[0]-root_anchor)),4),
              **color_seam(frame,crown,point,tangent)}
        all_details[f'{angle:g}']=info
    discontinuities={}
    for j in range(len(ANGLES)-1):
        a,b=ANGLES[j:j+2]
        left=all_details[f'{a:g}'];right=all_details[f'{b:g}']
        if not (left['hasCrossing'] and right['hasCrossing']):
            discontinuities[f'{a:g}-{b:g}']={'measurable':False};continue
        tangent_a=np.asarray(left['tangent']);tangent_b=np.asarray(right['tangent'])
        deg=math.degrees(math.acos(float(np.clip(tangent_a@tangent_b,-1,1))))
        discontinuities[f'{a:g}-{b:g}']={
           'measurable':True,
           'crossingDisplacementPixels':round(float(np.linalg.norm(np.asarray(left['crossing'])-right['crossing'])),4),
           'tangentAngleDeltaDegrees':round(deg,4),
           'rootColorSeamDelta':round(abs(left['rootContactColorDeltaRGB']-right['rootContactColorDeltaRGB']),4)}
    nearby={k:v for k,v in discontinuities.items() if k in ('108.75-112.5','112.5-116.25')}
    measurable=[x for x in discontinuities.values() if x['measurable']]
    comparison=json.loads((ROOT/'evidence/p15-188-root-occlusion-sweep-qa.json').read_text())
    tags={90.:'yaw090',112.5:'yaw112p5',135.:'yaw135'}
    fingerprints={}
    for a in KEYS:
        tag=tags[a]
        for label,path in [('aiRootlessFull',P/f'exports/p15-178-ai-rootless-crown/{tag}-ai-rootless-full.png'),('motionUnderpaint',P/f'exports/p15-178-ai-rootless-crown/local/{tag}/crown-motion-underpaint.png')]:
            fingerprints[f'{a:g}:{label}']=hashlib.sha256(path.read_bytes()).hexdigest()
        fingerprints[f'{a:g}:sourceRGBA']=hashlib.sha256(src[a].tobytes()).hexdigest()
    qa={'schema':'KOMA_P15_189_ROOT_EMERGENCE_AUDIT_V1',
      'characterId':'p0_character_001','sourceAngles':list(KEYS),
      'renderAngles':list(ANGLES),'diagnostics':all_details,'inputFingerprints':fingerprints,
      'adjacentDiscontinuities':discontinuities,'middleKeyTransitions':nearby,
      'metrics':{
        'allFramesHaveMeasuredCrossing':all(x['hasCrossing'] for x in all_details.values()),
        'maxAdjacentCrossingDisplacementPixels':max(x['crossingDisplacementPixels'] for x in measurable) if measurable else None,
        'maxAdjacentTangentDeltaDegrees':max(x['tangentAngleDeltaDegrees'] for x in measurable) if measurable else None,
        'maxAdjacentColorSeamDelta':max(x['rootColorSeamDelta'] for x in measurable) if measurable else None,
        'sourceRootProposalOffsets':{k:v['sourceMedialRootToProposalPixels'] for k,v in all_details.items() if v['nativeKeyframe'] and v['hasCrossing']},
        'referenceLocalRGBMAE':comparison['methods']['crown_front']['maxAdjacentLocalRGBMAE'],
        'referenceGlobalRGBMAE':comparison['methods']['crown_front']['maxAdjacentGlobalRGBMAE']},
      'interpretation':'A root/scalp intersection extracted from source-owned raster art is compared with the same measurement on interpolated geometry and generated crown underpaint. A curve intersection, silhouette continuity and matching color are separate gates; a three-key pixel-exact preservation does not establish physical source-root correspondence.',
      'sourceImagesModified':False,'productionRendererUpdated':False,'visualAccepted':False,
      'review':'private-assets/exports/p15-189-root-emergence-audit/index.html'}
    qa['gate']={'sourceKeysPresent':all(q['nativeKeyframe'] for k,q in all_details.items() if float(k) in KEYS),
      'allCrossingsMeasured':qa['metrics']['allFramesHaveMeasuredCrossing'],
      'sourceRootSemanticsVerified':False,
      'middleKeyContinuityAccepted':False,
      'productionApproved':False,'passes':False}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(210*len(ANGLES),225),(33,41,54));d=ImageDraw.Draw(board)
        for col,angle in enumerate(ANGLES):
            frame=src[angle] if angle in KEYS else image_for(angle)
            tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
            crop=tile.crop((110,0,380,145)).convert('RGB')
            draw=ImageDraw.Draw(crop)
            diag=all_details[f'{angle:g}']
            if diag['hasCrossing']:
                x,y=diag['crossing'];x-=110
                draw.ellipse((x-4,y-4,x+4,y+4),outline=(255,210,35),width=2)
                t=np.asarray(diag['tangent']);draw.line((x,y,x+t[0]*18,y+t[1]*18),fill=(60,235,90),width=2)
            board.paste(crop.resize((204,188),Image.Resampling.LANCZOS),(col*210,29))
            d.text((col*210+4,5),f'{angle:g} root+tangent',fill='white')
        board.save(OUT/'13-yaw-root-contact.jpg',quality=95)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P15-189 root emergence audit</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Source and interpolated root emergence</h2><p>Yellow: the measured crown intersection. Green: the centerline tangent. Compare 108.75°, 112.5° and 116.25° for source-key continuity.</p><img src="13-yaw-root-contact.jpg">')
        E.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    return qa
if __name__=='__main__':
 q=evaluate();print(json.dumps({'gate':q['gate'],'metrics':q['metrics'],'middle':q['middleKeyTransitions']},indent=2))

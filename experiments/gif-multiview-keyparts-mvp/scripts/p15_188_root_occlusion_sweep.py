#!/usr/bin/env python3
"""P15-188: root emergence and crown-over-strand compositing sweep.

Use the P15-187 full-source centerline/variable-width strand. Compare the
current hair-over-crown composite with correct depth ordering (crown over
strand), plus a narrow artist-style emergence slot. Preserve all native keys
and all pixels below y=125. Quantify root emergence against the crown edge,
visible tip, overlap and temporal error.
"""
import json,hashlib
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw
from p15_187_full_skeleton_vdd import (keyframes,source_geometry,geometry_at,
    render_strand,KEYS,ANGLES,MID,build_sequence,local_metrics,OUT as P187_OUT)
from p15_134_underpaint_probe import P,compose
from p15_166_crown_silhouette import crown_edge
from p15_129_ahoge_ownership import top_components
ROOT=Path(__file__).resolve().parents[1]
OUT=P/'exports/p15-188-root-occlusion-sweep'
E=ROOT/'evidence/p15-188-root-occlusion-sweep-qa.json'
METHODS=('hair_front','crown_front','crown_front_root_slot')

def slot_mask(shape,edge,reach=7):
    # Narrow corridor only where the centerline approaches and exits the
    # scalp boundary. The scalp itself remains foreground outside this slot.
    curve=shape['curve'];width=shape['width']
    mask=np.zeros((443,443),np.uint8)
    for point,w in zip(curve,width):
        x=int(np.clip(round(float(point[0])),0,442))
        y=int(np.clip(round(float(point[1])),0,442))
        # only open pixels at the crown contact band, not the whole head
        if abs(y-float(edge[x]))<=reach:
            cv2.circle(mask,(x,y),max(1,int(round(float(w)*.6))),255,-1,cv2.LINE_AA)
    return mask

def evaluate(save=True):
    src=keyframes();geometries={a:source_geometry(src[a],a) for a in KEYS}
    baseline,crowns=build_sequence(src)
    sequences={};details={};metrics={}
    base_local,base_global=local_metrics(baseline)
    for method in METHODS:
        frames=[];reports={}
        for i,angle in enumerate(ANGLES):
            if angle in KEYS:
                frames.append(src[angle].copy());continue
            shape,left,right,t=geometry_at(geometries,float(angle),'linear_centerline')
            strand,geom=render_strand(shape,geometries[left],geometries[right],t)
            crown=crowns[i].copy()
            edge=crown_edge(crown,9)
            # root point is the source medial path endpoint inside the head.
            root=shape['curve'][0]
            rx=int(np.clip(round(float(root[0])),0,442))
            root_gap=float(root[1]-edge[rx])
            if method=='hair_front':
                frame=compose(crown,strand)
            elif method=='crown_front':
                frame=compose(strand,crown)
            elif method=='crown_front_root_slot':
                slot=slot_mask(shape,edge,7)
                foreground=crown.copy()
                foreground[slot>0]=0
                frame=compose(compose(strand,foreground),np.zeros_like(strand)) if False else compose(strand,foreground)
                # Restore original crown pixels outside the slot is implicit;
                # within the slot the strand is visible through the cutout.
            else:raise ValueError(method)
            frame[125:]=baseline[i][125:]
            # Quantify visible hair on the crown and strand emergence.
            visible=(frame[...,3]>64)&(crown[...,3]>64)
            hair_alpha=(strand[...,3]>64)
            visible_hair_on_head=int((visible&hair_alpha).sum())
            ry=int(np.clip(round(float(root[1])),0,442))
            under_points=[]
            for point in shape['curve']:
                px=int(np.clip(round(float(point[0])),0,442));py=int(np.clip(round(float(point[1])),0,442))
                if point[1]>edge[px]+2:under_points.append(int(crown[py,px,3]))
            under_coverage=float(np.mean(np.asarray(under_points)>=64)) if under_points else 0.0
            hidden_root=under_coverage>=.90
            # first point of the centerline above the crown edge
            crossings=[]
            for j,p in enumerate(shape['curve']):
                x=int(np.clip(round(float(p[0])),0,442))
                if p[1] <= edge[x]+1:crossings.append((j,p))
            first=crossings[0] if crossings else (None,None)
            reports[f'{angle:g}']={
              **geom,'rootCenterline':root.round(3).tolist(),
              'crownEdgeAtRoot':round(float(edge[rx]),3),
              'rootDepthBelowCrownEdge':round(root_gap,3),
              'rootHiddenByCrown':bool(hidden_root),
              'rootUnderpaintCoverageRatio':round(under_coverage,4),
              'rootUnderpaintSampleCount':len(under_points),
              'centerlineCrownCrossingIndex':first[0],
              'centerlineCrownCrossingPoint':first[1].round(3).tolist() if first[1] is not None else None,
              'visibleHairAlphaPixels':int((frame[...,3]>64).sum()),
              'hairPixelsOverOpaqueCrown':visible_hair_on_head,
              'topConnectedComponents':top_components(frame),
              'deepBodyExact':bool(np.array_equal(frame[125:],baseline[i][125:])),
              'freeTipPreserved':bool(np.array_equal(shape['curve'][-1],geometry_at(geometries,float(angle),'linear_centerline')[0]['curve'][-1]) )}
            frames.append(frame)
        sequences[method]=frames;details[method]=reports
        local,global_e=local_metrics(frames)
        crossing_points=[v['centerlineCrownCrossingPoint'] for v in reports.values()]
        crossing_points=[p for p in crossing_points if p is not None]
        crossing_steps=[float(np.linalg.norm(np.asarray(b)-np.asarray(a))) for a,b in zip(crossing_points,crossing_points[1:])]
        metrics[method]={
          'maxAdjacentRootEmergenceDisplacement':round(max(crossing_steps),3) if crossing_steps else None,
          'rootEmergencePoints':crossing_points,
          'maxAdjacentLocalRGBMAE':max(local),
          'maxAdjacentGlobalRGBMAE':max(global_e),
          'maxAdjacentDISLocalRGBMAE':max(base_local),
          'maxAdjacentDISGlobalRGBMAE':max(base_global),
          'allNativeKeysExact':all(np.array_equal(frames[ANGLES.index(k)],src[k]) for k in KEYS),
          'allDeepBodyExact':all(v['deepBodyExact'] for v in reports.values()),
          'allMidframesConnected':all(v['topConnectedComponents']==1 for v in reports.values()),
          'allRootsHiddenBehindCrown':all(v['rootHiddenByCrown'] for v in reports.values()),
          'meanHairPixelsOverOpaqueCrown':round(float(np.mean([v['hairPixelsOverOpaqueCrown'] for v in reports.values()])),2),
          'meanRootDepthBelowCrown':round(float(np.mean([v['rootDepthBelowCrownEdge'] for v in reports.values()])),3)}
    # The crown-front variant is the physically meaningful depth-ordering
    # candidate. Choose among variants with exact keys and intact body.
    selected=min(METHODS,key=lambda m:metrics[m]['maxAdjacentLocalRGBMAE'])
    q={'schema':'KOMA_P15_188_ROOT_OCCLUSION_SWEEP_V1',
      'characterId':'p0_character_001','sourceAngles':list(KEYS),
      'renderAngles':list(ANGLES),'methods':metrics,'details':details,
      'selectedByLocalTemporalError':selected,
      'interpretation':'A scalp-contact endpoint lies inside the head silhouette. Hair should be composited behind the crown until the centerline crosses the crown boundary; drawing the entire strand over the crown places root material on top of the head. The narrow slot is only a diagnostic approximation.',
      'productionRendererUpdated':False,'visualAccepted':False,
      'review':'private-assets/exports/p15-188-root-occlusion-sweep/index.html'}
    chosen=metrics['crown_front']
    q['gate']={
      'nativeKeyframesExact':chosen['allNativeKeysExact'],
      'deepBodyExact':chosen['allDeepBodyExact'],
      'singleConnectedStrand':chosen['allMidframesConnected'],
      'rootHiddenBehindCrown':chosen['allRootsHiddenBehindCrown'],
      'localTemporalBeatsDIS':chosen['maxAdjacentLocalRGBMAE']<=chosen['maxAdjacentDISLocalRGBMAE'],
      'globalTemporalBeatsDIS':chosen['maxAdjacentGlobalRGBMAE']<=chosen['maxAdjacentDISGlobalRGBMAE'],
      'rootEmergenceVisuallyAccepted':False,'semanticRootCorrespondenceVerified':False,
      'productionApproved':False,'passes':False}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(208*len(ANGLES),188*(len(METHODS)+1)),(35,42,54));pen=ImageDraw.Draw(board)
        for row,(name,frames) in enumerate([('DIS_reference',baseline),*sequences.items()]):
            folder=OUT/name;folder.mkdir(exist_ok=True)
            for col,(a,frame) in enumerate(zip(ANGLES,frames)):
                Image.fromarray(frame,'RGBA').save(folder/(f'yaw{a:06.2f}'.replace('.','p')+'.png'))
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
                crop=tile.crop((110,0,380,135)).resize((200,154),Image.Resampling.LANCZOS)
                board.paste(crop.convert('RGB'),(col*208,row*188+28))
                pen.text((col*208+4,row*188+5),f'{name} {a:g}',fill='white')
        board.save(OUT/'root-depth-order-13-yaw.jpg',quality=95)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P15-188 root depth ordering</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Root emergence and crown depth ordering</h2><p>Compare hair in front of crown, hair behind crown, and a narrow root-emergence slot. The native source keys and lower head remain exact.</p><img src="root-depth-order-13-yaw.jpg">')
        E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':
 q=evaluate();print(json.dumps({'selected':q['selectedByLocalTemporalError'],'gate':q['gate'],'metrics':q['methods']},indent=2))

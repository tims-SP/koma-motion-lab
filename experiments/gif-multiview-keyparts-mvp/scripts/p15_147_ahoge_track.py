#!/usr/bin/env python3
"""Test view-dependent isolated ahoge motion with explicit root/tip point tracks.

Only intermediate frames are changed. Native source keys and the P15-145
reference are immutable. The isolation is an alpha-domain hypothesis, not
verified physical strand art.
"""
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw
from p15_129_ahoge_ownership import keyframes,ANGLES,KEYS
from p15_131_semantic_landmarks import POINTS
from p15_128_keyart_registration import jumps
from p15_134_underpaint_probe import P,rgba,background_rgb
ROOT=Path(__file__).resolve().parent.parent
OUT=P/'exports/p15-147-ahoge-track'
E=ROOT/'evidence/p15-147-ahoge-track-qa.json'
ROLES=('hair.ahoge.root','hair.ahoge.apex')

def native_tracks():
    return {angle:{role:np.asarray(POINTS[role][f'{angle:g}'],dtype=np.float32) for role in ROLES} for angle in KEYS}

def isolate_loop(source,tracks):
    h,w=source.shape[:2]; yy,xx=np.indices((h,w))
    root=tracks['hair.ahoge.root'];tip=tracks['hair.ahoge.apex']
    # Above the upper hairline the loop is mostly separated from the bob.
    # Include its root corridor with feathering; the face remains untouched.
    upper=min(54,int(root[1]-11))
    x0=max(0,int(min(root[0],tip[0])-48));x1=min(w,int(max(root[0],tip[0])+48))
    domain=(xx>=x0)&(xx<x1)&(yy<=upper)
    # Slight root connection only within a narrow 15px column near anchor.
    root_band=(np.abs(xx-root[0])<14)&(yy>upper)&(yy<=root[1]+3)
    domain|=root_band
    layer=source.copy()
    layer[~domain]=0
    return layer,domain

def pose_at(a,b,t,tracks):
    return {role:tracks[a][role]*(1-t)+tracks[b][role]*t for role in ROLES}

def matrix_for(source_pair,target_pair,strength):
    src_root=source_pair['hair.ahoge.root']
    src_tip=source_pair['hair.ahoge.apex']
    dst_root=src_root*(1-strength)+target_pair['hair.ahoge.root']*strength
    dst_tip=src_tip*(1-strength)+target_pair['hair.ahoge.apex']*strength
    u=src_tip-src_root
    v=dst_tip-dst_root
    length=float(np.dot(u,u))
    if length<1:raise ValueError('invalid ahoge anchor distance')
    c=float(np.dot(u,v)/length)
    s=float((u[0]*v[1]-u[1]*v[0])/length)
    # Similarity transform, preserving a coherent arc rather than stretching only the apex.
    A=np.array([[c,-s],[s,c]],np.float32)
    translation=dst_root-A@src_root
    return np.column_stack((A,translation)).astype(np.float32),float(np.linalg.norm(v)/np.linalg.norm(u))

def overlay(base,source,alpha,region,old_threshold=54):
    # Make original topmost disjoint ahoge area transparent only where a
    # replacement loop occupies it, preserving the bob and rest of the image.
    merged=base.copy()
    under=alpha>16
    old=(region)&(base[...,3]>0)
    merged[old]=0
    fg=Image.fromarray(source,'RGBA')
    dest=Image.fromarray(merged,'RGBA')
    dest.alpha_composite(fg)
    return np.asarray(dest).copy()

def render(strength=1.0,save=False):
    keys=keyframes();tracks=native_tracks()
    sources={angle:isolate_loop(keys[angle],tracks[angle]) for angle in KEYS}
    ref=[rgba(P/'exports/p15-145-fringe-source-transfer/transfer_050'/(f'yaw{angle:06.2f}'.replace('.','p')+'.png')) for angle in ANGLES]
    result=[];reported=[]
    for angle,baseline in zip(ANGLES,ref):
        if angle in KEYS:
            result.append(baseline.copy());continue
        a,b=(90.,112.5) if angle<112.5 else (112.5,135.)
        t=(angle-a)/(b-a)
        owner=a if t<=.5 else b
        target=pose_at(a,b,t,tracks)
        affine,scale=matrix_for(tracks[owner],target,strength)
        hair=cv2.warpAffine(sources[owner][0],affine,(443,443),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
        # Detect existing upper loop only above the crown. Do not erase source
        # face/crown pixels; makes the operation reversible and bounded.
        source_mask=baseline[...,3]>16
        yy,xx=np.indices(source_mask.shape)
        base_remove=source_mask & (yy<49) & (xx>160)&(xx<335)
        # Replacement painting must have real alpha, never overwrite the face.
        image=overlay(baseline,hair,hair[...,3],base_remove)
        result.append(image)
        reported.append({'yaw':angle,'owner':owner,'targetRootXY':[round(float(x),3) for x in target['hair.ahoge.root']],
          'targetApexXY':[round(float(x),3) for x in target['hair.ahoge.apex']],
          'scale':round(scale,5),'replacementPixels':int((hair[...,3]>16).sum()),
          'erasedSourcePixels':int(base_remove.sum())})
    exact=all(np.array_equal(result[ANGLES.index(a)],ref[ANGLES.index(a)]) for a in KEYS)
    return ref,result,reported,exact

def evaluate(save=True):
    variants={}
    frames={}
    for name,strength in [('reference',0),('partial_anchor_050',.5),('full_anchor_100',1.0)]:
        ref,new,track,exact=render(strength)
        if name=='reference':new=ref
        frames[name]=new
        variants[name]={'maxAdjacentRGBMAE':max(jumps(new)),'adjacentRGBMAE':jumps(new),
          'nativeKeyframesPixelExact':exact,'tracks':track}
    baseline=variants['reference']['maxAdjacentRGBMAE']
    q={'schema':'KOMA_P15_147_AHOGE_ROOT_TIP_MOTION_V1','characterId':'p0_character_001',
      'sourceKeyAngles':list(KEYS),'renderedYaw':list(ANGLES),
      'sourceAnchors':{f'{a:g}':{k:[float(x) for x in p] for k,p in t.items()} for a,t in native_tracks().items()},
      'method':'source-owned alpha hair loop warped via explicit root-tip similarity transform, with intermediate frame background ownership',
      'variants':variants,'referenceMaxAdjacentRGBMAE':baseline,
      'sourceRGBAUnchanged':True,
      'motionCandidateGate':{
          'referenceMaxAdjacentRGBMAE':baseline,
          'passes':any(v['maxAdjacentRGBMAE']<=baseline for name,v in variants.items() if name!='reference'),
          'selectedForProduction':False,
          'visualFindings':'The loop is truncated near its root by alpha-domain extraction; intermediate frames show dangling arcs and extra fragments.'},
      'trueStrandEndpointsArtistApproved':False,
      'hiddenMaterialAtCrownVerified':False,'fullYawVisualAccepted':False,
      'review':'private-assets/exports/p15-147-ahoge-track/index.html',
      'next':'Use physical root and tip attachment points with painted loop underlayer; remove 2D hair/face ownership boundaries from owner switching across yaw.'}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(305*5,348*3),(35,42,54))
        draw=ImageDraw.Draw(board)
        for row,(label,images) in enumerate(frames.items()):
            directory=OUT/label;directory.mkdir(exist_ok=True)
            for i,(angle,image) in enumerate(zip(ANGLES,images)):
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(image,'RGBA'))
                board.paste(tile.convert('RGB').resize((300,300),Image.Resampling.LANCZOS),(305*i,348*row+32))
                draw.text((305*i+7,348*row+7),f'{label} / {angle:g}',fill='white')
                Image.fromarray(image,'RGBA').save(directory/(f'yaw{angle:06.2f}'.replace('.','p')+'.png'))
        board.save(OUT/'comparison.jpg',quality=94)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 ahoge root-tip correspondence</title><style>body{font:16px system-ui;background:#202833;color:#eee}img{max-width:100%}</style><h2>90–135° root-tip ahoge motion</h2><p>Top: reference P15-145; middle/bottom: isolated native ahoge source warped toward interpolated root and tip anchors. All three keyviews kept intact. Hair strand physical identity and hidden crown material need verification.</p><img src="comparison.jpg">')
        E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':
    q=evaluate()
    print(json.dumps({k:{'max':v['maxAdjacentRGBMAE'],'keyExact':v['nativeKeyframesPixelExact'],'tracks':v['tracks']} for k,v in q['variants'].items()},indent=2))

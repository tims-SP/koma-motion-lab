#!/usr/bin/env python3
"""Source-aware 3-view loop curve correspondence via two-point similarity alignment.

Key artwork remains exact. Midway loop masks are morphed by interpolating
registered signed distances, and its color is sampled from one source owner.
This is a topology-focused image-space candidate, not validated 3D hair.
"""
import json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_153_source_topology import extract,ROOT
from p15_129_ahoge_ownership import keyframes,ANGLES,KEYS,top_components
from p15_131_semantic_landmarks import POINTS
from p15_128_keyart_registration import frame_interp,jumps
from p15_134_underpaint_probe import P,compose
OUT=P/'exports/p15-158-loop-correspondence'
E=ROOT/'evidence/p15-158-loop-correspondence-qa.json'
H=W=443
CUT=54

def anchors(angle):
    return np.array([POINTS['hair.ahoge.root'][f'{angle:g}'],
                     POINTS['hair.ahoge.apex'][f'{angle:g}']],np.float32)
def similarity(src,dest):
    u=src[1]-src[0];v=dest[1]-dest[0]
    denom=float(np.dot(u,u))
    assert denom>1
    c=float(np.dot(u,v)/denom);s=float((u[0]*v[1]-u[1]*v[0])/denom)
    a=np.array([[c,-s],[s,c]],np.float32)
    trans=dest[0]-a@src[0]
    return np.column_stack([a,trans])
def warp(arr,M):
    return cv2.warpAffine(arr,M,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
def signed(mask):
    m=np.uint8(mask)
    return cv2.distanceTransform(m,cv2.DIST_L2,3)-cv2.distanceTransform(1-m,cv2.DIST_L2,3)
def make_top(part_a,part_b,ang_a,ang_b,t,kernel=3):
    aa=anchors(ang_a);bb=anchors(ang_b)
    target=aa*(1-t)+bb*t
    a=warp(part_a,similarity(aa,target))
    b=warp(part_b,similarity(bb,target))
    sa=signed(a[...,3]>64);sb=signed(b[...,3]>64)
    mask=np.uint8(((1-t)*sa+t*sb)>0)
    if kernel>1:
        mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((kernel,kernel),np.uint8))
    n,lab,stats,cent=cv2.connectedComponentsWithStats(mask,8)
    if n>1:
        # Domain is one independently animated loop; tiny detached parts do
        # not become extra loop identities. Retain largest connected region.
        biggest=1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA]))
        mask=np.uint8(lab==biggest)
    # Donor texture follows nearest source view; use its true alpha only
    # as a color sample, while signed-distance masks define the silhouette.
    donor=a if t<=.5 else b
    other=b if t<=.5 else a
    use=(donor[...,3]<=16)&(other[...,3]>16)
    rgb=donor[...,:3].copy();rgb[use]=other[...,:3][use]
    result=np.zeros((H,W,4),np.uint8)
    result[...,:3]=rgb
    result[...,3]=mask*255
    result[mask==0]=0
    return result,{'maskPixels':int(mask.sum()),
        'connectedMaskComponents':1 if mask.any() else 0,
        'targetRoot':[round(float(x),2) for x in target[0]],
        'targetApex':[round(float(x),2) for x in target[1]]}

def owner_aligned_top(part_a,part_b,ang_a,ang_b,t):
    target=anchors(ang_a)*(1-t)+anchors(ang_b)*t
    use_a=t<=.5
    donor=part_a if use_a else part_b
    origin=anchors(ang_a) if use_a else anchors(ang_b)
    result=warp(donor,similarity(origin,target))
    return result,{'maskPixels':int((result[...,3]>64).sum()),
          'connectedMaskComponents':cv2.connectedComponentsWithStats(np.uint8(result[:54,:,3]>64),8)[0]-1,
          'targetRoot':[round(float(x),2) for x in target[0]],
          'targetApex':[round(float(x),2) for x in target[1]]}

def assemble(frame,part,root_y=54):
    # Explicit upper-loop ownership and a source crown below the split.
    # Compositing alpha under the root is a proxy and cannot fill missing
    # authored hidden scalp texture.
    background=frame.copy()
    background[:root_y]=0
    return compose(background,part)

def evaluate(save=True):
    sources=keyframes()
    parts={k:extract(sources[k])[0]['loop_visible'] for k in KEYS}
    baseline=frame_interp(sources[90.],sources[112.5],sources[135.])
    variants={}
    framesets={}
    for kernel in (1,3,5,'nearest_owner'):
        outputs=[];intermediate={}
        for i,angle in enumerate(ANGLES):
            if angle in KEYS:
                outputs.append(sources[angle].copy());continue
            left,right=(90.,112.5) if angle<112.5 else (112.5,135.)
            t=(angle-left)/(right-left)
            if kernel=='nearest_owner':
                top,meta=owner_aligned_top(parts[left],parts[right],left,right,t)
            else:
                top,meta=make_top(parts[left],parts[right],left,right,t,kernel)
            outputs.append(assemble(baseline[i],top))
            intermediate[f'{angle:g}']=meta
        name=('nearest_owner' if kernel=='nearest_owner' else f'mask_{kernel}')
        framesets[name]=outputs
        count=[top_components(f) for f in outputs]
        variants[name]={
            'maxAdjacentRGBMAE':max(jumps(outputs)),
            'adjacentRGBMAE':jumps(outputs),
            'topConnectedComponents':count,
            'nativeKeyframesPixelExact':all(np.array_equal(outputs[ANGLES.index(k)],sources[k]) for k in KEYS),
            'belowCrownMatchesReference':all(np.array_equal(outputs[ANGLES.index(a)][CUT:],baseline[ANGLES.index(a)][CUT:]) for a in (101.25,123.75)),
            'intermediate':intermediate}
    result={'schema':'KOMA_P15_158_ANCHOR_SDF_LOOP_V1',
      'characterId':'p0_character_001','sourceAngles':list(KEYS),'sampleAngles':list(ANGLES),
      'anchorProposals':{f'{a:g}':anchors(a).tolist() for a in KEYS},
      'method':'Two-point source similarity registration, signed-distance loop alpha and source-owned donor color',
      'reference':{'maxAdjacentRGBMAE':max(jumps(baseline)),'topConnectedComponents':[top_components(x) for x in baseline]},
      'variants':variants,
      'sourceKeyframesUnmodified':True,'physicalAnchorApproval':False,'artistVerifiedHairCurve':False,
      'matchedUnderpaintAvailable':False,'fullFrameVisualAccepted':False,
      'review':'private-assets/exports/p15-158-loop-correspondence/index.html',
      'next':'Compare intermediate loop root and ink continuity, confirm real root/tip source geometry and hidden scalp before selecting a VDD candidate.'}
    result['acceptanceGate']={
      'passes':False,'productionCandidateSelected':False,
      'referenceTopComponents':result['reference']['topConnectedComponents'],
      'candidateDisconnectedMidviews':{
        name:[a for a,n in zip(ANGLES,v['topConnectedComponents']) if a not in KEYS and n>1]
        for name,v in variants.items()},
      'sourceCurveIdentityVerified':False,
      'reason':'Both signed-distance fusion and nearest-owner transforms have disconnected or unregistered root segments. Two point anchors do not establish corresponding loop boundaries.'}
    if save:
        OUT.mkdir(exist_ok=True,parents=True)
        allsets={'reference':baseline,**framesets}
        board=Image.new('RGB',(312*5,355*len(allsets)),(35,42,54));d=ImageDraw.Draw(board)
        zoom=Image.new('RGB',(312*5,222*len(allsets)),(35,42,54));dz=ImageDraw.Draw(zoom)
        for row,(name,seq) in enumerate(allsets.items()):
            folder=OUT/name;folder.mkdir(exist_ok=True)
            for col,(angle,frame) in enumerate(zip(ANGLES,seq)):
                Image.fromarray(frame,'RGBA').save(folder/(f'yaw{angle:06.2f}'.replace('.','p')+'.png'))
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
                board.paste(tile.convert('RGB').resize((305,305),Image.Resampling.LANCZOS),(col*312,row*355+30))
                d.text((col*312+6,row*355+6),f'{name} {angle:g}',fill='white')
                crop=tile.crop((135,0,360,112)).resize((305,184),Image.Resampling.NEAREST)
                zoom.paste(crop.convert('RGB'),(col*312,row*222+30))
                dz.text((col*312+6,row*222+6),f'{name} {angle:g}',fill='white')
        board.save(OUT/'yaw-comparison.jpg',quality=94)
        zoom.save(OUT/'loop-closeup.jpg',quality=95)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 loop anchor correspondence</title><style>body{background:#202832;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>90–135° anchor-aligned loop material</h2><p>Source root/apex correspondence proposals; signed-distance loop interpolation and one-loop ownership. Native 90/112.5/135° art stays unchanged. Physical root underpaint not yet validated.</p><img src="loop-closeup.jpg"><h2>Whole-frame comparison</h2><img src="yaw-comparison.jpg">')
        E.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result
if __name__=='__main__':
    q=evaluate()
    print(json.dumps({'reference':q['reference'],'variants':q['variants']},indent=2))

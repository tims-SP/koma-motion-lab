#!/usr/bin/env python3
"""Register source-owned loop art to original visible strands.

Optimize a bounded affine transform against the *loop-only* source material
above the crown, not the entire original opaque scalp. Assess alignment,
root reach and in-between rendering. Never treat registration as painted scalp.
"""
import json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_162_root_layers_qa import source,ROOT,P,tag
from p15_153_source_topology import extract
from p15_129_ahoge_ownership import keyframes,ANGLES,KEYS,top_components
from p15_128_keyart_registration import frame_interp,jumps
from p15_158_loop_correspondence import similarity,anchors,warp
from p15_134_underpaint_probe import compose
OUT=P/'exports/p15-163-canonical-registration'
E=ROOT/'evidence/p15-163-canonical-registration-qa.json'
W=H=443
def affine(scale,dx,dy,center=(240,50)):
    cx,cy=center
    return np.float32([[scale,0,(1-scale)*cx+dx],[0,scale,(1-scale)*cy+dy]])
def transformed(arr,scale,dx,dy):
    return cv2.warpAffine(arr,affine(scale,dx,dy),(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
def metrics(mask,target,root_y):
    yy,xx=np.indices(mask.shape)
    region=(yy<54)&(xx>125)&(xx<375)
    a=mask&region;b=target&region
    inter=int((a&b).sum());uni=int((a|b).sum())
    iou=inter/max(1,uni)
    outside=int((a&~b).sum())
    # Endpoint remains a separate gate from visible silhouette alignment.
    root_region=(yy>=54)&(yy<=root_y+8)&(xx>125)&(xx<375)
    roots=int((mask&root_region).sum())
    return {'sourceVisibleLoopIoU':round(iou,5),'sourceVisibleLoopIntersection':inter,
      'offSourceVisibleLoopPixels':outside,'rootCandidatePixels':roots,
      'rootAtActualY':bool(mask[min(H-1,root_y)].any()),
      'opaqueAboveCrownPixels':int(a.sum())}
def find_affine(part,original,angle):
    reference=extract(original)[0]['loop_visible'][...,3]>64
    root_y=int(round(float(anchors(angle)[0,1])))
    cv2.setNumThreads(1)
    # Evaluate binary-alpha geometry on reduced 180px grids first; only
    # render the full 443px RGBA candidate once for the winning transform.
    factor=180/443
    target=cv2.resize(reference.astype('uint8'),(180,180),interpolation=cv2.INTER_NEAREST)>0
    material=cv2.resize((part[...,3]>64).astype('uint8'),(180,180),interpolation=cv2.INTER_NEAREST)
    yy,xx=np.indices((180,180))
    roi=(yy<int(54*factor))&(xx>int(125*factor))&(xx<int(375*factor))
    reference_mask=target&roi
    def searchscore(scale,dx,dy):
        cx,cy=240*factor,50*factor
        mat=np.float32([[scale,0,(1-scale)*cx+dx*factor],[0,scale,(1-scale)*cy+dy*factor]])
        shifted=cv2.warpAffine(material,mat,(180,180),flags=cv2.INTER_NEAREST)>0
        cropped=shifted&roi
        i=int((cropped&reference_mask).sum())
        u=int((cropped|reference_mask).sum())
        return i/max(1,u)-.025*abs(scale-1)-.00005*(abs(dx)+abs(dy))
    options=[(searchscore(s,dx,dy),s,dx,dy)
             for s in np.arange(.70,1.251,.05)
             for dx in range(-64,65,8) for dy in range(-30,31,6)]
    _,scale,dx,dy=max(options)
    fine=[(searchscore(float(s),x,y),float(s),x,y)
          for s in np.arange(scale-.035,scale+.036,.01)
          for x in range(dx-7,dx+8,2) for y in range(dy-5,dy+6,2)]
    _,s,x,y=max(fine)
    shifted=transformed(part,s,x,y)
    m=metrics(shifted[...,3]>64,reference,root_y)
    return shifted,{'scale':round(s,5),'translationXY':[x,y],
        'sourceLoopMatch':m,'actualRootY':root_y}

def run(save=True):
    native=keyframes()
    aligned={};report={};controls={}
    for yaw in KEYS:
        part,meta=source(yaw)
        before=metrics(part[...,3]>64,extract(native[yaw])[0]['loop_visible'][...,3]>64,
                       int(round(float(anchors(yaw)[0,1]))))
        image,fit=find_affine(part,native[yaw],yaw)
        aligned[yaw]=image;report[f'{yaw:g}']={'sourceSHA256':meta['sha256'],
            'original':before,'registered':fit}
        controls[yaw]=anchors(yaw)
    reference=frame_interp(native[90.],native[112.5],native[135.])
    candidate=[]
    for i,yaw in enumerate(ANGLES):
        if yaw in KEYS:
            candidate.append(native[yaw].copy());continue
        a,b=(90.,112.5) if yaw<112.5 else (112.5,135.)
        t=(yaw-a)/(b-a);owner=a if t<=.5 else b
        target=controls[a]*(1-t)+controls[b]*t
        part=warp(aligned[owner],similarity(controls[owner],target))
        base=reference[i].copy();base[:54]=0
        candidate.append(compose(base,part))
    results={'reference':{'maxAdjacentRGBMAE':max(jumps(reference)),'topComponents':[top_components(f) for f in reference]},
      'registeredCandidate':{'maxAdjacentRGBMAE':max(jumps(candidate)),
       'topComponents':[top_components(f) for f in candidate],
       'nativeKeyframesPixelExact':all(np.array_equal(candidate[ANGLES.index(yaw)],native[yaw]) for yaw in KEYS)}}
    qa={'schema':'KOMA_P15_163_CANONICAL_LOOP_REGISTRATION_V1','characterId':'p0_character_001',
      'sourceAngles':list(KEYS),'renderAngles':list(ANGLES),'views':report,'render':results,
      'artProvenancePreserved':True,'sourceKeyviewsPreserved':True,
      'matchedHiddenCrownVerified':False,'physicalRootContinuityArtistApproved':False,
      'fullYawVisualAccepted':False,'productionAdmitted':False,
      'review':'private-assets/exports/p15-163-canonical-registration/index.html',
      'next':'Use the correctly registered source-visible loop as artwork reference and paint actual attached roots plus hidden crown for each keyview before retesting VDD.'}
    qa['gate']={'allLoopIoUImproved':all(v['registered']['sourceLoopMatch']['sourceVisibleLoopIoU']>v['original']['sourceVisibleLoopIoU'] for v in report.values()),
      'allVisibleLoopIoUOver0p45':all(v['registered']['sourceLoopMatch']['sourceVisibleLoopIoU']>=.45 for v in report.values()),
      'allRootsReachActualY':all(v['registered']['sourceLoopMatch']['rootAtActualY'] for v in report.values()),
      'midYawSingleComponent':all(results['registeredCandidate']['topComponents'][i]==1 for i in (1,3)),
      'artisticAccepted':False,'passes':False}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(350*3,380*3),(36,42,53));draw=ImageDraw.Draw(board)
        for i,yaw in enumerate(KEYS):
            directory=OUT/tag(yaw);directory.mkdir(parents=True,exist_ok=True)
            source_part,_=source(yaw)
            for row,(label,arr) in enumerate([('canonical',native[yaw]),('generated',source_part),('registered',aligned[yaw])]):
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(arr,'RGBA'))
                board.paste(tile.convert('RGB').resize((343,343),Image.Resampling.LANCZOS),(350*i,380*row+28))
                draw.text((350*i+6,380*row+5),f'{yaw:g} {label}',fill='white')
            Image.fromarray(aligned[yaw],'RGBA').save(directory/'aligned.png')
        board.save(OUT/'source-registration.jpg',quality=94)
        yawboard=Image.new('RGB',(310*5,350*2),(36,42,53));d=ImageDraw.Draw(yawboard)
        for row,(label,seq) in enumerate((('reference',reference),('registered',candidate))):
          for col,(ang,arr) in enumerate(zip(ANGLES,seq)):
            tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(arr,'RGBA'))
            crop=tile.crop((135,0,360,115)).resize((304,304),Image.Resampling.NEAREST)
            yawboard.paste(crop.convert('RGB'),(col*310,row*350+30))
            d.text((col*310+6,row*350+7),f'{label} {ang:g}',fill='white')
            if row:
                Image.fromarray(arr,'RGBA').save(OUT/(f'candidate-{ang:06.2f}'.replace('.','p')+'.png'))
        yawboard.save(OUT/'yaw-comparison.jpg',quality=95)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 canonical loop registration</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Three-view source-loop alignment</h2><p>Actual generated RGBA art registered against the canonical visible loop, with root depth and independent yaw diagnostics. Hidden scalp and physical root geometry remain separate art requirements.</p><img src="source-registration.jpg"><h2>90–135° yaw comparison</h2><img src="yaw-comparison.jpg">')
        E.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    return qa
if __name__=='__main__':
 q=run()
 print(json.dumps({'views':q['views'],'render':q['render'],'gate':q['gate']},indent=2))

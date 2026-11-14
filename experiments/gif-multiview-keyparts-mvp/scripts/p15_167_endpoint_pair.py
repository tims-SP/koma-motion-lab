#!/usr/bin/env python3
"""Canonical three-view ahoge/crown asset pairs with visible-endpoint topology.

The root/tip endpoints are reviewed image-space *proposals*. Preserve all
source pixels by explicit ownership matte and record the synthetic inpainted
crown underlayer separately from source-derived visible hair. This is not a
fully painter-authored rig or verified physical hair attachment.
"""
import json,hashlib
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_129_ahoge_ownership import keyframes,KEYS,ANGLES,top_components
from p15_166_crown_silhouette import crown_edge
from p15_128_keyart_registration import frame_interp,jumps
from p15_134_underpaint_probe import P,compose
from p15_158_loop_correspondence import similarity,warp
from p15_153_source_topology import ROOT

OUT=P/'exports/p15-167-endpoint-pair'
E=ROOT/'evidence/p15-167-endpoint-pair-qa.json'
ROOT_AND_TIP={90.:{'root':(184,53),'tip':(264,46)},
              112.5:{'root':(258,77),'tip':(315,72)},
              135.:{'root':(222,55),'tip':(286,46)}}
TAGS={90.:'yaw090',112.5:'yaw112p5',135.:'yaw135'}
H=W=443

def mask_for(frame,angle):
    edge=crown_edge(frame,9)
    root=ROOT_AND_TIP[angle]['root']
    tip=ROOT_AND_TIP[angle]['tip']
    yy,xx=np.indices((H,W))
    xlo=min(root[0],tip[0])-11;xhi=max(root[0],tip[0])+15
    near=(xx>=xlo)&(xx<=xhi)&(yy<=118)
    above=(yy<edge[np.newaxis,:]-2)&near
    # Keep the original source's single visible strand above crown.
    alpha=frame[...,3]>24
    upper=above&alpha
    n,lab,stats,_=cv2.connectedComponentsWithStats(np.uint8(upper),8)
    if n>1:
        choices=[i for i in range(1,n) if int(stats[i,cv2.CC_STAT_AREA])>=20]
        if choices:
            dominant=max(choices,key=lambda i:stats[i,cv2.CC_STAT_AREA])
            upper=lab==dominant
    # A short source-painted root corridor enters the crown. Endpoint/tip
    # are distinct: do NOT force the right tip into an invented second root.
    x0,y0=root
    root_start=min(y0,int(edge[x0]))-5
    root_end=max(y0,int(edge[x0]))+9
    taper=np.maximum(2.1,4.0-1.9*np.clip((yy-root_start)/max(1,root_end-root_start),0,1))
    route=(abs(xx-x0)<=taper)&(yy>=root_start)&(yy<=root_end)&alpha
    # Connect all corridor pixels to the source loop via an ownership matte.
    owned=upper|route
    return owned,edge,{'aboveCrownPixels':int(upper.sum()),
      'rootSourcePixels':int((route&~upper).sum()),
      'ownerPixels':int(owned.sum()),
      'ownerComponents':int(cv2.connectedComponents(np.uint8(owned),8)[0]-1)}

def pair(frame,angle):
    owned,edge,stats=mask_for(frame,angle)
    root=ROOT_AND_TIP[angle]['root'];tip=ROOT_AND_TIP[angle]['tip']
    strand=frame.copy();strand[~owned]=0
    crown=frame.copy()
    # In open air the crown/underpaint is transparent. Under the root,
    # preserve original source alpha but reconstruct covered RGB locally.
    yy,xx=np.indices((H,W))
    above=yy<edge[None,:]-2
    crown[owned&above]=0
    covered=owned&~above
    scratch=cv2.cvtColor(frame[...,:3],cv2.COLOR_RGB2BGR)
    painted=cv2.inpaint(scratch,np.uint8(covered)*255,3,cv2.INPAINT_TELEA)
    repaired=cv2.cvtColor(painted,cv2.COLOR_BGR2RGB)
    crown[covered,:3]=repaired[covered]
    # Exact source assembly is possible because owned pixels and their
    # native antialias alpha are restored by a deterministic pixel-ownership
    # matte, rather than double alpha compositing.
    reconstruct=crown.copy();reconstruct[owned]=strand[owned]
    stats.update({
      'originalPixelExact':bool(np.array_equal(reconstruct,frame)),
      'inpaintedCrownPixels':int(covered.sum()),
      'headBelowY120Exact':bool(np.array_equal(crown[120:],frame[120:])),
      'sourceAlphaAtRoot':int(frame[root[1],root[0],3]),
      'sourceAlphaAtTip':int(frame[tip[1],tip[0],3]),
      'rootCrownSignedGapY':round(float(edge[root[0]]-root[1]),2),
      'tipCrownSignedGapY':round(float(edge[tip[0]]-tip[1]),2),
      'root':list(root),'freeTipProposal':list(tip)
    })
    return strand,crown,owned,stats

def place_at(part,old_root,old_tip,new_root,new_tip):
    return warp(part,similarity(np.float32([old_root,old_tip]),np.float32([new_root,new_tip])))

def render(save=True):
    source=keyframes()
    parts={};under={};mattes={};data={}
    for angle in KEYS:
        part,head,matte,info=pair(source[angle],angle)
        assert info['originalPixelExact']
        parts[angle]=part;under[angle]=head;mattes[angle]=matte
        info['sourceSHA256RGBA']=hashlib.sha256(source[angle].tobytes()).hexdigest()
        info['strandSHA256RGBA']=hashlib.sha256(part.tobytes()).hexdigest()
        info['crownSHA256RGBA']=hashlib.sha256(head.tobytes()).hexdigest()
        data[f'{angle:g}']=info
    baseline=frame_interp(source[90.],source[112.5],source[135.])
    candidate=[]
    intermediates={}
    for index,angle in enumerate(ANGLES):
        if angle in KEYS:
            candidate.append(source[angle].copy());continue
        left,right=(90.,112.5) if angle<112.5 else (112.5,135.)
        t=(angle-left)/(right-left)
        src=left if t<=.5 else right
        root_a=np.float32(ROOT_AND_TIP[left]['root']);root_b=np.float32(ROOT_AND_TIP[right]['root'])
        tip_a=np.float32(ROOT_AND_TIP[left]['tip']);tip_b=np.float32(ROOT_AND_TIP[right]['tip'])
        root=root_a*(1-t)+root_b*t;tip=tip_a*(1-t)+tip_b*t
        deformed=place_at(parts[src],ROOT_AND_TIP[src]['root'],ROOT_AND_TIP[src]['tip'],root,tip)
        # Use original inbetween frame as environment; separate the loop
        # using the same silhouette/crown ownership algorithm at each angle.
        # At intermediate angles, rely on the broad head contour; an authored
        # rootless underpaint for every intermediate frame is still missing.
        edge=crown_edge(baseline[index],9)
        yy,xx=np.indices((H,W))
        air=(yy<edge[None,:]-2)&(xx>=120)&(xx<=390)
        background=baseline[index].copy();background[air]=0
        upper=deformed.copy();upper[~air]=0
        frame=compose(background,upper)
        candidate.append(frame)
        intermediates[f'{angle:g}']={'donor':src,'interpolatedRoot':root.round(2).tolist(),
            'interpolatedFreeTip':tip.round(2).tolist(),
            'upperSourceOpaquePixels':int((upper[...,3]>64).sum()),
            'sourceCrownAlphaExact':bool(np.array_equal(frame[~air,3],baseline[index][~air,3]))}
    ref={'maxAdjacentRGBMAE':max(jumps(baseline)),
         'topConnectedComponents':[top_components(x) for x in baseline]}
    experiment={'maxAdjacentRGBMAE':max(jumps(candidate)),
         'topConnectedComponents':[top_components(x) for x in candidate],
         'originalKeyviewsPixelExact':all(np.array_equal(candidate[ANGLES.index(k)],source[k]) for k in KEYS)}
    report={'schema':'KOMA_P15_167_SOURCE_ENDPOINT_PAIRED_LAYERS_V1',
     'characterId':'p0_character_001','angles':list(KEYS),'renderAngles':list(ANGLES),
     'endpointModel':'one root contact and a second visible free-tip candidate in each source view',
     'legacyLandmarkDiagnostic':{'yaw112p5':[294,72],'sourceAlphaAtLegacyYaw112p5Root':int(source[112.5][72,294,3])},
     'keyviewPairs':data,'intermediateViews':intermediates,
     'reference':ref,'candidate':experiment,
     'sourceArtworkPixelExact':True,'hiddenCrownGeneratedByInpainting':True,
     'endpointLabelsArtistApproved':False,'physicalHairRigAccepted':False,
     'continuousYawVisualAccepted':False,'productionRendererChanged':False,
     'review':'private-assets/exports/p15-167-endpoint-pair/index.html'}
    report['gate']={
      'keyviewPairReassemblyExact':all(d['originalPixelExact'] for d in data.values()),
      'rootAnchorHasSourceAlpha':all(d['sourceAlphaAtRoot']>=64 for d in data.values()),
      'allSourcePairsHaveRootMaterial':all(d['rootSourcePixels']>0 for d in data.values()),
      'allSecondEndpointsAboveCrown':all(d['tipCrownSignedGapY']>5 for d in data.values()),
      'allSourceLoopMasksConnected':all(d['ownerComponents']==1 for d in data.values()),
      'keyviewOriginalsPreserved':experiment['originalKeyviewsPixelExact'],
      'bothMidviewsSingleComponent':all(experiment['topConnectedComponents'][i]==1 for i in (1,3)),
      'preservesIntermediateCrownAlpha':all(v['sourceCrownAlphaExact'] for v in intermediates.values()),
      'visualAccepted':False,'passes':False}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        for k in KEYS:
            folder=OUT/TAGS[k];folder.mkdir(exist_ok=True)
            Image.fromarray(parts[k],'RGBA').save(folder/'ahoge-source-visible.png')
            Image.fromarray(under[k],'RGBA').save(folder/'crown-underpaint-candidate.png')
            Image.fromarray(np.uint8(mattes[k])*255,'L').save(folder/'ownership-matte.png')
            reconstructed=under[k].copy();reconstructed[mattes[k]]=parts[k][mattes[k]]
            Image.fromarray(reconstructed,'RGBA').save(folder/'source-reassembled.png')
        board=Image.new('RGB',(370*3,393*3),(36,43,54));pen=ImageDraw.Draw(board)
        for col,k in enumerate(KEYS):
            for row,(label,img) in enumerate((('Source',source[k]),('Hair layer',parts[k]),('Crown underpaint',under[k]))):
                preview=Image.new('RGBA',(443,443),(48,61,79,255));preview.alpha_composite(Image.fromarray(img,'RGBA'))
                board.paste(preview.crop((125,0,365,145)).resize((364,345),Image.Resampling.NEAREST).convert('RGB'),(col*370,row*393+31))
                pen.text((col*370+7,row*393+6),f'{k:g}° {label}',fill='white')
        board.save(OUT/'keyview-pairs.jpg',quality=94)
        yaw=Image.new('RGB',(310*5,220*2),(36,43,54));pen=ImageDraw.Draw(yaw)
        for row,(name,seq) in enumerate((('Reference',baseline),('Paired source',candidate))):
            folder=OUT/name.lower().replace(' ','-');folder.mkdir(exist_ok=True)
            for col,(angle,img) in enumerate(zip(ANGLES,seq)):
                Image.fromarray(img,'RGBA').save(folder/(f'yaw{angle:06.2f}'.replace('.','p')+'.png'))
                preview=Image.new('RGBA',(443,443),(48,61,79,255));preview.alpha_composite(Image.fromarray(img,'RGBA'))
                yaw.paste(preview.crop((125,0,365,140)).resize((303,182),Image.Resampling.NEAREST).convert('RGB'),(col*310,row*220+29))
                pen.text((col*310+5,row*220+6),f'{name} {angle:g}°',fill='white')
        yaw.save(OUT/'yaw-comparison.jpg',quality=95)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 canonical loop endpoint pairs</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Original ahoge, isolated visible loop and underlying crown</h2><p>Source pixel ownership supports exact reassembly of all three original keyviews. The inner root underpaint is synthetic. Two visible endpoints are annotated according to source contact, rather than assumed double-root geometry.</p><img src="keyview-pairs.jpg"><h2>Mid-angle rendering</h2><img src="yaw-comparison.jpg">')
        E.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report

if __name__=='__main__':
    q=render()
    print(json.dumps({'keyviews':q['keyviewPairs'],'candidate':q['candidate'],'gate':q['gate']},indent=2))

#!/usr/bin/env python3
"""Source-registered crown-underpaint candidates for three native keyviews.

Uses P15-167 lossless ownership masks. The repair ROI covers the isolated
root stub plus the upper crown contact, with original opaque crown pixels
as the only RGB sources. Original key art and reversible source layers stay
unchanged. All restored textures are diagnostic, not approved artwork.
"""
import hashlib,json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_167_endpoint_pair import pair,ROOT_AND_TIP,ROOT,P
from p15_166_crown_silhouette import crown_edge
from p15_129_ahoge_ownership import keyframes,KEYS
OUT=P/'exports/p15-172-crown-underpaint';E=ROOT/'evidence/p15-172-crown-underpaint-qa.json'
H=W=443
def source_layers(yaw):
    native=keyframes()[yaw]
    strand,crown,owned,meta=pair(native,yaw)
    original=crown.copy()
    original[owned]=strand[owned]
    assert np.array_equal(original,native)
    return native,strand,crown,owned,meta
def repair(yaw,method):
    original,strand,base,owned,meta=source_layers(yaw)
    edge=crown_edge(original,9)
    x0,y0=ROOT_AND_TIP[yaw]['root']
    yy,xx=np.indices((H,W))
    # The crown-side part of source ownership is a mask with exact source
    # provenance; extra root ink within 5px can be conservatively cleared.
    above=(yy<edge[None,:]-2)
    root_roi=(abs(xx-x0)<=9)&(yy>=edge[None,:]-7)&(yy<edge[None,:]+13)&(yy<115)
    old_root=(owned&root_roi)
    if method=='conservative':
        mask=old_root
    elif method=='connected':
        # Include the root stump and its immediate 1-pixel ink border only.
        mask=(cv2.dilate(np.uint8(old_root),np.ones((3,3),np.uint8))>0)&root_roi
    elif method=='semantic_patch':
        # Root-line source stroke occupies multiple antialiased pixels around
        # the contact. Cover its whole local crown-side corridor for the
        # underlying material, leaving the canonical strand separately owned.
        mask=((abs(xx-x0)<=6)&(yy>=edge[None,:]+2)&
              (yy<=y0+12)&(yy<=110)&(original[...,3]>=245))
    elif method=='feathered':
        mask=(cv2.dilate(np.uint8(old_root),np.ones((3,3),np.uint8))>0)&root_roi
    else:raise ValueError(method)
    # Alpha ownership: retain exact source head outside strand pixels.
    # Any above-crown strand becomes transparent; under the crown the
    # original opaque coverage is maintained. Inpaint only RGB under alpha.
    result=base.copy()
    result[owned&above]=0
    opaque=(yy>=edge[None,:]-1)&(original[...,3]>=245)
    paintmask=np.uint8(mask&opaque)*255
    rgb=cv2.cvtColor(original[...,:3],cv2.COLOR_RGB2BGR)
    fill=cv2.cvtColor(cv2.inpaint(rgb,paintmask,4,cv2.INPAINT_TELEA),cv2.COLOR_BGR2RGB)
    w=cv2.GaussianBlur(np.float32(paintmask)/255,(0,0),1.0)
    if method=='feathered':w*=.7
    result[...,:3]=np.uint8(np.clip(np.round(result[...,:3].astype(np.float32)*(1-w[...,None])+fill.astype(np.float32)*w[...,None]),0,255))
    # Clip halo in transparent pixels and retain source alpha for the head.
    result[owned&above]=0
    result[~above,3]=original[~above,3]
    result[125:]=original[125:]
    changed=np.any(result!=base,axis=2)
    return result,strand,owned,{
      'sourceReassemblyPixelExact':meta['originalPixelExact'],
      'semanticRootPixels':int(old_root.sum()),
      'paintMaskPixels':int(np.count_nonzero(paintmask)),
      'rgbEditedPixels':int(changed.sum()),
      'headBelowY125Exact':bool(np.array_equal(result[125:],original[125:])),
      'alphaOutsideSourceAir':int(np.count_nonzero(result[above,3])),
      'sourceRoot':[x0,y0],
      'sourceSHA256':hashlib.sha256(original.tobytes()).hexdigest(),
      'underpaintRGBA_SHA256':hashlib.sha256(result.tobytes()).hexdigest(),
      'rootStubAboveCrownPixels':int((owned&above&root_roi).sum())}
def evaluate(save=True):
    source=keyframes()
    variants={};results={}
    for method in ('conservative','connected','feathered','semantic_patch'):
        variants[method]={};results[method]={}
        for angle in KEYS:
            base,strand,owned,diag=repair(angle,method)
            variants[method][angle]=(base,strand,owned)
            results[method][f'{angle:g}']=diag
    report={'schema':'KOMA_P15_172_SOURCE_REGISTERED_CROWN_UNDERPAINT_V1',
        'characterId':'p0_character_001','sourceAngles':list(KEYS),
        'methods':results,'materialType':'source-registered bounded crown RGB reconstruction',
        'originalKeyviewsPreserved':True,
        'nativeSourceRecompositionExact':all(x['sourceReassemblyPixelExact'] for row in results.values() for x in row.values()),
        'sourcePaintArtistApproved':False,'hiddenRootAndCrownArtistApproved':False,
        'crossViewPhysicalAttachmentValidated':False,'productionRendererUpdated':False,
        'review':'private-assets/exports/p15-172-crown-underpaint/index.html',
        'next':'Acquire source-matched crown art with the 112.5-degree root stub and 90/135 edge remnants painted out; inspect all three closeups and prove clean root boundary before mid-yaw VDD.'}
    report['gate']={'threeViewsAvailable':len(source)==3,
        'nativeLayerPairReconstructionExact':report['nativeSourceRecompositionExact'],
        'headBelowY125Exact':all(x['headBelowY125Exact'] for row in results.values() for x in row.values()),
        'allViewsHavePaintMask':all(x['paintMaskPixels']>0 for x in results['connected'].values()),
        'semanticPaintLocality':all(x['headBelowY125Exact'] and x['rgbEditedPixels']<1000 for x in results['semantic_patch'].values()),
        'rootStubsVisuallyCleared':False,
        'sourceCrownContourVisuallyMatched':False,
        'visualPaintApproved':False,'passes':False}
    if save:
        OUT.mkdir(exist_ok=True,parents=True)
        board=Image.new('RGB',(360*3,302*(1+len(variants))),(33,42,54));d=ImageDraw.Draw(board)
        for row,(label,images) in enumerate([('source',{a:source[a] for a in KEYS})]+[(method,{a:variants[method][a][0] for a in KEYS}) for method in variants]):
            for col,angle in enumerate(KEYS):
                arr=images[angle]
                bg=Image.new('RGBA',(443,443),(49,61,78,255));bg.alpha_composite(Image.fromarray(arr,'RGBA'))
                board.paste(bg.crop((133,0,356,127)).resize((351,260),Image.Resampling.NEAREST).convert('RGB'),(col*360,row*302+29))
                d.text((col*360+6,row*302+6),f'{angle:g} {label}',fill='white')
                if label!='source':
                    folder=OUT/label/('yaw'+str(angle).replace('.','p'));folder.mkdir(exist_ok=True,parents=True)
                    Image.fromarray(arr,'RGBA').save(folder/'rootless-crown-candidate.png')
                    Image.fromarray(variants[label][angle][1],'RGBA').save(folder/'source-owned-loop.png')
                    Image.fromarray(np.uint8(variants[label][angle][2])*255,'L').save(folder/'source-ownership-matte.png')
        board.save(OUT/'crown-contact.jpg',quality=95)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 crown texture review</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>P0 three-keyview crown material review</h2><p>Three source-preserving candidate RGB underpaints: conservative, connected, and feathered source root masks. All original keyviews and source-owned loop material are separately preserved. Requires visual acceptance before cross-view VDD.</p><img src="crown-contact.jpg">')
        E.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report
if __name__=='__main__':
    q=evaluate()
    print(json.dumps({'methods':q['methods'],'gate':q['gate']},indent=2))

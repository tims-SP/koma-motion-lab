#!/usr/bin/env python3
"""P15-173: root-stub material ownership and source-registered crown restoration.

Keep P15-167 native source hair layers and exact reconstruction separately.
Rootless crown candidates only affect a bounded RGB region inside opaque
head and a root-ink silhouette extending above the crown. Native source keys
are retained for all downstream exact-composition checks.
"""
import json,hashlib
from pathlib import Path
import cv2,numpy as np
from PIL import Image, ImageDraw
from p15_172_crown_underpaint import source_layers,ROOT_AND_TIP,crown_edge,KEYS,P,ROOT
OUT=P/'exports/p15-173-root-stub-ownership'
E=ROOT/'evidence/p15-173-root-stub-ownership-qa.json'
H=W=443

def source_masks(original,angle,width,down=14):
    x0,y0=ROOT_AND_TIP[angle]['root']
    edge=crown_edge(original,9)
    yy,xx=np.indices((H,W))
    # Root identity is a narrow material corridor attached to the source
    # landmark. Paint the root's entire dark tip, not only its blackhat core.
    corridor=(np.abs(xx-x0)<=width)&(yy>=edge[None,:]-5)&(yy<=max(y0+down,int(edge[x0])+down))&(yy<115)
    # Isolate original opaque head pixels for RGB fill; keep alpha exactly
    # as the original crown there.
    opaque=(original[...,3]>=245)&(yy>=edge[None,:]+1)
    paint=corridor&opaque
    # A source-visible post above the broad head is owned by the hair layer,
    # so the rootless crown must not carry it.
    airpost=corridor&(yy<edge[None,:]+1)&(yy<y0+3)
    return paint,airpost,edge

def opaque_hair_rgb(original):
    # Restrict to local crown color: fill transparent RGB from opaque source
    # before root line reconstruction. This is a synthetic texture estimate.
    rgba=original.copy()
    rgb=cv2.cvtColor(rgba[...,:3],cv2.COLOR_RGB2BGR)
    # For each transparent row pixel, use nearest opaque donor on the same
    # scanline or last known opaque row. The source art alpha is untouched.
    for y in range(125):
        valid=np.flatnonzero(rgba[y,:,3]>=245)
        if not len(valid): continue
        xs=np.arange(W)
        near=valid[np.argmin(np.abs(xs[:,None]-valid[None,:]),axis=1)]
        bad=rgba[y,:,3]<245
        rgb[y,bad]=rgb[y,near[bad]]
    return cv2.cvtColor(rgb,cv2.COLOR_BGR2RGB)

def make(angle,method):
    original,strand,base,owned,meta=source_layers(angle)
    width={'narrow':4,'wide':7,'cap':8}[method]
    paint,airpost,edge=source_masks(original,angle,width)
    # Fill RGB from the source on a deliberately padded hole, not from the
    # foreground loop or an already synthesized inpainted result.
    image=cv2.cvtColor(opaque_hair_rgb(original),cv2.COLOR_RGB2BGR)
    repaired=cv2.cvtColor(cv2.inpaint(image,np.uint8(paint)*255,5,cv2.INPAINT_TELEA),cv2.COLOR_BGR2RGB)
    result=base.copy()
    if method=='cap':
        # Preserve outer alpha contour: only cover the fully opaque region.
        # A hard paint inside the hole prevents old root ink from surviving.
        result[paint,:3]=repaired[paint]
    else:
        weight=cv2.GaussianBlur(np.float32(paint),(0,0),.8)
        weight=np.clip(weight,0,1)
        result[...,:3]=np.uint8(np.clip(np.round(base[...,:3].astype(np.float32)*(1-weight[...,None])
                                    +repaired.astype(np.float32)*weight[...,None]),0,255))
    # Crown coverage is retained only in opaque head, and remaining post
    # material is transparent where it belongs to the isolated hair strand.
    erase=airpost & (owned | (original[...,3]>16))
    result[erase]=0
    result[125:]=original[125:]
    changed=np.any(result!=base,axis=2)
    x0,y0=ROOT_AND_TIP[angle]['root']
    # Dark-pixel diagnostic at the exact root center; not art acceptance.
    gray=cv2.cvtColor(result[...,:3],cv2.COLOR_RGB2GRAY)
    line=(np.indices((H,W))[1]>=x0-2)&(np.indices((H,W))[1]<=x0+2)
    ink=(gray<145)&line&paint
    return result,strand,owned,{
       'root':list(ROOT_AND_TIP[angle]['root']),
       'paintPixels':int(paint.sum()),'airpostPixels':int(erase.sum()),
       'editedPixels':int(changed.sum()),'darkRootPixelCount':int(ink.sum()),
       'alphaAboveCrownRemaining':int(np.count_nonzero(result[airpost,3])),
       'belowY125Exact':bool(np.array_equal(result[125:],original[125:])),
       'sourceKeyReassembledExact':meta['originalPixelExact'],
       'sourceSHA256':hashlib.sha256(original.tobytes()).hexdigest(),
       'crownSHA256':hashlib.sha256(result.tobytes()).hexdigest(),
       'sourceStrandSHA256':hashlib.sha256(strand.tobytes()).hexdigest()
    }

def evaluate(save=True):
    methods=('narrow','wide','cap')
    data={};assets={}
    for mode in methods:
        data[mode]={};assets[mode]={}
        for angle in KEYS:
            head,strand,mask,info=make(angle,mode)
            assets[mode][angle]=(head,strand,mask)
            data[mode][f'{angle:g}']=info
    q={'schema':'KOMA_P15_173_ROOT_STUB_OWNERSHIP_V1','characterId':'p0_character_001',
       'sourceAngles':list(KEYS),'methods':data,
       'sourceLayerPairsExact':all(x['sourceKeyReassembledExact'] for row in data.values() for x in row.values()),
       'paintingType':'source-registered opaque-crown bounded underpaint and above-crown hair ownership',
       'nativeKeyArtworkUnchanged':True,'sourceMatchedHiddenPaintApproved':False,
       'continuousMotionAccepted':False,'canonicalRendererUpdated':False,
       'review':'private-assets/exports/p15-173-root-stub-ownership/index.html',
       'visualFindings':'Source-only RGB donors limit dark fill artifacts. Narrow mask leaves a 112.5 degree vertical post. Wider repair introduces loss of natural crown hair ink near 90 and 135. No visually acceptable crown part yet.'}
    q['gate']={'sourcePairExact':q['sourceLayerPairsExact'],
        'deepHeadPixelExact':all(x['belowY125Exact'] for row in data.values() for x in row.values()),
        'allRootROIsPainted':all(x['paintPixels']>0 for x in data['cap'].values()),
        'allAirPostsCleared':all(x['alphaAboveCrownRemaining']==0 for x in data['cap'].values()),
        'crownLineworkArtistApproved':False,
        'rootStubVisuallyCleared':False,
        'sourceCrownContourVisuallyMatched':False,
        'passes':False}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        panel=Image.new('RGB',(3*375,5*295),(35,42,54));d=ImageDraw.Draw(panel)
        src={}
        for k in KEYS:
            original,_,_,_,_=source_layers(k);src[k]=original
        collections=[('source',src),('p15_172_semantic',{}),
                     *[(m,{a:assets[m][a][0] for a in KEYS}) for m in methods]]
        from p15_172_crown_underpaint import repair as prior
        collections[1]=('p15_172_semantic',{a:prior(a,'semantic_patch')[0] for a in KEYS})
        for row,(label,images) in enumerate(collections):
            for col,a in enumerate(KEYS):
                arr=images[a];tile=Image.new('RGBA',(443,443),(49,61,78,255))
                tile.alpha_composite(Image.fromarray(arr,'RGBA'))
                panel.paste(tile.crop((128,0,361,130)).resize((367,259),Image.Resampling.NEAREST).convert('RGB'),(col*375,row*295+28))
                d.text((col*375+7,row*295+6),f'{label} {a:g}',fill='white')
                if label in methods:
                    folder=OUT/label/('yaw'+f'{a:g}'.replace('.','p'));folder.mkdir(exist_ok=True,parents=True)
                    Image.fromarray(arr,'RGBA').save(folder/'rootless-crown.png')
                    Image.fromarray(assets[label][a][1],'RGBA').save(folder/'source-loop.png')
        panel.save(OUT/'root-stub-comparison.jpg',quality=95)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 crown root art comparison</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Canonical source root-stub and crown restoration candidates</h2><p>Lossless original source keys retained. Compare narrow, wide, and complete cap root masks against the prior source-registered underpaint. Painter approval is separate from geometry and pixel tests.</p><img src="root-stub-comparison.jpg">')
        E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':
    q=evaluate()
    print(json.dumps({'methods':q['methods'],'gate':q['gate']},indent=2))

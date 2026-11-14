#!/usr/bin/env python3
"""Crown root-contact material repair using source-owned ink masks.

Keeps the P15-176 three-layer alpha contract. Inpainting is constrained to
the source ahoge ownership below the measured crown silhouette and to opaque
hair material. Evaluate two conservative support widths without altering the
native strand or the original canonical reference.
"""
import hashlib,json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_176_alpha_safe_crown import make,KEYS,TAGS
from p15_166_crown_silhouette import crown_edge
from p15_167_endpoint_pair import ROOT_AND_TIP
from p15_175_layered_crown_assets import rgba_over
from p15_134_underpaint_probe import P
ROOT=Path(__file__).resolve().parents[1]
OUT=P/'exports/p15-177-crown-root-repaint'
E=ROOT/'evidence/p15-177-crown-root-repaint-qa.json'
def repaint(angle,radius):
    src,strand,motion,static,owner,old_composite,_=make(angle)
    edge=crown_edge(src,9)
    rx,ry=ROOT_AND_TIP[angle]['root']
    yy,xx=np.indices(owner.shape)
    roi=(abs(xx-rx)<=12)&(yy>=edge[None,:]-2)&(yy<=edge[None,:]+24)&(yy<115)
    seed=owner&roi&(src[...,3]>=220)
    kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(radius*2+1,radius*2+1))
    mask=cv2.dilate(np.uint8(seed),kernel)>0
    mask&=roi&(src[...,3]>=245)
    # Keep only opaque crown material in the inpaint support and replace
    # transparent RGB donors with nearby opaque source colors.
    source_rgb=src[...,:3].copy()
    for y in range(125):
        valid=np.flatnonzero((src[y,:,3]>=245)&~mask[y])
        if len(valid):
            xs=np.arange(src.shape[1])
            idx=np.searchsorted(valid,xs)
            l=valid[np.clip(idx-1,0,len(valid)-1)]
            r=valid[np.clip(idx,0,len(valid)-1)]
            nearest=np.where(abs(xs-l)<=abs(xs-r),l,r)
            bad=(src[y,:,3]<245)|mask[y]
            source_rgb[y,bad]=source_rgb[y,nearest[bad]]
    repaired=cv2.cvtColor(cv2.inpaint(cv2.cvtColor(source_rgb,cv2.COLOR_RGB2BGR),
                       np.uint8(mask)*255,3,cv2.INPAINT_TELEA),cv2.COLOR_BGR2RGB)
    fixed=motion.copy()
    fixed[mask,:3]=repaired[mask]
    # Use only original crown alpha for full motion underpaint.
    fixed[...,3]=motion[...,3]
    # Remove source-strand remnants protruding above the head silhouette.
    # Keep a small antialiased transition at the crown edge, restricted to
    # root-near hair-ownership source pixels.
    yy,xx=np.indices(mask.shape)
    rx,ry=ROOT_AND_TIP[angle]['root']
    above=(yy<edge[None,:]+1)&(abs(xx-rx)<=12)&(yy<110)
    source_hair=(src[...,3]>0)
    root_air=above&source_hair
    # Existing motion crown already owns the lower bulk head; only clear
    # narrow above-edge connected strands and their antialiasing.
    fixed[root_air]=0
    fixed[125:]=src[125:]
    key=static.copy()
    key[mask,:3]=fixed[mask,:3]
    key[owner,3]=0
    over=rgba_over(key,strand)
    diff=np.any(over!=src,axis=2)&(src[...,3]>24)
    delta_from_baseline=np.any(over!=old_composite,axis=2)
    edit=np.any(fixed!=motion,axis=2)
    allowed=mask|owner|root_air
    return src,strand,motion,fixed,key,owner,mask,over,{
        'seedPixels':int(seed.sum()),'paintPixels':int(mask.sum()),
        'rootAirPixels':int(root_air.sum()),
        'actualEditedPixels':int(edit.sum()),
        'visibleCompositeDiffPixels':int(diff.sum()),
        'visibleDiffOutsideOwnershipOrPaint':int((diff&~allowed).sum()),
        'candidateDeltaOutsideRootRegion':int((delta_from_baseline&~allowed).sum()),
        'doubleAlphaPixels':int(((key[...,3]>0)&(strand[...,3]>0)).sum()),
        'sourceAlphaOutsideRootAirPreserved':bool(np.array_equal(fixed[...,3][~root_air],motion[...,3][~root_air])),
        'deepHeadExact':bool(np.array_equal(fixed[125:],src[125:])),
        'underpaintChangedOnlyMaskAndRootAir':bool(np.array_equal(fixed[~(mask|root_air)],motion[~(mask|root_air)])),
        'sourceSHA256':hashlib.sha256(src.tobytes()).hexdigest(),
        'crownSHA256':hashlib.sha256(fixed.tobytes()).hexdigest(),
        'root':list((rx,ry))
    }
def run(save=True):
    modes={'tight':1,'local':2,'broad':3}
    material={};data={}
    for mode,r in modes.items():
        material[mode]={};data[mode]={}
        for yaw in KEYS:
            item=repaint(yaw,r)
            material[mode][yaw]=item
            data[mode][f'{yaw:g}']=item[-1]
    q={'schema':'KOMA_P15_177_CROWN_ROOT_REPAINT_V1',
       'characterId':'p0_character_001','sourceAngles':list(KEYS),
       'methods':data,'methodRadii':modes,
       'originalSourceKeysPreserved':True,
       'materialMethod':'source-ahoge ownership seed, opaque-crown pixel inpainting, separate static alpha-safe and motion crown',
       'visualAccepted':False,'midYawRendered':False,'productionRendererUpdated':False,
       'review':'private-assets/exports/p15-177-crown-root-repaint/index.html'}
    q['gate']={
      'threeViewsRepainted':len(data['local'])==3,
      'originalAlphaOutsideRootAirPreserved':all(v['sourceAlphaOutsideRootAirPreserved'] for d in data.values() for v in d.values()),
      'inpaintInsideSourceRootMaskAndAir':all(v['underpaintChangedOnlyMaskAndRootAir'] for d in data.values() for v in d.values()),
      'belowY125PixelExact':all(v['deepHeadExact'] for d in data.values() for v in d.values()),
      'noDoubleAlphaOwnership':all(v['doubleAlphaPixels']==0 for d in data.values() for v in d.values()),
      'newCompositeDeltaLocalized':all(v['candidateDeltaOutsideRootRegion']==0 for d in data.values() for v in d.values()),
      'rootlessCrownVisualAccepted':False,'passes':False}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(300*3,245*4),(35,43,55))
        pen=ImageDraw.Draw(board)
        for row,mode in enumerate(['source',*modes]):
            for col,yaw in enumerate(KEYS):
                if mode=='source':
                    arr=material['local'][yaw][0]
                else:
                    src,strand,old,new,key,owner,mask,comp,info=material[mode][yaw]
                    arr=new
                    folder=OUT/mode/TAGS[yaw];folder.mkdir(parents=True,exist_ok=True)
                    Image.fromarray(new,'RGBA').save(folder/'crown-motion-underpaint.png')
                    Image.fromarray(key,'RGBA').save(folder/'crown-static-alpha-safe.png')
                    Image.fromarray(strand,'RGBA').save(folder/'ahoge.png')
                    Image.fromarray(np.uint8(mask)*255,'L').save(folder/'root-paint-mask.png')
                    Image.fromarray(comp,'RGBA').save(folder/'keyframe-composite.png')
                tile=Image.new('RGBA',(443,443),(47,59,76,255))
                tile.alpha_composite(Image.fromarray(arr,'RGBA'))
                board.paste(tile.crop((130,0,365,145)).resize((292,210),Image.Resampling.NEAREST).convert('RGB'),(col*300,row*245+26))
                pen.text((col*300+5,row*245+5),f'{mode} {yaw:g}',fill='white')
        board.save(OUT/'crown-root-comparison.jpg',quality=96)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P15-177 crown paint</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Source registered crown root texture repair</h2><p>Opaque-crown inpaint using three mask radii. Full motion underpaint and alpha-safe static crown are exported separately; canonical source pixels are retained unchanged.</p><img src="crown-root-comparison.jpg">')
        E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':
    q=run()
    print(json.dumps({'gate':q['gate'],'methods':q['methods']},indent=2))

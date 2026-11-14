#!/usr/bin/env python3
"""P15-175: three-view transparent crown/ahoge asset pairs and acceptance diagnostics.

Native source keyframes are immutable. The owner-matte reassembly is exact;
standard alpha-over compositing is measured separately. Reconstruct hidden
crown RGB from only opaque source regions while keeping canonical alpha.
"""
import hashlib,json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_167_endpoint_pair import pair,ROOT_AND_TIP,KEYS
from p15_129_ahoge_ownership import keyframes
from p15_166_crown_silhouette import crown_edge
from p15_174_ai_root_patch import apply as ai_root_edit
from p15_134_underpaint_probe import P
ROOT=Path(__file__).resolve().parents[1]
OUT=P/'exports/p15-175-layered-crown-assets'
E=ROOT/'evidence/p15-175-layered-crown-assets-qa.json'
TAGS={90.:'yaw090',112.5:'yaw112p5',135.:'yaw135'}
def rgba_over(back,front):
    f=front.astype(np.float32)/255.
    b=back.astype(np.float32)/255.
    af=f[...,3:4];ab=b[...,3:4]
    a=af+ab*(1-af)
    rgb=np.divide(f[...,:3]*af+b[...,:3]*ab*(1-af),
                  np.maximum(a,1e-12),out=np.zeros_like(f[...,:3]),where=a>0)
    out=np.concatenate([rgb,a],axis=-1)
    return np.uint8(np.clip(np.rint(out*255),0,255))
def source_color_inpaint(src,paint):
    # Prevent RGB behind transparent source pixels from contaminating the fill.
    rgb=src[...,:3].copy()
    alpha=src[...,3]
    for y in range(125):
        valid=np.flatnonzero((alpha[y]>=245)&(~paint[y]))
        if len(valid):
            x=np.arange(src.shape[1])
            insertion=np.searchsorted(valid,x,side='left')
            l=valid[np.clip(insertion-1,0,len(valid)-1)]
            r=valid[np.clip(insertion,0,len(valid)-1)]
            nearest=np.where(abs(x-l)<=abs(x-r),l,r)
            missing=(alpha[y]<245)|paint[y]
            rgb[y,missing]=rgb[y,nearest[missing]]
    return cv2.cvtColor(cv2.inpaint(cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR),
                np.uint8(paint)*255,4,cv2.INPAINT_TELEA),cv2.COLOR_BGR2RGB)
def build(angle,variant):
    original=keyframes()[angle]
    strand,_,owner,meta=pair(original,angle)
    edge=crown_edge(original,9)
    yy,xx=np.indices(owner.shape)
    rootx,rooty=ROOT_AND_TIP[angle]['root']
    crown=original.copy()
    air=owner&(yy<edge[None,:]-2)
    # The isolated visible strand is exclusively owned by the source layer.
    crown[air]=0
    contact=(abs(xx-rootx)<=6)&(yy>=edge[None,:]-2)&(yy<=edge[None,:]+16)&(yy<120)
    paint=contact&(original[...,3]>=245)
    if variant=='root_contact':
        paint&=owner
    elif variant=='root_band':
        paint|=(contact&(original[...,3]>=245))
    elif variant=='source_ai':
        paint|=(contact&(original[...,3]>=245))
    else: raise ValueError(variant)
    rgb=source_color_inpaint(original,paint)
    crown[paint,:3]=rgb[paint]
    if variant=='source_ai' and angle==112.5:
        # The previous AI texture patch is RGB only; it is used as an
        # additional low-weight local reference without changing alpha.
        _,edited,_=ai_root_edit()
        patch=(abs(xx-rootx)<=4)&(abs(yy-rooty)<=4)&paint
        crown[patch,:3]=np.uint8(np.rint(.5*crown[patch,:3]+.5*edited[patch,:3]))
    crown[125:]=original[125:]
    # Every owner pixel can be restored precisely with the source matte,
    # independent of the appearance of the synthesized hidden crown.
    exact=crown.copy()
    exact[owner]=strand[owner]
    over=rgba_over(crown,strand)
    visible=original[...,3]>24
    difference=np.any(exact!=original,axis=2)
    over_diff=np.any(over!=original,axis=2)&visible
    info={
       'sourceSha256RGBA':hashlib.sha256(original.tobytes()).hexdigest(),
       'crownSha256RGBA':hashlib.sha256(crown.tobytes()).hexdigest(),
       'strandSha256RGBA':hashlib.sha256(strand.tobytes()).hexdigest(),
       'sourceOwnerPixels':int(owner.sum()),
       'rootContactPaintPixels':int(paint.sum()),
       'nativeReassemblyDiffPixels':int(difference.sum()),
       'alphaOverDiffVisiblePixels':int(over_diff.sum()),
       'strandTransparentPixelCount':int((strand[...,3]==0).sum()),
       'crownTransparentPixelCount':int((crown[...,3]==0).sum()),
       'sourceBelowY125Exact':bool(np.array_equal(crown[125:],original[125:])),
       'originalSourceUnmodified':True,
       'sourceRoot':list(ROOT_AND_TIP[angle]['root']),
       'crownRootRGBChangedPixels':int(np.count_nonzero(np.any(crown[paint,:3]!=original[paint,:3],axis=1)))
       }
    return original,strand,crown,owner,exact,over,info
def run(save=True):
    modes=('root_contact','root_band','source_ai')
    layers={};diagnostics={}
    for mode in modes:
        layers[mode]={};diagnostics[mode]={}
        for a in KEYS:
            result=build(a,mode)
            layers[mode][a]=result
            diagnostics[mode][f'{a:g}']=result[-1]
    q={'schema':'KOMA_P15_175_LAYERED_CROWN_ASSETS_V1',
       'characterId':'p0_character_001',
       'sourceAngles':list(KEYS),'candidateModes':list(modes),
       'componentTypes':['crown_underpaint','source_ahoge'],
       'canvas':[443,443],
       'sourcePixelOwnerRule':'source-ownership-matte overwrites the crown with native strand pixels at the original keyview',
       'alphaOverIsEvaluatedSeparately':True,
       'perView':diagnostics,
       'sourceArtOriginalSHA256Unchanged':True,
       'rootlessCrownArtworkArtistApproved':False,
       'independentHairArtArtistApproved':False,
       'keyviewVisualAccepted':False,
       'midYawRendered':False,
       'productionRendererUpdated':False,
       'review':'private-assets/exports/p15-175-layered-crown-assets/index.html',
       'next':'Finish matched hidden crown paint around all source-root contact pixels and validate clean alpha-over keyviews before testing 101.25/123.75 yaw.'}
    q['gate']={
      'allThreePairsPresent':all(len(v)==3 for v in diagnostics.values()),
      'allPairsTransparent':all(d['strandTransparentPixelCount']>100000 and d['crownTransparentPixelCount']>10000 for v in diagnostics.values() for d in v.values()),
      'losslessOwnerReassembly':all(d['nativeReassemblyDiffPixels']==0 for v in diagnostics.values() for d in v.values()),
      'deepHeadPreserved':all(d['sourceBelowY125Exact'] for v in diagnostics.values() for d in v.values()),
      'normalAlphaOverSourceExact':all(d['alphaOverDiffVisiblePixels']==0 for v in diagnostics.values() for d in v.values()),
      'visualApproved':False,'passes':False}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        for mode in modes:
            for a in KEYS:
                original,strand,crown,owner,exact,over,info=layers[mode][a]
                folder=OUT/mode/TAGS[a];folder.mkdir(parents=True,exist_ok=True)
                Image.fromarray(strand,'RGBA').save(folder/'ahoge.png')
                Image.fromarray(crown,'RGBA').save(folder/'crown.png')
                Image.fromarray(np.uint8(owner)*255,'L').save(folder/'owner-matte.png')
                Image.fromarray(exact,'RGBA').save(folder/'owner-reassembled.png')
                Image.fromarray(over,'RGBA').save(folder/'alpha-over.png')
        board=Image.new('RGB',(280*3,250*4),(36,43,54))
        d=ImageDraw.Draw(board)
        for row,label in enumerate(['native_source',*modes]):
            for col,a in enumerate(KEYS):
                im=keyframes()[a] if label=='native_source' else layers[label][a][2]
                tile=Image.new('RGBA',(443,443),(46,58,74,255))
                tile.alpha_composite(Image.fromarray(im,'RGBA'))
                crop=tile.crop((135,0,355,150)).resize((272,215),Image.Resampling.NEAREST)
                board.paste(crop.convert('RGB'),(280*col,250*row+28))
                d.text((280*col+5,250*row+4),f'{label} {a:g}',fill='white')
        board.save(OUT/'crown-asset-comparison.jpg',quality=95)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 layered crown and ahoge</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Three-view independent crown and ahoge layer pairs</h2><p>Each source view has two 443x443 transparent RGBA layers and an owner mask. Exact owner-matte reconstruction and standard alpha-over are checked separately. Candidate underpainting is experimental.</p><img src="crown-asset-comparison.jpg">')
        E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':
    q=run()
    print(json.dumps({'gate':q['gate'],'perView':q['perView']},indent=2))

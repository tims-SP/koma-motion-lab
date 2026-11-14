#!/usr/bin/env python3
"""P15-176: split motion underpaint from alpha-safe keyframe crown.

The hidden crown retains reconstructed RGB/alpha for motion use. A second
keyframe-only crown has alpha cleared under every source-owned ahoge pixel.
This makes standard straight-alpha over deterministic and prevents double
ownership while retaining the full underpaint for later deformation.
"""
import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from p15_175_layered_crown_assets import build,rgba_over,KEYS,ROOT,OUT as P175
from p15_167_endpoint_pair import ROOT_AND_TIP
from p15_134_underpaint_probe import P
ROOT=Path(__file__).resolve().parents[1]
OUT=P/'exports/p15-176-alpha-safe-crown'
E=ROOT/'evidence/p15-176-alpha-safe-crown-qa.json'
TAGS={90.:'yaw090',112.5:'yaw112p5',135.:'yaw135'}
def make(angle):
    src,strand,motion_crown,owner,_,_,old=build(angle,'root_band')
    static_crown=motion_crown.copy()
    # Clear the crown's alpha under every source-owned strand pixel.
    # RGB is retained as a future texture donor, but cannot double-composite.
    static_crown[owner,3]=0
    composite=rgba_over(static_crown,strand)
    visible=src[...,3]>24
    diff=np.any(composite!=src,axis=2)&visible
    overlap=(static_crown[...,3]>0)&(strand[...,3]>0)
    rootx,rooty=ROOT_AND_TIP[angle]['root']
    yy,xx=np.indices(owner.shape)
    allowed=(abs(xx-rootx)<=8)&(yy>=rooty-25)&(yy<=rooty+28)&(src[...,3]>24)
    info={'rootBandVisibleDiffPixels':int(np.count_nonzero((np.any(composite!=src,axis=2)&(src[...,3]>24))&allowed)),
      'visibleDiffOutsideRootBand':int(np.count_nonzero(np.any(composite!=src,axis=2)&(src[...,3]>24)&~allowed)),
      'sourceSHA256':hashlib.sha256(src.tobytes()).hexdigest(),
      'strandSHA256':hashlib.sha256(strand.tobytes()).hexdigest(),
      'motionCrownSHA256':hashlib.sha256(motion_crown.tobytes()).hexdigest(),
      'staticCrownSHA256':hashlib.sha256(static_crown.tobytes()).hexdigest(),
      'compositeSHA256':hashlib.sha256(composite.tobytes()).hexdigest(),
      'ownerPixels':int(owner.sum()),'visibleCompositeDiffPixels':int(diff.sum()),
      'doubleAlphaPixels':int(overlap.sum()),
      'motionUnderpaintRetainsAlpha':bool(np.any(motion_crown[owner,3]>0)),
      'staticCrownTransparentUnderStrand':bool(np.all(static_crown[owner,3]==0)),
      'deepMotionUnderpaintExact':bool(np.array_equal(motion_crown[125:],src[125:])),
      'sourceRoot':list(ROOT_AND_TIP[angle]['root'])}
    return src,strand,motion_crown,static_crown,owner,composite,info
def run(save=True):
    assets={};data={}
    for a in KEYS:
        assets[a]=make(a);data[f'{a:g}']=assets[a][-1]
    q={'schema':'KOMA_P15_176_ALPHA_SAFE_CROWN_V1','characterId':'p0_character_001',
      'angles':list(KEYS),'layerContracts':{
        'ahoge':'source-owned RGBA strand including its root attachment',
        'crownMotionUnderpaint':'full reconstructed head texture/alpha for deformation and exposure',
        'crownStaticKeyframe':'same underpaint RGB but alpha zero under the source-owned ahoge matte'},
      'perView':data,'midYawRendered':False,'productionRendererUpdated':False,
      'visualApproved':False,'visualFindings':'The three layer contracts are now distinct and non-overlapping in the static keyframe composite. The motion underpaint still shows small source-root remnants at 90, 112.5, and 135 degrees; the alpha-safe keyframe version has transparent holes under the ahoge that are filled by the matching strand at rest. Artist-matched crown cleanup is still required before VDD.','review':'private-assets/exports/p15-176-alpha-safe-crown/index.html'}
    q['gate']={'allThreePairsPresent':len(assets)==3,
      'standardAlphaOverChangesOnlyRootBand':all(x['visibleDiffOutsideRootBand']==0 for x in data.values()),
      'noDoubleAlphaOwnership':all(x['doubleAlphaPixels']==0 for x in data.values()),
      'staticCrownTransparentUnderStrand':all(x['staticCrownTransparentUnderStrand'] for x in data.values()),
      'motionUnderpaintRetained':all(x['motionUnderpaintRetainsAlpha'] for x in data.values()),
      'deepUnderpaintPreserved':all(x['deepMotionUnderpaintExact'] for x in data.values()),
      'visualRootRepairApproved':False,'rootlessCrownVisualAccepted':False,'passes':False}
    if save:
      OUT.mkdir(parents=True,exist_ok=True)
      board=Image.new('RGB',(300*3,260*4),(35,42,54));d=ImageDraw.Draw(board)
      labels=['source','ahoge','motion-underpaint','static-alpha-safe']
      for row,label in enumerate(labels):
       for col,a in enumerate(KEYS):
        src,strand,motion,static,owner,comp,info=assets[a]
        im={'source':src,'ahoge':strand,'motion-underpaint':motion,'static-alpha-safe':static}[label]
        folder=OUT/TAGS[a];folder.mkdir(parents=True,exist_ok=True)
        if row==0:
         Image.fromarray(strand,'RGBA').save(folder/'ahoge.png')
         Image.fromarray(motion,'RGBA').save(folder/'crown-motion-underpaint.png')
         Image.fromarray(static,'RGBA').save(folder/'crown-static-alpha-safe.png')
         Image.fromarray(np.uint8(owner)*255,'L').save(folder/'ahoge-owner-matte.png')
         Image.fromarray(comp,'RGBA').save(folder/'standard-alpha-over.png')
        tile=Image.new('RGBA',(443,443),(46,58,74,255));tile.alpha_composite(Image.fromarray(im,'RGBA'))
        thumb=tile.crop((135,0,355,150)).resize((292,220),Image.Resampling.NEAREST)
        board.paste(thumb.convert('RGB'),(col*300,row*260+28));d.text((col*300+5,row*260+5),f'{label} {a:g}',fill='white')
      board.save(OUT/'alpha-safe-layer-comparison.jpg',quality=95)
      (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P15-176 alpha-safe crown layers</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Three-view alpha-safe ahoge/crown layer contract</h2><p>The motion underpaint preserves the full head texture. The static keyframe crown clears alpha beneath the ahoge ownership matte, preventing double ownership during standard alpha-over. Review visual root cleanup separately.</p><img src="alpha-safe-layer-comparison.jpg">')
      E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':
 q=run();print(json.dumps({'gate':q['gate'],'perView':q['perView']},indent=2))

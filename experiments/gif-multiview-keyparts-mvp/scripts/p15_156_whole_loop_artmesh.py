#!/usr/bin/env python3
"""Source-owned complete upper-loop deformation with an anchored crown boundary.

The single connected, visible upper-crown loop is treated as one ArtMesh
material. This test does not imply independently painted hidden roots.
"""
import json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_129_ahoge_ownership import keyframes
from p15_134_underpaint_probe import P,compose,move,background_rgb
from p15_153_source_topology import extract,ROOT
OUT=P/'exports/p15-156-whole-loop-artmesh'
E=ROOT/'evidence/p15-156-whole-loop-artmesh-qa.json'
ROOT_Y=54
TIP_Y=12
def warp_loop(source,shift):
    yy,xx=np.indices(source.shape[:2],dtype=np.float32)
    t=np.clip((ROOT_Y-yy)/(ROOT_Y-TIP_Y),0,1)
    # Smooth source-to-destination displacement in x; zero at the root line.
    t=t*t*(3-2*t)
    return cv2.remap(source,xx-shift*t,yy,cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
def make_frame(source,loop,base,dx,kind):
    moved=move(loop,dx,0) if kind=='rigid' else warp_loop(loop,dx)
    return compose(base,moved),moved
def analyze(save=True):
    source=keyframes()[90.]
    assets,base,parts=extract(source)
    loop=assets['loop_visible']
    assert parts['otherUpperPixels']==0
    frames={}
    metrics={}
    yy,xx=np.indices(source.shape[:2])
    for dx in (0,2,4,8):
        for kind in ('rigid','anchored'):
            label=f'{kind}_{dx:02d}'
            image,moved=make_frame(source,loop,base,dx,kind)
            # 0 shift should use the exact key source pixels.
            if dx==0:assert np.array_equal(image,source)
            holes=(source[...,3]>160)&(image[...,3]<64)
            exposed_air=holes&(yy<ROOT_Y)
            exposed_crown=holes&(yy>=ROOT_Y)&(yy<102)
            root_roi=np.s_[46:58,170:307]
            metrics[label]={
                'exposedFormerOpaquePixels':int(holes.sum()),
                'exposedAirPixels':int(exposed_air.sum()),
                'exposedCrownPixels':int(exposed_crown.sum()),
                'rootBoundaryBelowExact':bool(np.array_equal(image[ROOT_Y:],source[ROOT_Y:])),
                'sourcePartBelowRootExact':bool(np.array_equal(moved[ROOT_Y:],loop[ROOT_Y:])),
                'rootRGBMAE':round(float(np.abs(background_rgb(image)[root_roi]-background_rgb(source)[root_roi]).mean()),4),
                'localRGBMAE':round(float(np.abs(background_rgb(image)[0:110,160:320]-background_rgb(source)[0:110,160:320]).mean()),4),
            }
            frames[label]=image
    qa={'schema':'KOMA_P15_156_WHOLE_VISIBLE_LOOP_ARTMESH_V1',
        'characterId':'p0_character_001','sourceYaw':90.,
        'material':'one complete connected visible-source upper loop',
        'sourceLoopPixels':parts['loopVisiblePixels'],
        'topology':'source-owned connected silhouette; pixel-sampled smooth inverse warp with root fixed',
        'rootAnchorY':ROOT_Y,'tipAnchorY':TIP_Y,'offsets':[0,2,4,8],
        'results':metrics,
        'nativeSourcePreserved':True,
        'zeroShiftPixelExact':bool(np.array_equal(frames['anchored_00'],source)),
        'independentHiddenRootAuthored':False,
        'artistApprovedPhysicalLoop':False,
        'continuousYawVisualAccepted':False,
        'review':'private-assets/exports/p15-156-whole-loop-artmesh/index.html',
        'next':'Evaluate root-boundary visual continuity at 8px and prepare matched source-owned loop shapes at 112.5° and 135° only after local render acceptance.'}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        panel=Image.new('RGB',(350*4,390*3),(36,42,54));draw=ImageDraw.Draw(panel)
        for row,label in enumerate(('reference','rigid','anchored')):
            for col,dx in enumerate((0,2,4,8)):
                im=source if label=='reference' else frames[f'{label}_{dx:02d}']
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(im,'RGBA'))
                crop=tile.crop((153,0,314,125)).resize((344,337),Image.Resampling.NEAREST)
                panel.paste(crop.convert('RGB'),(col*350,row*390+30))
                draw.text((col*350+7,row*390+7),f'{label} / {dx}px',fill='white')
                if label!='reference':
                    Image.fromarray(im,'RGBA').save(OUT/f'{label}-shift-{dx:02d}.png')
        panel.save(OUT/'comparison.jpg',quality=94)
        Image.fromarray(loop,'RGBA').save(OUT/'whole-visible-loop.png')
        Image.fromarray(base,'RGBA').save(OUT/'underlying-source.png')
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 whole-loop anchored ArtMesh</title><style>body{background:#202832;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>90° complete visible-loop ArtMesh</h2><p>Top original, middle rigid loop translation, bottom smooth anchor-preserving loop warp. Displacement is 0/2/4/8px. Crown pixels below root stay source-owned.</p><img src="comparison.jpg">')
        E.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    return qa
if __name__=='__main__':
 q=analyze()
 print(json.dumps(q['results'],indent=2))

#!/usr/bin/env python3
"""Extract pixel-exact visible crown-strand ownership from confirmed P0 source keys.

Separates (1) suspended loop and (2) fine detached left strand from the
actual source, retaining every source pixel. This is visible-source topology
only; hidden roots and anatomical correspondence require authored paint.
"""
import json,hashlib
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_129_ahoge_ownership import keyframes,ANGLES
from p15_128_keyart_registration import frame_interp,jumps
from p15_134_underpaint_probe import P,compose
ROOT=Path(__file__).resolve().parent.parent
OUT=P/'exports/p15-153-source-topology'
E=ROOT/'evidence/p15-153-source-topology-qa.json'
# The confirmed 90° source has an arched major strand and a secondary thin
# stroke on its left. We preserve separate source identities in the extraction.
YTOP=54
VIEWS=(90.,112.5,135.)

def components(source):
    alpha=source[...,3]>24
    yy,xx=np.indices(alpha.shape)
    # Keep only free-standing top-of-crown visible hair; lower roots retained
    # in canonical head layer instead of inventing hidden material.
    floating=(alpha&(yy<YTOP))
    n, labels,stats,centroids=cv2.connectedComponentsWithStats(floating.astype(np.uint8),8)
    comps=[]
    for i in range(1,n):
        size=int(stats[i,cv2.CC_STAT_AREA])
        if size<6:continue
        mask=(labels==i)
        comps.append({'size':size,'bbox':[int(v) for v in stats[i,:4]],'centroid':[round(float(v),2) for v in centroids[i]],'mask':mask})
    comps.sort(key=lambda x:x['size'],reverse=True)
    return comps,floating

def extract(source):
    comps,upper=components(source)
    # Source above crown is potentially connected to hair at y54; retain an
    # exact partition regardless of component count.
    major=np.zeros(upper.shape,dtype=bool)
    minor=np.zeros_like(major)
    if comps: major=comps[0]['mask']
    for c in comps[1:]:minor|=c['mask']
    remaining=source.copy();remaining[upper]=0
    pieces={}
    for name,mask in [('loop_visible',major),('other_upper_strands',minor)]:
        layer=source.copy();layer[~mask]=0;pieces[name]=layer
    rebuilt=remaining.copy()
    for name,mask in [('loop_visible',major),('other_upper_strands',minor)]:
        rebuilt[mask]=pieces[name][mask]
    # Pixel alpha<=24 is still source-owned background and stays intact.
    assert np.array_equal(rebuilt,source)
    return pieces,remaining,{'components':[{k:v for k,v in c.items() if k!='mask'} for c in comps],
        'loopVisiblePixels':int(major.sum()),'otherUpperPixels':int(minor.sum()),
        'upperTotal':int(upper.sum()),'recompositionExact':True}

def render(save=True):
    keys=keyframes()
    per_view={}
    source_layers={}
    for a in VIEWS:
        parts,remaining,info=extract(keys[a])
        per_view[f'{a:g}']=info
        source_layers[a]=(parts,remaining)
    # Control: the source-equivalent recomposition must stay pixel-exact.
    control=frame_interp(keys[90.],keys[112.5],keys[135.])
    # Experimental selective movement: use same exact source-owner per view,
    # never overlay new art on existing native loop.
    motion=[]
    for angle in ANGLES:
        if angle in VIEWS:
            motion.append(keys[angle].copy())
            continue
        start,end=(90.,112.5) if angle<112.5 else (112.5,135.)
        t=(angle-start)/(end-start)
        owner=start if t<=.5 else end
        loop=source_layers[owner][0]['loop_visible']
        # Tiny rigid displacement, original upper strand removed from remainder.
        yy,xx=np.indices(loop.shape[:2])
        dx=int(round((t if owner==start else t-1)*4))
        transformed=cv2.warpAffine(loop,np.float32([[1,0,dx],[0,1,0]]),(443,443),
                                   flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
        rest=source_layers[owner][1]
        minor=source_layers[owner][0]['other_upper_strands']
        motion.append(compose(compose(rest,minor),transformed))
    q={'schema':'KOMA_P15_153_CANONICAL_HAIR_STRAND_SOURCE_V1',
       'characterId':'p0_character_001','sourceAngles':list(VIEWS),'renderAngles':list(ANGLES),
       'pixelExactPartRecomposition':True,'sourceSourceKeyframesUnchanged':True,
       'perView':per_view,
       'sourceFreeLoopType':'single connected visible-source alpha component per key, above a diagnostic horizontal crown cutoff',
       'separateSecondaryStrand':False,
       'visualFindings':'The original profile displays a broad loop and fine adjacent stroke; their visible alpha merges into one connected component at all three tested viewpoints. Source reconstruction is lossless, but connected-component partitioning does not distinguish their physical roots. A generated short-root patch depicts different anatomy.',
       'motionComparison':{'canonicalMaxAdjacentRGBMAE':max(jumps(control)),
          'sourceOwnedMotionMaxAdjacentRGBMAE':max(jumps(motion)),
          'canonicalAdjacentRGBMAE':jumps(control),'sourceOwnedAdjacentRGBMAE':jumps(motion)},
       'artistApprovedRootTopology':False,'hiddenRootScalpPaintComplete':False,
       'crossViewPhysicalCorrespondence':False,'fullYawVisualAccepted':False,
       'selectedForProduction':False,
       'review':'private-assets/exports/p15-153-source-topology/index.html',
       'next':'Author a loop plus fine-strand asset from confirmed visible-source shapes, including occluded root underpaint and matching keyview coordinates. Gate closeup before interpolation.'}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        for angle in VIEWS:
            directory=OUT/('yaw'+f'{angle:g}'.replace('.','p'));directory.mkdir(exist_ok=True)
            for label,asset in source_layers[angle][0].items():
                Image.fromarray(asset,'RGBA').save(directory/(label+'.png'))
            Image.fromarray(source_layers[angle][1],'RGBA').save(directory/'remaining-head.png')
        board=Image.new('RGB',(340*3,360*3),(37,43,53));d=ImageDraw.Draw(board)
        for col,angle in enumerate(VIEWS):
            layers=source_layers[angle][0]
            for row,(label,image) in enumerate([('original',keys[angle]),('visible loop',layers['loop_visible']),('other upper',layers['other_upper_strands'])]):
                bg=Image.new('RGBA',(443,443),(49,61,78,255));bg.alpha_composite(Image.fromarray(image,'RGBA'))
                board.paste(bg.convert('RGB').resize((332,332),Image.Resampling.LANCZOS),(340*col,360*row+24))
                d.text((340*col+6,360*row+5),f'{angle:g} {label}',fill='white')
        board.save(OUT/'source-ownership.jpg',quality=94)
        compare=Image.new('RGB',(310*5,345*2),(37,43,53));draw=ImageDraw.Draw(compare)
        for row,(label,frames) in enumerate([('Canonical',control),('Source-owned test',motion)]):
            for col,(angle,image) in enumerate(zip(ANGLES,frames)):
                bg=Image.new('RGBA',(443,443),(49,61,78,255));bg.alpha_composite(Image.fromarray(image,'RGBA'))
                compare.paste(bg.convert('RGB').resize((303,303),Image.Resampling.LANCZOS),(310*col,345*row+25))
                draw.text((310*col+5,345*row+5),f'{label} {angle:g}',fill='white')
        compare.save(OUT/'yaw-comparison.jpg',quality=94)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 source hair identities</title><style>body{background:#202733;color:white;font:16px system-ui}img{max-width:100%}</style><h2>P0 canonical loop and fine strand visible ownership</h2><p>Extracted directly and losslessly from three source keyviews. Only visible source is present: root underpaint remains a separate art requirement.</p><img src="source-ownership.jpg"><h2>Motion study</h2><img src="yaw-comparison.jpg">')
        E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':
    q=render()
    print(json.dumps({'parts':q['perView'],'motion':q['motionComparison']},indent=2))

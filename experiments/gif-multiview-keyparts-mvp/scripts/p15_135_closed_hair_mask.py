#!/usr/bin/env python3
"""Closed hair region extraction and underpaint reveal stress diagnostics."""
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
from p15_134_underpaint_probe import P, SOURCE, HAIR, rgba, transform, compose, move, background_rgb

ROOT = Path(__file__).resolve().parent.parent
OUT = P/'exports/p15-135-closed-hair'
EVIDENCE = ROOT/'evidence/p15-135-closed-hair-qa.json'

def closed_mask(source):
    base = rgba(HAIR)[..., 3] > 0
    alpha = source[..., 3] > 0
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(13,13))
    enclosed = cv2.morphologyEx(base.astype('uint8'),cv2.MORPH_CLOSE,kernel)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(enclosed, 8)
    mass = np.zeros_like(enclosed)
    for i in range(1,n):
        if stats[i,cv2.CC_STAT_AREA]>55 and stats[i,cv2.CC_STAT_TOP]<270:
            mass[lab==i]=1
    contours,_=cv2.findContours(mass,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    filled=np.zeros_like(mass)
    cv2.drawContours(filled,contours,-1,1,-1)
    rr,gg,bb=[source[...,i].astype(np.int16) for i in range(3)]
    yy,xx=np.indices(alpha.shape)
    skin=(rr>gg+14)&(gg>bb+3)&(rr>123)&(gg>86)&(bb<205)
    protect=skin&(xx>224)&(yy>151)&(yy<330)
    eye_oval=(((xx-319)/32)**2+((yy-244)/65)**2)<1.
    region=filled.astype(bool)&alpha&~(protect|(eye_oval&(yy>170)))
    return region, {'seedPixels':int(base.sum()),'closedPixels':int(region.sum()),'contourCount':len(contours)}

def split(source,region):
    hair=source.copy();hair[~region]=0
    rest=source.copy();rest[region]=0
    rebuilt=rest.copy();rebuilt[region]=hair[region]
    assert np.array_equal(rebuilt,source)
    return hair,rest

def assess(save=True):
    source=rgba(SOURCE)
    under=transform(np.asarray(Image.open(P/'p15-134-occlusion-underpaint/underpaint-native.png').convert('RGBA').resize((443,443),Image.Resampling.LANCZOS)))
    mask,detail=closed_mask(source)
    new_hair,rest=split(source,mask)
    old_hair=rgba(HAIR)
    old_rest=split(source,old_hair[...,3]>0)[1]
    def trial(hair,base,dx):
        return compose(compose(under,base),move(hair,dx,0))
    views={'pigment':{v:trial(old_hair,old_rest,v) for v in (0,12,24)},
           'closed':{v:trial(new_hair,rest,v) for v in (0,12,24)}}
    roi=np.s_[125:350,125:390]
    errors={name:{str(v):round(float(np.abs(background_rgb(img)[roi]-background_rgb(source)[roi]).mean()),4) for v,img in data.items()} for name,data in views.items()}
    holes={name:{str(v):int(((source[...,3]>160)&(img[...,3]<64)).sum()) for v,img in data.items()} for name,data in views.items()}
    n,_,stats,_=cv2.connectedComponentsWithStats(mask.astype('uint8'),8)
    components=sorted([int(stats[i,cv2.CC_STAT_AREA]) for i in range(1,n) if stats[i,cv2.CC_STAT_AREA]>20],reverse=True)
    qa={'schema':'KOMA_P15_135_CLOSED_HAIR_REVEAL_V1','characterId':'p0_character_001','angle':112.5,
        'sourceRGBAExactAfterSplit':True,'pixelOwnershipExclusive':True,'maskMethod':'filled pigment-derived contours with protected facial features; provisional image-space boundary',
        'maskInfo':detail,'connectedRegionsOver20Pixels':components,'displacementRGBMAE':errors,'displacementAlphaHoles':holes,
        'referenceGeometryArtistApproved':False,'semanticArtMeshGeometryApproved':False,'physicalUnderpaintRegistrationApproved':False,
        'visualAccepted':False,'review':'private-assets/exports/p15-135-closed-hair/index.html',
        'next':'Inspect masks and visible ear/face/neck seams, then obtain artist-corrected coherent hair boundary and registered hidden material.'}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        Image.fromarray(mask.astype('uint8')*255,'L').save(OUT/'hair-region-mask.png')
        Image.fromarray(new_hair,'RGBA').save(OUT/'hair-visible.png')
        Image.fromarray(rest,'RGBA').save(OUT/'rest-visible.png')
        board=Image.new('RGB',(350*4,400*2),(37,42,52));draw=ImageDraw.Draw(board)
        for row,(name,images) in enumerate(views.items()):
            for col,(description,arr) in enumerate([('source',source)]+[(f'shift-{v}',images[v]) for v in (0,12,24)]):
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(arr,'RGBA'))
                board.paste(tile.convert('RGB').resize((344,344),Image.Resampling.LANCZOS),(350*col,400*row+32))
                draw.text((350*col+8,400*row+8),f'{name} / {description}',fill='white')
        board.save(OUT/'comparison.jpg',quality=94)
        for name,images in views.items():
            for v,img in images.items():Image.fromarray(img,'RGBA').save(OUT/f'{name}-shift-{v:02}.png')
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 hair visibility boundary</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>112.5° hair-region reveal</h2><p>Source image and 0/12/24 px hair offsets using existing pigment mask (top) versus closed boundary (bottom). Underpainting and ArtMesh geometry require visual approval.</p><img src="comparison.jpg">')
        EVIDENCE.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    return qa

if __name__=='__main__':
    r=assess()
    print(json.dumps({k:r[k] for k in ('maskInfo','connectedRegionsOver20Pixels','sourceRGBAExactAfterSplit','displacementRGBMAE','displacementAlphaHoles')},indent=2))

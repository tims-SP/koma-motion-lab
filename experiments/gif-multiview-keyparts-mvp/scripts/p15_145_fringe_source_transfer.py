#!/usr/bin/env python3
"""Conservative registered fringe texture transfer with a single source owner.

A cutout of the original source hair supplies its exact silhouette/alpha and
the independent fringe painting contributes texture only in jointly visible,
face-safe pixels. Hidden source art is used for displacement tests.
"""
import json,hashlib
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_144_bangs_registration import old_bangs_mask,eye_mask
from p15_134_underpaint_probe import P,SOURCE,rgba,compose,move,background_rgb
from p15_129_ahoge_ownership import keyframes,ANGLES
from p15_128_keyart_registration import frame_interp,jumps
ROOT=Path(__file__).resolve().parent.parent
OUT=P/'exports/p15-145-fringe-source-transfer'
E=ROOT/'evidence/p15-145-fringe-source-transfer-qa.json'
PRIOR=P/'exports/p15-144-bangs-registration'
PARAMS=(.25,.5,.75,1.)
def soft(binary,sigma=3):
    return np.clip(cv2.GaussianBlur(binary.astype(np.float32),(0,0),sigma),0,1)
def paint_registered(source,art,mask,strength):
    sourcef=source.astype(np.float32)
    artf=art.astype(np.float32)
    yy,xx=np.indices(mask.shape)
    # Reuse original fully opaque silhouette as the only visible owner.
    # Remove all material where the source feature roles say face/eye.
    protected=eye_mask()
    valid=(art[...,3]>64)&mask&~protected
    # Color compatibility is a heuristic: avoid replacing ink with disconnected shading.
    diff=np.abs(sourcef[...,:3]-artf[...,:3]).mean(axis=2)
    compatibility=np.clip((90-diff)/70,0,1)
    stroke_weight=soft(valid,2)*compatibility*strength*valid
    stroke_weight*=source[...,3].astype(np.float32)/255
    out=source.copy()
    out[...,:3]=np.uint8(np.clip(np.round(sourcef[...,:3]*(1-stroke_weight[...,None])
                                           +artf[...,:3]*stroke_weight[...,None]),0,255))
    # Source alpha is preserved; transparent pixels remain transparent.
    out[...,3]=source[...,3]
    out[source[...,3]==0]=source[source[...,3]==0]
    return out,stroke_weight
def cutout(original,mask):
    visible=original.copy()
    visible[~mask]=0
    remainder=original.copy()
    remainder[mask]=0
    rebuilt=remainder.copy();rebuilt[mask]=visible[mask]
    assert np.array_equal(rebuilt,original)
    return visible,remainder
def audit(save=True):
    source=rgba(SOURCE)
    art=rgba(PRIOR/'registered-bangs.png')
    under=rgba(P/'exports/p15-137-occlusion-regions/eye_08-underpaint.png')
    mask=old_bangs_mask(source)
    source_hair,rest=cutout(source,mask)
    variants={'canonical':{'image':source.copy(),'texturePixels':0,'textureWeightTotal':0.}}
    for power in PARAMS:
        adapted,weights=paint_registered(source,art,mask,power)
        variants[f'transfer_{int(power*100):03d}']={'image':adapted,
            'texturePixels':int((weights>.01).sum()),
            'textureWeightTotal':round(float(weights.sum()),2)}
    qa={'schema':'KOMA_P15_145_FRINGE_TEXTURE_OWNERSHIP_V1','characterId':'p0_character_001',
        'yaw':112.5,'sourceOwner':'native 112.5 forehead and hair silhouette',
        'registeredTextureOwner':'P15-143 independently generated front-bangs pixels',
        'maskPixels':int(mask.sum()),'variants':{},'sourceKeyRGBAUnmodified':True,
        'sourceMaskRecompositionExact':True,'eyesProtected':True,
        'fullYawVisualAccepted':False,'artistApprovedStrandIdentity':False,
        'hiddenScalpGeometryApproved':False,
        'review':'private-assets/exports/p15-145-fringe-source-transfer/index.html'}
    keys=keyframes()
    scores={}
    for name,d in variants.items():
        image=d['image']
        assert np.array_equal(image[...,3],source[...,3])
        changed=np.any(image!=source,axis=2)
        assert not np.any(changed&~mask)
        assert not np.any(changed&eye_mask())
        frames=frame_interp(keys[90.],image,keys[135.])
        jump=jumps(frames)
        scores[name]={'maxAdjacentRGBMAE':max(jump),'adjacentRGBMAE':jump}
        cut,remainder=cutout(image,mask)
        displacement={}
        for dx in (0,12,24):
            # For zero displacement, return the frame itself exactly. This is a
            # source-preserving compositing identity; at nonzero displacement
            # the underpaint replaces newly exposed old hair pixels.
            frame=image.copy() if dx==0 else compose(compose(under,remainder),move(cut,dx,0))
            hole=(source[...,3]>160)&(frame[...,3]<64)
            roi=np.s_[160:310,245:395]
            displacement[str(dx)]={'alphaHoles':int(hole.sum()),
                  'faceRGBMAE':round(float(np.abs(background_rgb(frame)[roi]-background_rgb(source)[roi]).mean()),4)}
            if save and name in ('canonical','transfer_025','transfer_050','transfer_075'):
                directory=OUT/name;directory.mkdir(parents=True,exist_ok=True)
                Image.fromarray(frame,'RGBA').save(directory/f'hair-shift-{dx:02d}.png')
        qa['variants'][name]={**scores[name],'texturePixels':d['texturePixels'],
                              'textureWeightTotal':d['textureWeightTotal'],
                              'zeroOffsetSourceExact':bool(np.array_equal(image,source)),
                              'native90And135Exact':bool(np.array_equal(frames[0],keys[90.]) and np.array_equal(frames[-1],keys[135.])),
                              'stress':displacement}
        if save:
            directory=OUT/name;directory.mkdir(parents=True,exist_ok=True)
            Image.fromarray(image,'RGBA').save(directory/'keyview.png')
            for angle,frame in zip(ANGLES,frames):
                Image.fromarray(frame,'RGBA').save(directory/(f'yaw{angle:06.2f}'.replace('.','p')+'.png'))
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        selected=('canonical','transfer_025','transfer_050','transfer_075')
        board=Image.new('RGB',(310*5,350*len(selected)),(35,41,53));draw=ImageDraw.Draw(board)
        for j,name in enumerate(selected):
            for i,a in enumerate(ANGLES):
                frame=rgba(OUT/name/(f'yaw{a:06.2f}'.replace('.','p')+'.png'))
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
                board.paste(tile.convert('RGB').resize((305,305),Image.Resampling.LANCZOS),(310*i,350*j+30))
                draw.text((310*i+6,350*j+7),f'{name} {a:g}°',fill='white')
        board.save(OUT/'yaw-comparison.jpg',quality=94)
        static=Image.new('RGB',(350*4,400*2),(35,41,53));d=ImageDraw.Draw(static)
        for row,name in enumerate(('canonical','transfer_050')):
            for col,(label,pth) in enumerate([('key',OUT/name/'keyview.png')]+[(f'{x}px',OUT/name/f'hair-shift-{x:02d}.png') for x in (0,12,24)]):
                image=rgba(pth);tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(image,'RGBA'))
                static.paste(tile.convert('RGB').resize((344,344),Image.Resampling.LANCZOS),(350*col,400*row+32))
                d.text((350*col+6,400*row+8),f'{name} {label}',fill='white')
        static.save(OUT/'stress-comparison.jpg',quality=94)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 front hair source transfer</title><style>body{font:16px system-ui;background:#202833;color:white}img{max-width:100%}</style><h2>90–135° single-owner front fringe texture</h2><p>Native canonical hair owns the final visible geometry. Independent painting contributes only masked texture. Source face and eye remain unchanged.</p><img src="yaw-comparison.jpg"><h2>Local hair movement</h2><img src="stress-comparison.jpg">')
        E.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    return qa
if __name__=='__main__':
    q=audit()
    print(json.dumps({name:{'error':v['maxAdjacentRGBMAE'],'texturePixels':v['texturePixels'],'face24':v['stress']['24']['faceRGBMAE'],'holes24':v['stress']['24']['alphaHoles']} for name,v in q['variants'].items()},indent=2))

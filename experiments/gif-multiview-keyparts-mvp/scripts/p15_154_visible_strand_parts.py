#!/usr/bin/env python3
"""Manually bounded source-pixel strand ownership at the 90° crown.

Distinguishes a left hairline stroke from the principal loop where visible.
This produces source-exact RGBA layers, a local motion stress test and honest
visibility limits; it does not claim hidden roots or physical strand identity.
"""
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
from p15_129_ahoge_ownership import keyframes
from p15_134_underpaint_probe import P,compose,move,background_rgb
ROOT=Path(__file__).resolve().parent.parent
OUT=P/'exports/p15-154-visible-strand-parts'
E=ROOT/'evidence/p15-154-visible-strand-parts-qa.json'
CUT=55
def split(source):
    yy,xx=np.indices(source.shape[:2])
    visible=(source[...,3]>24)&(yy<CUT)
    # The lower-left stroke shares visible pixels with the large loop. This
    # hand-authored bounded separation is a diagnostic semantic hypothesis.
    # No unobserved crown pixels are classified.
    fine=(visible&(yy>=27)&(xx<=np.interp(yy,[27,35,45,54],[190,188,186,187])))
    loop=visible&~fine
    remaining=source.copy();remaining[visible]=0
    assets={}
    for name,mask in [('main_loop_visible',loop),('left_fine_visible',fine)]:
        image=source.copy();image[~mask]=0;assets[name]=image
    composed=remaining.copy()
    composed[loop]=assets['main_loop_visible'][loop]
    composed[fine]=assets['left_fine_visible'][fine]
    assert np.array_equal(source,composed)
    return assets,remaining,{'sourceExact':True,'loopPixels':int(loop.sum()),
     'finePixels':int(fine.sum()),'exclusive':not np.any(loop&fine),
     'fineBBox':bbox(fine),'loopBBox':bbox(loop),
     'ownershipMethod':'manually bounded split at left visible line; root attachment still source-owned below y55'}
def bbox(mask):
    y,x=np.where(mask)
    return [int(x.min()),int(y.min()),int(x.max()),int(y.max())] if len(x) else None
def evaluate(save=True):
    source=keyframes()[90.]
    assets,base,info=split(source)
    trials={}
    output={}
    for amount in (0,2,4,8):
        loop=assets['main_loop_visible']
        minor=move(assets['left_fine_visible'],amount,0)
        result=compose(compose(base,loop),minor) if amount else source.copy()
        holes=(source[...,3]>160)&(result[...,3]<64)
        seam=holes[25:83,175:288]
        trials[str(amount)]={'sourceExact':bool(np.array_equal(result,source)),
          'newAlphaHoles':int(holes.sum()),'rootROIAlphaHoles':int(seam.sum()),
          'rootROIRGBMAE':round(float(np.abs(background_rgb(result)[25:83,175:288]-
                            background_rgb(source)[25:83,175:288]).mean()),4)}
        output[amount]=result
    result={'schema':'KOMA_P15_154_VISIBLE_SOURCE_STRAND_PARTS_V1',
      'characterId':'p0_character_001','sourceYaw':90.,
      'sourcePixelOwnership':info,'motionStress':trials,
      'sourceArtUnmodified':True,'sourcePaintOnly':True,
      'hiddenRootPaintAvailable':False,'rootGeometryVerified':False,
      'physicalStrandIdentityArtistApproved':False,'independentMotionVisuallyApproved':False,
      'crossViewCorrespondenceVerified':False,'fullYawVisualAccepted':False,
      'review':'private-assets/exports/p15-154-visible-strand-parts/index.html',
      'next':'Paint and register two source-matched underlying root patches at the crown; then repeat independent displacement with zero junction voids before cross-view interpolation.'}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        Image.fromarray(base,'RGBA').save(OUT/'remaining-head.png')
        for name,im in assets.items():Image.fromarray(im,'RGBA').save(OUT/(name+'.png'))
        board=Image.new('RGB',(355*4,405*2),(33,41,52));d=ImageDraw.Draw(board)
        views=[('Original source',source),('Major visible loop',assets['main_loop_visible']),
               ('Left fine stroke',assets['left_fine_visible']),('Remaining crown',base)]
        views+= [(f'Fine strand offset {x}px',output[x]) for x in (0,2,4,8)]
        for i,(name,img) in enumerate(views):
            tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(img,'RGBA'))
            x=(i%4)*355;y=(i//4)*405
            board.paste(tile.convert('RGB').resize((347,347),Image.Resampling.LANCZOS),(x,y+28))
            d.text((x+6,y+6),name,fill='white')
            if i>=4: Image.fromarray(img,'RGBA').save(OUT/f'fine-shift-{(0,2,4,8)[i-4]:02}.png')
        board.save(OUT/'comparison.jpg',quality=95)
        close=Image.new('RGB',(344*4,385),(33,41,52));draw=ImageDraw.Draw(close)
        for i,(name,img) in enumerate([('Source',source),('Source-owned split',output[0]),
              ('2px shift',output[2]),('8px shift',output[8])]):
            tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(img,'RGBA'))
            crop=tile.crop((159,0,302,125)).resize((337,343),Image.Resampling.NEAREST)
            close.paste(crop.convert('RGB'),(344*i,29))
            draw.text((344*i+8,6),name,fill='white')
        close.save(OUT/'attachment-closeup.jpg',quality=96)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 visible hair ownership</title><style>body{background:#202832;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>90° canonical loop and fine-hair layers</h2><p>Source-exact visible pixel partition, with a manually bounded split where strokes connect. 0/2/4/8px independent displacement tests show whether exposed root anatomy is sufficiently painted.</p><img src="comparison.jpg"><h2>Root junction close-up</h2><img src="attachment-closeup.jpg">')
        E.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result
if __name__=='__main__':
 q=evaluate()
 print(json.dumps({'parts':q['sourcePixelOwnership'],'motion':q['motionStress']},indent=2))

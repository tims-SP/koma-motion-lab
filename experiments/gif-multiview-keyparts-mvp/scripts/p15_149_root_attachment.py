#!/usr/bin/env python3
"""Blend independent ahoge attachment into a painted crown with source-owned visibility.

Native keys and native source are unchanged. Only a 112.5° compositing
candidate is rendered; independently painted root anatomy is not verified.
"""
import json, hashlib
from pathlib import Path
import cv2, numpy as np
from PIL import Image, ImageDraw
from p15_148_ahoge_registration import shift
from p15_148_native_ahoge_review import actual_source, PNG
from p15_134_underpaint_probe import SOURCE, rgba, compose, background_rgb, P
from p15_129_ahoge_ownership import ANGLES, keyframes
from p15_128_keyart_registration import frame_interp, jumps

ROOT=Path(__file__).resolve().parent.parent
OUT=P/'exports/p15-149-root-attachment'
E=ROOT/'evidence/p15-149-root-attachment-qa.json'
PARAMS={'crown_fade_65':(46,65),'crown_fade_78':(49,78),'crown_fade_90':(52,90)}

def smoothstep(t):
    t=np.clip(t,0.,1.)
    return t*t*(3.-2.*t)

def compose_crown(original, fitted, start, finish):
    assert start<finish
    yy,xx=np.indices((443,443),dtype=np.float32)
    original_loop=(original[...,3]>32)&(yy<56)&(xx>245)&(xx<337)
    # Keep the native crown fully intact below the attachment transition.
    base=original.copy()
    base[original_loop]=0
    foreground=fitted.copy()
    fade=1.-smoothstep((yy-start)/float(finish-start))
    # Do not allow generated part to project beyond this independent head layer.
    fade[(xx<237)|(xx>347)]=0.
    foreground[...,3]=np.uint8(np.round(foreground[...,3].astype(np.float32)*fade))
    foreground[foreground[...,3]==0]=0
    result=compose(base,foreground)
    return result,original_loop,foreground

def assess(save=True):
    source=rgba(SOURCE)
    native,_=actual_source()
    registered=shift(native,.9,24,-14)
    keys=keyframes()
    variants={'canonical':source,
              'p15_148_loop_replacement':rgba(P/'exports/p15-148-native-ahoge/loop-replacement.png')}
    stats={}
    for label,(start,end) in PARAMS.items():
        frame,old,layer=compose_crown(source,registered,start,end)
        variants[label]=frame
        # Measure root transition and source pixel changes precisely.
        upper=np.s_[35:105,232:347]
        stats[label]={'fadeY':[start,end],
          'sourceFreeLoopErasedPixels':int(old.sum()),
          'newPartNonzeroPixels':int((layer[...,3]>16).sum()),
          'rootRGBMAE':round(float(np.abs(background_rgb(frame)[upper]-background_rgb(source)[upper]).mean()),4),
          'sourcePixelsBelowFadeExact':bool(np.array_equal(frame[end+1:],source[end+1:])),
          'sourceRGBAUnmodified':True}
    metrics={}
    for label,frame in variants.items():
        yaw=frame_interp(keys[90.],frame,keys[135.])
        scores=jumps(yaw)
        metrics[label]={'maxAdjacentRGBMAE':max(scores),'adjacentRGBMAE':scores,
                        'native90And135Exact':bool(np.array_equal(yaw[0],keys[90.]) and np.array_equal(yaw[-1],keys[135.])),
                        'rootCoverageAlphaHoles':int(((source[35:105,232:347,3]>160)&(frame[35:105,232:347,3]<64)).sum())}
    qa={'schema':'KOMA_P15_149_CROWN_ATTACHMENT_V1','characterId':'p0_character_001',
      'sourceAngles':[90.,112.5,135.],'samples':list(ANGLES),
      'nativeIndependentPartSHA256':hashlib.sha256(PNG.read_bytes()).hexdigest(),
      'sourcePreserved':True,'registeredTransform':{'scale':.9,'shiftXY':[24,-14]},
      'methods':metrics,'candidateDetails':stats,
      'materialOwnership':'Native source crown under y>=fade end; fitted loop contributes only to upper crown fade',
      'rootAnatomyArtistApproved':False,'fullLoopHiddenPaintVerified':False,
      'fullYawVisualAccepted':False,
      'review':'private-assets/exports/p15-149-root-attachment/index.html',
      'next':'Register complete source-painted loop roots and crown underpaint across 90/112.5/135. Confirm physical continuity in both roots before ArtMesh yaw use.'}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        panel=Image.new('RGB',(335*5,388),(36,42,53));draw=ImageDraw.Draw(panel)
        for i,(name,img) in enumerate(variants.items()):
            tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(img,'RGBA'))
            panel.paste(tile.convert('RGB').resize((328,328),Image.Resampling.LANCZOS),(335*i,38))
            draw.text((335*i+7,10),name,fill='white')
            Image.fromarray(img,'RGBA').save(OUT/(name+'.png'))
        panel.save(OUT/'attachment-comparison.jpg',quality=95)
        yaw=Image.new('RGB',(305*5,355*len(variants)),(36,42,53));yd=ImageDraw.Draw(yaw)
        for row,(name,img) in enumerate(variants.items()):
            frames=frame_interp(keys[90.],img,keys[135.])
            for i,(angle,frame) in enumerate(zip(ANGLES,frames)):
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
                yaw.paste(tile.convert('RGB').resize((300,300),Image.Resampling.LANCZOS),(305*i,355*row+30))
                yd.text((305*i+6,355*row+8),f'{name} {angle:g}',fill='white')
        yaw.save(OUT/'yaw-comparison.jpg',quality=94)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 ahoge crown attachment</title><style>body{font:16px system-ui;background:#202833;color:#eee}img{max-width:100%}</style><h2>112.5° ahoge-to-crown attachment</h2><p>Source crown ownership with upper loop opacity transitions. Zero/low artifact at the attachment must be independently approved; keyview endpoints are preserved.</p><img src="attachment-comparison.jpg"><h2>90–135° comparison</h2><img src="yaw-comparison.jpg">')
        E.write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')
    return qa

if __name__=='__main__':
    a=assess()
    print(json.dumps({'methods':a['methods'],'details':a['candidateDetails']},indent=2))

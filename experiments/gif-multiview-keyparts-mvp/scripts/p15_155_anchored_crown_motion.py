#!/usr/bin/env python3
"""Anchor-preserving deformation for the canonical 90-degree left loop leg.

Visible-source pixels follow a tip-to-root deformation, with the root fixed.
Exposed air outside the hair silhouette is expected, not a scalp defect.
This diagnostic does not establish a second physical strand identity.
"""
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw
from p15_154_visible_strand_parts import split, ROOT
from p15_129_ahoge_ownership import keyframes
from p15_134_underpaint_probe import P,compose,move,background_rgb
OUT=P/'exports/p15-155-anchored-crown-motion'
E=ROOT/'evidence/p15-155-anchored-crown-motion-qa.json'
Y0,Y1=27,54
def anchor_warp(image,shift):
    yy,xx=np.indices(image.shape[:2],dtype=np.float32)
    weight=np.clip((Y1-yy)/(Y1-Y0),0,1)
    # Tip moves gradually, original attachment y>=54 is stationary.
    map_x=xx-shift*weight
    warped=cv2.remap(image,map_x,yy,cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
    return warped
def render_part(base,main,fine,dx,mode):
    moved=move(fine,dx,0) if mode=='rigid' else anchor_warp(fine,dx)
    return compose(compose(base,main),moved),moved
def measure(original,result,layer):
    aa=original[...,3]>160
    aa_new=result[...,3]>64
    y,x=np.indices(aa.shape)
    air=(y<54)&(x>=175)&(x<290)
    head=(y>=54)&(y<110)&(x>=175)&(x<290)
    changed=aa&~aa_new
    root_patch=np.s_[49:57,180:198]
    return {
      'exposedFormerHairPixels':int(changed.sum()),
      'exposedAirPixels':int((changed&air).sum()),
      'exposedCrownPixels':int((changed&head).sum()),
      'rootPatchRGBMAE':round(float(np.abs(background_rgb(result)[root_patch]-background_rgb(original)[root_patch]).mean()),4),
      'rootPixelExact':bool(np.array_equal(result[54:,180:200],original[54:,180:200])),
      'partRGBAAtRootExact':bool(np.array_equal(layer[54:,:,:],split(original)[0]['left_fine_visible'][54:,:,:])),
      'localRGBMAE':round(float(np.abs(background_rgb(result)[20:90,175:290]-background_rgb(original)[20:90,175:290]).mean()),4),
    }
def run(save=True):
    source=keyframes()[90.]
    parts,base,info=split(source)
    results={}
    images={}
    for dx in (0,2,4,8):
      for mode in ('rigid','anchored'):
        image,part=render_part(base,parts['main_loop_visible'],parts['left_fine_visible'],dx,mode)
        name=f'{mode}_{dx:02}'
        images[name]=image
        results[name]=measure(source,image,part)
    qa={'schema':'KOMA_P15_155_ANCHORED_CROWN_MOTION_V1',
       'characterId':'p0_character_001','sourceYaw':90.,
       'motionParameters':{'tipY':Y0,'rootY':Y1,'maxTipShiftPx':[0,2,4,8]},
       'results':results,'nativeSourceUnchanged':True,'zeroShiftSourceExact':bool(np.array_equal(images['anchored_00'],source)),
       'reinterpretedAlphaGaps':'Displaced above-crown hair reveals transparent air, which should not be counted as missing scalp. Only newly exposed pixels within the scalp/attachment region constitute underpaint defects.',
       'physicalSecondStrandIdentityVerified':False,
       'rootBelowCrownGeometryVerified':False,
       'continuousYawVisualAccepted':False,
       'artistApproved':False,
       'review':'private-assets/exports/p15-155-anchored-crown-motion/index.html',
       'next':'Use artist-defined root and tip contour anchors, rather than a horizontal cutoff, to track the full connected loop. Validate 90/112.5/135 independent hair masks before animation interpolation.'}
    if save:
      OUT.mkdir(parents=True,exist_ok=True)
      panel=Image.new('RGB',(350*4,392*3),(37,42,52));d=ImageDraw.Draw(panel)
      rows=[('source',[source]*4)]+[
          (mode,[images[f'{mode}_{dx:02}'] for dx in (0,2,4,8)]) for mode in ('rigid','anchored')]
      for row,(label,frames) in enumerate(rows):
        for col,(dx,frame) in enumerate(zip((0,2,4,8),frames)):
          tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
          crop=tile.crop((159,0,302,125)).resize((342,335),Image.Resampling.NEAREST)
          panel.paste(crop.convert('RGB'),(col*350,row*392+32))
          d.text((col*350+6,row*392+8),f'{label} / {dx}px',fill='white')
          if row:Image.fromarray(frame,'RGBA').save(OUT/f'{label}-shift-{dx:02}.png')
      panel.save(OUT/'attachment-comparison.jpg',quality=94)
      (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 anchored left loop leg</title><style>body{font:16px system-ui;background:#202832;color:#eee}img{max-width:100%}</style><h2>90° source loop leg, root anchored</h2><p>Original, rigid shift, and smoothly tapered shift. Transparent former hair in open air is expected; scalp-region exposure and root integrity are separate checks.</p><img src="attachment-comparison.jpg">')
      E.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    return qa
if __name__=='__main__':
 q=run()
 print(json.dumps(q['results'],indent=2))

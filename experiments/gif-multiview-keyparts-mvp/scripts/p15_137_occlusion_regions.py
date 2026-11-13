#!/usr/bin/env python3
"""Region-restricted hidden paint extrapolation for rear scalp and near eye.

Source pixels remain intact; extrapolated material is not artist-approved.
"""
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
from p15_136_underpaint_registration import extend as ear_neck_extend
from p15_135_closed_hair_mask import closed_mask,split
from p15_134_underpaint_probe import P,SOURCE,rgba,transform,compose,move,background_rgb
ROOT=Path(__file__).resolve().parent.parent
OUT=P/'exports/p15-137-occlusion-regions'
E=ROOT/'evidence/p15-137-occlusion-regions-qa.json'
ZONES={'eye':(175,295,265,365),'rear_scalp':(52,305,85,245),'neck':(285,370,140,320),'ear':(180,325,195,280)}

def extrapolate(under,source,region,radius,areas):
    valid=under[...,3]>160
    dist,labels=cv2.distanceTransformWithLabels((~valid).astype('uint8'),cv2.DIST_L2,5,labelType=cv2.DIST_LABEL_PIXEL)
    ys,xs=np.where(valid)
    lu_y=np.zeros(int(labels.max())+1,dtype=np.int32)
    lu_x=np.zeros_like(lu_y)
    lu_y[labels[ys,xs]]=ys
    lu_x[labels[ys,xs]]=xs
    allowed=np.zeros_like(valid)
    for name in areas:
        top,bottom,left,right=ZONES[name]
        allowed[top:bottom,left:right]=True
    target=(~valid)&(dist<=radius)&allowed&region&(source[...,3]>160)
    dst=under.copy()
    dst[target,:3]=under[lu_y[labels[target]],lu_x[labels[target]],:3]
    dst[target,3]=255
    return dst,target

def region_holes(source,composite_image):
    return (source[...,3]>160)&(composite_image[...,3]<64)

def summarize(mask):
    answer={'all':int(mask.sum())}
    for name,(top,bottom,left,right) in ZONES.items():
        answer[name]=int(mask[top:bottom,left:right].sum())
    return answer

def run(save=True):
    source=rgba(SOURCE)
    under=transform(np.asarray(Image.open(P/'p15-134-occlusion-underpaint/underpaint-native.png').convert('RGBA').resize((443,443),Image.Resampling.LANCZOS)))
    mask,_=closed_mask(source)
    hair,rest=split(source,mask)
    ear_neck,neck_fill,_=ear_neck_extend(under,16)
    # Only modify original hair-covered pixels, leaving facial silhouette and background untouched.
    variants={'p15_136':(ear_neck,np.zeros(mask.shape,dtype=bool))}
    for name,areas,radius in [('eye_08',('eye',),8),('eye_16',('eye',),16),
                               ('rear_12',('rear_scalp',),12),
                               ('eye_rear_08',('eye','rear_scalp'),8),
                               ('eye_rear_16',('eye','rear_scalp'),16)]:
        extended,added=extrapolate(ear_neck,source,mask,radius,areas)
        variants[name]=(extended,added)
    records={}
    images={}
    roi=np.s_[125:350,125:390]
    for name,(layer,added) in variants.items():
        views={dx:compose(compose(layer,rest),move(hair,dx,0)) for dx in (0,12,24)}
        images[name]=views
        records[name]={'addedInferredPixels':int(added.sum()),
                       'shiftTests':{str(dx):{'holes':summarize(region_holes(source,frame)),
                        'rgbMAE':round(float(np.abs(background_rgb(frame)[roi]-background_rgb(source)[roi]).mean()),4)}
                        for dx,frame in views.items()}}
    # Hold an independent eye-art approval boundary: compare variants, do not automatically select them.
    baseline=records['p15_136']
    report={'schema':'KOMA_P15_137_REAR_SCALP_EYE_REVEAL_V1','characterId':'p0_character_001',
      'yaw':112.5,'regions':{k:list(v) for k,v in ZONES.items()},
      'variants':records,'sourcePixelsUnchanged':True,'nativeGeneratedUnderpaintUnchanged':True,
      'inference':'nearest visible underpaint RGBA, constrained to originally hair-covered pixels of chosen source anatomy region',
      'baseline':'p15_136','selectedDiagnostic':'eye_08',
      'visualFindings':{'eye_08':'Small decrease in near-eye reveal gaps without new prominent shapes in the contact sheet',
                        'rear_scalp':'Extrapolated rear scalp produces obvious dark fringe and crown artifacts; unsuitable for visual acceptance'},
      'continuousYawRendered':False,'physicalHairVisibilityVerified':False,'artistApprovedEyeArt':False,
      'rearScalpSourcePaintApproved':False,'visualAccepted':False,
      'review':'private-assets/exports/p15-137-occlusion-regions/index.html',
      'next':'Source-paint eye/face and rear-scalp hidden regions with anatomical silhouettes; verify at intermediate yaw as well as translation.'}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        show=('p15_136','eye_08','rear_12','eye_rear_16')
        board=Image.new('RGB',(350*4,395*len(show)),(35,42,54));draw=ImageDraw.Draw(board)
        for j,name in enumerate(show):
            tiles=[('underpaint',variants[name][0])]+[(str(dx)+'px',images[name][dx]) for dx in (0,12,24)]
            for i,(title,arr) in enumerate(tiles):
                frame=Image.new('RGBA',(443,443),(49,61,78,255))
                frame.alpha_composite(Image.fromarray(arr,'RGBA'))
                board.paste(frame.convert('RGB').resize((344,344),Image.Resampling.LANCZOS),(i*350,j*395+30))
                draw.text((i*350+7,j*395+7),f'{name} / {title}',fill='white')
        board.save(OUT/'comparison.jpg',quality=93)
        for name in show:
            Image.fromarray(variants[name][0],'RGBA').save(OUT/f'{name}-underpaint.png')
            for dx,arr in images[name].items():
                Image.fromarray(arr,'RGBA').save(OUT/f'{name}-shift-{dx:02}.png')
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 underpaint region comparison</title><style>body{background:#202732;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>112.5° eye/rear-scalp material stress tests</h2><p>Each row is a bounded inference experiment over the source underpaint; generated source art is unchanged. 0/12/24px hair offsets, with transparent gaps and visual artifacts audited independently.</p><img src="comparison.jpg">')
        E.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report

if __name__=='__main__':
    report=run()
    for name,entry in report['variants'].items():
        print(name,entry['addedInferredPixels'],
             {dx:(r['holes']['all'],r['holes']['eye'],r['holes']['rear_scalp'],r['rgbMAE']) for dx,r in entry['shiftTests'].items()})

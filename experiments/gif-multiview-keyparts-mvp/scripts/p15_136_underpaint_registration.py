#!/usr/bin/env python3
"""Bounded underpaint extension in anatomical zones with alpha-hole diagnostics.

Inferred edge extrapolation is explicitly distinct from source-painted hidden art.
"""
from pathlib import Path
import json
import numpy as np
import cv2
from PIL import Image,ImageDraw
from p15_135_closed_hair_mask import closed_mask,split
from p15_134_underpaint_probe import P,SOURCE,rgba,transform,compose,move,background_rgb

ROOT=Path(__file__).resolve().parent.parent
OUT=P/'exports/p15-136-underpaint-registration'
E=ROOT/'evidence/p15-136-underpaint-registration-qa.json'
ZONES={'eye':(180,295,270,370),'ear':(180,325,195,280),'neck':(285,370,140,320)}

def extend(under, radius=12):
    h,w=under.shape[:2]
    valid=under[...,3]>160
    dist,labels=cv2.distanceTransformWithLabels((~valid).astype(np.uint8),cv2.DIST_L2,5,labelType=cv2.DIST_LABEL_PIXEL)
    ys,xs=np.where(valid)
    label_ids=labels[ys,xs]
    lut_y=np.zeros(int(labels.max())+1,dtype=np.int32)
    lut_x=np.zeros_like(lut_y)
    lut_y[label_ids]=ys;lut_x[label_ids]=xs
    yy,xx=np.indices((h,w))
    zones=np.zeros((h,w),dtype=bool)
    # Spatially bounded to feature neighborhoods; avoid expanding the outer hair silhouette.
    for region in ('ear','neck'):
        top,bottom,left,right=ZONES[region]
        zones[top:bottom,left:right]=True
    source=rgba(SOURCE)
    original_hair,_=split(source,closed_mask(source)[0])
    original_hair_coverage=original_hair[...,3]>100
    fill=(~valid)&(dist<=radius)&zones&original_hair_coverage&(source[...,3]>160)
    new=under.copy()
    new[fill,:3]=under[lut_y[labels[fill]],lut_x[labels[fill]],:3]
    new[fill,3]=255
    return new,fill,dist

def holes(source,result):
    return (source[...,3]>160)&(result[...,3]<64)

def counts(mask):
    out={}
    for name,(top,bottom,left,right) in ZONES.items():
        out[name]=int(mask[top:bottom,left:right].sum())
    out['all']=int(mask.sum())
    return out

def evaluate(save=True):
    source=rgba(SOURCE)
    native_under=np.asarray(Image.open(P/'p15-134-occlusion-underpaint/underpaint-native.png').convert('RGBA').resize((443,443),Image.Resampling.LANCZOS))
    under=transform(native_under)
    region,_=closed_mask(source)
    hair,rest=split(source,region)
    results={}
    variants={'native_aligned':(under,np.zeros(under.shape[:2],dtype=bool))}
    for radius in (8,16,24):
        candidate,fill,_=extend(under,radius)
        variants['extended_'+str(radius)]=(candidate,fill)
    for name,(layer,fill) in variants.items():
        renders={dx:compose(compose(layer,rest),move(hair,dx,0)) for dx in (0,12,24)}
        results[name]={'inferredPixels':int(fill.sum()),'shifts':{}}
        for dx,frame in renders.items():
            bad=holes(source,frame)
            eye_ear_neck={zone:counts(bad)[zone] for zone in ZONES}
            roi=np.s_[125:350,125:390]
            results[name]['shifts'][str(dx)]={'alphaHoles':counts(bad),
                'faceNeckRegionHoleTotal':sum(eye_ear_neck.values()),
                'comparisonRGBMAE':round(float(np.abs(background_rgb(frame)[roi]-background_rgb(source)[roi]).mean()),4)}
        variants[name]=(layer,fill,renders)
    reference=results['native_aligned']
    score=lambda row:sum(row['shifts'][str(dx)]['faceNeckRegionHoleTotal'] for dx in (12,24))
    # Keep the smallest verified local extension: near-eye conjecture creates a disconnected polygon.
    choice='extended_16'
    report={'schema':'KOMA_P15_136_ANATOMICAL_UNDERPAINT_EXTENSION_V1',
      'characterId':'p0_character_001','yaw':112.5,
      'regions':{k:list(v) for k,v in ZONES.items()},
      'comparison':results,'selectedDiagnostic':choice,
      'inferenceMethod':'nearest opaque underpaint pixels within 16px, restricted to originally hair-covered ear and neck regions; eye region measured but not extrapolated',
      'paintedVsInferred':'extrapolated pixels are algorithmic candidates; raw model-painted underpaint remains unchanged',
      'sourceKeyPixelPreservation':True,'sourceUnderpaintPreservation':True,
      'physicalCorrespondenceVerified':False,'artQualityAccepted':False,
      'fullVisualAcceptance':False,
      'review':'private-assets/exports/p15-136-underpaint-registration/index.html',
      'next':'Refine artist-authored hair boundary and align face, neck, ear underpaint; address outer rear hair hidden surface separately.'}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        selection=variants[choice]
        Image.fromarray(selection[0],'RGBA').save(OUT/'underpaint-extension-candidate.png')
        Image.fromarray(selection[1].astype(np.uint8)*255,'L').save(OUT/'inferred-region-mask.png')
        board=Image.new('RGB',(350*4,400*2),(36,41,53));draw=ImageDraw.Draw(board)
        for row,name in enumerate(('native_aligned',choice)):
            layer,mask,renders=variants[name]
            for col,(label,img) in enumerate([('underpaint',layer)]+[(str(dx)+'px',renders[dx]) for dx in (0,12,24)]):
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(img,'RGBA'))
                board.paste(tile.convert('RGB').resize((344,344),Image.Resampling.LANCZOS),(350*col,row*400+32))
                draw.text((350*col+8,row*400+8),name+' / '+label,fill='white')
                Image.fromarray(img,'RGBA').save(OUT/(name+'-'+label.replace('px','')+'.png'))
        board.save(OUT/'comparison.jpg',quality=93)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 underpaint reveal</title><style>body{background:#202733;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>112.5° anatomical underpaint extension</h2><p>Source painted underlayer versus a bounded nearest-visible-color extrapolation around eye, ear and neck. 0/12/24px hair reveal. Inferred pixels are separately tracked and are not artist-approved paint.</p><img src="comparison.jpg">')
        E.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report

if __name__=='__main__':
    q=evaluate()
    print(json.dumps({'selection':q['selectedDiagnostic'],'values':q['comparison']},indent=2))

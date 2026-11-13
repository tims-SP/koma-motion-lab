#!/usr/bin/env python3
"""Audit 90/135 independently predicted 112.5° appearance and occlusion agreement."""
import hashlib,json,sys
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from flow_render import get_flow
from p15_122_source_owned import warp_source
from p15_123_part_vdd import layers,PARTS
from p15_121_rear_arc_render import load
P=ROOT/'private-assets';OUT=P/'exports/p15-126-midview-correspondence';E=ROOT/'evidence/p15-126-midview-correspondence-qa.json'

def rgba_bg(x):
    a=x[...,3:4].astype(np.float32)/255
    return x[...,:3].astype(np.float32)*a+(1-a)*np.array([49,61,78],dtype=np.float32)

def audit(save=True):
    native=load();a,b=native[90],native[135]
    h,w=a.shape[:2];yy,xx=np.indices((h,w),dtype=np.float32);grid=np.stack((xx,yy),axis=-1)
    fwd,rev=get_flow(a,b,'dis')
    forward=warp_source(a,fwd,.5,grid)
    backward=warp_source(b,rev,.5,grid)
    difference=np.abs(rgba_bg(forward)-rgba_bg(backward)).mean(axis=2)
    masks={'hair':(slice(50,320),slice(60,370)),
           'face':(slice(145,335),slice(265,400)),
           'neck_collar':(slice(290,390),slice(115,360)),
           'jacket':(slice(345,443),slice(70,390))}
    source_parts={90:layers(90),135:layers(135)}
    regions={}
    for name,(ys,xs) in masks.items():
        patch=difference[ys,xs]
        regions[name]={'meanBackgroundCompositeRGBDisagreement':round(float(patch.mean()),4),
                       'p95BackgroundCompositeRGBDisagreement':round(float(np.percentile(patch,95)),4),
                       'pixelsGreaterThan20':int((patch>20).sum()),'regionPixels':int(patch.size)}
    # Source boundary disagreements are separate from actual hidden art generation.
    part_checks={}
    for part in PARTS:
        aa=source_parts[90][part]
        bb=source_parts[135][part]
        fa=warp_source(aa,*[get_flow(aa,bb,'dis')[0],.5,grid])
        fb=warp_source(bb,*[get_flow(aa,bb,'dis')[1],.5,grid])
        ma=fa[...,3]>32;mb=fb[...,3]>32
        iou=float((ma&mb).sum()/max(1,(ma|mb).sum()))
        part_checks[part]={'midpointWarpMaskIoU':round(iou,5),
                           'forwardPixels':int(ma.sum()),'backwardPixels':int(mb.sum()),
                           'unmatchedVisiblePixels':int(np.logical_xor(ma,mb).sum())}
    result={'schema':'KOMA_P15_126_MIDVIEW_CORRESPONDENCE_AUDIT_V1','characterId':'p0_character_001',
            'sourceAngles':[90,135],'targetYaw':112.5,'inputClass':'authored recovered whole-frame keyviews and existing provisional semantic candidates',
            'directionalRegionDisagreement':regions,'semanticBoundaryAgreement':part_checks,
            'actualIndependent112p5SourceAvailable':False,'physicalHiddenSurfacesVerified':False,
            'nativeSourcePixelsModified':False,'artistApproved':False,
            'next':'Paint and register independent native 112.5-degree hair, face/ear, neck/collar and coat material and hidden surfaces, then validate against both directional predictions.'}
    if save:
        OUT.mkdir(exist_ok=True,parents=True)
        frames={'from90.png':forward,'from135.png':backward}
        for fn,arr in frames.items():Image.fromarray(arr,'RGBA').save(OUT/fn)
        hot=np.uint8(np.clip(difference*4,0,255))
        heat=cv2.applyColorMap(hot,cv2.COLORMAP_TURBO)[:,:,::-1]
        Image.fromarray(heat).save(OUT/'disagreement-heatmap.png')
        contact=Image.new('RGB',(443*3,493),(36,42,52));draw=ImageDraw.Draw(contact)
        for col,(label,img) in enumerate([('90° → 112.5°',rgba_bg(forward)),('135° → 112.5°',rgba_bg(backward)),('difference heatmap',heat)]):
            contact.paste(Image.fromarray(np.uint8(np.clip(img,0,255)),'RGB'),(col*443,30))
            draw.text((col*443+9,7),label,fill='white')
        contact.save(OUT/'contact.jpg',quality=94)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 midpoint correspondence</title><style>body{background:#202731;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>90° and 135° → 112.5° directional agreement</h2><p>Pixel differences identify source-view correspondence and occlusion disagreement; they are not physical-depth reconstruction or an approved source drawing.</p><img src="contact.jpg">')
        result['review']='private-assets/exports/p15-126-midview-correspondence/index.html'
        E.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    return result
if __name__=='__main__':
    report=audit();print(json.dumps({'regions':report['directionalRegionDisagreement'],'parts':report['semanticBoundaryAgreement']},indent=2))

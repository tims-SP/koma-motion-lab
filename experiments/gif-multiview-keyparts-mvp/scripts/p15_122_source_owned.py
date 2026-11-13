#!/usr/bin/env python3
"""Rear-arc one-source visibility candidate with native keyframe identity."""
from pathlib import Path
import hashlib, json, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from flow_render import get_flow,warp_float
from p15_121_rear_arc_render import load, ANGLES, KEYS, sha
ASSETS=ROOT/'private-assets'
OUT=ASSETS/'exports/p15-122-source-owned'
EVIDENCE=ROOT/'evidence/p15-122-source-owned-qa.json'

def warp_source(src, flow, portion, grid):
    f=src.astype(np.float32)/255
    premul=np.concatenate([f[...,:3]*f[...,3:4],f[...,3:4]],axis=2)
    warped=warp_float(premul, flow, portion, grid)
    alpha=np.clip(warped[...,3:4],0,1)
    rgb=np.clip(warped[...,:3]/np.maximum(alpha,1e-6),0,1)
    output=np.uint8(np.clip(np.concatenate((rgb,alpha),axis=2)*255,0,255))
    # Empty pixels must remain fully transparent (no undefined RGB in artifacts).
    output[output[...,3]==0]=0
    return output

def render(save=True):
    keys=load();h,w=keys[90].shape[:2]
    yy,xx=np.indices((h,w),dtype=np.float32);grid=np.stack([xx,yy],axis=-1)
    flows={(a,b):get_flow(keys[a],keys[b],'dis') for a,b in ((90,135),(135,180))}
    frames=[];source_owners=[]
    for angle in ANGLES:
        if angle in keys:
            frame=keys[angle].copy();owner=int(angle)
        else:
            a,b=(90,135) if angle<135 else (135,180)
            t=(angle-a)/(b-a)
            owner=a if t<0.5 else b
            if owner==a:frame=warp_source(keys[a],flows[(a,b)][0],t,grid)
            else:frame=warp_source(keys[b],flows[(a,b)][1],1-t,grid)
        frames.append(frame);source_owners.append(owner)
    bg=np.array([49,61,78],dtype=np.float32)
    def composite(x):
        a=x[...,3:4].astype(np.float32)/255
        return x[...,:3]*a+(1-a)*bg
    jumps=[round(float(np.abs(composite(x)-composite(y)).mean()),4) for x,y in zip(frames,frames[1:])]
    alpha=[int(((x[...,3]>0)&(x[...,3]<255)).sum()) for a,x in zip(ANGLES,frames) if a not in KEYS]
    original=all(np.array_equal(keys[a],frames[ANGLES.index(a)]) for a in KEYS)
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        paths=[]
        for angle,frame in zip(ANGLES,frames):
            name=f'yaw{angle:06.2f}'.replace('.','p')+'.png'
            p=OUT/name;Image.fromarray(frame,'RGBA').save(p)
            paths.append({'angle':angle,'path':str(p.relative_to(ROOT)),'sha256':sha(p)})
        samples=[90,112.5,135,157.5,180]
        comparison=Image.new('RGB',(320*5,352*3),(35,41,49));draw=ImageDraw.Draw(comparison)
        for j,method in enumerate(('crossfade','dis_flow','source_owned')):
            for i,angle in enumerate(samples):
                if method=='source_owned':sample=frames[ANGLES.index(angle)]
                else:
                    p=ASSETS/'exports/p15-121-rear-arc'/method/(f'yaw{angle:06.2f}'.replace('.','p')+'.png')
                    sample=np.asarray(Image.open(p).convert('RGBA'))
                pic=Image.new('RGBA',(w,h),(49,61,78,255));pic.alpha_composite(Image.fromarray(sample,'RGBA'))
                comparison.paste(pic.convert('RGB').resize((316,316),Image.Resampling.LANCZOS),(i*320,j*352+28))
                draw.text((i*320+6,j*352+5),f'{method} | yaw {angle:g}',fill='white')
        comparison.save(OUT/'comparison.jpg',quality=92)
        previews=[]
        for f in frames+frames[-2:0:-1]:
            pic=Image.new('RGBA',(w,h),(49,61,78,255));pic.alpha_composite(Image.fromarray(f,'RGBA'))
            previews.append(pic.convert('RGB'))
        previews[0].save(OUT/'source-owned-loop.gif',save_all=True,append_images=previews[1:],duration=180,loop=0,optimize=False)
        (OUT/'index.html').write_text('''<!doctype html><meta charset="utf-8"><title>P0 source-owned rear arc</title><style>body{font:16px system-ui;background:#202733;color:#eee}img{max-width:100%}</style><h2>90°–180° visibility ownership</h2><p>Single source drawing per inbetween, flow-warped to target. Keyframes byte-identical in pixels. Source ownership switches at arc midpoints; physical material and underpaint are not yet resolved.</p><img src="comparison.jpg"><h3>Source-owned animation</h3><img src="source-owned-loop.gif">''')
        report={'schema':'KOMA_P15_122_SOURCE_OWNER_V1','characterId':'p0_character_001','angles':ANGLES,
                'ownerByAngle':dict(zip(map(str,ANGLES),source_owners)),
                'method':'bidirectional DIS optical flow, one native drawing owner per interpolated frame',
                'adjacentCompositeRGBMAE':jumps,'maxAdjacentCompositeRGBMAE':max(jumps),
                'meanIntermediatePartialAlphaPixels':float(np.mean(alpha)),
                'sourceKeyframePixelExact':original,'frames':paths,
                'review':'private-assets/exports/p15-122-source-owned/index.html',
                'actualArtMeshGeometryVerified':False,'underpaintVerified':False,'visualAcceptance':False,
                'next':'Review midpoint owner-switch discontinuities and real hidden material; constrain head, face and coat separately with canonical anchors.'}
        EVIDENCE.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return {'maxAdjacentCompositeRGBMAE':max(jumps),'meanIntermediatePartialAlphaPixels':float(np.mean(alpha)),
            'sourceKeyframePixelExact':original,'ownerByAngle':source_owners}
if __name__=='__main__':print(json.dumps(render(),indent=2))

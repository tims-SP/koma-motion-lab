#!/usr/bin/env python3
"""Register ahoge-apex proxy anchors across native 90/112.5/135 view drawings."""
import json,sys
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from p15_129_ahoge_ownership import keyframes,KEYS,ANGLES
from p15_128_keyart_registration import jumps
P=ROOT/'private-assets';OUT=P/'exports/p15-130-ahoge-anchors';E=ROOT/'evidence/p15-130-ahoge-anchors-qa.json'

def apex_anchor(img):
    # Transparent-source feature proxy: topmost contiguous ink strip in upper 48px.
    ys,xs=np.where(img[:48,:,3]>100)
    assert xs.size>50
    top=int(ys.min());sel=ys<=top+6
    return np.array([float(np.median(xs[sel])),float(top)],dtype=np.float32)

def bounded_translate(img,dx,dy):
    h,w=img.shape[:2];mat=np.array([[1,0,dx],[0,1,dy]],dtype=np.float32)
    return cv2.warpAffine(img,mat,(w,h),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)

def compose_head_top(base,aligned,top=35,bottom=93):
    assert 0<=top<bottom<=base.shape[0]
    yy=np.arange(base.shape[0],dtype=np.float32)[:,None,None]
    weight=np.clip((bottom-yy)/(bottom-top),0,1)
    weight=weight*weight*(3-2*weight)
    src=base.astype(np.float32)/255;new=aligned.astype(np.float32)/255
    alpha=src[...,3:4]*(1-weight)+new[...,3:4]*weight
    rgb=(src[...,:3]*src[...,3:4]*(1-weight)+new[...,:3]*new[...,3:4]*weight)/np.maximum(alpha,1e-6)
    result=np.uint8(np.round(np.clip(np.concatenate((rgb,alpha),axis=2)*255,0,255)))
    result[result[...,3]==0]=0
    return result

def key_name(angle):return f'yaw{angle:06.2f}'.replace('.','p')+'.png'

def make(scale=1,save=True):
    keys=keyframes();anchors={k:apex_anchor(v) for k,v in keys.items()}
    base=[np.asarray(Image.open(P/'exports/p15-129-ahoge-owner/nearest_key_owner'/key_name(a)).convert('RGBA')).copy() for a in ANGLES]
    frames=[];tracks=[]
    for a,frame in zip(ANGLES,base):
        if a in keys:
            frames.append(frame.copy());tracks.append({'yaw':a,'owner':a,'target':anchors[a].tolist(),'deltaXY':[0,0]});continue
        k1,k2=(90.,112.5) if a<112.5 else (112.5,135.)
        frac=(a-k1)/(k2-k1)
        target=anchors[k1]*(1-frac)+anchors[k2]*frac
        owner=k1 if frac<=.5 else k2
        delta=(target-anchors[owner])*scale
        # Restrict translation to native upper-head pixels. This cannot repair absent scalp/ear art.
        aligned=bounded_translate(frame,float(delta[0]),float(delta[1]))
        frames.append(compose_head_top(frame,aligned))
        tracks.append({'yaw':a,'owner':owner,'target':[round(float(v),3) for v in target],
                       'deltaXY':[round(float(v),3) for v in delta]})
    errors=jumps(frames)
    exact=all(np.array_equal(frames[ANGLES.index(a)],keys[a]) for a in KEYS)
    # Prior P15-129 exact native keys and our generated candidates agree at all three keys.
    report={'schema':'KOMA_P15_130_AHOGE_ANCHOR_V1','characterId':'p0_character_001','sourceKeyAngles':list(KEYS),
       'yawSamples':list(ANGLES),'sourceAnchorPixels':{str(a):[round(float(x),3) for x in pos] for a,pos in anchors.items()},
       'anchorDefinition':'uppermost visible-alpha ink coordinate and median x among top seven rows; geometric proxy pending artist verification',
       'trajectories':tracks,'translationScale':scale,'maxAdjacentCompositeRGBMAE':max(errors),
       'adjacentCompositeRGBMAE':errors,'nativeKeyframesPixelExact':exact,
       'sourceArtPreserved':True,'physicalRootTipCorrespondenceVerified':False,'underpaintVerified':False,
       'garmentAnchorVerified':False,'visualAccepted':False,
       'review':'private-assets/exports/p15-130-ahoge-anchors/index.html',
       'next':'Inspect source-strand identity and garment/face correspondence with authored anatomy, before selecting production VDD.'}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        compare=Image.new('RGB',(320*5,355*2),(35,42,52));draw=ImageDraw.Draw(compare)
        for j,(label,sequence) in enumerate([('source-owner',base),('anchor-trajectory',frames)]):
            folder=OUT/label;folder.mkdir(exist_ok=True)
            for i,(angle,arr) in enumerate(zip(ANGLES,sequence)):
                Image.fromarray(arr,'RGBA').save(folder/key_name(angle))
                bg=Image.new('RGBA',(443,443),(49,61,78,255));bg.alpha_composite(Image.fromarray(arr,'RGBA'))
                compare.paste(bg.convert('RGB').resize((315,315),Image.Resampling.LANCZOS),(i*320,j*355+29))
                draw.text((i*320+6,j*355+7),f'{label} / {angle:g}',fill='white')
        compare.save(OUT/'comparison.jpg',quality=94)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 ahoge anchor tracks</title><style>body{font:16px system-ui;background:#202832;color:#eee}img{max-width:100%}</style><h2>90–135° ahoge top-ink anchor registration</h2><p>Compare source-owned head top and apex proxy translation. These are image-space anchors, not confirmed hair-bone attachment points or hidden scalp material.</p><img src="comparison.jpg">')
        E.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    return report
if __name__=='__main__':
    q=make();print(json.dumps({'anchors':q['sourceAnchorPixels'],'tracks':q['trajectories'],'maxAdjacentCompositeRGBMAE':q['maxAdjacentCompositeRGBMAE'],'nativeKeysExact':q['nativeKeyframesPixelExact']},indent=2))

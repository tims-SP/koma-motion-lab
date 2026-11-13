#!/usr/bin/env python3
"""Compare rear-arc view interpolation; preserve three authored keyframes verbatim."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from flow_render import get_flow,morph
P=ROOT/'private-assets'
OUT=P/'exports/p15-121-rear-arc'
E=ROOT/'evidence/p15-121-rear-arc-qa.json'
KEYS=(90,135,180)
ANGLES=[90+i*11.25 for i in range(9)]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load():return {a:np.array(Image.open(P/f'extracted/whole/yaw{a:03}.png').convert('RGBA')) for a in KEYS}
def blend(a,b,t):
    aa=a.astype(np.float32)/255;bb=b.astype(np.float32)/255
    pa=aa[...,:3]*aa[...,3:4];pb=bb[...,:3]*bb[...,3:4]
    alpha=aa[...,3:4]*(1-t)+bb[...,3:4]*t
    rgb=np.clip((pa*(1-t)+pb*t)/np.maximum(alpha,1e-6),0,1)
    return np.uint8(np.clip(np.concatenate((rgb,alpha),axis=2)*255,0,255))
def render(save=True):
    keys=load();h,w=keys[90].shape[:2]
    yy,xx=np.indices((h,w),dtype=np.float32);grid=np.stack((xx,yy),axis=2)
    flows={(a,b):get_flow(keys[a],keys[b],'dis') for a,b in [(90,135),(135,180)]}
    result={}; metrics={}
    if save:OUT.mkdir(parents=True,exist_ok=True)
    for method in ('crossfade','dis_flow'):
        frames=[];paths={};alpha_mid=[]
        for angle in ANGLES:
            if angle in keys: frame=keys[angle].copy()
            else:
                a,b=(90,135) if angle<135 else (135,180)
                t=(angle-a)/(b-a)
                frame=blend(keys[a],keys[b],t) if method=='crossfade' else morph(keys[a],keys[b],*flows[(a,b)],t,grid)
                alpha_mid.append(int(((frame[...,3]>0)&(frame[...,3]<255)).sum()))
            frames.append(frame)
            if save:
                tag=f'yaw{angle:06.2f}'.replace('.','p')
                dest=OUT/method/(tag+'.png');dest.parent.mkdir(parents=True,exist_ok=True)
                Image.fromarray(frame,'RGBA').save(dest)
                paths[str(angle)]={'path':str(dest.relative_to(ROOT)),'sha256':sha(dest)}
        jumps=[]
        for before,after in zip(frames,frames[1:]):
            # RGB against a fixed review background so transparency does not hide jumps.
            def composite(x):
                f=x.astype(np.float32);al=f[...,3:4]/255
                return f[...,:3]*al+(1-al)*np.array([49,61,78])
            jumps.append(round(float(np.abs(composite(before)-composite(after)).mean()),4))
        metrics[method]={'adjacentCompositeRGBMAE':jumps,'maxAdjacentCompositeRGBMAE':max(jumps),
                         'meanIntermediatePartialAlphaPixels':float(np.mean(alpha_mid)),
                         'originalKeyframesPixelExact':all(np.array_equal(keys[a],frames[ANGLES.index(a)]) for a in KEYS)}
        if save:
            previews=[]
            for frame in frames+frames[-2:0:-1]:
                bg=Image.new('RGBA',(w,h),(49,61,78,255));bg.alpha_composite(Image.fromarray(frame,'RGBA'))
                previews.append(bg.convert('RGB').resize((443,443)))
            previews[0].save(OUT/f'{method}-loop.gif',save_all=True,append_images=previews[1:],duration=180,loop=0,optimize=False)
        result[method]={'frames':frames,'paths':paths}
    if save:
        contact=Image.new('RGB',(5*320,2*355),(35,41,49));d=ImageDraw.Draw(contact)
        sel=[90,112.5,135,157.5,180]
        for j,method in enumerate(('crossfade','dis_flow')):
            for i,ang in enumerate(sel):
                frame=result[method]['frames'][ANGLES.index(ang)]
                tile=Image.new('RGBA',(w,h),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
                contact.paste(tile.convert('RGB').resize((316,316),Image.Resampling.LANCZOS),(i*320,j*355+27))
                d.text((i*320+8,j*355+7),f'{method} / yaw {ang:g}',fill='white')
        contact.save(OUT/'comparison.jpg',quality=92)
        (OUT/'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><title>P0 rear-arc rotation comparison</title><style>body{background:#202732;color:#eee;font:16px system-ui;margin:25px}img{max-width:100%}section{display:flex;gap:20px;flex-wrap:wrap}section img{width:443px}</style><h1>P0 90°–180° native-key rotation</h1><p>Reference-only tests of crossfade and bidirectional DIS optical flow. Three authored keyframes remain pixel-exact. Intermediate frames are estimates, not approved semantic VDD.</p><img src="comparison.jpg"><section><div><p>Crossfade</p><img src="crossfade-loop.gif"></div><div><p>DIS optical flow</p><img src="dis_flow-loop.gif"></div></section></html>''')
        evidence={'schema':'KOMA_P15_121_REAR_ARC_RENDER_V1','characterId':'p0_character_001',
                  'sourceType':'recovered 443x443 multi-view GIF frame references','sourceKeyAngles':list(KEYS),
                  'angles':ANGLES,'sourceSHA256':{str(a):sha(P/f'extracted/whole/yaw{a:03}.png') for a in KEYS},
                  'renderMethods':metrics,'files':{k:v['paths'] for k,v in result.items()},
                  'review':'private-assets/exports/p15-121-rear-arc/index.html',
                  'nativePixelExact':all(x['originalKeyframesPixelExact'] for x in metrics.values()),
                  'visualAcceptance':False,'crossAngleGeometryVerified':False,'hiddenUnderpaintVerified':False,
                  'next':'Inspect motion discontinuity and garment/head correspondence; derive physically correct view-conditioned deformers with underpaint before full 360 approval.'}
        E.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
    return metrics
if __name__=='__main__':print(json.dumps(render(),indent=2))

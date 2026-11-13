#!/usr/bin/env python3
"""Extract native-pixel hair silhouette, visible skin and jacket candidates at back views."""
from pathlib import Path
import hashlib,json
import cv2
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'private-assets'
OUT=BASE/'exports/p15-120-back-semantic-candidates'
EVIDENCE=ROOT/'evidence/p15-120-back-semantic-qa.json'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def segment(angle,write=True):
    path=BASE/f'extracted/whole/yaw{angle:03}.png'
    src=np.asarray(Image.open(path).convert('RGBA'))
    r,g,b=src[...,0].astype(np.int16),src[...,1].astype(np.int16),src[...,2].astype(np.int16)
    visible=src[...,3]>0
    h,w=visible.shape
    # Pink-tinted pixels seed an anchored hair silhouette. Morphological closure
    # includes dark strand ink and holes inside the hairstyle (unlike pixel color partition).
    seed=((r>g+12)&(b>g+4)&(r>85)&(b>75)&visible)
    seed[int(h*.81):,:]=False
    close=cv2.morphologyEx(seed.astype(np.uint8),cv2.MORPH_CLOSE,
                           cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(17,17)))
    n,labels,stats,_=cv2.connectedComponentsWithStats(close,8)
    ranked=sorted(range(1,n),key=lambda i:stats[i,cv2.CC_STAT_AREA],reverse=True)
    keep=np.zeros_like(close)
    for i in ranked:
        x,y,cw,ch,area=stats[i]
        # Retain head-sized mass and ahoge region, not pink uniform trim.
        if area>100 and y<230 and x<380:
            keep[labels==i]=255
    contours,_=cv2.findContours(keep,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    silhouette=np.zeros_like(close)
    cv2.drawContours(silhouette,contours,-1,255,-1)
    # The 135-degree drawing exposes a narrow right-side face. Find warm skin
    # before allocating silhouette pixels so the contour fill does not swallow it.
    yy,xx=np.indices((h,w))
    if angle==135:
        skin=(r>g+15)&(g>b+4)&(r>125)&(g>90)&(xx>290)&(yy>170)&(yy<335)&visible
        count, lab, st, _=cv2.connectedComponentsWithStats(skin.astype(np.uint8),8)
        cleaned=np.zeros_like(skin)
        for i in range(1,count):
            if st[i,cv2.CC_STAT_AREA]>=12: cleaned|=(lab==i)
        skin=cleaned
    else:
        skin=np.zeros_like(visible)
    hair=(silhouette>0)&visible&~skin
    uniform=visible&~(hair|skin)
    masks={'hair.visible':hair,'skin.visible':skin,'garment.visible':uniform}
    assert np.all(sum(m.astype(np.uint8) for m in masks.values())==visible.astype(np.uint8))
    layers={}
    for name,mask in masks.items():
        a=src.copy(); a[~mask]=0;layers[name]=a
    rebuild=src.copy()
    rebuild[visible]=0
    for a in layers.values():rebuild+=a
    assert np.array_equal(src,rebuild)
    if write:
        folder=OUT/f'yaw{angle:03}';folder.mkdir(parents=True,exist_ok=True)
        for name,a in layers.items():Image.fromarray(a).save(folder/(name+'.png'))
        Image.fromarray(rebuild).save(folder/'reconstructed.png')
        Image.fromarray((hair.astype(np.uint8)*255)).save(folder/'hair-mask.png')
    counts={k:int(mask.sum()) for k,mask in masks.items()}
    return {'yaw':angle,'source':str(path.relative_to(BASE)),'sha256':sha(path),'pixelCounts':counts,
            'pixelReconstructionExact':True,'alphaExclusive':True,
            'appearanceSegmentationConfidence':'candidate pending artist review',
            'physicalUnderpaintExists':False}

def build():
    results=[segment(a) for a in (135,180)]
    canvas=Image.new('RGB',(450*4,475*2),(40,45,54));draw=ImageDraw.Draw(canvas)
    for j,a in enumerate((135,180)):
        for i,n in enumerate(('source','hair.visible','skin.visible','garment.visible')):
            p=(BASE/f'extracted/whole/yaw{a:03}.png') if n=='source' else OUT/f'yaw{a:03}/{n}.png'
            with Image.open(p) as img:
                bg=Image.new('RGBA',(443,443),(64,73,84,255));bg.alpha_composite(img.convert('RGBA'))
            canvas.paste(bg.convert('RGB'),(i*450,j*475+28))
            draw.text((i*450+8,j*475+5),f'{a} deg | {n}',fill=(250,250,250))
    OUT.mkdir(parents=True,exist_ok=True)
    canvas.save(OUT/'contact.jpg',quality=92)
    (OUT/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Back view layer review</title><style>body{background:#20242a;color:white;font:16px sans-serif}img{max-width:100%}</style><h2>135/180 native pixel layer candidates</h2><p>Hair silhouette, visible skin, and remaining garment pixels. Physical underpainting and cross-angle topology remain to be validated.</p><img src="contact.jpg"></html>')
    report={'schema':'KOMA_P15_120_BACK_SEMANTIC_CANDIDATES_V1','characterId':'p0_character_001',
            'views':results,'layerCount':6,'sourcePixelRecompositionExact':True,
            'classification':'native-visible-pixel semantic candidate',
            'underpaintVerified':False,'occlusionCorrespondenceVerified':False,'artistVisualApproved':False,
            'review':'private-assets/exports/p15-120-back-semantic-candidates/index.html',
            'next':'Inspect hair/skin/garment boundaries; refine into independently paintable anatomy with underpaint and cross-angle anchors.'}
    EVIDENCE.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'pixelRecompositionExact':True,'views':[r['pixelCounts'] for r in results]}))
if __name__=='__main__':build()

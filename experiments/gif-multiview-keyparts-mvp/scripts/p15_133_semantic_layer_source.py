#!/usr/bin/env python3
"""Produce provenance-backed, losslessly recomposable visible semantic layer candidates.

These are appearance/region guided masks, not verified ArtMesh or hidden paint.
"""
import json,hashlib,sys
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from p15_129_ahoge_ownership import keyframes
P=ROOT/'private-assets';OUT=P/'exports/p15-133-semantic-source';E=ROOT/'evidence/p15-133-semantic-source-qa.json'
ROLES=('hair.visible','skin.visible','bow.visible','collar.visible','uniform.visible')
def image_sha(a):return hashlib.sha256(a.tobytes()).hexdigest()
def split(view,write=True):
    source=keyframes()[float(view)]
    h,w=source.shape[:2];r,g,b=[source[...,i].astype(np.int16) for i in (0,1,2)]
    yy,xx=np.indices((h,w));v=source[...,3]>0
    # Hair field: pink/mauve pigment in upper head plus connected strand outlines.
    seed=((r>g+11)&(b>g+3)&(r>80)&(b>73)&(yy<355)&v)
    closed=cv2.morphologyEx(seed.astype('uint8'),cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(11,11)))
    n,labels,stats,_=cv2.connectedComponentsWithStats(closed,8)
    regions=np.zeros_like(closed)
    for i in range(1,n):
        x,y,cw,ch,area=stats[i]
        if area>75 and y<260: regions[labels==i]=1
    contours,_=cv2.findContours(regions,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    silhouette=np.zeros_like(regions)
    cv2.drawContours(silhouette,contours,-1,1,-1)
    # Mask narrow color-based semantic regions before hair so visible face is retained.
    warm=(r>g+13)&(g>b+3)&(r>115)&(g>85)&v
    # Back face is small; eyeline and ear are retained in a generous head box.
    skin=warm&(xx>205)&(yy>140)&(yy<344)
    # Restrict face-colored stray hair/reflections via saturation and region.
    skin &= (b<207)
    red=(r>g+14)&(r>b+18)&(r>79)&(yy>310)&(yy<443)&v
    # Bow has strong burgundy pigmentation and sits at front of uniform.
    bow=red & (xx>205)
    pale=(r>90)&(g>85)&(b>85)&(abs(r-g)<55)&(abs(g-b)<55)&(yy>292)&(yy<404)&v
    collar=pale & (xx>120)
    # Assign independently, conserving every source RGBA byte exactly.
    masks={}
    used=np.zeros_like(v)
    for role,candidate in [('skin.visible',skin),('bow.visible',bow),('collar.visible',collar),('hair.visible',silhouette.astype(bool)&v)]:
        available=candidate & ~used
        masks[role]=available;used|=available
    masks['uniform.visible']=v&~used
    all_count=sum(m.astype('uint8') for m in masks.values())
    assert np.array_equal(all_count,v.astype('uint8'))
    parts={}
    for role in ROLES:
        arr=source.copy();arr[~masks[role]]=0;parts[role]=arr
    reconstructed=source.copy();reconstructed[v]=0
    for layer in parts.values():reconstructed+=layer
    assert np.array_equal(reconstructed,source)
    if write:
        folder=OUT/f'yaw{view:g}'.replace('.','p');folder.mkdir(parents=True,exist_ok=True)
        for role,a in parts.items():Image.fromarray(a,'RGBA').save(folder/(role+'.png'))
        Image.fromarray(reconstructed,'RGBA').save(folder/'recomposed.png')
    return {'angle':view,'sourcePixelSHA256':image_sha(source),'sourceDimensions':[w,h],
            'sourceAlphaPixels':int(v.sum()),'layerVisiblePixelCounts':{role:int(masks[role].sum()) for role in ROLES},
            'recompositionByteExact':True,'sourceUnmodified':True,'paintedHiddenPixels':0,
            'semanticClass':'appearance/region-guided candidate; pixel-wise exclusive; artwork quality pending review'}
def run():
    OUT.mkdir(parents=True,exist_ok=True)
    views=[split(a) for a in (90.,112.5,135.)]
    grid=Image.new('RGB',(320*6,370*3),(37,42,52));d=ImageDraw.Draw(grid)
    for row,angle in enumerate((90.,112.5,135.)):
        folder=OUT/f'yaw{angle:g}'.replace('.','p')
        for col,name in enumerate(('recomposed',)+ROLES):
            path=folder/(name+'.png')
            with Image.open(path) as im:
                tile=Image.new('RGBA',(443,443),(58,65,78,255));tile.alpha_composite(im.convert('RGBA'))
            grid.paste(tile.convert('RGB').resize((312,312),Image.Resampling.LANCZOS),(col*320,row*370+29))
            d.text((col*320+8,row*370+7),f'{angle:g}° / {name}',fill='white')
    grid.save(OUT/'contact.jpg',quality=92)
    (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 source semantic layer candidates</title><style>body{background:#202733;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>90° / 112.5° / 135° RGBA visible semantic candidates</h2><p>Five mutually exclusive pixel layers per view. Pixel recomposition is exact. The semantic boundary estimates are provisional; hidden underpaint and painter-approved ArtMesh remain outside this source layer set.</p><img src="contact.jpg">')
    report={'schema':'KOMA_P15_133_SOURCE_SEMANTIC_LAYER_CANDIDATES_V1','characterId':'p0_character_001','sourceAngles':[90,112.5,135],
      'parts':list(ROLES),'views':views,'visibleSourceRecompositionExact':True,'artistApprovedSemantics':False,
      'sourceNativeReferenceApproved':False,'hiddenUnderpaintVerified':False,'physicalOcclusionValidated':False,
      'fullRotationVisualAcceptance':False,'review':'private-assets/exports/p15-133-semantic-source/index.html',
      'next':'Assess each segmentation boundary visually, then add separately generated painted occluded materials and correct geometry correspondence before using as ArtMesh.'}
    E.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'views':[x['layerVisiblePixelCounts'] for x in views],'exact':report['visibleSourceRecompositionExact']}))
if __name__=='__main__':run()

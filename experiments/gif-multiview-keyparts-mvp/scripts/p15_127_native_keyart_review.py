#!/usr/bin/env python3
"""Register an independently generated 112.5° source painting for visual acceptance."""
from pathlib import Path
import json,hashlib
import cv2,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent.parent
P=ROOT/'private-assets'
GEN=P/'p15-127-yaw112p5'
OUT=P/'exports/p15-127-yaw112p5-review'
EVIDENCE=ROOT/'evidence/p15-127-native-keyart-qa.json'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def source(angle):return np.array(Image.open(P/f'extracted/whole/yaw{angle:03}.png').convert('RGBA'))
def registered():
    native=np.array(Image.open(GEN/'yaw112p5-native.png').convert('RGBA'))
    # Source paintings are 443² frames. Preserve the full native art separately,
    # and use a normalized review raster only; no new art is painted here.
    # Whole-canvas resampling approximately matches the original silhouette scale.
    res=Image.fromarray(native,'RGBA').resize((443,443),Image.Resampling.LANCZOS)
    return np.asarray(res).copy()
def bbox(a):
    binary=(a[...,3]>128).astype('uint8');n,l,stats,_=cv2.connectedComponentsWithStats(binary,8)
    k=max(range(1,n),key=lambda i:stats[i,cv2.CC_STAT_AREA]);return [int(x) for x in stats[k]]
def audit(save=True):
    meta=json.loads((GEN/'generation-result.json').read_text())
    path=GEN/'yaw112p5-native.png'
    assert meta['actual_image_tool_used'] and meta['tool']=='image_gen.imagegen'
    assert path.is_file() and sha(path)==meta['sha256']
    native=Image.open(path);assert native.mode=='RGBA' and native.size==(1254,1254)
    inputs={str(a):P/f'extracted/whole/yaw{a:03}.png' for a in (90,135,180)}
    assert all(p.exists() for p in inputs.values())
    normalized=registered();src={a:source(a) for a in (90,135,180)}
    positions={str(a):bbox(f) for a,f in src.items()};positions['112.5']=bbox(normalized)
    meta_out={'schema':'KOMA_P15_127_NATIVE_KEYART_VISUAL_REVIEW_V1','characterId':'p0_character_001',
      'generator':meta['tool'],'actualNativeToolInvoked':True,'nativeImage':'private-assets/p15-127-yaw112p5/yaw112p5-native.png',
      'nativeSHA256':meta['sha256'],'nativeDimensions':[1254,1254],'sourceReferenceSHA256':{a:sha(p) for a,p in inputs.items()},
      'registeredOutput':'private-assets/exports/p15-127-yaw112p5-review/yaw112p5-review.png',
      'reviewCanvasDimensions':[443,443],'normalization':'whole canvas Lanczos resampling; native image remains unchanged',
      'largestForegroundBBoxXYWH':positions,'originalImageAlphaExtrema':list(native.getchannel('A').getextrema()),
      'independentNativeRasterConfirmed':True,'matchedPhysicalYawVerified':False,
      'geometryAndIdentityArtistApproved':False,'semanticArtMeshApproved':False,'hiddenUnderpaintApproved':False,
      'visualAcceptance':False,
      'next':'Visually assess size/linework, orientation, hair/face/shoulder identity; validate 90–112.5–135 transition before using as VDD keyview.'}
    if save:
        OUT.mkdir(exist_ok=True,parents=True)
        Image.fromarray(normalized,'RGBA').save(OUT/'yaw112p5-review.png')
        board=Image.new('RGB',(4*350,400),(36,43,54));draw=ImageDraw.Draw(board)
        for i,(a,image) in enumerate([(90,src[90]),(112.5,normalized),(135,src[135]),(180,src[180])]):
            tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(image,'RGBA'))
            board.paste(tile.convert('RGB').resize((345,345),Image.Resampling.LANCZOS),(i*350,30))
            draw.text((i*350+8,8),f'{a:g} deg / '+('model source candidate' if a==112.5 else 'recovered source'),fill='white')
        board.save(OUT/'source-contact.jpg',quality=94)
        (OUT/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>P0 112.5 independent art</title><style>body{background:#202832;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Original 90° / generated 112.5° / original 135° / original 180°</h2><p>Native model-generated 112.5° image registered for candidate visual QA. Requested angle and anatomical registration are not proven. Native RGBA source is preserved.</p><img src="source-contact.jpg">')
        meta_out['review']='private-assets/exports/p15-127-yaw112p5-review/index.html'
        EVIDENCE.write_text(json.dumps(meta_out,indent=2,ensure_ascii=False)+'\n')
    return meta_out
if __name__=='__main__':
    qa=audit();print(json.dumps({'nativeSHA256':qa['nativeSHA256'],'sourceBBoxes':qa['largestForegroundBBoxXYWH'],'review':qa.get('review')},indent=2))

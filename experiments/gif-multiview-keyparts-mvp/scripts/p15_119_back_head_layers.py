#!/usr/bin/env python3
"""Create reversible, appearance-classified candidate layers from original back-head drawings."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent.parent
P=R/'private-assets'
OUT=P/'exports/p15-119-back-head-layers'
E=R/'evidence/p15-119-back-head-layers-qa.json'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def split(angle,save=True):
    src=P/f'extracted/whole/yaw{angle:03}.png'
    arr=np.array(Image.open(src).convert('RGBA'))
    rgb=arr[...,:3].astype(np.int16)
    # Deterministic approximate pink/mauve color selection; NOT a semantic hair segmentation.
    r,g,b=np.moveaxis(rgb,-1,0)
    pink=(r>g+9)&(b>g+1)&(r>67)&(b>60)&(arr[...,3]>0)
    a=arr.copy(); bkg=arr.copy()
    a[~pink]=0; bkg[pink]=0
    # A lossless, non-overlapping visible-pixel partition (no inferred hidden underpaint).
    composed=a.astype(np.int16)+bkg.astype(np.int16)
    exact=np.array_equal(composed,arr.astype(np.int16))
    assert exact
    if save:
        folder=OUT/f'yaw{angle:03}';folder.mkdir(parents=True,exist_ok=True)
        Image.fromarray(a,'RGBA').save(folder/'pink-appearance.png')
        Image.fromarray(bkg,'RGBA').save(folder/'remaining-visible.png')
        Image.fromarray(arr,'RGBA').save(folder/'reassembled.png')
    total=int(np.count_nonzero(arr[...,3]));count=int(np.count_nonzero(a[...,3]));left=int(np.count_nonzero(bkg[...,3]))
    return {'angle':angle,'source':str(src.relative_to(P)),'sourceSHA256':sha(src),
            'visiblePixelCount':total,'pinkClassifiedPixelCount':count,'remainingVisiblePixelCount':left,
            'pixelRecompositionExact':exact,'partOverlapPixels':0,
            'classSemantics':'pixel appearance candidate, not verified anatomy or paintable hair',
            'occludedSurfaceReconstruction':False}

def build():
    rows=[split(i) for i in (135,180)]
    contact=Image.new('RGB',(450*4,505*2),(34,39,47));draw=ImageDraw.Draw(contact)
    for row_index,angle in enumerate((135,180)):
        for col,name in enumerate(('source','pink-appearance','remaining-visible','reassembled')):
            src=(P/f'extracted/whole/yaw{angle:03}.png') if name=='source' else OUT/f'yaw{angle:03}/{name}.png'
            tile=Image.new('RGBA',(443,443),(65,72,84,255))
            with Image.open(src) as im:tile.alpha_composite(im.convert('RGBA'))
            contact.paste(tile.convert('RGB'),(450*col,505*row_index+33))
            draw.text((450*col+12,505*row_index+8),f'{angle} | {name}',fill=(255,255,255))
    contact.save(OUT/'contact.jpg',quality=93)
    (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 rear-head candidate layers</title><style>body{background:#222;color:#eee;font:16px system-ui}img{max-width:100%}</style><h1>135° / 180° reversible appearance layers</h1><p>Pixel-exact partition of existing head references, not semantic ArtMesh, hidden-surface painting or body/garment reconstruction.</p><img src="contact.jpg">')
    report={'schema':'KOMA_P15_119_BACK_HEAD_VISIBLE_PARTITION_V1','characterId':'p0_character_001',
            'outputs':rows,'candidateLayerCount':4,'angles':[135,180],
            'recompositionExact':all(x['pixelRecompositionExact'] for x in rows),
            'nativeSourcePreserved':True,'semanticallyRegisteredArtMesh':False,
            'bodyAndGarmentCovered':False,'hiddenUnderpaintCovered':False,'artistApproved':False,
            'review':'private-assets/exports/p15-119-back-head-layers/index.html',
            'next':'Create approved independently painted back head/hair anatomy plus clothing and underlay art at 135/180, register to P0 anchors and test visual occlusion.'}
    E.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False)[:1100])
if __name__=='__main__': build()

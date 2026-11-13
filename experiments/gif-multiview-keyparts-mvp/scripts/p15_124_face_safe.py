#!/usr/bin/env python3
"""Compare face-safe source ownership with region-limited garment deformation."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw
from p15_121_rear_arc_render import ANGLES,KEYS,load,sha
ROOT=Path(__file__).resolve().parent.parent
P=ROOT/'private-assets'
OUT=P/'exports/p15-124-face-safe'
EVIDENCE=ROOT/'evidence/p15-124-face-safe-qa.json'

def key(angle): return f'yaw{angle:06.2f}'.replace('.','p')+'.png'
def source(angle,variant):
    return np.asarray(Image.open(P/f'exports/p15-{variant}/{key(angle)}').convert('RGBA')).copy()
def blend_premultiplied(a,b,w):
    aa=a.astype(np.float32)/255;bb=b.astype(np.float32)/255
    alpha=aa[...,3:4]*(1-w)+bb[...,3:4]*w
    rgb=(aa[...,:3]*aa[...,3:4]*(1-w)+bb[...,:3]*bb[...,3:4]*w)/np.maximum(alpha,1.e-6)
    out=np.uint8(np.round(np.clip(np.concatenate([rgb,alpha],axis=-1)*255,0,255)))
    out[out[...,3]==0]=0
    return out

def compose(angle,neckline=330,feather=24):
    if angle in KEYS: return load()[angle]
    single=source(angle,'122-source-owned')
    parts=source(angle,'123-part-vdd')
    height=single.shape[0]
    yy=np.arange(height,dtype=np.float32)[:,None,None]
    w=np.broadcast_to(np.clip((yy-(neckline-feather/2))/feather,0,1),single[...,3:4].shape)
    w=w*w*(3-2*w)
    # Source-owned full head/facial material; alternative garment affects lower torso only.
    return blend_premultiplied(single,parts,w)

def composite_rgb(x):
    al=x[...,3:4].astype(np.float32)/255
    return x[...,:3]*al+(1-al)*np.array([49,61,78])
def build():
    OUT.mkdir(parents=True,exist_ok=True)
    frames=[compose(a) for a in ANGLES]
    for angle,im in zip(ANGLES,frames):Image.fromarray(im,'RGBA').save(OUT/key(angle))
    jumps=[round(float(np.abs(composite_rgb(a)-composite_rgb(b)).mean()),4) for a,b in zip(frames,frames[1:])]
    native=load();exact=all(np.array_equal(frames[ANGLES.index(a)],native[a]) for a in KEYS)
    contact=Image.new('RGB',(320*5,352*3),(35,41,49));draw=ImageDraw.Draw(contact)
    for j,method in enumerate(('122-source-owned','123-part-vdd','124-face-safe')):
        for i,a in enumerate((90,112.5,135,157.5,180)):
            sample=frames[ANGLES.index(a)] if j==2 else source(a,method)
            tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(sample,'RGBA'))
            contact.paste(tile.convert('RGB').resize((315,315),Image.Resampling.LANCZOS),(i*320,j*352+28))
            draw.text((i*320+6,j*352+5),f'P15-{method} / {a:g}',fill='white')
    contact.save(OUT/'comparison.jpg',quality=93)
    previews=[]
    for f in frames+frames[-2:0:-1]:
        pic=Image.new('RGBA',(443,443),(49,61,78,255));pic.alpha_composite(Image.fromarray(f,'RGBA'))
        previews.append(pic.convert('RGB'))
    previews[0].save(OUT/'face-safe-loop.gif',save_all=True,append_images=previews[1:],duration=180,loop=0,optimize=False)
    (OUT/'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><title>P0 facial integrity and garment ownership</title><style>body{background:#202731;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>90–180° face-safe / garment source studies</h2><p>Face/head source ownership is retained from P15-122. Torso pixels below the neckline use P15-123's independently warped part textures. This is a visibility-region diagnostic, not a physically validated ArtMesh.</p><img src="comparison.jpg"><p>Temporal diagnostic</p><img src="face-safe-loop.gif">''')
    face_roi=(slice(155,320),slice(200,370))
    deviations={}
    for a in (101.25,112.5,123.75,146.25,157.5,168.75):
        actual=frames[ANGLES.index(a)][face_roi]
        baseline=source(a,'122-source-owned')[face_roi]
        deviations[str(a)]=round(float(np.abs(actual.astype('float32')-baseline.astype('float32')).mean()),5)
    qa={'schema':'KOMA_P15_124_FACE_SAFE_REGION_V1','characterId':'p0_character_001','angles':ANGLES,
        'interpolation':'P15-122 head/face region and P15-123 lower-garment region blended in premultiplied alpha',
        'necklineRegion':{'centerY':330,'featherPixels':24},'nativeKeyframesPixelExact':exact,
        'adjacentCompositeRGBMAE':jumps,'maxAdjacentCompositeRGBMAE':max(jumps),
        'faceRoiAbsoluteDifferenceFromSourceOwned':deviations,
        'underpaintVerified':False,'physicalCorrespondenceVerified':False,'artistVisualAccepted':False,
        'review':'private-assets/exports/p15-124-face-safe/index.html',
        'next':'Assess face integrity vs garment seam. Produce source-drawn masks, hidden geometry and physically matched anchors before final VDD selection.'}
    EVIDENCE.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'maxAdjacentCompositeRGBMAE':max(jumps),'nativeKeyframesPixelExact':exact,'faceRoiDifference':deviations}))
if __name__=='__main__':build()

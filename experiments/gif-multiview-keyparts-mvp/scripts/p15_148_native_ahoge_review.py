#!/usr/bin/env python3
"""Provenance and alpha-domain spatial acceptance of independently painted ahoge."""
import json,hashlib
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw
from p15_134_underpaint_probe import P,SOURCE,rgba,compose,background_rgb
from p15_129_ahoge_ownership import keyframes,ANGLES,KEYS
from p15_128_keyart_registration import frame_interp,jumps
from p15_131_semantic_landmarks import POINTS
ROOT=Path(__file__).resolve().parent.parent
GEN=P/'p15-148-ahoge';PNG=GEN/'ahoge-native.png';META=GEN/'generation-result.json'
OUT=P/'exports/p15-148-native-ahoge';E=ROOT/'evidence/p15-148-native-ahoge-qa.json'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def actual_source():
    data=json.loads(META.read_text())
    assert 'image_gen.imagegen' in json.dumps(data)
    assert sha(PNG) in json.dumps(data)
    with Image.open(PNG) as im:
        assert im.mode=='RGBA' and im.size==(1254,1254)
        return np.asarray(im.resize((443,443),Image.Resampling.LANCZOS)).copy(),data

def overlap_stats(source,part):
    alpha=part[...,3]>128
    ys,xs=np.where(alpha)
    assert xs.size>0
    source_alpha=source[...,3]>64
    outside=alpha&~source_alpha
    yy,xx=np.indices(alpha.shape)
    permitted=(yy<120)&(xx>=165)&(xx<360)
    part_region=alpha&permitted
    face_zone=(yy>130)&(xx>245)&(yy<330)
    face=alpha&face_zone
    n,_,stats,_=cv2.connectedComponentsWithStats(alpha.astype('uint8'),8)
    large=[int(stats[i,cv2.CC_STAT_AREA]) for i in range(1,n) if stats[i,cv2.CC_STAT_AREA]>50]
    return {'opaquePixels':int(alpha.sum()),'boundingBoxXYXY':[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())],
            'insideExpectedTopRegion':int(part_region.sum()),'outsideExpectedTopRegion':int((alpha&~permitted).sum()),
            'outsideSourceSilhouette':int(outside.sum()),
            'faceRegionPixels':int(face.sum()),'componentSizesOver50':sorted(large,reverse=True)}

def evaluate(save=True):
    source=rgba(SOURCE)
    part,metadata=actual_source()
    stats=overlap_stats(source,part)
    # Registration must be judged before use; the untouched new part can
    # only be overlaid as diagnostic because source contains its own ahoge.
    over=compose(source,part)
    source_keys=keyframes()
    images=frame_interp(source_keys[90.],over,source_keys[135.])
    baseline=frame_interp(source_keys[90.],source_keys[112.5],source_keys[135.])
    reported={'schema':'KOMA_P15_148_NATIVE_ISOLATED_AHOGE_QA_V1',
     'characterId':'p0_character_001','requestedYaw':112.5,
     'generator':'image_gen.imagegen','nativeAssetSHA256':sha(PNG),'nativeDimensions':[1254,1254],
     'registeredReviewCanvas':[443,443],'alphaStats':stats,'nativeAssetPreserved':True,
     'sourceOriginalUnchanged':True,'sourceEndpoints90And135Exact':all(np.array_equal(images[ANGLES.index(k)],source_keys[k]) for k in (90.,135.)),
     'maxAdjacentRGBMAE':{'source':max(jumps(baseline)),'directOverlayCandidate':max(jumps(images))},
     'directOverlayRGBAAbsoluteMAE':round(float(np.abs(over.astype(np.float32)-source.astype(np.float32)).mean()),4),
     'registrationGatePassed':bool(stats['faceRegionPixels']==0 and stats['outsideExpectedTopRegion']<100 and stats['boundingBoxXYXY'][2]<360),
     'rootTipArtistVerified':False,'nativeSourceCompatible':False,'completeHiddenScalpApproved':False,'continuousVisualAccepted':False,
     'review':'private-assets/exports/p15-148-native-ahoge/index.html',
     'next':'Register an isolated root and tip with original source ahoge and remove original owned pixels. Only then test replacement under 90–135° yaw.'}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        Image.fromarray(part,'RGBA').save(OUT/'ahoge-source-review.png')
        Image.fromarray(over,'RGBA').save(OUT/'direct-overlay-review.png')
        board=Image.new('RGB',(350*4,410),(35,42,52));draw=ImageDraw.Draw(board)
        for i,(label,img) in enumerate([('canonical 112.5',source),('isolated ahoge',part),('direct overlay',over),
                                       ('original 135',source_keys[135.])]):
            tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(img,'RGBA'))
            board.paste(tile.convert('RGB').resize((343,343),Image.Resampling.LANCZOS),(350*i,33))
            draw.text((350*i+8,9),label,fill='white')
        board.save(OUT/'comparison.jpg',quality=94)
        yaw=Image.new('RGB',(310*5,355*2),(35,42,52));draw=ImageDraw.Draw(yaw)
        for j,(label,sequence) in enumerate((('source',baseline),('independent overlay',images))):
            for i,(angle,img) in enumerate(zip(ANGLES,sequence)):
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(img,'RGBA'))
                yaw.paste(tile.convert('RGB').resize((305,305),Image.Resampling.LANCZOS),(310*i,j*355+28))
                draw.text((310*i+5,j*355+6),f'{label} {angle:g}',fill='white')
        yaw.save(OUT/'yaw-comparison.jpg',quality=94)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 isolated ahoge source</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>112.5° independent loop ahoge asset</h2><p>Native RGBA source versus canonical reference and direct overlay diagnostic. Isolated source must be registered and have the existing ahoge removed before use.</p><img src="comparison.jpg"><h2>Yaw diagnostic</h2><img src="yaw-comparison.jpg">')
        E.write_text(json.dumps(reported,indent=2,ensure_ascii=False)+'\n')
    return reported
if __name__=='__main__':
    q=evaluate()
    print(json.dumps({k:q[k] for k in ('alphaStats','registrationGatePassed','maxAdjacentRGBMAE','directOverlayRGBAAbsoluteMAE')},indent=2))

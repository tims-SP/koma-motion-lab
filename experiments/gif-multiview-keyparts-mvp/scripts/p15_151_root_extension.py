#!/usr/bin/env python3
"""Local geometric extension of 90-degree loop roots into existing crown.

Geometry-only registration study: it cannot invent artist-authored hidden
scalp material. Compare with the original 90/112.5/135 source keys.
"""
import json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_150_three_view_ahoge import SOURCE_KEYS,load_native,fit,replace_upper,keyframes
from p15_151_double_root_gate import root_tracks,ATTACHMENT_Y
from p15_129_ahoge_ownership import ANGLES
from p15_128_keyart_registration import frame_interp,jumps
from p15_134_underpaint_probe import P,compose,background_rgb
ROOT=Path(__file__).resolve().parent.parent
OUT=P/'exports/p15-151-root-extension'
E=ROOT/'evidence/p15-151-root-extension-qa.json'

def extend_lower_roots(src,source_end=56,new_end=81,top=28):
    h,w=src.shape[:2]
    xs,ys=np.meshgrid(np.arange(w,dtype=np.float32),np.arange(h,dtype=np.float32))
    mapped=ys.copy()
    # An invertible vertical piecewise affine field retains crown-loop top
    # and gradually lengthens both lower legs.
    between=(ys>top)&(ys<=new_end)
    mapped[between]=top+(ys[between]-top)*(source_end-top)/(new_end-top)
    beyond=ys>new_end
    mapped[beyond]=source_end+(ys[beyond]-new_end)
    result=cv2.remap(src,xs,mapped,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
    return result

def composite_new(source,fitted,end):
    y,x=np.indices((443,443))
    old=(source[...,3]>96)&(y<55)&(x>195)&(x<360)
    base=source.copy();base[old]=0
    f=fitted.copy()
    fade=np.clip((end+10-y)/18,0,1).astype(np.float32)
    fade=fade*fade*(3-2*fade)
    f[...,3]=np.uint8(np.round(f[...,3].astype(np.float32)*fade))
    f[(x<177)|(x>365)]=0
    f[f[...,3]==0]=0
    return compose(base,f)

def evaluate(save=True):
    original=keyframes()
    native,_=load_native(90.)
    fitted,_=fit(native,original[90.])
    baseline={a:original[a].copy() for a in SOURCE_KEYS}
    variants={}
    for name,end in [('source_fit',56),('root_075',75),('root_081',81),('root_087',87)]:
        extra=fitted.copy() if name=='source_fit' else extend_lower_roots(fitted,new_end=end)
        part=extra if name!='source_fit' else fitted
        result=composite_new(original[90.],part,end)
        tracks=root_tracks(part)
        root75=next(row for row in tracks if row['y']==ATTACHMENT_Y)
        # Keep other two generated replacements identical to P15-150.
        parts={90.:result}
        for angle in (112.5,135.):
            raw,_=load_native(angle)
            reg,_=fit(raw,original[angle])
            parts[angle]=replace_upper(original[angle],reg)
        seq=frame_interp(parts[90.],parts[112.5],parts[135.])
        distortion=jumps(seq)
        upper=np.s_[:105,155:365]
        variants[name]={'geometryEnd':end,'rootAtY75':root75['twoRootsVisible'],
                        'lastPairedRowY':max((r['y'] for r in tracks if r['twoRootsVisible']),default=None),
                        'upperRootRGBAAbsoluteMAE':round(float(np.abs(result[upper].astype(np.float32)-original[90.][upper].astype(np.float32)).mean()),4),
                        'maxAdjacentRGBMAE':max(distortion),'adjacentRGBMAE':distortion,
                        'sourceBelowY130Exact':bool(np.array_equal(result[130:],original[90.][130:]))}
        if save:
            OUT.mkdir(parents=True,exist_ok=True)
            Image.fromarray(part,'RGBA').save(OUT/(name+'-isolated.png'))
            Image.fromarray(result,'RGBA').save(OUT/(name+'-composite.png'))
        variants[name]['part']=part;variants[name]['composite']=result;variants[name]['frames']=seq
    source_sequence=frame_interp(original[90.],original[112.5],original[135.])
    ref=max(jumps(source_sequence))
    q={'schema':'KOMA_P15_151_ROOT_EXTENSION_STUDY_V1','characterId':'p0_character_001',
       'sourceAngles':list(SOURCE_KEYS),'samples':list(ANGLES),
       'sourceMaximumAdjacentRGBMAE':ref,
       'variants':{name:{k:v for k,v in data.items() if k not in ('part','composite','frames')} for name,data in variants.items()},
       'geometry':'piecewise vertical inverse remap constrained above crown and source-preserving alpha composite',
       'nativeSourcePreserved':True,'actualHiddenCrownScalpPaintVerified':False,
       'rootTopologyArtistApproved':False,'fullYawVisualAccepted':False,
       'review':'private-assets/exports/p15-151-root-extension/index.html',
       'next':'Create an authored loop with both roots physically embedded beneath matching scalp material in each source view; confirm source-level registration and yaw frame appearance.'}
    if save:
        board=Image.new('RGB',(335*4,375),(35,42,53));d=ImageDraw.Draw(board)
        for i,(name,value) in enumerate(variants.items()):
            img=value['composite']
            canvas=Image.new('RGBA',(443,443),(49,61,78,255));canvas.alpha_composite(Image.fromarray(img,'RGBA'))
            board.paste(canvas.convert('RGB').resize((328,328),Image.Resampling.LANCZOS),(i*335,30))
            d.text((i*335+6,7),name,fill='white')
        board.save(OUT/'root-composites.jpg',quality=94)
        board=Image.new('RGB',(310*5,350*2),(35,42,53));d=ImageDraw.Draw(board)
        for row,(name,images) in enumerate([('source',source_sequence),('root_081',variants['root_081']['frames'])]):
            for i,(angle,im) in enumerate(zip(ANGLES,images)):
                layer=Image.new('RGBA',(443,443),(49,61,78,255));layer.alpha_composite(Image.fromarray(im,'RGBA'))
                board.paste(layer.convert('RGB').resize((305,305),Image.Resampling.LANCZOS),(i*310,row*350+30))
                d.text((i*310+6,row*350+7),f'{name} {angle:g}',fill='white')
        board.save(OUT/'yaw-comparison.jpg',quality=94)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 ahoge root extension</title><style>body{font:16px system-ui;background:#202833;color:#eee}img{max-width:100%}</style><h2>90° double-root geometric attachment study</h2><p>Source 90° loop material stretched toward y75–87 while preserving original raw keys and provenance. Generated extrapolation is not painter-authored hidden scalp.</p><img src="root-composites.jpg"><h2>Yaw stress</h2><img src="yaw-comparison.jpg">')
        E.write_text(json.dumps(q,indent=2,ensure_ascii=False)+'\n')
    return q
if __name__=='__main__':
    q=evaluate();print(json.dumps({'baseline':q['sourceMaximumAdjacentRGBMAE'],'variants':q['variants']},indent=2))

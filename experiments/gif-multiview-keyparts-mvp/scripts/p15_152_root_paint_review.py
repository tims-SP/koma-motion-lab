#!/usr/bin/env python3
"""QA for a painter-generated 90° ahoge-to-crown junction source.

Compare only real rendered candidates; the source keyviews remain unchanged.
An independent root patch does not imply artist-approved matched root topology.
"""
import json,hashlib
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_134_underpaint_probe import P,rgba,compose,background_rgb
from p15_129_ahoge_ownership import keyframes,ANGLES
from p15_128_keyart_registration import frame_interp,jumps
from p15_151_double_root_gate import root_tracks
ROOT=Path(__file__).resolve().parent.parent
GEN=P/'p15-152-root-paint'
PNG=GEN/'root-patch-native.png';META=GEN/'generation-result.json'
OUT=P/'exports/p15-152-root-paint'; E=ROOT/'evidence/p15-152-root-paint-qa.json'
YAW=90.
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def native():
    info=json.loads(META.read_text())
    assert 'image_gen.imagegen' in json.dumps(info) and sha(PNG) in json.dumps(info)
    with Image.open(PNG) as im:
        assert im.mode=='RGBA' and im.size==(1254,1254)
        source=np.asarray(im.resize((443,443),Image.Resampling.LANCZOS)).copy()
    return source
def measure(part,source):
    yy,xx=np.indices(part.shape[:2])
    visible=part[...,3]>128
    ys,xs=np.where(visible)
    if not len(xs): raise ValueError('empty generated art')
    expected=(xx>=170)&(xx<=300)&(yy>=32)&(yy<=107)
    near_head=(source[...,3]>48)
    return {'opaquePixels':int(visible.sum()),'bboxXYXY':[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())],
            'opaqueOutsideExpectedROI':int((visible&~expected).sum()),
            'opaqueOutsideSourceSilhouette':int((visible&~near_head).sum()),
            'overlapExistingArt':int((visible&near_head).sum())}
def translate(src,dx,dy):
    return cv2.warpAffine(src,np.float32([[1,0,dx],[0,1,dy]]),(443,443),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
def registration(source,part):
    yy,xx=np.indices((443,443))
    target=(source[...,3]>64)&(xx>=180)&(xx<=300)&(yy>=45)&(yy<100)
    result=[]
    for dx in range(-32,33,4):
        for dy in range(-24,25,4):
            moved=translate(part,dx,dy)
            valid=moved[...,3]>128
            inter=(valid&target).sum();union=(valid|target).sum()
            score=inter/max(1,union)
            # Strongly penalize the added patch outside source silhouette, but
            # retain crown-root extension beyond existing source as a possible asset.
            over=(valid&(source[...,3]<=64)).sum()/max(1,int(valid.sum()))
            result.append((float(score-.4*over),dx,dy,float(score)))
    _,dx,dy,iou=max(result)
    return translate(part,dx,dy),{'shiftXY':[dx,dy],'jacketExcludedCrownIoU':round(iou,5)}
def bounded_clean(part,threshold=32):
    yy,xx=np.indices(part.shape[:2])
    domain=(xx>=170)&(xx<=300)&(yy>=32)&(yy<=107)
    mask=(part[...,3]>threshold)&domain
    cleaned=part.copy()
    cleaned[~mask]=0
    return cleaned,mask

def compose_patch(source,patch,alpha_strength=.5):
    mask=patch[...,3].astype(np.float32)/255
    dest=patch.copy()
    dest[...,3]=np.uint8(np.round(dest[...,3].astype(np.float32)*alpha_strength))
    # Keep underlying canonical ink and crown. Alpha overlay is source-only diagnostic.
    return compose(source,dest)
def evaluate(save=True):
    keys=keyframes()
    part=native()
    raw=measure(part,keys[90.])
    aligned,fit=registration(keys[90.],part)
    aligned_stats=measure(aligned,keys[90.])
    cleaned,cleanmask=bounded_clean(aligned)
    original_alpha=part[...,3]
    yy,xx=np.indices(part.shape[:2])
    intended=(xx>=170)&(xx<=300)&(yy>=32)&(yy<=107)
    alpha_leak=(original_alpha>0)&~intended
    raw_leak_count=int(alpha_leak.sum())
    versions={'original':keys[90.],
              'root_patch_025':compose_patch(keys[90.],aligned,.25),
              'root_patch_050':compose_patch(keys[90.],aligned,.5),
              'root_patch_075':compose_patch(keys[90.],aligned,.75),
              'bounded_clean_025':compose_patch(keys[90.],cleaned,.25),
              'bounded_clean_050':compose_patch(keys[90.],cleaned,.5)}
    scores={}
    for name,frame in versions.items():
        seq=frame_interp(frame,keys[112.5],keys[135.])
        roi=np.s_[35:106,168:307]
        dif=np.abs(background_rgb(frame)[roi]-background_rgb(keys[90.])[roi])
        scores[name]={'maxAdjacentRGBMAE':max(jumps(seq)),
                      'rootPatchRGBMAE':round(float(dif.mean()),4),
                      'native112p5And135Exact':bool(np.array_equal(seq[2],keys[112.5]) and np.array_equal(seq[4],keys[135.])),
                      'sourceBelowY130Exact':bool(np.array_equal(frame[130:],keys[90.][130:]))}
    qa={'schema':'KOMA_P15_152_NATIVE_AHOGE_ROOT_PATCH_V1','characterId':'p0_character_001',
       'sourceYaw':90.,'referenceAngles':[90.,112.5,135.],'samples':list(ANGLES),
       'nativeSHA256':sha(PNG),'nativeRGBA':True,'nativeCanvas':[1254,1254],
       'rawMaterial':raw,'alignedMaterial':aligned_stats,'alignment':fit,'variants':scores,
       'rawNonzeroAlphaOutsideExpectedROI':raw_leak_count,
       'rawTransparentRegionGatePassed':bool(raw_leak_count<300),
       'boundedCleanRemovedPixels':int(((aligned[...,3]>0)&~cleanmask).sum()),
       'boundedCleanBelowY130Exact':bool(np.array_equal(versions['bounded_clean_050'][130:],keys[90.][130:])),
       'candidateAdmissionGatePassed':False,
       'visualFindings':'Native paint adds large low-alpha grey-white noise around the crown; bounded cleaning restores the alpha domain, but the root drawing does not establish physical double-root attachment and frame continuity does not exceed the original baseline.',
       'nativeSourcePreserved':True,
       'artistVerifiedDoubleRootJunction':False,'hiddenScalpPaintApproved':False,
       'physicalStrandIdentityVerified':False,'continuousVisualAccepted':False,
       'review':'private-assets/exports/p15-152-root-paint/index.html',
       'next':'Complete physically matched double-root layers and scalp underpaint at all three source views, and verify their actual attachment without duplicate ink.'}
    if save:
        OUT.mkdir(exist_ok=True,parents=True)
        Image.fromarray(aligned,'RGBA').save(OUT/'aligned-root-patch.png')
        Image.fromarray(cleaned,'RGBA').save(OUT/'bounded-root-patch.png')
        panel=Image.new('RGB',(344*6,395),(36,42,53));d=ImageDraw.Draw(panel)
        for i,(label,img) in enumerate([('original',keys[90.]),('raw native patch',part),
                                         ('aligned patch',aligned),
                                         ('alpha .25',versions['root_patch_025']),
                                         ('alpha .50',versions['root_patch_050']),('bounded .50',versions['bounded_clean_050'])]):
            tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(img,'RGBA'))
            panel.paste(tile.convert('RGB').resize((338,338),Image.Resampling.LANCZOS),(344*i,30))
            d.text((344*i+6,6),label,fill='white')
        panel.save(OUT/'root-patch-comparison.jpg',quality=94)
        yaw=Image.new('RGB',(310*5,350*2),(36,42,53));draw=ImageDraw.Draw(yaw)
        for row,(name,source) in enumerate([('original',keys[90.]),('root_patch_050',versions['root_patch_050'])]):
            frames=frame_interp(source,keys[112.5],keys[135.])
            for i,(angle,img) in enumerate(zip(ANGLES,frames)):
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(img,'RGBA'))
                yaw.paste(tile.convert('RGB').resize((304,304),Image.Resampling.LANCZOS),(310*i,row*350+30))
                draw.text((310*i+6,row*350+7),f'{name} {angle:g}',fill='white')
        yaw.save(OUT/'yaw-comparison.jpg',quality=93)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 90° root paint</title><style>body{font:16px system-ui;background:#202833;color:#eee}img{max-width:100%}</style><h2>90° isolated crown attachment paint</h2><p>Native paint, bounded alignment, and alpha overlays compared with canonical key. Actual double-root continuity and physical scalp registration require independent visual acceptance.</p><img src="root-patch-comparison.jpg"><h2>90–135° yaw probe</h2><img src="yaw-comparison.jpg">')
        E.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    return qa
if __name__=='__main__':
    q=evaluate()
    print(json.dumps({k:q[k] for k in ('rawMaterial','alignedMaterial','alignment','variants')},indent=2))

#!/usr/bin/env python3
"""Validate three independently generated P0 loop ahoge RGBA parts.

Source-view region registration is measurable, while physical double-root
identity and hidden scalp paint need separate artist approval. Store artwork
outside Git and machine-readable QA evidence inside the lab repository.
"""
import hashlib,json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_129_ahoge_ownership import keyframes,ANGLES
from p15_128_keyart_registration import frame_interp,jumps
from p15_134_underpaint_probe import P,compose,background_rgb,rgba
from p15_148_ahoge_registration import shift
ROOT=Path(__file__).resolve().parent.parent
GEN=P/'p15-150-ahoge'
OUT=P/'exports/p15-150-three-view-ahoge'
E=ROOT/'evidence/p15-150-three-view-ahoge-qa.json'
SOURCE_KEYS=(90.,112.5,135.)
def image_for(a):
    return P/'p15-148-ahoge/ahoge-native.png' if a==112.5 else GEN/f'yaw{int(a):03d}'/'ahoge-native.png'
def metadata_for(a):
    return P/'p15-148-ahoge/generation-result.json' if a==112.5 else GEN/f'yaw{int(a):03d}'/'generation-result.json'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def view_name(a):return f'yaw{int(a):03d}'
def load_native(a):
    path=image_for(a)
    meta=json.loads(metadata_for(a).read_text())
    assert path.exists() and path.stat().st_size>50000
    assert 'image_gen.imagegen' in json.dumps(meta)
    assert sha(path) in json.dumps(meta)
    with Image.open(path) as img:
        assert img.mode=='RGBA' and img.size==(1254,1254)
        converted=np.asarray(img.resize((443,443),Image.Resampling.LANCZOS)).copy()
        assert img.getchannel('A').getextrema()[0]==0
    return converted,{'nativeSHA256':sha(path),'nativeDimensions':[1254,1254],'nativeFormat':'RGBA',
                      'alphaBBox443':list(Image.fromarray(converted).getchannel('A').getbbox() or [])}
def alpha_shape(part,source):
    alpha=part[...,3]>128
    y,x=np.where(alpha)
    assert len(x)
    n,_,stats,_=cv2.connectedComponentsWithStats(alpha.astype('uint8'),8)
    return {'opaquePixels':int(alpha.sum()),'boundingBoxXYXY':[int(x.min()),int(y.min()),int(x.max()),int(y.max())],
        'componentsOver20Pixels':sorted((int(stats[i,cv2.CC_STAT_AREA]) for i in range(1,n)
                        if stats[i,cv2.CC_STAT_AREA]>20),reverse=True),
        'opaqueBelowY120':int(alpha[120:].sum()),
        'opaqueOutsideSourceSilhouette':int((alpha&(source[...,3]<=64)).sum())}
def old_source_loop(source):
    yy,xx=np.indices(source.shape[:2])
    # Keep all 55px-and-lower original hair as immutable crown. The upper
    # visible ahoge is not a root/strand mask; this is a QA-only proxy.
    return (source[...,3]>96)&(yy<55)&(xx>195)&(xx<360)
def fit(part,source):
    target=old_source_loop(source)
    yy,xx=np.indices(target.shape)
    zone=(yy<56)&(xx>180)&(xx<375)
    results=[]
    # Source-view-specific bounded registration on the visible ahoge ink.
    for scale in (.8,.9,1.,1.1):
        for dx in range(-48,49,8):
            for dy in range(-24,25,8):
                aligned=shift(part,scale,dx,dy)
                current=(aligned[...,3]>128)&zone
                common=(current&target).sum()
                union=(current|target).sum()
                score=common/max(1,union)
                results.append((float(score),scale,dx,dy))
    score,scale,dx,dy=max(results)
    return shift(part,scale,dx,dy),{'scale':scale,'shiftXY':[dx,dy],'freeLoopAlphaIoU':round(score,5)}
def replace_upper(source,part,start=47,end=75):
    yy,xx=np.indices((443,443))
    old=old_source_loop(source)
    base=source.copy()
    base[old]=0
    foreground=part.copy()
    w=np.clip((end-yy)/float(end-start),0,1).astype(np.float32)
    w=w*w*(3-2*w)
    foreground[...,3]=np.uint8(np.round(foreground[...,3].astype(np.float32)*w))
    foreground[(xx<190)|(xx>365)]=0
    foreground[foreground[...,3]==0]=0
    return compose(base,foreground)
def run(save=True):
    nativekeys=keyframes()
    originals={};native_parts={};aligned_parts={};candidates={};details={}
    for a in SOURCE_KEYS:
        original=nativekeys[a]
        raw,provenance=load_native(a)
        fitted,params=fit(raw,original)
        candidate=replace_upper(original,fitted)
        originals[a]=original;native_parts[a]=raw;aligned_parts[a]=fitted;candidates[a]=candidate
        source_shape=alpha_shape(raw,original)
        fitted_shape=alpha_shape(fitted,original)
        eye_original=bool(np.array_equal(candidate[130:],original[130:]))
        details[f'{a:g}']={'provenance':provenance,'raw':source_shape,'aligned':fitted_shape,
                   'registration':params,'sourceBelowY130Exact':eye_original,
                   'freeLoopPixelsSource':int(old_source_loop(original).sum()),
                   'candidateDifferenceRGBMAE':round(float(np.abs(background_rgb(candidate)-background_rgb(original)).mean()),4),
                   'visibleSourceReplacementOnly':True}
    old=frame_interp(originals[90.],originals[112.5],originals[135.])
    new=frame_interp(candidates[90.],candidates[112.5],candidates[135.])
    baseline=jumps(old);trial=jumps(new)
    def ghost_proxy(frames):
        # Difference between alpha above source crown may detect doubled ghost silhouettes,
        # but material identity must still be checked with image QA.
        return [int(np.logical_xor((frames[i][:55,:,3]>128),(frames[i+1][:55,:,3]>128)).sum())
                for i in range(len(frames)-1)]
    result={'schema':'KOMA_P15_150_THREE_VIEW_INDEPENDENT_AHOGE_QA_V1',
        'characterId':'p0_character_001','sourceAngles':list(SOURCE_KEYS),'samples':list(ANGLES),
        'views':details,
        'render':{'baselineMaxAdjacentRGBMAE':max(baseline),'candidateMaxAdjacentRGBMAE':max(trial),
                  'baselineAdjacentRGBMAE':baseline,'candidateAdjacentRGBMAE':trial,
                  'baselineTopAlphaXor':ghost_proxy(old),'candidateTopAlphaXor':ghost_proxy(new)},
        'visualFindings':{
            'yaw090':'Generated loop is a disconnected arch with incomplete double-root attachment, and registered replacement shows a thin duplicate root stroke.',
            'yaw112p5':'Source-aligned part retains a root crossing and loop tail mismatch.',
            'yaw135':'Generated loop and root placement differ from source; registered replacement still leaves overlapping hair arcs.',
            'intermediates':'At 101.25 and 123.75 degrees, double loops and source face/garment ghosting remain visible.'
        },
        'assetAdmissionGate':{'passes':False,'candidateSelectedForProduction':False,
                              'reason':'Complete painted root identity, local source registration, scalp underpaint and continuous visual acceptance remain unverified.'},
        'sourceArtUnmodified':True,'nativeGeneratedFilesPreserved':True,
        'physicalDoubleRootIdentityVerified':False,'sourceAlignedPerPartArtApproved':False,
        'hiddenCrownUnderpaintApproved':False,'continuousVisualAccepted':False,
        'review':'private-assets/exports/p15-150-three-view-ahoge/index.html',
        'next':'Correct each original source-root attachment with independently painted hidden scalp and matching double-root anatomy; use actual verified strand identity before ArtMesh yaw.'}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(350*3,365*3),(34,42,54));d=ImageDraw.Draw(board)
        for row,(label,items) in enumerate([('Original key',originals),('Isolated source',native_parts),('Replacement candidate',candidates)]):
            for col,a in enumerate(SOURCE_KEYS):
                im=items[a]
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(im,'RGBA'))
                board.paste(tile.convert('RGB').resize((344,344),Image.Resampling.LANCZOS),(col*350,row*365+20))
                d.text((col*350+6,row*365+2),f'{label} {a:g}',fill='white')
                directory=OUT/view_name(a);directory.mkdir(exist_ok=True)
                Image.fromarray(im,'RGBA').save(directory/(label.lower().replace(' ','-')+'.png'))
                Image.fromarray(aligned_parts[a],'RGBA').save(directory/'aligned-part.png')
        board.save(OUT/'keyview-comparison.jpg',quality=94)
        yaw=Image.new('RGB',(310*5,348*2),(34,42,54));draw=ImageDraw.Draw(yaw)
        for row,(label,seq) in enumerate([('Reference',old),('Three-source',new)]):
            for i,(a,img) in enumerate(zip(ANGLES,seq)):
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(img,'RGBA'))
                yaw.paste(tile.convert('RGB').resize((304,304),Image.Resampling.LANCZOS),(310*i,row*348+28))
                draw.text((310*i+6,row*348+5),f'{label} {a:g}',fill='white')
                if row==1:Image.fromarray(img,'RGBA').save(OUT/(f'candidate-yaw{a:06.2f}'.replace('.','p')+'.png'))
        yaw.save(OUT/'yaw-comparison.jpg',quality=94)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 three keyview ahoge parts</title><style>body{background:#202832;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Three independent keyview ahoge parts</h2><p>Native generated transparent loop parts, source-view registrations, original-source-owned crown and five-angle interpolation. Source identity and crown underpaint require visual acceptance.</p><img src="keyview-comparison.jpg"><h2>Yaw comparison</h2><img src="yaw-comparison.jpg">')
        E.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result
if __name__=='__main__':
    q=run()
    print(json.dumps({'views':q['views'],'render':q['render']},indent=2))

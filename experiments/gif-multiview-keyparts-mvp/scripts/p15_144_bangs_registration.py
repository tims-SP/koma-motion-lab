#!/usr/bin/env python3
"""Register native front bangs to the 112.5° view with explicit eye ownership.

Runs bounded affine trials and reconstructs a painter-style layer composite.
All produced images are experimental; no source drawing is modified.
"""
import json,hashlib
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw
from p15_134_underpaint_probe import P,SOURCE,rgba,compose,background_rgb
from p15_143_native_bangs_review import PNG,META,sha
from p15_142_face_ownership import protect_mask
from p15_135_closed_hair_mask import closed_mask
ROOT=Path(__file__).resolve().parent.parent
OUT=P/'exports/p15-144-bangs-registration'
E=ROOT/'evidence/p15-144-bangs-registration-qa.json'
ROI=np.s_[88:290,230:400]
EYE=(316,218)
def eye_mask():
    y,x=np.indices((443,443))
    return ((x-EYE[0])/22.)**2+((y-EYE[1])/17.)**2<1
def native():
    d=json.loads(META.read_text())
    assert d['sha256']==sha(PNG) and d['tool']=='image_gen.imagegen'
    return np.asarray(Image.open(PNG).convert('RGBA').resize((443,443),Image.Resampling.LANCZOS)).copy()
def affine(image,scale,tx,ty):
    center=221.5
    mat=np.float32([[scale,0,center*(1-scale)+tx],[0,scale,center*(1-scale)+ty]])
    return cv2.warpAffine(image,mat,(443,443),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
def soft_mask(binary,kernel=5):
    return cv2.GaussianBlur((binary.astype(np.float32)),(0,0),kernel)
def alpha_gate(image,source):
    alpha=image[...,3]>128
    outside=alpha & (source[...,3]<=64)
    eye=alpha&eye_mask()
    return int(outside.sum()),int(eye.sum())
def old_bangs_mask(source):
    # Source-side hair and fringe envelope restricted to the forehead/right face.
    hair,_=closed_mask(source)
    yy,xx=np.indices((443,443))
    region=(xx>250)&(yy<305)&(yy>63)
    face=protect_mask(112.5,strength=1.15)
    # Strong anatomical face ownership, regardless of pigment color.
    return hair&region&~face
def compose_variant(source,under,generated,mask,feather=3):
    # Source layer is explicitly erased only where the authored front hair was
    # previously visible. Underpaint remains stationary.
    # Alpha blend soft edge for mask separation without cloning face pixels.
    loss=soft_mask(mask,feather)
    base=source.astype(np.float32)/255
    base[...,3]*=(1-loss)
    base[...,:3]*=(1-loss[...,None])
    body=np.uint8(np.clip(np.round(base*255),0,255))
    return compose(compose(under,body),generated)
def evaluate(save=True):
    source=rgba(SOURCE)
    under=rgba(P/'exports/p15-137-occlusion-regions/eye_08-underpaint.png')
    new=native()
    guard=eye_mask()
    original_mask=old_bangs_mask(source)
    # Probe registrations in a bounded scale and translation window.
    trials=[]
    for scale in (0.80,0.86,0.92,0.98,1.04):
      for tx in (-32,-24,-16,-8,0,8):
       for ty in (-22,-12,-2,8,18):
        moved=affine(new,scale,tx,ty)
        outside,eye=alpha_gate(moved,source)
        alpha=moved[...,3]>128
        intersection=(alpha&original_mask).sum()
        union=(alpha|original_mask).sum()
        iou=intersection/max(1,union)
        # Preserve source silhouette and eye; do not favor tiny hair purely
        # because it falls within bounds.
        score=iou - .9*outside/max(1,int(alpha.sum())) - 1.25*eye/max(1,int(guard.sum()))
        trials.append((float(score),float(iou),scale,tx,ty,outside,eye))
    score,iou,scale,tx,ty,outside,eye=max(trials,key=lambda t:t[0])
    registered=affine(new,scale,tx,ty)
    # Protect the original eye region from new hair in this test only.
    alpha=np.clip(1-soft_mask(guard,2),0,1)
    guarded=registered.copy()
    guarded[...,3]=np.uint8(np.round(guarded[...,3].astype(np.float32)*alpha))
    guarded[guarded[...,3]==0]=0
    # Alternative source-only composite with no extra eye protection.
    direct=compose_variant(source,under,registered,original_mask)
    protected=compose_variant(source,under,guarded,original_mask)
    direct_over=compose(source,new)
    outputs={'original':source,'direct_overlay':direct_over,'registered_unprotected':direct,'registered_eye_owned':protected}
    metrics={}
    region=np.s_[155:305,245:395]
    for name,img in outputs.items():
        alpha_holes=(source[...,3]>160)&(img[...,3]<64)
        local_difference=np.abs(background_rgb(img)[region]-background_rgb(source)[region])
        metrics[name]={'facePatchRGBMAE':round(float(local_difference.mean()),4),
                       'alphaHolesOverOriginal':int(alpha_holes.sum()),
                       'eyePatchRGBMAE':round(float(np.abs(background_rgb(img)[guard]-background_rgb(source)[guard]).mean()),4)}
    # Do not count source keyframe image as pixel-exact after composite replacement.
    result={'schema':'KOMA_P15_144_BANGS_SPATIAL_REGISTRATION_V1','characterId':'p0_character_001',
      'sourceYaw':112.5,'nativeAssetSHA256':sha(PNG),'nativeGeneratedArtUnmodified':True,
      'registeredScale':scale,'registeredTranslationXY':[tx,ty],
      'sourceBangsCandidatePixels':int(original_mask.sum()),
      'registeredMaskIoU':round(float(iou),5),
      'registeredOffSilhouettePixels':int(outside),'registeredEyeOpaquePixels':int(eye),
      'afterEyeOwnerOpaquePixels':int(((guarded[...,3]>128)&guard).sum()),
      'methods':metrics,'eyeIsSourceOwned':True,
      'sourcePixelIdentityRetainedInUnmodifiedRegions':True,
      'sourceKeyframePixelExactAfterRegistration':False,
      'underpaintSourcePhysicalRegistrationApproved':False,'artisticBangsIdentityApproved':False,
      'fullYawVisualAccepted':False,
      'review':'private-assets/exports/p15-144-bangs-registration/index.html',
      'next':'Inspect the registered hairline and face source ownership. If acceptable, evaluate displacement and 90–135 yaw; otherwise revise independent painted front-hair source.'}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        Image.fromarray(registered,'RGBA').save(OUT/'registered-bangs.png')
        Image.fromarray(guarded,'RGBA').save(OUT/'eye-owned-bangs.png')
        Image.fromarray(np.uint8(original_mask)*255,'L').save(OUT/'old-bangs-removal-mask.png')
        board=Image.new('RGB',(350*4,420),(35,41,52));draw=ImageDraw.Draw(board)
        for i,(name,img) in enumerate(outputs.items()):
            tile=Image.new('RGBA',(443,443),(49,61,78,255))
            tile.alpha_composite(Image.fromarray(img,'RGBA'))
            board.paste(tile.convert('RGB').resize((343,343),Image.Resampling.LANCZOS),(350*i,35))
            draw.text((350*i+6,8),name,fill='white')
            Image.fromarray(img,'RGBA').save(OUT/(name+'.png'))
        board.save(OUT/'comparison.jpg',quality=93)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 112.5 bangs registration</title><style>body{font:16px system-ui;background:#202833;color:#eee}img{max-width:100%}</style><h2>P0 independent bangs spatial registration</h2><p>Compare native overlay, registered hair replacement and eye-protected candidate. Registration optimizes silhouette and eye coverage, but artistic identity and yaw continuity require visual acceptance.</p><img src="comparison.jpg">')
        E.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result
if __name__=='__main__':
    q=evaluate()
    print(json.dumps({k:q[k] for k in ('registeredScale','registeredTranslationXY','registeredMaskIoU','registeredOffSilhouettePixels','registeredEyeOpaquePixels','afterEyeOwnerOpaquePixels','methods')},indent=2))

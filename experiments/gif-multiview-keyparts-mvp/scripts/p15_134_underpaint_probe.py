#!/usr/bin/env python3
"""Audit independent 112.5° occlusion-underpaint art in hair-displacement composition."""
import hashlib,json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent.parent
P=ROOT/'private-assets';GEN=P/'p15-134-occlusion-underpaint'
OUT=P/'exports/p15-134-underpaint-review';E=ROOT/'evidence/p15-134-underpaint-qa.json'
SOURCE=P/'exports/p15-128-keyart-registration/yaw112p5-registration-candidate.png'
HAIR=P/'exports/p15-133-semantic-source/yaw112p5/hair.visible.png'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rgba(path):
    with Image.open(path) as im:return np.asarray(im.convert('RGBA')).copy()
def transform(x,scale=.97,dx=12,dy=12):
    h,w=x.shape[:2]
    matrix=np.float32([[scale,0,(1-scale)*w/2+dx],[0,scale,(1-scale)*h/2+dy]])
    return cv2.warpAffine(x,matrix,(w,h),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
def compose(bg,fg):
    dst=Image.fromarray(bg,'RGBA');dst.alpha_composite(Image.fromarray(fg,'RGBA'));return np.asarray(dst).copy()
def move(arr,dx,dy):
    return cv2.warpAffine(arr,np.float32([[1,0,dx],[0,1,dy]]),(arr.shape[1],arr.shape[0]),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
def background_rgb(x):
    al=x[...,3:4].astype(np.float32)/255
    return x[...,:3].astype(np.float32)*al+(1-al)*np.array([49,61,78])
def assess(save=True):
    info=json.loads((GEN/'generation-result.json').read_text())
    native=GEN/'underpaint-native.png'
    assert info['tool']=='image_gen.imagegen' and info['actual_image_tool_used']
    assert sha(native)==info['SHA256']
    with Image.open(native) as im:assert im.mode=='RGBA' and im.size==(1254,1254)
    source=rgba(SOURCE);hair=rgba(HAIR)
    under=np.asarray(Image.open(native).convert('RGBA').resize((443,443),Image.Resampling.LANCZOS)).copy()
    aligned=transform(under)
    assert source.shape==hair.shape==aligned.shape==(443,443,4)
    cut=hair[...,3]>0
    remainder=source.copy();remainder[cut]=0
    # Part extraction was source-exact because hair and remainder never share a pixel.
    reconstruction=remainder.copy();reconstruction[cut]=hair[cut]
    exact=bool(np.array_equal(reconstruction,source));assert exact
    demos={}
    for dx in (0,12,24):
        displaced=move(hair,dx,0)
        demos[f'hair_shift_{dx:02d}']=compose(compose(aligned,remainder),displaced)
    roi=np.s_[335:435,80:375]
    opaque_source=(source[roi][...,3]>128)
    opaque_under=(aligned[roi][...,3]>128)
    iou=float((opaque_source&opaque_under).sum()/max(1,(opaque_source|opaque_under).sum()))
    mae=float(np.abs(background_rgb(source)[roi]-background_rgb(aligned)[roi]).mean())
    shifts={}
    for dx in (0,12,24):
        composed=demos[f'hair_shift_{dx:02d}']
        shiftroi=np.s_[130:335,125:390]
        shifts[str(dx)]={'compositeDifferenceAgainstOriginalRGBMAE':round(float(np.abs(background_rgb(composed)[shiftroi]-background_rgb(source)[shiftroi]).mean()),4),
                         'newVisibleAlphaPixelsOutsideOriginal':int(((composed[...,3]>16)&(source[...,3]<=16)).sum())}
    result={'schema':'KOMA_P15_134_NATIVE_OCCLUSION_UNDERPAINT_V1','characterId':'p0_character_001','requestedYaw':112.5,
       'tool':info['tool'],'nativeUnderpaintSHA256':info['SHA256'],'nativeDimensions':[1254,1254],
       'sourceSHA256':sha(SOURCE),'hairCandidateSHA256':sha(HAIR),
       'nativeRGBAProven':True,'sourceAndHairPixelReconstructionExact':exact,
       'underpaintRegistration':{'scale':.97,'translationXY':[12,12],'method':'reuse P15-128 generated source transform; no physical-anchor optimization',
           'jacketROI':[80,335,375,435],'jacketAlphaIoU':round(iou,5),'jacketCompositeRGBMAE':round(mae,4)},
       'displacementStress':shifts,'underpaintClass':'independently model-generated painted scalp, ear, cheek, neck and jacket behind front hair',
       'hairLayerClass':'P15-133 approximate visible-pigment mask',
       'paintedHiddenScalpPresent':True,'artistApprovedGeometry':False,'occlusionEdgeRegistrationAccepted':False,
       'physicalCorrespondenceValidated':False,'fullRotationVisualAccepted':False,
       'review':'private-assets/exports/p15-134-underpaint-review/index.html',
       'next':'Correct scalp/ear/face/collar underpaint geometry and replace P15-133 hair-pigment mask with source-authored closed ArtMesh silhouette. Validate recovered hidden region under hair displacement.'}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        Image.fromarray(aligned,'RGBA').save(OUT/'underpaint-aligned-candidate.png')
        for name,img in demos.items():Image.fromarray(img,'RGBA').save(OUT/(name+'.png'))
        board=Image.new('RGB',(340*5,420),(34,41,52));draw=ImageDraw.Draw(board)
        for i,(label,img) in enumerate([('source 112.5',source),('underpaint',aligned),('reveal 0px',demos['hair_shift_00']),('reveal 12px',demos['hair_shift_12']),('reveal 24px',demos['hair_shift_24'])]):
            tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(img,'RGBA'))
            board.paste(tile.convert('RGB').resize((333,333),Image.Resampling.LANCZOS),(i*340,38))
            draw.text((i*340+9,11),label,fill='white')
        board.save(OUT/'contact.jpg',quality=94)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 source occlusion underpaint</title><style>body{font:16px system-ui;background:#202733;color:#eee}img{max-width:100%}</style><h2>112.5° independent scalp/ear/neck underpaint</h2><p>Original reference, aligned generated short-hair scalp underlayer, and 0/12/24px hair-displacement stress tests. Source layer is pigment-extracted and not a verified ArtMesh silhouette. Registration and visual acceptance must be checked separately.</p><img src="contact.jpg">')
        E.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result
if __name__=='__main__':
    d=assess();print(json.dumps({'sourceExact':d['sourceAndHairPixelReconstructionExact'],'jacketIoU':d['underpaintRegistration']['jacketAlphaIoU'],'jacketMAE':d['underpaintRegistration']['jacketCompositeRGBMAE'],'stress':d['displacementStress']},indent=2))

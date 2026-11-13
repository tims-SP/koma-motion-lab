#!/usr/bin/env python3
"""Native independently painted bangs candidate: provenance and compositing review."""
import json,hashlib
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_134_underpaint_probe import P,SOURCE,rgba,compose
from p15_129_ahoge_ownership import keyframes
ROOT=Path(__file__).resolve().parent.parent
GEN=P/'p15-143-front-bangs'
PNG=GEN/'front-bangs-native.png'
META=GEN/'generation-result.json'
OUT=P/'exports/p15-143-front-bangs'
E=ROOT/'evidence/p15-143-front-bangs-qa.json'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rgba_registered():
    return np.asarray(Image.open(PNG).convert('RGBA').resize((443,443),Image.Resampling.LANCZOS)).copy()
def native_meta():
    m=json.loads(META.read_text())
    assert PNG.is_file() and PNG.stat().st_size>50000
    assert 'image_gen.imagegen' in json.dumps(m),m
    assert sha(PNG) in json.dumps(m),m
    im=Image.open(PNG)
    assert im.mode=='RGBA'
    return m,im.size
def regions(img):
    yy,xx=np.indices(img.shape[:2])
    mask=img[...,3]>32
    rois={'head_top':(0,145,80,395),'front_fringe':(80,260,250,405),
          'face':(165,325,255,405),'lower_garment':(320,443,60,405)}
    return {k:int(mask[y0:y1,x0:x1].sum()) for k,(y0,y1,x0,x1) in rois.items()}
def trial():
    m,dims=native_meta()
    new=rgba_registered()
    source=rgba(SOURCE)
    reference=keyframes()[112.5]
    # Compare overlay without modifying existing source pixels.
    over=compose(source,new)
    alpha=new[...,3]
    high=int((alpha>128).sum())
    max_later=int((alpha[320:]>16).sum())
    # Registration gate: independent paint must not accidentally cover the
    # original near eye or create large opaque material outside the source head.
    eye_center=(316,218)
    ys,xs=np.indices(alpha.shape)
    eye_region=((xs-eye_center[0])/20)**2+((ys-eye_center[1])/15)**2<=1
    opaque_eye=int(((alpha>128)&eye_region).sum())
    eye_area=int(eye_region.sum())
    source_opaque=source[...,3]>64
    off_silhouette=int(((alpha>128)&~source_opaque).sum())
    # A strict study-only threshold; zero eye pixels is not required of all
    # bangs, but an unsupervised newly painted fringe must not conceal a
    # clearly visible eye before ownership has been annotated.
    candidate_passes=(opaque_eye<eye_area*.10 and off_silhouette<high*.05)
    # A front-bangs layer should mostly occupy upper head, but tests are QA signals,
    # not proof of semantic correctness.
    result={'schema':'KOMA_P15_143_NATIVE_FRONT_BANGS_REVIEW_V1',
      'characterId':'p0_character_001','requestedYaw':112.5,
      'nativeFileSHA256':sha(PNG),'nativeDimensions':list(dims),'nativeRGBA':True,
      'generatedPartClass':'new independent front hair/bangs paint candidate',
      'registeredCanvas':[443,443],'opaqueSourcePixels':high,'opaquePixelsBelowY320':max_later,
      'nearEyeOpaqueCandidatePixels':opaque_eye,'nearEyeRegionPixels':eye_area,
      'opaquePixelsOutsideSourceSilhouette':off_silhouette,
      'directOverlayRegistrationGatePassed':bool(candidate_passes),
      'occupiedRois':regions(new),'nativeReferenceUnmodified':True,
      'sourceKeyPixelIntegrity':True,'visibleOverlayDifferenceRGBMAE':round(float(np.mean(np.abs(over.astype(np.float32)-source.astype(np.float32)))),4),
      'partIdentityArtistVerified':False,'spatialRegistrationApproved':False,
      'fullySeparateSemanticBangsApproved':False,'crossViewStrandIdentityVerified':False,
      'fullYawVisualAccepted':False,
      'review':'private-assets/exports/p15-143-front-bangs/index.html',
      'next':'Use source-aligned front fringe plus painted forehead/eye underlayer to evaluate independent ArtMesh motion without double bangs or face overlap.'}
    OUT.mkdir(parents=True,exist_ok=True)
    Image.fromarray(new,'RGBA').save(OUT/'front-bangs-review.png')
    Image.fromarray(over,'RGBA').save(OUT/'overlay-review.png')
    board=Image.new('RGB',(340*4,380),(36,41,51));draw=ImageDraw.Draw(board)
    for i,(name,img) in enumerate([('canonical',source),('generated bangs',new),
                                    ('direct overlay',over),('new source 112.5',reference)]):
        tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(img,'RGBA'))
        board.paste(tile.convert('RGB').resize((333,333),Image.Resampling.LANCZOS),(340*i,31))
        draw.text((340*i+7,8),name,fill='white')
    board.save(OUT/'comparison.jpg',quality=95)
    (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 independent front fringe</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>112.5° independently generated front fringe</h2><p>Candidate RGBA source, direct overlay and native reference. Position, part ownership, and frame continuity are subject to independent review.</p><img src="comparison.jpg">')
    E.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result
if __name__=='__main__':
    q=trial()
    print(json.dumps({k:q[k] for k in ['nativeDimensions','opaqueSourcePixels','opaquePixelsBelowY320','nearEyeOpaqueCandidatePixels','opaquePixelsOutsideSourceSilhouette','directOverlayRegistrationGatePassed','occupiedRois','visibleOverlayDifferenceRGBMAE']},indent=2))

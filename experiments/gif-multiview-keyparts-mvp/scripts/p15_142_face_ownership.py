#!/usr/bin/env python3
"""Protect near-eye and ear source pixels from cross-view hair mesh deformation.

Per-view source pixels remain losslessly partitioned. The proximity masks are
explicit image-space proposals, not painter-approved anatomical layer art.
"""
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw
from p15_140_contour_yaw_mesh import contour_mesh,interpolate_mesh,choose_owner,load_roles
from p15_139_hair_artmesh import warp_triangles,area
from p15_131_semantic_landmarks import POINTS
from p15_129_ahoge_ownership import ANGLES,KEYS
from p15_128_keyart_registration import jumps
from p15_134_underpaint_probe import P,rgba,compose
ROOT=Path(__file__).resolve().parent.parent
OUT=P/'exports/p15-142-face-ownership'
E=ROOT/'evidence/p15-142-face-ownership-qa.json'
ROLES=('eye.near.center','ear.center','nose.tip','chin')

def protect_mask(angle,shape=(443,443),strength=1):
    yy,xx=np.indices(shape)
    mask=np.zeros(shape,dtype=bool)
    sizes={'eye.near.center':(29,20),'ear.center':(20,29),'nose.tip':(15,18),'chin':(18,13)}
    for role in ROLES:
        xy=POINTS[role].get(f'{angle:g}')
        if xy is None:continue
        rx,ry=sizes[role];rx*=strength;ry*=strength
        mask|=((xx-xy[0])/rx)**2+((yy-xy[1])/ry)**2<=1
    return mask

def separate(angle,part_mask_strength):
    source,hair,rest,mask=load_roles(angle)
    protected=protect_mask(angle,strength=part_mask_strength)
    ownership=mask&~protected
    foreground=source.copy();foreground[~ownership]=0
    body=source.copy();body[ownership]=0
    rebuild=body.copy();rebuild[ownership]=foreground[ownership]
    assert np.array_equal(rebuild,source)
    return source,foreground,body,ownership,protected

def run(save=True):
    baseline={a:load_roles(a) for a in KEYS}
    source_mesh={a:contour_mesh(baseline[a][3]) for a in KEYS}
    faces=source_mesh[90.][1]
    geometry={a:source_mesh[a][0] for a in KEYS}
    baseline_frames=[rgba(P/'exports/p15-140-contour-yaw-mesh'/(f'yaw{a:06.2f}'.replace('.','p')+'.png')) for a in ANGLES]
    candidates={}
    for name,strength in [('face_guard_075',.75),('face_guard_100',1),('face_guard_125',1.25)]:
        sources={a:separate(a,strength) for a in KEYS}
        rendered=[];frame_meta=[]
        for angle in ANGLES:
            if angle in KEYS:
                arr=sources[angle][0].copy();owner=angle
            else:
                a,b=(90.,112.5) if angle<112.5 else (112.5,135.)
                t=(angle-a)/(b-a)
                owner=choose_owner(a,b,t)
                target=interpolate_mesh(geometry,a,b,t)
                moved=warp_triangles(sources[owner][1],geometry[owner],target,faces)
                arr=compose(sources[owner][2],moved)
            rendered.append(arr)
            frame_meta.append({'yaw':angle,'owner':owner})
        candidates[name]={'frames':rendered,'source':sources,'owners':frame_meta}
    qa={'schema':'KOMA_P15_142_FACE_HAIR_PIXEL_OWNERSHIP_V1','characterId':'p0_character_001',
        'angles':list(ANGLES),'sourceAngles':list(KEYS),'protectedRoles':list(ROLES),
        'referenceMaxAdjacentRGBMAE':max(jumps(baseline_frames)),
        'variants':{},'sourceReconstructionExact':True,'originalSourceUnmodified':True,
        'sourceRoleStatus':'image-space feature protection proposals; eye/ear/face extraction not artist-approved',
        'physicalSourceCorrespondenceValidated':False,'hiddenSurfaceRegistrationValidated':False,
        'visualAccepted':False,'review':'private-assets/exports/p15-142-face-ownership/index.html',
        'next':'Validate feature owner boundaries against true source-painted eye/ear/face layer artwork, then register hair strand identities and view-specific underpaint.'}
    for name,d in candidates.items():
        js=jumps(d['frames'])
        removed={str(a):int((baseline[a][3]&~d['source'][a][3]).sum()) for a in KEYS}
        qa['variants'][name]={'maxAdjacentRGBMAE':max(js),'adjacentRGBMAE':js,
           'reassignedFacePixelsByYaw':removed,
           'nativeKeyframesPixelExact':all(np.array_equal(d['frames'][ANGLES.index(a)],d['source'][a][0]) for a in KEYS)}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(310*5,350*4),(36,42,53));draw=ImageDraw.Draw(board)
        for row,(name,images) in enumerate([('P15-140',baseline_frames)]+[(name,d['frames']) for name,d in candidates.items()]):
            for i,(angle,arr) in enumerate(zip(ANGLES,images)):
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(arr,'RGBA'))
                board.paste(tile.convert('RGB').resize((305,305),Image.Resampling.LANCZOS),(310*i,row*350+30))
                draw.text((310*i+6,row*350+7),f'{name} / {angle:g}',fill='white')
                if row>0:Image.fromarray(arr,'RGBA').save(OUT/(name+'-'+f'yaw{angle:06.2f}'.replace('.','p')+'.png'))
        board.save(OUT/'comparison.jpg',quality=94)
        maskboard=Image.new('RGB',(443*3,510),(35,42,52));mark=ImageDraw.Draw(maskboard)
        for i,a in enumerate(KEYS):
            source,*_=candidates['face_guard_100']['source'][a]
            tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(source,'RGBA'))
            mask=protect_mask(a)
            shade=np.zeros((443,443,4),dtype=np.uint8);shade[mask]=[0,235,235,120]
            tile.alpha_composite(Image.fromarray(shade,'RGBA'))
            maskboard.paste(tile.convert('RGB'),(i*443,29))
            mark.text((i*443+6,7),f'{a:g} source face/ear protection',fill='white')
        maskboard.save(OUT/'face-ownership-masks.jpg',quality=93)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 hair/face source pixel ownership</title><style>body{background:#202733;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>90–135° hair ArtMesh with face/ear pixel ownership</h2><p>Top: P15-140. Rows: three local face protection radii. Native keyframes are pixel exact; protected face pixels are attached to the source owner body and do not yet have a physical cross-yaw transform.</p><img src="comparison.jpg"><h3>Owner masks</h3><img src="face-ownership-masks.jpg">')
        E.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    return qa
if __name__=='__main__':
    q=run()
    print(json.dumps({'baseline':q['referenceMaxAdjacentRGBMAE'],'variants':q['variants']},indent=2))

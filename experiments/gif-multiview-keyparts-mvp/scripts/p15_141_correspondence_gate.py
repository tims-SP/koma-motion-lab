#!/usr/bin/env python3
"""Raster evidence gate for hair material correspondence across native keyviews.

The gate compares directionally deformed artwork and provisional semantic
landmarks; it deliberately does not label optical similarity as physical
strand identity.
"""
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
from p15_140_contour_yaw_mesh import load_roles,contour_mesh
from p15_139_hair_artmesh import warp_triangles
from p15_131_semantic_landmarks import POINTS
from p15_129_ahoge_ownership import KEYS
from p15_134_underpaint_probe import P,background_rgb
ROOT=Path(__file__).resolve().parent.parent
OUT=P/'exports/p15-141-correspondence-gate'
EVIDENCE=ROOT/'evidence/p15-141-correspondence-gate-qa.json'
PAIRS=((90.,112.5),(112.5,135.))
PATCH_ROIS={
 'ahoge_crown':(0,135,125,395),
 'rear_hair':(100,325,55,260),
 'face_ear':(160,335,205,400),
 'lower_hair_boundary':(275,345,95,365),
}
def edge_ink(image):
    # RGB gradients over a fixed background capture line work and cel shading.
    grey=cv2.cvtColor(np.uint8(np.clip(background_rgb(image),0,255)),cv2.COLOR_RGB2GRAY)
    grad=cv2.Canny(grey,70,160)
    # Exclude hard outer silhouette for internal strand matching.
    opaque=(image[...,3]>64).astype('uint8')
    interior=cv2.erode(opaque,np.ones((5,5),np.uint8),iterations=1)
    return ((grad>0)&(interior>0)).astype('uint8')
def f1(a,b):
    both=np.logical_and(a,b).sum()
    return round(float(2*both/max(1,a.sum()+b.sum())),5)
def patch_metrics(a,b,mask,roi):
    y0,y1,x0,x1=roi
    alpha_a=a[y0:y1,x0:x1,3]>64
    alpha_b=b[y0:y1,x0:x1,3]>64
    union=alpha_a|alpha_b
    overlap=alpha_a&alpha_b
    rgb_a=background_rgb(a)[y0:y1,x0:x1]
    rgb_b=background_rgb(b)[y0:y1,x0:x1]
    rgb_diff=np.abs(rgb_a-rgb_b).mean(axis=2)
    ea=edge_ink(a)[y0:y1,x0:x1].astype(bool)
    eb=edge_ink(b)[y0:y1,x0:x1].astype(bool)
    # Dilate only a couple pixels for tolerance to nearest ink stroke.
    ea_close=cv2.dilate(ea.astype('uint8'),np.ones((3,3),np.uint8))>0
    eb_close=cv2.dilate(eb.astype('uint8'),np.ones((3,3),np.uint8))>0
    matches=((ea&eb_close).sum()+(eb&ea_close).sum())
    line_score=round(float(matches/max(1,ea.sum()+eb.sum())),5)
    return {
      'alphaIoU':round(float(overlap.sum()/max(1,union.sum())),5),
      'rgbMAE':round(float(rgb_diff.mean()),4),
      'overlapRGBMAE':round(float(rgb_diff[overlap].mean()) if overlap.any() else 0.,4),
      'edgeAgreement3px':line_score,
      'foregroundXorPixels':int(np.logical_xor(alpha_a,alpha_b).sum()),
      'regionPixels':int((y1-y0)*(x1-x0))
    }
def audit(save=True):
    roles={angle:load_roles(angle) for angle in KEYS}
    meshes={angle:contour_mesh(roles[angle][3]) for angle in KEYS}
    faces=meshes[90.][1]
    q={'schema':'KOMA_P15_141_MATERIAL_CORRESPONDENCE_GATE_V1',
       'characterId':'p0_character_001','referenceAngles':list(KEYS),
       'keyPairs':[list(pair) for pair in PAIRS],
       'method':'warp each source hair texture onto the adjacent keyview contour mesh; compare alpha, color, and interior line strokes',
       'comparisonRois':{k:list(v) for k,v in PATCH_ROIS.items()},
       'pairs':{},
       'artistVerifiedStrandIdentity':False,'physical3DAnchorCorrespondenceVerified':False,
       'perViewUnderpaintComplete':False,'productionVDDApproved':False,
       'sourceArtClassification':'provisional appearance masks; some eye and face ink is included in the hair source',
       'gateRGBThreshold':15.0,
       'next':'Replace source-view hair masks with matched strand layers. Draw/approve actual root-tip-corresponding parts and ear/face/neck underpaint before shared mesh production.'}
    pairboards=[]
    for start,end in PAIRS:
        original_a,paint_a,_,_=roles[start]
        original_b,paint_b,_,_=roles[end]
        source_positions=meshes[start][0];target_positions=meshes[end][0]
        displaced=warp_triangles(paint_a,source_positions,target_positions,faces)
        reverse=warp_triangles(paint_b,target_positions,source_positions,faces)
        # Compare hair-only samples; source donor and true target mask are independent.
        scores={'forward':{},'reverse':{}}
        for name,roi in PATCH_ROIS.items():
            scores['forward'][name]=patch_metrics(displaced,paint_b,None,roi)
            scores['reverse'][name]=patch_metrics(reverse,paint_a,None,roi)
        landmark_notes={}
        for landmark,entry in POINTS.items():
            x0=entry.get(f'{start:g}')
            x1=entry.get(f'{end:g}')
            if x0 is None or x1 is None: continue
            delta=np.array(x1,dtype=np.float32)-np.array(x0,dtype=np.float32)
            landmark_notes[landmark]={'deltaXY':delta.tolist(),'distancePx':round(float(np.linalg.norm(delta)),3)}
        q['pairs'][f'{start:g}-{end:g}']={
           'directionalHairAgreement':scores,
           'landmarkProposals':landmark_notes,
           'hasValidatedPhysicalStrandLabels':False}
        pairboards.append((start,end,paint_a,displaced,paint_b,reverse))
    ranked=sorted([(v['rgbMAE'],pair,part) for pair,values in q['pairs'].items()
             for part,v in values['directionalHairAgreement']['forward'].items()],reverse=True)
    q['rankedVisibleDisagreements']=[{'pair':pair,'region':name,'rgbMAE':mae} for mae,pair,name in ranked]
    q['gateResults']={
        'sourceVisibilityAndIdentityGatePassed':all(row['rgbMAE']<=q['gateRGBThreshold'] for row in q['rankedVisibleDisagreements']),
        'regionsOverThreshold':[row for row in q['rankedVisibleDisagreements'] if row['rgbMAE']>q['gateRGBThreshold']],
        'interpretation':'Image-space forward texture disagreement threshold is a candidate selection check, not physical identity proof.'
    }
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        panel=Image.new('RGB',(315*4,355*len(pairboards)),(35,42,54));d=ImageDraw.Draw(panel)
        for row,(start,end,a,fwd,b,rev) in enumerate(pairboards):
            for col,(tag,img) in enumerate((
                (f'source {start:g}',a),(f'{start:g} → {end:g}',fwd),
                (f'target {end:g}',b),(f'{end:g} → {start:g}',rev))):
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(img,'RGBA'))
                panel.paste(tile.convert('RGB').resize((310,310),Image.Resampling.LANCZOS),(315*col,row*355+30))
                d.text((315*col+6,row*355+7),tag,fill='white')
            Image.fromarray(fwd,'RGBA').save(OUT/f'yaw{start:g}-to-{end:g}.png')
            Image.fromarray(rev,'RGBA').save(OUT/f'yaw{end:g}-to-{start:g}.png')
        panel.save(OUT/'source-material-correspondence.jpg',quality=93)
        # Independent QA panel with per-region scores.
        def region_score(pair,name):
            return q['pairs'][pair]['directionalHairAgreement']['forward'][name]
        q['review']='private-assets/exports/p15-141-correspondence-gate/index.html'
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 keyview material correspondence</title><style>body{background:#202832;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>P0 90° / 112.5° / 135° head material audit</h2><p>Observed forward/reverse hair deformation versus actual source paint. This is an image-space diagnostic. No physical strand correspondence has been verified.</p><img src="source-material-correspondence.jpg"><pre>'+json.dumps(q['rankedVisibleDisagreements'],indent=2)+'</pre>')
        EVIDENCE.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':
    q=audit()
    print(json.dumps({'ranked':q.get('rankedVisibleDisagreements'),'forward':{p:{k:v['rgbMAE'] for k,v in x['directionalHairAgreement']['forward'].items()} for p,x in q['pairs'].items()}},indent=2))

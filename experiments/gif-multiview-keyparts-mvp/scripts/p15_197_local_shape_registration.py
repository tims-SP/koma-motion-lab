#!/usr/bin/env python3
"""P15-197 native-view pose/shape separation by landmark registration.

Measure which portion of 112.5-degree source hair geometry can be explained
by translation, rigid, similarity and affine registration to 90/135 source
landmarks and full source-owned alpha masks. Source-key pixels are
immutable. A hold-out landmark and raster mask IoU prevent overfit.
"""
import json,hashlib
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw
from p15_129_ahoge_ownership import keyframes,KEYS
from p15_187_full_skeleton_vdd import source_geometry
from p15_196_descending_shoulder_identity import semantic_indices
from p15_167_endpoint_pair import pair
from p15_134_underpaint_probe import P
ROOT=Path(__file__).resolve().parents[1]
OUT=P/'exports/p15-197-local-shape-registration'
E=ROOT/'evidence/p15-197-local-shape-registration-qa.json'
PAIRS=((90.,112.5),(135.,112.5),(90.,135.))
METHODS=('translation','rigid','similarity','affine')
H=W=443

def transforms(moving,reference):
    a=np.asarray(moving,np.float64);b=np.asarray(reference,np.float64)
    # Fit first four features, then evaluate the held-out free tip.
    x=a[:4];y=b[:4]
    ta=y.mean(0)-x.mean(0)
    result={'translation':np.array([[1,0,ta[0]],[0,1,ta[1]]],np.float64)}
    cx=x.mean(0);cy=y.mean(0)
    xx=x-cx;yy=y-cy
    u,_,vt=np.linalg.svd(xx.T@yy)
    fix=np.eye(2)
    if np.linalg.det(u@vt)<0:fix[-1,-1]=-1
    rotation=u@fix@vt
    # Row-vector map is x @ rotation + shift.
    def mat(scale):
        linear=rotation*scale
        shift=cy-cx@linear
        return np.c_[linear.T,shift]
    result['rigid']=mat(1)
    scale=float(np.sum((xx@rotation)*yy)/max(np.sum(xx**2),1e-9))
    result['similarity']=mat(scale)
    augmented=np.c_[x,np.ones(len(x))]
    coef=np.linalg.lstsq(augmented,y,rcond=None)[0]
    result['affine']=np.c_[coef[:2].T,coef[2]]
    return result

def apply(points,m):
    p=np.asarray(points,np.float64)
    return p@m[:,:2].T+m[:,2]

def mask_score(moving,target,matrix):
    warped=cv2.warpAffine(np.uint8(moving>0),matrix,(W,H),flags=cv2.INTER_NEAREST)
    truth=np.uint8(target>0)
    inter=int(((warped>0)&(truth>0)).sum())
    union=int(((warped>0)|(truth>0)).sum())
    return {'maskIoU':round(inter/max(union,1),5),
            'warpedArea':int(warped.sum()),'nativeTargetArea':int(truth.sum())}

def measure():
    frames=keyframes()
    geometries={a:source_geometry(frames[a],a) for a in KEYS}
    landmarks={};masks={}
    for a in KEYS:
        g=geometries[a]
        ids,score,window=semantic_indices(g)
        strand,_,_,status=pair(frames[a],a)
        assert status['originalPixelExact']
        masks[a]=np.uint8(strand[...,3]>24)
        landmarks[a]={'indices':ids.tolist(),
          'coordinates':g['curve'][ids].round(4).tolist(),
          'sourceHash':hashlib.sha256(frames[a].tobytes()).hexdigest(),
          'alphaArea':int(masks[a].sum()),
          'rootRelativeLandmarks':(g['curve'][ids]-g['curve'][ids][0]).round(4).tolist(),
          'rootToTipDistancePixels':round(float(np.linalg.norm(g['curve'][ids][-1]-g['curve'][ids][0])),4)}
    comparisons={}
    for a,b in PAIRS:
        moving=np.asarray(landmarks[a]['coordinates'],np.float64)
        target=np.asarray(landmarks[b]['coordinates'],np.float64)
        variants={}
        for name,m in transforms(moving,target).items():
            projected=apply(moving,m)
            residual=np.linalg.norm(projected-target,axis=1)
            det=float(np.linalg.det(m[:,:2]))
            singular=np.linalg.svd(m[:,:2])[1]
            variants[name]={
              'matrix':m.round(6).tolist(),
              'fitLandmarkRMS':round(float(np.sqrt(np.mean(residual[:4]**2))),4),
              'heldOutTipErrorPixels':round(float(residual[4]),4),
              'allFiveLandmarkRMS':round(float(np.sqrt(np.mean(residual**2))),4),
              'perLandmarkResidualPixels':residual.round(4).tolist(),
              'determinant':round(det,5),'axisScales':singular.round(5).tolist(),
              **mask_score(masks[a],masks[b],m)}
        comparisons[f'{a:g}->{b:g}']=variants
    q={'schema':'KOMA_P15_197_LOCAL_SHAPE_REGISTRATION_V1',
      'characterId':'p0_character_001','sourceAngles':list(KEYS),
      'method':'Register source-owned hair masks and five semantic landmarks using translation, rigid, similarity and affine models. Fit root, entry shoulder, arc apex, descending shoulder; hold out free tip and evaluate full-mask IoU.',
      'landmarkNames':['root','entry_shoulder','outer_apex','descending_shoulder','heldout_free_tip'],
      'source':landmarks,'comparisons':comparisons,
      'sourceAssetsModified':False,'productionRendererUpdated':False,'visualAccepted':False,
      'review':'private-assets/exports/p15-197-local-shape-registration/index.html'}
    q['gate']={
      'threeNativeMasksFingerprinted':all(len(v['sourceHash'])==64 for v in landmarks.values()),
      'allPositiveTransformDeterminants':all(v['determinant']>0 for cases in comparisons.values() for v in cases.values()),
      'affineExplainsMiddleViewShape':all(comparisons[k]['affine']['maskIoU']>=.75 and comparisons[k]['affine']['heldOutTipErrorPixels']<=5 for k in ('90->112.5','135->112.5')),
      'sourceSemanticIdentityApproved':False,
      'productionApproved':False,'passes':False}
    return q,frames,geometries,masks

def save():
    q,frames,geometries,masks=measure()
    OUT.mkdir(parents=True,exist_ok=True)
    board=Image.new('RGB',(480*2,300*len(PAIRS)),(37,44,57))
    draw=ImageDraw.Draw(board)
    for row,(a,b) in enumerate(PAIRS):
        original=masks[a];target=masks[b]
        for col,(method,v) in enumerate(q['comparisons'][f'{a:g}->{b:g}'].items()):
            mat=np.asarray(v['matrix'],np.float32)
            warp=cv2.warpAffine(original,mat,(W,H),flags=cv2.INTER_NEAREST)
            crop=(130,0,370,130)
            side=np.zeros((H,W,3),np.uint8)
            side[...,0]=target*235;side[...,1]=warp*205
            tile=Image.fromarray(side,'RGB').crop(crop).resize((470,235),Image.Resampling.NEAREST)
            # First two models at top row, latter at bottom, one row per pair.
            x=(col%2)*480;y=row*300+(col//2)*120
            # Separate rows for compact 2x2 model comparison.
            # Render full model panels to individual images as well.
            Image.fromarray(side,'RGB').crop(crop).resize((720,390),Image.Resampling.NEAREST).save(
                OUT/(f'{a:g}-to-{b:g}-{method}.png'))
    # A summary strip for the pair most relevant to 112.5°.
    summary=Image.new('RGB',(460*4,340*2),(37,44,57))
    pen=ImageDraw.Draw(summary)
    for row,a in enumerate((90.,135.)):
        b=112.5
        for col,method in enumerate(METHODS):
            v=q['comparisons'][f'{a:g}->{b:g}'][method]
            m=np.asarray(v['matrix'],np.float32)
            warped=cv2.warpAffine(masks[a],m,(W,H),flags=cv2.INTER_NEAREST)
            overlap=np.zeros((H,W,3),np.uint8)
            overlap[...,0]=masks[b]*235
            overlap[...,1]=warped*220
            img=Image.fromarray(overlap,'RGB').crop((120,0,380,140)).resize((446,294),Image.Resampling.NEAREST)
            summary.paste(img,(460*col,340*row+36))
            pen.text((460*col+4,340*row+4),f'{a:g} to 112.5 {method} IoU={v["maskIoU"]:.3f} tip={v["heldOutTipErrorPixels"]:.1f}',fill='white')
    summary.save(OUT/'registration-comparison.jpg',quality=96)
    (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P15-197 view registration</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Three native source views: pose versus shape</h2><p>Red is native target alpha, green is the aligned moving view; yellow overlap. Free tip is held out of fitting. Masks are original source-owned ahoge layers.</p><img src="registration-comparison.jpg">')
    E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':
    q=save()
    print(json.dumps({'comparisons':{k:{m:{'maskIoU':v['maskIoU'],'tip':v['heldOutTipErrorPixels'],'fit':v['fitLandmarkRMS']} for m,v in c.items()} for k,c in q['comparisons'].items()},'gate':q['gate']},indent=2))

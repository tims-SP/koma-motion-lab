#!/usr/bin/env python3
"""Align generated P0 mid-yaw painting to the neighboring source silhouettes, keeping native pixels untouched."""
import json,hashlib,sys
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from p15_127_keyview_transition import B, key, face_skin_count
from p15_121_rear_arc_render import load
from flow_render import get_flow,morph
P=ROOT/'private-assets';OUT=P/'exports/p15-128-keyart-registration';E=ROOT/'evidence/p15-128-keyart-registration-qa.json'
SAMPLES=(90.,101.25,112.5,123.75,135.)
def mask(img):return np.uint8(img[...,3]>128)
def sd(m):
    inner=cv2.distanceTransform(m,cv2.DIST_L2,3)
    outer=cv2.distanceTransform(1-m,cv2.DIST_L2,3)
    return inner-outer

def target_mask(a,b):
    # Target is a signed-distance midpoint estimate between the two source silhouettes,
    # not a physical mid-yaw 3D projection.
    return np.uint8((sd(mask(a))+sd(mask(b)))>=0)

def transform(src,scale,tx,ty):
    h,w=src.shape[:2]
    matrix=np.float32([[scale,0,(1-scale)*w/2+tx],[0,scale,(1-scale)*h/2+ty]])
    return cv2.warpAffine(src,matrix,(w,h),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)

def iou(a,b):
    a=a.astype(bool);b=b.astype(bool)
    return float(np.count_nonzero(a&b)/max(1,np.count_nonzero(a|b)))

def optimize(reference,paint):
    # This bounded search can only correct registration, not facial pose or art style.
    native=mask(paint);target=reference
    scores=[]
    for scale in (0.94,0.97,1.,1.03,1.06):
        for tx in (-12,-6,0,6,12):
            for ty in (-12,-6,0,6,12):
                registered=transform(native,scale,tx,ty)
                score=iou(registered,target)
                scores.append((score,scale,tx,ty))
    return max(scores,key=lambda a:(a[0],-abs(a[1]-1),-abs(a[2]),-abs(a[3])))

def frame_interp(start,mid,end):
    frames=[];h,w=start.shape[:2];y,x=np.indices((h,w),dtype=np.float32);grid=np.stack((x,y),axis=-1)
    flows={(90.,112.5):get_flow(start,mid,'dis'),(112.5,135.):get_flow(mid,end,'dis')}
    for angle in SAMPLES:
        if angle in (90.,112.5,135.):
            frames.append({90.:start,112.5:mid,135.:end}[angle].copy())
        else:
            a,b=(90.,112.5) if angle<112.5 else (112.5,135.)
            src={90.:start,112.5:mid,135.:end}
            frames.append(morph(src[a],src[b],*flows[a,b],(angle-a)/(b-a),grid))
    return frames

def composite(x):
    a=x[...,3:4].astype(np.float32)/255
    return x[...,:3].astype(np.float32)*a+(1-a)*np.array([49,61,78])
def jumps(frames):return [round(float(np.mean(np.abs(composite(a)-composite(b)))),4) for a,b in zip(frames,frames[1:])]

def measure(save=True):
    sources=load();start,end=sources[90],sources[135]
    native_path=B
    record=json.loads((B.parent/'generation-result.json').read_text())
    assert record['tool']=='image_gen.imagegen' and record['actual_image_tool_used']
    assert hashlib.sha256(B.read_bytes()).hexdigest()==record['sha256']
    paint=np.asarray(Image.open(B).convert('RGBA').resize((443,443),Image.Resampling.LANCZOS)).copy()
    target=target_mask(start,end)
    best=optimize(target,paint)
    score,scale,tx,ty=best
    corrected=transform(paint,scale,tx,ty)
    base=iou(mask(paint),target)
    assert score+1e-6>=base
    before=frame_interp(start,paint,end)
    after=frame_interp(start,corrected,end)
    score_before=jumps(before);score_after=jumps(after)
    exact=all(np.array_equal(frames[0],start) and np.array_equal(frames[-1],end) for frames in (before,after))
    result={'schema':'KOMA_P15_128_NATIVE_KEYART_ALIGNMENT_V1','characterId':'p0_character_001','sourceAngles':[90,135],
       'targetYaw':112.5,'nativeCandidateSHA256':record['sha256'],
       'method':'bounded scale/translation registration to signed-distance interpolated silhouette; keyframe-preserving bidirectional DIS review',
       'candidateScale':scale,'candidateShiftXY':[tx,ty],
       'targetDefinition':'0.5 weighted source silhouette signed distance',
       'maskIoUBefore':round(base,5),'maskIoUAfter':round(score,5),
       'faceSkinPixelsBefore':face_skin_count(paint),'faceSkinPixelsAfter':face_skin_count(corrected),
       'adjacentCompositeRGBMAEBefore':score_before,'adjacentCompositeRGBMAEAfter':score_after,
       'maxAdjacentCompositeRGBMAEBefore':max(score_before),'maxAdjacentCompositeRGBMAEAfter':max(score_after),
       'sourceKeyframesPixelExact':exact,'nativeImageUnmodified':True,'semanticAnchorVerified':False,
       'hairStrokeCorrespondenceVerified':False,'physicalYawVerified':False,'hiddenSurfaceVerified':False,'visualAccepted':False,
       'review':'private-assets/exports/p15-128-keyart-registration/index.html',
       'next':'Use verified native art to solve individual line identity, eyes and garment visibility, with painted hidden surface; approve only after actual frame continuity improves.'}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        Image.fromarray(corrected,'RGBA').save(OUT/'yaw112p5-registration-candidate.png')
        Image.fromarray(np.uint8(target*255)).save(OUT/'interpolated-silhouette-mask.png')
        for variant,frames in [('source',before),('registered',after)]:
            directory=OUT/variant;directory.mkdir(exist_ok=True)
            for yaw,frame in zip(SAMPLES,frames):
                name=f'yaw{yaw:06.2f}'.replace('.','p')+'.png'
                Image.fromarray(frame,'RGBA').save(directory/name)
        board=Image.new('RGB',(5*300,2*345),(35,42,53));draw=ImageDraw.Draw(board)
        for j,(label,frames) in enumerate([('source',before),('registered',after)]):
            for i,(angle,frame) in enumerate(zip(SAMPLES,frames)):
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
                board.paste(tile.convert('RGB').resize((295,295),Image.Resampling.LANCZOS),(i*300,j*345+30))
                draw.text((i*300+8,j*345+6),f'{label}: yaw {angle:g}',fill='white')
        board.save(OUT/'comparison.jpg',quality=93)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 112.5 art registration</title><style>body{font:16px system-ui;background:#202733;color:#eee}img{max-width:100%}</style><h2>P0 90–112.5–135° local silhouette registration</h2><p>Top: native candidate in current pose; bottom: source-silhouette aligned candidate. This checks registration only. Style and art/occlusion quality must be judged from the images.</p><img src="comparison.jpg">')
        E.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    return result
if __name__=='__main__':
    r=measure();print(json.dumps({k:r[k] for k in ('candidateScale','candidateShiftXY','maskIoUBefore','maskIoUAfter','maxAdjacentCompositeRGBMAEBefore','maxAdjacentCompositeRGBMAEAfter','faceSkinPixelsBefore','faceSkinPixelsAfter')},indent=2))

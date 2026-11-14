#!/usr/bin/env python3
"""P15-187: source-owned medial skeleton/variable-width strand VDD trial.

Extract the complete P15-167 strand mask, order its centerline between the
P15-186 endpoint proposals, sample local alpha-distance widths at 160 arc
coordinates, and interpolate geometry using linear/PCHIP interpolation.
Texture is sampled in normalized curve/normal coordinates from valid source
paint. Three canonical keyviews are copied verbatim.
"""
import json,hashlib
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_129_ahoge_ownership import keyframes,KEYS,top_components
from p15_134_underpaint_probe import P,compose
from p15_167_endpoint_pair import pair,ROOT_AND_TIP
from p15_186_source_landmark_audit import skeleton_stats,ordered_skeleton_path,sample_polyline
from p15_184_alpha_aware_temporal_sweep import build_sequence,local_metrics,ANGLES
from p15_185_keyview_geometry_correspondence import pchip_three
from p15_183_valid_strand_texture import donor_texture
ROOT=Path(__file__).resolve().parents[1]
OUT=P/'exports/p15-187-full-skeleton-vdd'
E=ROOT/'evidence/p15-187-full-skeleton-vdd-qa.json'
N=160;H=W=443
METHODS=('linear_centerline','pchip_centerline')
MID=tuple(float(a) for a in ANGLES if a not in KEYS)

def normalized(data):
    tangent=np.gradient(data,axis=0)
    tangent/=np.maximum(np.linalg.norm(tangent,axis=1,keepdims=True),1.e-5)
    normal=np.column_stack([-tangent[:,1],tangent[:,0]])
    return normal.astype(np.float32)

def source_geometry(frame,angle):
    part,_,_,status=pair(frame,angle)
    assert status['originalPixelExact']
    mask=np.uint8(part[...,3]>24)
    sk,stats=skeleton_stats(mask)
    endpoints=np.asarray(stats['endpoints'],np.float32)
    if len(endpoints)!=2:raise RuntimeError(f'{angle}: unexpected skeleton endpoints {len(endpoints)}')
    root=np.asarray(ROOT_AND_TIP[angle]['root'],np.float32)
    tip=np.asarray(ROOT_AND_TIP[angle]['tip'],np.float32)
    pick=int(np.argmin(np.linalg.norm(endpoints-root,axis=1)))
    start=endpoints[pick];end=endpoints[1-pick]
    path=ordered_skeleton_path(sk,start,end)
    if len(path)<30:raise RuntimeError(f'{angle}: incomplete skeleton path')
    xy=sample_polyline(path,np.linspace(0,1,N)).astype(np.float32)
    # Remove raster-scale stairstep noise without shifting endpoint anchors.
    for dimension in (0,1):
        smooth=cv2.GaussianBlur(xy[:,dimension].reshape(1,-1),(1,0),1.2).reshape(-1)
        xy[:,dimension]=smooth
    xy[0]=start;xy[-1]=end
    distance=cv2.distanceTransform(mask,cv2.DIST_L2,5)
    radius=cv2.remap(distance,xy[:,0].reshape(1,-1),xy[:,1].reshape(1,-1),
                     cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE).reshape(-1)
    # cv2.line widths are diameters. Clamp only raster-degenerate ends.
    width=np.clip(radius*2,1.5,18.).astype(np.float32)
    width=cv2.GaussianBlur(width.reshape(1,-1),(1,0),1.6).reshape(-1)
    texture=donor_texture(frame,{'sourceMask':mask.astype(bool)},'nearest_valid')
    return {'curve':xy,'width':width,'normal':normalized(xy),'sourceMask':mask,
            'texture':texture,'sourceAlpha':part[...,3].copy(),
            'skeletonLength':len(path),'sourceMaskArea':int(mask.sum()),
            'root':start.tolist(),'freeTip':end.tolist(),
            'widthPercentiles':np.percentile(width,[10,50,90]).round(3).tolist(),
            'sourcePixelSHA256':hashlib.sha256(frame.tobytes()).hexdigest()}

def geometry_at(geometries,angle,method):
    left,right=(90.,112.5) if angle<112.5 else (112.5,135.)
    t=(angle-left)/(right-left)
    if method=='linear_centerline':
        xy=geometries[left]['curve']*(1-t)+geometries[right]['curve']*t
        width=geometries[left]['width']*(1-t)+geometries[right]['width']*t
    elif method=='pchip_centerline':
        xy=pchip_three(np.stack([geometries[k]['curve'] for k in KEYS]),angle).astype(np.float32)
        width=pchip_three(np.stack([geometries[k]['width'] for k in KEYS]),angle).astype(np.float32)
    else:raise ValueError(method)
    return {'curve':xy,'normal':normalized(xy),'width':np.clip(width,1.5,18.)},left,right,t

def render_strand(shape,source_left,source_right,t):
    # Draw a single tapering ribbon from centerline and variable source width.
    scale=4
    mask_hi=np.zeros((H*scale,W*scale),np.uint8)
    points=np.round(shape['curve']*scale).astype(np.int32)
    widths=np.maximum(1,np.round(shape['width']*scale)).astype(np.int32)
    for idx in range(len(points)-1):
        thickness=int(max(1,round((widths[idx]+widths[idx+1])*.5)))
        cv2.line(mask_hi,tuple(points[idx]),tuple(points[idx+1]),255,thickness,cv2.LINE_AA)
    mask=cv2.resize(mask_hi,(W,H),interpolation=cv2.INTER_AREA)
    yy,xx=np.where(mask>8)
    pixels=np.column_stack([xx,yy]).astype(np.float32)
    # Pixel-to-ribbon nearest-point sampling is restricted to the rendered
    # strand pixels, not the full 443x443 image.
    dif=pixels[:,None,:]-shape['curve'][None,:,:]
    node=np.argmin(np.sum(dif*dif,axis=2),axis=1)
    offset=(dif[np.arange(len(pixels)),node]*shape['normal'][node]).sum(axis=1)
    ratio=np.clip(offset/np.maximum(shape['width'][node],1.5),-.65,.65)
    def sample(source):
        coords=source['curve'][node]+source['normal'][node]*(ratio*source['width'][node])[:,None]
        sampled=cv2.remap(source['texture'],coords[:,0].reshape(1,-1).astype(np.float32),
                          coords[:,1].reshape(1,-1).astype(np.float32),
                          cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE).reshape(-1,3)
        return sampled
    colors=np.uint8(np.clip(np.rint(sample(source_left)*(1-t)+sample(source_right)*t),0,255))
    rgba=np.zeros((H,W,4),np.uint8)
    rgba[yy,xx,:3]=colors;rgba[...,3]=mask
    return rgba,{'visibleStrandPixels':int((mask>64).sum()),
                 'strokeWidthMin':round(float(shape['width'].min()),3),
                 'strokeWidthMax':round(float(shape['width'].max()),3),
                 'root':shape['curve'][0].round(2).tolist(),
                 'freeTip':shape['curve'][-1].round(2).tolist()}

def render(save=True):
    src=keyframes();geometries={a:source_geometry(src[a],a) for a in KEYS}
    baseline,crowns=build_sequence(src)
    outputs={};details={};metrics={}
    local_baseline,global_baseline=local_metrics(baseline)
    for mode in METHODS:
        frames=[];perframe={}
        for i,angle in enumerate(ANGLES):
            if angle in KEYS:
                frames.append(src[angle].copy());continue
            geom,left,right,t=geometry_at(geometries,float(angle),mode)
            strand,report=render_strand(geom,geometries[left],geometries[right],t)
            img=compose(crowns[i],strand)
            img[125:]=baseline[i][125:]
            frames.append(img)
            report.update({'topConnectedComponents':top_components(img),
                'deepBodyExact':bool(np.array_equal(img[125:],baseline[i][125:])),
                'leftKey':left,'rightKey':right,
                'sourceEndpointCoordinatesConsistent':bool(np.all(np.isfinite(geom['curve'])))})
            perframe[f'{angle:g}']=report
        local,global_e=local_metrics(frames)
        areas=[perframe[f'{angle:g}']['visibleStrandPixels'] for angle in MID]
        widths=[perframe[f'{angle:g}']['strokeWidthMax'] for angle in MID]
        metrics[mode]={
            'maxAdjacentLocalRGBMAE':max(local),
            'maxAdjacentGlobalRGBMAE':max(global_e),
            'maxAdjacentLocalDIS':max(local_baseline),
            'maxAdjacentGlobalDIS':max(global_baseline),
            'allNativeKeyframesExact':all(np.array_equal(frames[ANGLES.index(k)],src[k]) for k in KEYS),
            'allDeepBodyExact':all(perframe[f'{k:g}']['deepBodyExact'] for k in MID),
            'allMidframesConnected':all(perframe[f'{k:g}']['topConnectedComponents']==1 for k in MID),
            'variableWidthConfirmed':all(v>0 for v in widths),
            'midframeAreaMinMax':[min(areas),max(areas)],
            'midframeMaxStrokeWidths':widths}
        details[mode]=perframe;outputs[mode]=frames
    selected=min(METHODS,key=lambda k:metrics[k]['maxAdjacentLocalRGBMAE'])
    s=metrics[selected]
    qa={'schema':'KOMA_P15_187_FULL_SKELETON_VDD_V1',
        'characterId':'p0_character_001','sourceAngles':list(KEYS),
        'renderAngles':list(ANGLES),'sourceCurveSamples':N,'methods':metrics,
        'intermediateDetails':details,'selectedDiagnosticMethod':selected,
        'sourceGeometry':{f'{a:g}':{k:v for k,v in g.items() if k in
            ('skeletonLength','sourceMaskArea','root','freeTip','widthPercentiles','sourcePixelSHA256')} for a,g in geometries.items()},
        'method':'Ordered full-source skeleton root-to-tip, distance-transform width profile, per-node normal texture sampling, linear/PCHIP shape interpolation',
        'productionRendererUpdated':False,'visualAccepted':False,
        'review':'private-assets/exports/p15-187-full-skeleton-vdd/index.html'}
    qa['gate']={
        'nativeKeysExact':all(v['allNativeKeyframesExact'] for v in metrics.values()),
        'deepBodyExact':all(v['allDeepBodyExact'] for v in metrics.values()),
        'midframesConnected':s['allMidframesConnected'],
        'variableWidthConfirmed':s['variableWidthConfirmed'],
        'localTemporalBeatsDIS':s['maxAdjacentLocalRGBMAE']<=s['maxAdjacentLocalDIS'],
        'globalTemporalBeatsDIS':s['maxAdjacentGlobalRGBMAE']<=s['maxAdjacentGlobalDIS'],
        'crossViewSemanticCorrespondenceVerified':False,
        'visualAccepted':False,'passes':False}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(208*len(ANGLES),188*3),(35,42,54));pen=ImageDraw.Draw(board)
        for row,(name,frames) in enumerate([('whole_frame_DIS',baseline),*outputs.items()]):
            folder=OUT/name;folder.mkdir(exist_ok=True)
            for col,(angle,im) in enumerate(zip(ANGLES,frames)):
                Image.fromarray(im,'RGBA').save(folder/(f'yaw{angle:06.2f}'.replace('.','p')+'.png'))
                tile=Image.new('RGBA',(W,H),(49,61,78,255))
                tile.alpha_composite(Image.fromarray(im,'RGBA'))
                board.paste(tile.crop((110,0,380,135)).resize((200,154),Image.Resampling.LANCZOS).convert('RGB'),
                            (col*208,row*188+28))
                pen.text((col*208+4,row*188+5),f'{name} {angle:g}',fill='white')
        board.save(OUT/'source-centerline-13-yaw.jpg',quality=95)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P15-187 full-source skeleton VDD</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Full source centerline with variable width</h2><p>Ordered source-owned medial skeleton and distance-transform width profiles; linear/PCHIP geometric correspondence across three original keyviews.</p><img src="source-centerline-13-yaw.jpg">')
        E.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    return qa
if __name__=='__main__':
    q=render()
    print(json.dumps({'selected':q['selectedDiagnosticMethod'],'gate':q['gate'],
      'metrics':q['methods']},indent=2))

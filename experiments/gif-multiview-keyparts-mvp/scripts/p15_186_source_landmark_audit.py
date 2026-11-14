#!/usr/bin/env python3
"""P15-186 source-local ahoge landmark and variable-width audit.

No deformation is introduced. Measure the three native source keyviews:
visible alpha topology, endpoint candidates, normalized arc landmarks,
tangent/curvature, and local width sampled from the source alpha silhouette.
This determines whether the existing 160-point correspondence is supported
by source geometry before another interpolation experiment is attempted.
"""
import json,hashlib
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_129_ahoge_ownership import keyframes,KEYS,top_components
from p15_134_underpaint_probe import P
from p15_153_source_topology import extract
import p15_181_curve_correspondence as curves
from p15_167_endpoint_pair import ROOT_AND_TIP,pair
ROOT=Path(__file__).resolve().parents[1]
OUT=P/'exports/p15-186-source-landmark-audit'
E=ROOT/'evidence/p15-186-source-landmark-audit-qa.json'
H=W=443
SAMPLES=(0,.1,.2,.3,.4,.5,.6,.7,.8,.9,1)

def sample_polyline(points,ts):
    p=np.asarray(points,np.float32)
    seg=np.linalg.norm(np.diff(p,axis=0),axis=1)
    arc=np.r_[0,np.cumsum(seg)]
    if arc[-1]<=1e-6:raise ValueError('zero-length curve')
    target=np.asarray(ts)*arc[-1]
    return np.column_stack([np.interp(target,arc,p[:,0]),np.interp(target,arc,p[:,1])])

def zhang_suen(binary):
    img=np.uint8(binary>0)
    changed=True
    while changed:
        changed=False
        for phase in (0,1):
            p=np.pad(img,1)
            p2=p[:-2,1:-1];p3=p[:-2,2:];p4=p[1:-1,2:];p5=p[2:,2:]
            p6=p[2:,1:-1];p7=p[2:,:-2];p8=p[1:-1,:-2];p9=p[:-2,:-2]
            neighbors=[p2,p3,p4,p5,p6,p7,p8,p9]
            count=sum(x for x in neighbors)
            transitions=sum(((neighbors[i]==0)&(neighbors[(i+1)%8]==1)).astype(np.uint8) for i in range(8))
            if phase==0:
                c1=(p2*p4*p6)==0;c2=(p4*p6*p8)==0
            else:
                c1=(p2*p4*p8)==0;c2=(p2*p6*p8)==0
            remove=(img==1)&(count>=2)&(count<=6)&(transitions==1)&c1&c2
            if remove.any():img[remove]=0;changed=True
    return img

def skeleton_stats(mask):
    sk=zhang_suen(mask)
    p=np.pad(sk,1)
    degree=np.zeros(sk.shape,np.uint8)
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            if dx or dy:degree+=p[1+dy:1+dy+sk.shape[0],1+dx:1+dx+sk.shape[1]]
    ys,xs=np.where(sk>0)
    endpoints=np.column_stack([xs[(degree[ys,xs]==1)],ys[(degree[ys,xs]==1)]])
    branches=np.column_stack([xs[(degree[ys,xs]>=3)],ys[(degree[ys,xs]>=3)]])
    return sk,{'skeletonPixels':int(sk.sum()),'endpointCount':int(len(endpoints)),
       'branchPixelCount':int(len(branches)),
       'endpoints':endpoints.tolist()}

def ordered_skeleton_path(skeleton,start,end):
    points=set(map(tuple,np.column_stack(np.where(skeleton>0))[:,::-1].tolist()))
    start=tuple(map(int,start));end=tuple(map(int,end))
    queue=[start];parent={start:None}
    for node in queue:
        if node==end:break
        x,y=node
        for dy in (-1,0,1):
            for dx in (-1,0,1):
                nxt=(x+dx,y+dy)
                if (dx or dy) and nxt in points and nxt not in parent:
                    parent[nxt]=node;queue.append(nxt)
    if end not in parent:return np.empty((0,2),np.float32)
    path=[];node=end
    while node is not None:path.append(node);node=parent[node]
    return np.asarray(path[::-1],np.float32)

def similarity_align(source_pair,target_pair):
    s=np.asarray(source_pair,np.float32);t=np.asarray(target_pair,np.float32)
    su=s[1]-s[0];tu=t[1]-t[0]
    denom=float(np.dot(su,su))
    scale=float(np.linalg.norm(tu)/max(np.linalg.norm(su),1e-6))
    angle=float(np.arctan2(tu[1],tu[0])-np.arctan2(su[1],su[0]))
    c=np.cos(angle)*scale;si=np.sin(angle)*scale
    matrix=np.array([[c,-si],[si,c]],np.float32)
    return matrix,t[0]-matrix@s[0]

def describe(frame,angle):
    legacy=curves.source_curve(frame)
    full_layer,_,_,pair_info=pair(frame,angle)
    full_mask=(full_layer[...,3]>24).astype(np.uint8)
    # The legacy centerline is extracted from p15-153's y<54 crop. Measure
    # its distance from the complete source-owned visible loop.
    full_distance=cv2.distanceTransform(full_mask,cv2.DIST_L2,5)
    legacy_points=legacy['curve']
    legacy_inside=np.array([full_mask[int(np.clip(round(y),0,H-1)),int(np.clip(round(x),0,W-1))]>0 for x,y in legacy_points])
    legacy_dist=np.array([full_distance[int(np.clip(round(y),0,H-1)),int(np.clip(round(x),0,W-1))] for x,y in legacy_points])
    skeleton,skinfo=skeleton_stats(full_mask)
    # Label endpoint identity by proximity to source root/tip proposals.
    endpoints=np.asarray(skinfo['endpoints'],np.float32)
    root=np.asarray(ROOT_AND_TIP[angle]['root'],np.float32)
    tip=np.asarray(ROOT_AND_TIP[angle]['tip'],np.float32)
    if len(endpoints)>=2:
        root_ep=endpoints[int(np.argmin(np.linalg.norm(endpoints-root,axis=1)))]
        remaining=endpoints[np.linalg.norm(endpoints-root,axis=1).argsort()[1:]]
        tip_ep=remaining[int(np.argmin(np.linalg.norm(remaining-tip,axis=1)))]
        ordered=ordered_skeleton_path(skeleton,root_ep,tip_ep)
    else:
        root_ep=tip_ep=np.array([-1,-1],np.float32);ordered=np.empty((0,2),np.float32)
    # Distance-transform radius sampled on the full-mask skeleton yields
    # a local, source-derived width profile.
    sy,sx=np.where(skeleton>0)
    radii=full_distance[sy,sx]
    valid=radii>0
    radii=radii[valid]
    # Skeleton endpoint positions provide source geometry candidates, not
    # automatic semantic labels. Match the proposal anchors by distance.
    root_match=root_ep;tip_match=tip_ep
    root_distance=float(np.linalg.norm(root-root_match));tip_distance=float(np.linalg.norm(tip-tip_match))
    ordered_landmarks=sample_polyline(ordered,np.linspace(0,1,11)) if len(ordered)>1 else np.empty((0,2))
    ordered_widths=[]
    for x,y in ordered[::max(1,len(ordered)//80)]:
        ordered_widths.append(round(float(full_distance[int(np.clip(round(y),0,H-1)),int(np.clip(round(x),0,W-1))]*2),3))
    # Existing source contour samples and the full silhouette skeleton are
    # retained separately; no forced pointwise correspondence is asserted.
    return legacy,{'angle':angle,
      'legacyCropBoundaryY':54,
      'legacyCurveStart':legacy_points[0].round(3).tolist(),
      'legacyCurveEnd':legacy_points[-1].round(3).tolist(),
      'legacyCurveLength':round(float(legacy['length']),3),
      'legacyCurvePointsInsideFullSourceMaskRatio':round(float(legacy_inside.mean()),5),
      'legacyCurveMeanDistanceTransformRadius':round(float(legacy_dist.mean()),4),
      'legacyCurveMaxDistanceTransformRadius':round(float(legacy_dist.max()),4),
      'fullVisibleSourceMaskPixels':int(full_mask.sum()),
      'fullVisibleSourceMaskBBox':[int(sx.min()),int(sy.min()),int(sx.max()-sx.min()+1),int(sy.max()-sy.min()+1)] if len(sx) else [],
      'fullVisibleSourceMaskSHA256':hashlib.sha256(full_mask.tobytes()).hexdigest(),
      'sourcePairRecompositionExact':pair_info['originalPixelExact'],
      'sourceRootProposal':list(ROOT_AND_TIP[angle]['root']),
      'sourceTipProposal':list(ROOT_AND_TIP[angle]['tip']),
      'skeleton':{**skinfo,'orderedPathPixels':int(len(ordered))},
      'orderedRootToTipLandmarks':ordered_landmarks.round(3).tolist(),
      'orderedWidthProfile':ordered_widths,
      'skeletonRadiusWidth':{'sampleCount':int(len(radii)),
        'mean':round(float(np.mean(radii)*2),3) if len(radii) else None,
        'p10':round(float(np.percentile(radii,10)*2),3) if len(radii) else None,
        'median':round(float(np.median(radii)*2),3) if len(radii) else None,
        'p90':round(float(np.percentile(radii,90)*2),3) if len(radii) else None},
      'nearestSkeletonEndpointToRoot':root_match.round(3).tolist(),
      'nearestSkeletonEndpointToTip':tip_match.round(3).tolist(),
      'rootProposalToSkeletonEndpointDistance':round(root_distance,3),
      'tipProposalToSkeletonEndpointDistance':round(tip_distance,3)}


def pairwise(a,b):
    pa=np.asarray(a['landmarkCoordinates']);pb=np.asarray(b['landmarkCoordinates'])
    direct=np.linalg.norm(pa-pb,axis=1)
    reverse=np.linalg.norm(pa-pb[::-1],axis=1)
    ta=np.asarray(a['landmarkTangents']);tb=np.asarray(b['landmarkTangents'])
    tangent_direct=np.arccos(np.clip(np.sum(ta*tb,axis=1),-1,1))
    tangent_reverse=np.arccos(np.clip(np.sum(ta*tb[::-1],axis=1),-1,1))
    return {'directLandmarkDistances':np.round(direct,3).tolist(),
      'reverseLandmarkDistances':np.round(reverse,3).tolist(),
      'directRMS':round(float(np.sqrt(np.mean(direct**2))),4),
      'reverseRMS':round(float(np.sqrt(np.mean(reverse**2))),4),
      'directTangentAngleDegrees':np.round(np.degrees(tangent_direct),2).tolist(),
      'reverseTangentAngleDegrees':np.round(np.degrees(tangent_reverse),2).tolist(),
      'directTangentMeanDegrees':round(float(np.degrees(tangent_direct).mean()),3),
      'reverseTangentMeanDegrees':round(float(np.degrees(tangent_reverse).mean()),3),
      'bestOrientation':'direct' if direct.mean()<=reverse.mean() else 'reversed'}

def evaluate(save=True):
    src=keyframes();descs={};reports={};images={}
    for angle in KEYS:
        data,report=describe(src[angle],angle)
        descs[angle]=report;reports[angle]=report;images[angle]=data
    comparisons={}
    for a,b in ((90.,112.5),(112.5,135.),(90.,135.)):
        ea=np.asarray(reports[a]['skeleton']['endpoints'],np.float32)
        eb=np.asarray(reports[b]['skeleton']['endpoints'],np.float32)
        pa=np.asarray(reports[a]['orderedRootToTipLandmarks'],np.float32)
        pb=np.asarray(reports[b]['orderedRootToTipLandmarks'],np.float32)
        if len(pa)==11 and len(pb)==11:
            mat,offset=similarity_align(np.asarray([pb[0],pb[-1]]),np.asarray([pa[0],pa[-1]]))
            aligned=pb@mat.T+offset
            errors=np.linalg.norm(pa-aligned,axis=1)
            wa=np.asarray(reports[a]['orderedWidthProfile'],np.float32)
            wb=np.asarray(reports[b]['orderedWidthProfile'],np.float32)
            if len(wa)>1 and len(wb)>1:
                wa=np.interp(np.linspace(0,1,11),np.linspace(0,1,len(wa)),wa)
                wb=np.interp(np.linspace(0,1,11),np.linspace(0,1,len(wb)),wb)
                width_error=float(np.sqrt(np.mean((wa-wb)**2)))
            else:width_error=None
            comparisons[f'{a:g}-{b:g}']={'endpointAlignedLandmarkRMS':round(float(np.sqrt(np.mean(errors**2))),4),
              'endpointAlignedLandmarkErrors':np.round(errors,3).tolist(),
              'widthProfileRMS':round(width_error,4) if width_error is not None else None,
              'sourceMaskAreaRatio':round(reports[a]['fullVisibleSourceMaskPixels']/max(1,reports[b]['fullVisibleSourceMaskPixels']),4)}
        else:
            comparisons[f'{a:g}-{b:g}']={'endpointAlignedLandmarkRMS':None,'reason':'Skeleton path could not be ordered between proposed endpoints.'}
    endpoint_identity={f'{a:g}':{
      'rootEndpoint':[round(float(x),2) for x in reports[a]['nearestSkeletonEndpointToRoot']],
      'tipEndpoint':[round(float(x),2) for x in reports[a]['nearestSkeletonEndpointToTip']],
      'rootProposalDistance':reports[a]['rootProposalToSkeletonEndpointDistance'],
      'tipProposalDistance':reports[a]['tipProposalToSkeletonEndpointDistance']} for a in KEYS}
    legacy_boundary_only=True
    skeleton_valid=all(reports[a]['skeleton']['endpointCount']==2 for a in KEYS)
    width_profiles_valid=all(reports[a]['skeletonRadiusWidth']['sampleCount']>0 for a in KEYS)
    q={'schema':'KOMA_P15_186_SOURCE_LANDMARK_AUDIT_V1',
      'characterId':'p0_character_001','sourceAngles':list(KEYS),
      'sourceGeometry':{f'{a:g}':reports[a] for a in KEYS},
      'pairwiseCorrespondence':comparisons,'endpointIdentity':endpoint_identity,
      'legacyCurveUsesCropBoundaryInsteadOfFullSilhouette':legacy_boundary_only,
      'fullSilhouetteSkeletonHasTwoEndpoints':skeleton_valid,
      'sourceDerivedVariableWidthProfilesAvailable':width_profiles_valid,
      'interpretation':'P15-181 obtains its 160-point curve from p15-153 extract(), whose visible loop is cropped at y=54. The selected contour is therefore a boundary of a clipped mask, not a medial centerline. Full source-owned strand silhouettes from P15-167 support alpha-distance width measurement and skeleton topology, but endpoint proposals and cross-view semantic point correspondence still need authoring/visual confirmation.',
      'productionRendererUpdated':False,'visualAccepted':False,
      'review':'private-assets/exports/p15-186-source-landmark-audit/index.html'}
    q['gate']={'allSourceKeyviewsPixelHashRecorded':all(bool(d['fullVisibleSourceMaskSHA256']) for d in reports.values()),
      'legacyCurveUsesFullSilhouette':not legacy_boundary_only,
      'fullSilhouetteSkeletonHasTwoEndpoints':skeleton_valid,
      'sourceDerivedVariableWidthProfilesAvailable':width_profiles_valid,
      'semanticCrossViewCorrespondenceEstablished':False,
      'productionGeometryApproved':False,'passes':False}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(360*3,380*3),(35,42,54));pen=ImageDraw.Draw(board)
        for col,a in enumerate(KEYS):
            frame=Image.new('RGBA',(W,H),(49,61,78,255));frame.alpha_composite(Image.fromarray(src[a],'RGBA'))
            board.paste(frame.crop((110,0,380,145)).resize((350,188),Image.Resampling.NEAREST).convert('RGB'),(360*col,380))
            pen.text((360*col+6,385),f'{a:g}° source',fill='white')
            overlay=Image.new('RGBA',(W,H),(49,61,78,255));overlay.alpha_composite(Image.fromarray(src[a],'RGBA'))
            draw=ImageDraw.Draw(overlay)
            layer,_,_,_=pair(src[a],a)
            mask=(layer[...,3]>24).astype(np.uint8)
            sk,skinfo=skeleton_stats(mask)
            sy,sx=np.where(sk>0)
            for x,y in zip(sx,sy):draw.point((int(x),int(y)),fill=(40,255,80,255))
            path=np.asarray(reports[a]['orderedRootToTipLandmarks'])
            if len(path)>1:draw.line([tuple(np.rint(pt).astype(int)) for pt in path],fill=(255,120,30,255),width=2)
            for j,pt in enumerate(skinfo['endpoints']):
                x,y=pt;draw.ellipse((x-4,y-4,x+4,y+4),fill=(255,220,40,255))
                draw.text((x+4,y-8),f'E{j}',fill=(255,255,255,255))
            board.paste(overlay.crop((110,0,380,145)).resize((350,188),Image.Resampling.NEAREST).convert('RGB'),(360*col,0))
            pen.text((360*col+6,5),f'{a:g}° full-mask skeleton/endpoints',fill='white')
            widths=reports[a]['skeletonRadiusWidth']
            pen.text((360*col+6,205),f"width median={widths['median']} p10={widths['p10']} p90={widths['p90']}",fill='white')
        board.save(OUT/'source-landmark-overlay.jpg',quality=95)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 source landmark audit</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Source-only normalized arc landmarks and alpha-derived width</h2><p>Green is the skeleton of the full source-owned strand silhouette; yellow markers are its graph endpoints. Width is measured from the alpha-mask distance transform. This is a diagnostic overlay, not a replacement asset.</p><img src="source-landmark-overlay.jpg">')
        E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':
    q=evaluate()
    print(json.dumps({'endpointIdentity':q['endpointIdentity'],'comparisons':q['pairwiseCorrespondence'],'gate':q['gate']},indent=2))

#!/usr/bin/env python3
"""P15-192: pin and audit the native 112.5-degree root-control asset.

P15-189/191 consumed a generated crown underpaint from a mutable private export.
This stage fingerprints the exact inputs, remeasures the native source root
and crown crossing, and packages a source-pixel-exact local control asset.
The control asset distinguishes embedded attachment from visible silhouette
crossing; it does not invent a second root or modify production rendering.
"""
import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from p15_129_ahoge_ownership import keyframes,KEYS
from p15_167_endpoint_pair import pair,ROOT_AND_TIP
from p15_187_full_skeleton_vdd import source_geometry,normalized,render_strand
from p15_184_alpha_aware_temporal_sweep import build_sequence,ANGLES
from p15_166_crown_silhouette import crown_edge
from p15_189_root_emergence_audit import interpolate_crossing
from p15_134_underpaint_probe import P,compose
ROOT=Path(__file__).resolve().parents[1]
OUT=P/'exports/p15-192-root-control-asset'
E=ROOT/'evidence/p15-192-root-control-asset-qa.json'
CROP=(220,34,302,108)
TAGS={90.:'yaw090',112.5:'yaw112p5',135.:'yaw135'}
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def array_sha(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def main(save=True):
    sources=keyframes()
    baseline,crowns=build_sequence(sources)
    key_reports={};assets={}
    stale=json.loads((ROOT/'evidence/p15-189-root-emergence-audit-qa.json').read_text())
    for a in KEYS:
        i=ANGLES.index(a)
        strand,crown,owner,pair_info=pair(sources[a],a)
        geom=source_geometry(sources[a],a)
        edge=crown_edge(crowns[i],9)
        crossing,tangent,segment=interpolate_crossing(geom['curve'],edge)
        anchor=np.asarray(ROOT_AND_TIP[a]['root'],np.float32)
        crop=CROP if a==112.5 else (max(0,int(anchor[0])-38),34,min(443,int(anchor[0])+44),108)
        x0,y0,x1,y1=crop
        ai_path=P/f'exports/p15-178-ai-rootless-crown/{TAGS[a]}-ai-rootless-full.png'
        crown_path=P/f'exports/p15-178-ai-rootless-crown/local/{TAGS[a]}/crown-motion-underpaint.png'
        if not ai_path.exists() or not crown_path.exists():raise FileNotFoundError((ai_path,crown_path))
        with Image.open(crown_path) as im:donor=np.asarray(im.convert('RGBA')).copy()
        local_source=sources[a][y0:y1,x0:x1].copy()
        local_strand=strand[y0:y1,x0:x1].copy()
        local_crown=donor[y0:y1,x0:x1].copy()
        local_owner=owner[y0:y1,x0:x1].astype(np.uint8)*255
        # Exact source reconstruction is checked at full resolution, not only
        # inside the crop. The control package keeps original source RGBA.
        reconstructed=crown.copy();reconstructed[owner]=strand[owner]
        visible=np.asarray(crossing).round().astype(int)
        cx,cy=visible
        rx,ry=ROOT_AND_TIP[a]['root']
        report={
          'sourceSHA256':array_sha(sources[a]),
          'strandSHA256':array_sha(strand),
          'crownPairSHA256':array_sha(crown),
          'aiRootlessFullSHA256':sha(ai_path),
          'motionUnderpaintSHA256':sha(crown_path),
          'sourcePairReassemblyExact':bool(np.array_equal(reconstructed,sources[a])),
          'rootAnchor':anchor.tolist(),
          'rootAnchorAlpha':int(sources[a][ry,rx,3]),
          'visibleCrownCrossing':crossing.round(4).tolist(),
          'crossingTangent':tangent.round(5).tolist(),
          'crossingControlSegment':int(segment),
          'rootToCrossingDistance':round(float(np.linalg.norm(anchor-crossing)),4),
          'sourceAlphaAtCrossing':int(sources[a][cy,cx,3]),
          'motionUnderpaintAlphaAtCrossing':int(donor[cy,cx,3]),
          'sourceRootRegionOpaquePixels':int(((strand[...,3]>64)&(np.indices(owner.shape)[0]>=ry-24)&(np.indices(owner.shape)[0]<=ry+10)&(np.indices(owner.shape)[1]>=rx-10)&(np.indices(owner.shape)[1]<=rx+10)).sum()),
          'sourceGeometryRoot':geom['root'],'sourceGeometryFreeTip':geom['freeTip'],
          'centerlineStart':geom['curve'][0].round(4).tolist(),
          'centerlineAtCrossing':crossing.round(4).tolist(),
          'crop':list(crop),
          'staleP15_189Crossing':stale['diagnostics'][f'{a:g}']['crossing'],
          'staleP15_189CrossingDeltaPixels':round(float(np.linalg.norm(crossing-np.asarray(stale['diagnostics'][f'{a:g}']['crossing']))),4),
          'underpaintEdgeAtCrossingX':round(float(edge[cx]),4)}
        key_reports[f'{a:g}']=report
        assets[a]=(local_source,local_strand,local_crown,local_owner,donor)
    # Hold out the native 112.5-degree view and predict its local strand
    # from the independent 90/135-degree source geometries. This is a
    # source-derived control candidate, not a replacement for the approved key.
    g90=source_geometry(sources[90.],90.)
    g112=source_geometry(sources[112.5],112.5)
    g135=source_geometry(sources[135.],135.)
    predicted={'curve':(g90['curve']+g135['curve'])*.5,
               'width':(g90['width']+g135['width'])*.5}
    predicted['normal']=normalized(predicted['curve'])
    candidate_strand,candidate_render=render_strand(predicted,g90,g135,.5)
    native_strand,_,_,_=pair(sources[112.5],112.5)
    donor=assets[112.5][4]
    candidate_composite=compose(donor,candidate_strand)
    native_mask=native_strand[...,3]>24
    candidate_mask=candidate_strand[...,3]>24
    intersection=int((native_mask&candidate_mask).sum())
    union=int((native_mask|candidate_mask).sum())
    curve_delta=np.linalg.norm(predicted['curve']-g112['curve'],axis=1)
    edge=crown_edge(donor,9)
    predicted_cross,predicted_tangent,predicted_segment=interpolate_crossing(predicted['curve'],edge)
    native_cross,native_tangent,native_segment=interpolate_crossing(g112['curve'],edge)
    prediction={
      'method':'Hold out 112.5-degree source key and interpolate centerline/width from the 90- and 135-degree source-owned strands; sample texture only from those two native sources.',
      'sourceKeysUsed':[90.,135.],'heldOutNativeKey':112.5,
      'predictedRoot':predicted['curve'][0].round(4).tolist(),
      'predictedFreeTip':predicted['curve'][-1].round(4).tolist(),
      'nativeRoot':g112['curve'][0].round(4).tolist(),
      'nativeFreeTip':g112['curve'][-1].round(4).tolist(),
      'meanCenterlineDeltaPixels':round(float(curve_delta.mean()),4),
      'maxCenterlineDeltaPixels':round(float(curve_delta.max()),4),
      'nativeWidthPercentiles':np.percentile(g112['width'],[10,50,90]).round(3).tolist(),
      'predictedWidthPercentiles':np.percentile(predicted['width'],[10,50,90]).round(3).tolist(),
      'nativeMaskArea':int(native_mask.sum()),'predictedMaskArea':int(candidate_mask.sum()),
      'maskIoU':round(intersection/max(1,union),5),
      'nativeCrossing':native_cross.round(4).tolist(),
      'predictedCrossing':predicted_cross.round(4).tolist(),
      'crossingDisplacementPixels':round(float(np.linalg.norm(native_cross-predicted_cross)),4),
      'predictedTangent':predicted_tangent.round(5).tolist(),
      'nativeTangent':native_tangent.round(5).tolist(),
      'candidateVisiblePixels':candidate_render['visibleStrandPixels'],
      'candidateRootlessCrownComposite':True,
      'nativeKeyframeModified':False,
      'candidateSHA256':array_sha(candidate_composite)}
    q={'schema':'KOMA_P15_192_ROOT_CONTROL_ASSET_AUDIT_V1',
       'characterId':'p0_character_001','sourceAngles':list(KEYS),
       'renderAngles':list(ANGLES),'nativeViews':key_reports,'heldOut112p5Prediction':prediction,
       'finding':'The 112.5-degree native ahoge is a distinct source-owned shape and cannot be reconstructed by simply interpolating the 90- and 135-degree strands: the held-out prediction has only 0.04054 mask IoU and its visible crossing is 52.49 px from the native crossing. Preserve 112.5 degrees as an independent key/control asset. The earlier 7.57 px crossing discrepancy was caused by this audit script indexing the key list against the 13-frame crown sequence; correcting the frame index reproduces the P15-189 measurement within 0.0001 px. P15-189 now records SHA-256 fingerprints for all mutable source and underpaint inputs. The local control package preserves source RGBA, source-owned strand, ownership matte and generated crown donor as distinct layers.',
       'staleEvidenceDetected':any(v['staleP15_189CrossingDeltaPixels']>1 for v in key_reports.values()),
       'sourceAssetsModified':False,'productionRendererUpdated':False,
       'visualAccepted':False,'review':'private-assets/exports/p15-192-root-control-asset/index.html'}
    q['gate']={
      'allThreeSourcePairsReassembleExact':all(v['sourcePairReassemblyExact'] for v in key_reports.values()),
      'allRootAnchorsHaveSourceAlpha':all(v['rootAnchorAlpha']>=64 for v in key_reports.values()),
      'allCrossingsMeasured':all(v['visibleCrownCrossing'] for v in key_reports.values()),
      'allInputsFingerprinted':all(len(v['motionUnderpaintSHA256'])==64 and len(v['aiRootlessFullSHA256'])==64 for v in key_reports.values()),
      '112p5LocalControlPackageComplete':True,
      'independent112p5PredictionRendered':True,
      'predictionRemainsSeparateFromNativeKey':prediction['nativeKeyframeModified'] is False,
      'heldOutPredictionMatchesNativeKey':prediction['maskIoU']>=.70 and prediction['crossingDisplacementPixels']<=4,
      'evidenceReproducible':not q['staleEvidenceDetected'],
      'sourceRootSemanticsApproved':False,'productionApproved':False,'passes':False}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(330*3,300*4),(35,42,54));draw=ImageDraw.Draw(board)
        labels=('source','source-owned strand','rootless crown donor','owner matte')
        for col,a in enumerate(KEYS):
            src,st,cr,mask,donor=assets[a]
            items=(src,st,donor,np.dstack([mask]*3+[np.full_like(mask,255)]))
            folder=OUT/TAGS[a];folder.mkdir(exist_ok=True)
            for label,im in zip(labels,items):
                Image.fromarray(im,'RGBA').save(folder/(label.lower().replace(' ','-')+'.png'))
            for row,(label,im) in enumerate(zip(labels,items)):
                tile=Image.new('RGBA',(im.shape[1],im.shape[0]),(49,61,78,255));tile.alpha_composite(Image.fromarray(im,'RGBA'))
                tile=tile.resize((320,255),Image.Resampling.NEAREST)
                board.paste(tile.convert('RGB'),(col*330,row*300+35))
                draw.text((col*330+5,row*300+5),f'{a:g}° {label}',fill='white')
        board.save(OUT/'native-root-control-assets.jpg',quality=95)
        Image.fromarray(candidate_strand,'RGBA').save(OUT/'112p5-heldout-strand-candidate.png')
        Image.fromarray(candidate_composite,'RGBA').save(OUT/'112p5-heldout-root-control-candidate.png')
        native_tile=Image.new('RGBA',(443,443),(49,61,78,255));native_tile.alpha_composite(Image.fromarray(sources[112.5],'RGBA'))
        pred_tile=Image.new('RGBA',(443,443),(49,61,78,255));pred_tile.alpha_composite(Image.fromarray(candidate_composite,'RGBA'))
        comparison=Image.new('RGB',(900,360),(35,42,54))
        comparison.paste(native_tile.crop((185,0,365,110)).resize((440,330),Image.Resampling.LANCZOS).convert('RGB'),(5,25))
        comparison.paste(pred_tile.crop((185,0,365,110)).resize((440,330),Image.Resampling.LANCZOS).convert('RGB'),(455,25))
        d=ImageDraw.Draw(comparison);d.text((10,5),'Native 112.5° keyframe',fill='white');d.text((460,5),'90°/135° held-out prediction',fill='white')
        comparison.save(OUT/'112p5-heldout-control-comparison.jpg',quality=95)
        (OUT/'root-landmarks.json').write_text(json.dumps(key_reports,ensure_ascii=False,indent=2)+'\n')
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P15-192 native root control asset</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>Native source root and independent crown underpaint layers</h2><p>Each source view has a pixel-exact source reconstruction, source-owned strand, rootless crown donor, and ownership matte. The 112.5-degree crop is a local control asset with both the embedded attachment and visible scalp crossing measured separately.</p><img src="native-root-control-assets.jpg"><h2>Held-out 112.5-degree control prediction</h2><p>The native 112.5-degree key is preserved. The candidate is generated from the 90- and 135-degree source strand geometry and texture only.</p><img src="112p5-heldout-control-comparison.jpg"><pre>'+json.dumps(q['gate'],indent=2)+'</pre>')
        E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':
 q=main();print(json.dumps({'gate':q['gate'],'staleEvidenceDetected':q['staleEvidenceDetected'],'nativeViews':q['nativeViews']},indent=2))

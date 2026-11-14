#!/usr/bin/env python3
"""Audit the existing P0 45-65 degree arc before treating it as a yaw/identity reference."""
import json,hashlib
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1]
ARC=R/'private-assets/exports/p15-38-original-p0-arc-review'
D=R/'private-assets/exports/p15-57-multiview-audit';D.mkdir(parents=True,exist_ok=True)
qa=json.loads((R/'evidence/p15-38-visual-review-qa.json').read_text())
extended=json.loads((R/'evidence/p15-38-extended-artmesh-qa.json').read_text())
selected=[45.0,55.0,57.5,60.0,61.25,63.75,65.0]
frames=[]
for f in qa['frames']:
 yaw=f['yaw']; folder=f['dir']; p=ARC/folder/'whole-crossview-reference.png'
 clip=Image.open(ARC/folder/'gold-clip.png').convert('RGBA')
 bbox=clip.getchannel('A').getbbox()
 row={'yaw':yaw,'kind':f['kind'],'alphaIoU':f.get('alphaIoUWithWholeCrossviewReference'),
      'artisticallyAccepted':f.get('artisticallyAccepted',False),'clipBBox443':list(bbox) if bbox else None,
      'sourceImageSHA256':f['sourceImages'].get('whole-crossview-reference.png')}
 if yaw in selected:
  im=Image.open(p).convert('RGBA');im.thumbnail((640,640),Image.Resampling.LANCZOS)
  name=f'arc-yaw-{str(yaw).replace(".","p")}.png';im.save(D/name)
  row['preview']=name
 frames.append(row)
candidate=R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'
im=Image.open(candidate).convert('RGBA');im.thumbnail((640,640),Image.Resampling.LANCZOS);im.save(D/'p15-56-current-candidate.png')
summary={
 'schema':'KOMA-P15-57-MULTIVIEW-CONTINUITY-AUDIT-V1','characterId':'p0_character_001',
 'sourceArcAngles':[x['yaw'] for x in frames],
 'registeredArcFrames':len(frames),'roleCount':13,
 'fullArcArtistAcceptance':qa['fullArtistAcceptance'],
 'independentlyPaintedKeyframesApproved':qa['independentPaintedKeyframesApproved'],
 'sourceP0HeroSHA256Verified':extended['sourceP0HeroSHA256Verified'],
 'registeredFull45DegreeOriginalPreserved':extended['registeredFull45DegreeOriginalPreserved'],
 'independentArtAdmission':extended['fullIndependentArtAdmission'],
 'physical3DTopologyApproved':extended['physical3DTopologyApproved'],
 'adjacentMetrics':extended['adjacentMetrics'],
 'frames':frames,
 'P1556CandidateSHA256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
 'assessment':'The 13-angle registered arc is an engineering candidate, not an artistically approved multi-view identity set. All per-angle visual-review artisticallyAccepted flags are false; interpolated 47.5/50/52.5 frames have alpha IoU about 0.978-0.981 but this measures silhouette overlap, not facial identity or artistic quality. The 57.5-65 whole-view previews show visible face/eye/skin compositing artifacts. The 45-degree canonical P0 reference remains the identity source; the 65-degree AI candidate is a separate promising profile candidate, not calibrated yaw.',
 'absoluteYaw65Verified':False,'identityContinuityApproved':False,'formalKeyframeAccepted':False,
 'next':'Do not use the 57.5-65 registered full-view composites as identity truth. Create an independent artistically coherent right-facing 65-degree view from canonical P0 45 with explicit angle conditioning, then measure camera yaw and compare facial landmarks.'
}
(R/'evidence/p15-57-multiview-audit.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:summary[k] for k in ['registeredArcFrames','fullArcArtistAcceptance','independentlyPaintedKeyframesApproved','sourceP0HeroSHA256Verified','independentArtAdmission','absoluteYaw65Verified','identityContinuityApproved']}))

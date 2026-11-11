#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw
import json,hashlib
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-81-image-layered'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
q=json.loads((R/'evidence/p15-81-sam3-qa.json').read_text())
source=Image.open(P/'p15-56-edge-matting/candidate-erode-2.png').convert('RGBA')
old=Image.open(P/'p15-76-seam-source/eye-shift-18.png').convert('RGBA')
old.crop((445,265,795,605)).resize((700,680),Image.Resampling.LANCZOS).save(D/'previous-p15-76-18-face.png')
oldhair=Image.open(P/'p15-74-bangs-repair/hair.front.alpha-dedup.png').convert('RGBA')
oldhair.getchannel('A').crop((450,141,790,590)).resize((680,898)).save(D/'previous-sam-alpha-preview.png')
# Forehead and eye anchors for both model masks; source coordinates.
anchors={
 'frontHair':[620,305],
 'bangNearEyebrow':[590,395],
 'nearIris':[600,475],
 'cheekSkin':[640,555],
 'goldClip':[720,320],
 'sideHair':[430,420]}
q['samplingAnchors']=anchors
for name in ('027','083'):
 mask=Image.open(D/f'sam3-{name}-aligned-alpha.png').convert('L')
 info=q['masks'][name]
 info['anchorAlpha']={k:mask.getpixel(tuple(v)) for k,v in anchors.items()}
 out=Image.open(D/f'sam3-{name}-rest-composite.png').convert('RGBA')
 diff=ImageChops.difference(source,out)
 info['actualRestPoseChangedPixels']=sum(v>0 for v in diff.convert('L').getdata())
 info['actualRestPoseExact']=diff.getbbox() is None
 holes={}
 for dx in (9,18):
  f=Image.open(D/f'sam3-{name}-motion-{dx:02d}.png').convert('RGBA')
  roi=(510,425,685,530)
  holes[str(dx)]=sum(a>128 and b<32 for a,b in zip(source.getchannel('A').crop(roi).getdata(),f.getchannel('A').crop(roi).getdata()))
 info['newHolesByOffset']=holes
# Derive model candidate validity without claiming detailed strands are correct
q['comparison']={
 'narrowMask':'027 candidate selectively retains front hair and leaves the iris/cheek sample outside',
 'wideMask':'083 includes large back-hair region and is not an isolated bangs layer',
 'sourceRestReconstruction':'mathematical binary mask complementary decomposition reassembles the original; actual moving pipeline 0px does not',
 'visual':'SAM3 reduces grid holes of the previous SAM output, but current face underpaint and 0px compositing still produce duplicate eyebrow/eyelid edges, and hair-clip-specific layering is not fully solved'}
q['provisionalNarrowMaskAvailable']=True
q['newIndependentCleanBangAndHiddenSkinLayerAccepted']=False
q['realRestPoseExact']=False
q['visualGate']='SAM3_IMPROVED_BANGS_MASK_BUT_ACTUAL_REST_AND_DYNAMIC_VISUAL_FAIL'
q['formalArtMeshAccepted']=False;q['formalKeyframeAccepted']=False
q['next']='P15-82 create true occluded clean forehead/eyelash underlay matching SAM3-027 bangs, fix real 0px before dynamic 9/18; do not use old SAM or claim Qwen Image Layered succeeded.'
(R/'evidence/p15-81-sam3-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'mask027':q['masks']['027'],'mask083':q['masks']['083']},ensure_ascii=False)[:4000])

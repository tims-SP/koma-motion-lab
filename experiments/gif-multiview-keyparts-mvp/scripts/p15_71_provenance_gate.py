#!/usr/bin/env python3
"""P15-71 real provenance/semantic gate: same-view hair unavailable, SAM2 inference blocked."""
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw
import json,hashlib
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-71-sam-semantic';D.mkdir(parents=True,exist_ok=True)
src=R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'
p69=R/'private-assets/exports/p15-69-clip-separation/hair-front-no-gold-candidate.png'
p70=R/'private-assets/exports/p15-70-seam-repair/eye-shift-18-seam-repaired.png'
inputs={
 'yaw045':R/'private-assets/p15-20-canonical-source-views/yaw045/hair.front.png',
 'yaw090':R/'private-assets/p15-20-canonical-source-views/yaw090/hair.front.png',
 'prior41':R/'private-assets/exports/p15-41-profile-candidate/layers/hair.front.png'
}
source=Image.open(src).convert('RGBA')
old=Image.open(p69).convert('RGBA')
alpha=old.getchannel('A')
# Inspect a fixed face/bangs crop and the actual independent donor masks.
crop=(395,100,855,630)
def save_crop(im,stem):
 im.crop(crop).resize((690,795),Image.Resampling.LANCZOS).save(D/(stem+'.png'))
save_crop(source,'current-right-source')
save_crop(old,'p15-69-color-layer')
save_crop(Image.open(p70).convert('RGBA'),'p15-70-composite')
for k,p in inputs.items():
 donor=Image.open(p).convert('RGBA')
 save_crop(donor,f'prior-{k}-layer')
 # Direct overlay at unmodified anchor reveals incorrect silhouette/texture.
 mix=Image.alpha_composite(source,donor)
 save_crop(mix,f'prior-{k}-overlay')
# Distinguish genuine approved same-view source from mere transparent pixels.
p71=json.loads((R/'evidence/p15-71-sam-probe.json').read_text())
p71all=json.loads((R/'evidence/p15-71-sam-everything.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
q={
 'schema':'KOMA-P15-71-FRONT_HAIR_SOURCE_GATE_V1',
 'characterId':'p0_character_001',
 'baselineCommit':'b69f9d250e888fd5e072d9fba6aa779b85ee9e9e',
 'currentSourceSHA256':sha(src),
 'colorLayerSHA256':sha(p69),
 'p15_70CompositeSHA256':sha(p70),
 'legacyIndependentHairSHA256':{k:sha(p) for k,p in inputs.items()},
 'legacySourcesAreSameP156Source':False,
 'sam2InputSHA256':sha(D/'input-512.png'),
 'sam2EndpointStatus':{'on_image_select':p71['status'],'segment_everything':p71all['status']},
 'sam2SegmentEverythingError':p71all.get('error',''),
 'sam2VisibleCutoutProduced':bool(list(D.glob('sam-output-*.png'))),
 'sameViewCleanFrontHairAvailable':False,
 'fullFrontHairSegmentationApproved':False,
 'fullHairHiddenUnderpaintAvailable':False,
 'movementOffsetsAvailable':[0,9,18],
 'visualAssessment':'The existing full hair is a visible chroma matte containing a horizontal grey-purple forehead line and incomplete true eye-overlap strands. Older independent frontal/profile PSD layers are different camera views or source composites and fail exact P15-56 provenance. SAM2 prompt attempted; click returned generic backend failure and segment-everything returned ZeroGPU quota exhausted.',
 'visualGate':'FAIL_NO_SAME_VIEW_SEMANTIC_HAIR_SOURCE_SAM2_COMPUTE_BLOCKED',
 'formalArtMeshAccepted':False,'formalKeyframeAccepted':False,
 'next':'Acquire or render a true clean same-view hair alpha through an available semantic segmentation service or independent same-pose layered drawing; do not optimize color thresholds further.'
}
(R/'evidence/p15-71-source-gate-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'sourcesCompared':len(inputs),'sam2':q['sam2EndpointStatus'],'semanticAccepted':False,'files':len(list(D.glob('*.png')))}))

#!/usr/bin/env python3
"""Same-source near-eye upper-lash sublayer: honest geometric split, no new artwork claim."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageChops,ImageFilter
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-77-art-layer';D.mkdir(exist_ok=True,parents=True)
files={
 'source':P/'p15-56-edge-matting/candidate-erode-2.png',
 'eye':P/'p15-65-eyelid-refinement/eye.near.refined-layer.png',
 'base':P/'p15-70-seam-repair/forehead-seam-repaired.png',
 'clip':P/'p15-69-clip-separation/hair-clip-gold-independent.png'}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
im={key:Image.open(f).convert('RGBA') for key,f in files.items()}
eye=im['eye']
# Following geometry is manually specified using the current same-view eye,
# not a semantic learned edge. It encloses most upper eyeliner/lash silhouettes.
polygon=[(519,454),(521,447),(529,437),(545,427),(561,423),(587,419),
 (610,419),(632,423),(645,430),(651,441),(654,451),(645,457),
 (633,449),(615,443),(593,439),(566,439),(547,447),(533,458),(525,463)]
mask=Image.new('L',eye.size,0);ImageDraw.Draw(mask).polygon(polygon,fill=255)
# Restrict the mask to actual current eye alpha, avoid unrelated pixels.
alpha=eye.getchannel('A');mask=ImageChops.multiply(mask,alpha.point(lambda v:255 if v>0 else 0))
raw=eye.tobytes();m=mask.tobytes()
lash=bytearray(raw);lower=bytearray(raw)
for i,v in enumerate(m):
 if v:lower[4*i+3]=0
 else:lash[4*i+3]=0
lash_im=Image.frombytes('RGBA',eye.size,bytes(lash))
lower_im=Image.frombytes('RGBA',eye.size,bytes(lower))
lash_im.save(D/'eye.upper-lash.same-view.png')
lower_im.save(D/'eye.iris-lower.same-view.png')
mask.save(D/'eye.upper-lash-selection.png')
# Reconstruct original independent eye exactly by picking one source pixel
# for each raster position. Pillow RGBA alpha_composite may differ in fully
# transparent RGB, so verify visible texture on white matte as well.
reconstructed=Image.alpha_composite(lower_im,lash_im)
reconstructed.save(D/'eye.reconstructed-layer-composite.png')
same_alpha=(ImageChops.difference(alpha,reconstructed.getchannel('A')).getbbox() is None)
diff=ImageChops.difference(eye,reconstructed)
diff_bbox=diff.getbbox()
rgb_visible_diff=sum(eye.getpixel((x,y))[:3]!=reconstructed.getpixel((x,y))[:3]
  for y in range(420,502) for x in range(518,655) if eye.getpixel((x,y))[3]>0)
# Build a same-frame verification on current visual baseline; use existing
# P15-76 pose as unchanged reference, and layer split only as diagnostic.
for name,layer in [('lash',lash_im),('iris',lower_im)]:
 layer.crop((490,390,695,535)).resize((820,580),Image.Resampling.LANCZOS).save(D/f'{name}-close.png')
source=im['source']
for dx in [0,9,18]:
 # Keep exact motion baseline from P15-76 rather than silently modifying artwork.
 frame=Image.open(P/f'p15-76-seam-source/eye-shift-{dx:02d}.png').convert('RGBA')
 frame.save(D/f'baseline-{dx:02d}.png')
# Show old mismatched donors using actual comparisons from P15-77 source probe.
q={'schema':'KOMA-P15-77-SOURCE_LASH_GEOMETRIC_SPLIT_V1',
 'characterId':'p0_character_001','sourcesSHA256':{k:sha(v) for k,v in files.items()},
 'lashLayerSHA256':sha(D/'eye.upper-lash.same-view.png'),
 'irisLayerSHA256':sha(D/'eye.iris-lower.same-view.png'),
 'maskSHA256':sha(D/'eye.upper-lash-selection.png'),
 'maskBBox':list(mask.getbbox()),'upperLashVisiblePixels':sum(v>0 for v in lash_im.getchannel('A').getdata()),
 'lowerEyeVisiblePixels':sum(v>0 for v in lower_im.getchannel('A').getdata()),
 'sameEyeAlphaAfterSplit':same_alpha,'eyeRecompositeDiffBBox':list(diff_bbox) if diff_bbox else None,
 'eyeVisibleRGBDiffPixels':rgb_visible_diff,
 'method':'MANUALLY_GEO_BOUND_SPLIT_CURRENT_P15_65_EYE_ART_NOT_TRUE_SEMANTIC_TRACING',
 'olderYaw45DonorsAccepted':False,'olderFrontDonorsAccepted':False,
 'newSourceConsistentEyeUpperLashLayerExists':True,
 'currentFullHairSemanticApproved':False,'dynamicVisualGatePassed':False,
 'formalArtMeshAccepted':False,'formalKeyframeAccepted':False,
 'visualGate':'LOCAL_EYE_COMPONENT_SPLIT_AVAILABLE_FULL_BANG_INTERSECTION_UNRESOLVED',
 'next':'P15-78 refine upper-lash strand boundary to eliminate hard polygon, then test moving eye-under-lash against actual front hair at 9/18 with 0px source identity preserved'}
(R/'evidence/p15-77-layer-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'upperLashPixels':q['upperLashVisiblePixels'],'lowerEyePixels':q['lowerEyeVisiblePixels'],'bbox':q['maskBBox'],'sameAlpha':same_alpha,'visibleRGBDiff':rgb_visible_diff,'diffBBox':q['eyeRecompositeDiffBBox']}))

#!/usr/bin/env python3
"""Remove eye contamination from full-area hair trial; preserve transparent edge evidence."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFilter,ImageChops
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-67-front-hair'
S=Image.open(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png').convert('RGBA')
B=Image.open(R/'private-assets/exports/p15-63-masked-lama/underpaint-full.png').convert('RGBA')
E=Image.open(R/'private-assets/exports/p15-65-eyelid-refinement/eye.near.refined-layer.png').convert('RGBA')
original=Image.open(D/'hair.front.full-area-mask.png').convert('L')
# Protect both eyes: remove directly assigned near-eye RGBA and the far-eye
# region. This is conservative, and also sacrifices real strands overlapping eyes.
exclude=Image.new('L',S.size,0)
ex=ImageDraw.Draw(exclude)
ex.ellipse((525,414,653,514),fill=255)
ex.ellipse((691,411,757,519),fill=255)
exclude=exclude.filter(ImageFilter.GaussianBlur(2.0))
keep=ImageChops.invert(exclude)
# Avoid the visibly amputated upper-left cut edge: this remains a candid
# failure, not silently replacing the missing left-side hair with fake art.
clean=ImageChops.multiply(original,keep)
clean=clean.filter(ImageFilter.GaussianBlur(.6))
out=Image.new('RGBA',S.size)
out.paste(S,(0,0),clean)
out.save(D/'hair.front.eye-excluded-v2.png')
clean.save(D/'hair.front.eye-excluded-mask.png')
frames=[]
for dx in (0,9,18):
 moved=Image.new('RGBA',S.size);moved.alpha_composite(E,(dx,0))
 combined=Image.alpha_composite(Image.alpha_composite(B,moved),out)
 combined.save(D/f'eye-shift-{dx:02d}-v2.png')
 combined.crop((445,265,795,605)).resize((700,680),Image.Resampling.LANCZOS).save(D/f'eye-shift-{dx:02d}-v2-face.png')
 frames.append({'dx':dx,'image':f'eye-shift-{dx:02d}-v2.png'})
alpha=out.getchannel('A')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
qa=json.loads((R/'evidence/p15-67-front-hair-qa.json').read_text())
qa.update({
 'refinedEyeExcludedSHA256':sha(D/'hair.front.eye-excluded-v2.png'),
 'refinedMaskSHA256':sha(D/'hair.front.eye-excluded-mask.png'),
 'eyeExcludedLayerBBox':list(alpha.getbbox()),
 'eyeExcludedNonzeroAlphaPixels':sum(v>0 for v in alpha.getdata()),
 'eyeExcludedPartialAlphaPixels':sum(0<v<255 for v in alpha.getdata()),
 'refinedFrames':frames,
 'eyeRegionExclusionMethod':'COARSE_NEAR_FAR_EYE_ELLIPSE_VISUAL_QA_ONLY',
 'eyePixelsConservativelyExcluded':True,
 'frontBangOcclusionPreservedAcrossEyes':False,
 'fullHairTopologyMatched':False,
 'hiddenForeheadSkinIndependentlyReconstructed':False,
 'actualVisualFailures':['top-left hair cap sheared by coarse envelope',
   'hair texture and facial pigment cannot be separated cleanly from a flat composite',
   'exclusion of eye regions also removes real overlapping bang strands',
   'hidden forehead/roots behind movable front hair remain absent'],
 'visualGate':'FAIL_FULL_FRONT_HAIR_MATTE_SEMANTICS_AND_HIDDEN_UNDERPAINT',
 'formalArtMeshAccepted':False,'formalKeyframeAccepted':False,
 'next':'Stop color-only extraction. Obtain genuine semantic hair alpha with manual strand boundary correction and independent hidden forehead underpaint before treating hair as a deformable ArtMesh.'
})
(R/'evidence/p15-67-front-hair-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'fullHairV1Pixels':qa['visiblePixels'],'v2Pixels':qa['eyeExcludedNonzeroAlphaPixels'],'maskBBox':qa['eyeExcludedLayerBBox'],'gate':qa['visualGate']}))

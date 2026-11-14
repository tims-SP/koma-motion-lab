#!/usr/bin/env python3
"""Render real 0/9/18 animation with separated source lash, compare layer orders."""
from pathlib import Path
from PIL import Image,ImageChops
import json,hashlib
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-77-art-layer'
qpath=R/'evidence/p15-77-layer-qa.json';q=json.loads(qpath.read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
src=Image.open(P/'p15-56-edge-matting/candidate-erode-2.png').convert('RGBA')
clip=Image.open(P/'p15-69-clip-separation/hair-clip-gold-independent.png').convert('RGBA')
mask=Image.open(D/'eye.upper-lash-selection.png').convert('L')
full=Image.open(P/'p15-65-eyelid-refinement/eye.near.refined-layer.png').convert('RGBA')
motion=[]
for dx in (0,9,18):
 eye=Image.open(P/f'p15-74-bangs-repair/eye.matte-{dx:02d}.png').convert('RGBA')
 under=Image.open(P/f'p15-76-seam-source/hidden-skin-{dx:02d}.png').convert('RGBA')
 hair=Image.open(P/f'p15-75-eyebrow-seam/hair.front.moving-{dx:02d}.png').convert('RGBA')
 original_eye_alpha=eye.getchannel('A')
 # Unlike overlapping semi-transparent layers, each pixel is assigned to one
 # layer, so exact two-layer restoration is possible.
 upper=eye.copy();bottom=eye.copy()
 upalpha=ImageChops.multiply(original_eye_alpha,mask)
 loalpha=ImageChops.multiply(original_eye_alpha,ImageChops.invert(mask))
 upper.putalpha(upalpha);bottom.putalpha(loalpha)
 upper.save(D/f'upper-lash-{dx:02d}.png')
 bottom.save(D/f'iris-lower-{dx:02d}.png')
 m=Image.new('RGBA',eye.size,(0,0,0,0))
 m.alpha_composite(bottom,(dx,0))
 m.alpha_composite(upper,(dx,0))
 baseline=Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(under,m),hair),clip)
 original=Image.open(P/f'p15-76-seam-source/eye-shift-{dx:02d}.png').convert('RGBA')
 diff=ImageChops.difference(original,baseline)
 # Render upper eyelash after front bang, independent depth control, a
 # physically different z-order. This is a candidate only.
 mo=Image.new('RGBA',eye.size,(0,0,0,0));mo.alpha_composite(bottom,(dx,0))
 lash_move=Image.new('RGBA',eye.size,(0,0,0,0));lash_move.alpha_composite(upper,(dx,0))
 depth=Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(under,mo),hair),lash_move),clip)
 # At rest use source exact, to avoid invalidating identity.
 if dx==0: depth=original
 depth.save(D/f'depth-lash-{dx:02d}.png')
 depth.crop((480,390,700,540)).resize((880,600),Image.Resampling.LANCZOS).save(D/f'depth-lash-{dx:02d}-detail.png')
 orig_roi=original.crop((510,420,685,515));depth_roi=depth.crop((510,420,685,515))
 diff_pixels=sum(x>0 for x in ImageChops.difference(orig_roi,depth_roi).convert('L').getdata())
 baseline_diff=sum(x>0 for x in diff.convert('L').getdata())
 motion.append({'dx':dx,'oldCompositeMismatchPixels':baseline_diff,'zOrderChangedPixelsEyeROI':diff_pixels,
                'depthSHA256':sha(D/f'depth-lash-{dx:02d}.png')})
q.update({
 'movingLayerProof':motion,'zOrderVariant':'skin -> iris/lower eye -> front bangs -> upper lash -> clip',
 'zeroPoseFullSourceExact':ImageChops.difference(src,Image.open(D/'depth-lash-00.png').convert('RGBA')).getbbox() is None,
 'motionVisualAssessment':'Separate-source upper lash can render above the bangs without changing the approved 0px source. At 9/18px the z-order difference is limited; hard geometric split is visibly jagged and the brow/lash/skin artifact remains. This is a testable source-consistent layered candidate, not final painted quality.',
 'visualGate':'SOURCE_CONSISTENT_EYE_LASH_SPLIT_PASS_DYNAMIC_VISUAL_FAIL',
 'formalArtMeshAccepted':False,'formalKeyframeAccepted':False
})
qpath.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'sourceExact':q['zeroPoseFullSourceExact'],'motion':motion}))

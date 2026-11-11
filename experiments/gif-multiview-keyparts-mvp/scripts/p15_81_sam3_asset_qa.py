#!/usr/bin/env python3
"""Validate actual SAM3 text masks on P15-56, strict identity/rest and dynamic realism."""
from pathlib import Path
from PIL import Image,ImageFilter,ImageChops,ImageDraw
import hashlib,json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-81-image-layered'
srcp=P/'p15-56-edge-matting/candidate-erode-2.png';original=Image.open(srcp).convert('RGBA')
eye=Image.open(P/'p15-65-eyelid-refinement/eye.near.refined-layer.png').convert('RGBA')
base=Image.open(P/'p15-70-seam-repair/forehead-seam-repaired.png').convert('RGBA')
clip=Image.open(P/'p15-69-clip-separation/hair-clip-gold-independent.png').convert('RGBA')
oldhair=Image.open(P/'p15-74-bangs-repair/hair.front.alpha-dedup.png').convert('RGBA')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
crop=(150,45,850,745);cw,ch=700,700
assets={}
for name in ('027','083'):
 m=Image.open(D/f'sam3-mask-{name}.png').getchannel('A').resize((cw,ch),Image.Resampling.BILINEAR)
 m=m.filter(ImageFilter.GaussianBlur(.4))
 full=Image.new('L',original.size,0);full.paste(m,(crop[0],crop[1]))
 src_alpha=original.getchannel('A')
 final_alpha=ImageChops.multiply(src_alpha,full)
 h=original.copy();h.putalpha(final_alpha)
 mpath=D/f'sam3-{name}-aligned-alpha.png';full.save(mpath)
 hpath=D/f'sam3-{name}-hair-rgba.png';h.save(hpath)
 # Diagnostic baseline and real zero-pose compositing using actual underpaint.
 out=Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(base,eye),h),clip)
 opath=D/f'sam3-{name}-rest-composite.png';out.save(opath)
 diff=ImageChops.difference(original,out)
 diff_box=diff.getbbox()
 # True fixed-source extraction of same pixels: exact restoration by
 # alpha complement, but not equivalent to an inpainted hidden underlay.
 complement=original.copy()
 m0=full.point(lambda v:255 if v>127 else 0)
 complement.putalpha(ImageChops.multiply(src_alpha,ImageChops.invert(m0)))
 hm=original.copy();hm.putalpha(ImageChops.multiply(src_alpha,m0))
 # Since RGB is from the same source, exact roundtrip only if binary mask.
 recomposed=Image.alpha_composite(complement,hm)
 math_bbox=ImageChops.difference(original,recomposed).getbbox()
 assets[name]={
  'rawMaskSHA256':sha(D/f'sam3-mask-{name}.png'),
  'alignedMaskSHA256':sha(mpath),'hairSHA256':sha(hpath),
  'maskOriginalPixels':sum(v>0 for v in Image.open(D/f'sam3-mask-{name}.png').getchannel('A').getdata()),
  'alignedAlphaPixels':sum(v>0 for v in final_alpha.getdata()),
  'alignedBBox':list(final_alpha.getbbox()) if final_alpha.getbbox() else None,
  'actualRestPoseDiffBBox':list(diff_box) if diff_box else None,
  'mathComplementRestDiffBBox':list(math_bbox) if math_bbox else None}
 # Moving eye; same original hair image, no pose-dependent alpha patching
 for dx in (9,18):
  under=Image.open(P/f'p15-76-seam-source/hidden-skin-{dx:02d}.png').convert('RGBA')
  em=Image.open(P/f'p15-74-bangs-repair/eye.matte-{dx:02d}.png').convert('RGBA')
  moved=Image.new('RGBA',original.size);moved.alpha_composite(em,(dx,0))
  frame=Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(under,moved),h),clip)
  frame.save(D/f'sam3-{name}-motion-{dx:02d}.png')
  frame.crop((445,265,795,605)).resize((700,680),Image.Resampling.LANCZOS).save(D/f'sam3-{name}-motion-{dx:02d}-face.png')
  assets[name][f'dynamic{dx}SHA256']=sha(D/f'sam3-{name}-motion-{dx:02d}.png')
 out.crop((445,265,795,605)).resize((700,680),Image.Resampling.LANCZOS).save(D/f'sam3-{name}-rest-face.png')
# UI review overlay each mask on the source; no labels that falsely claim approval.
for name in ('027','083'):
 a=Image.open(D/f'sam3-{name}-aligned-alpha.png').convert('L')
 tint=Image.new('RGBA',original.size,(0,196,87,0));tint.putalpha(a.point(lambda x:round(x*.35)))
 Image.alpha_composite(original,tint).crop((150,45,850,745)).save(D/f'sam3-{name}-overlay.png')
qa={
 'schema':'KOMA-P15-81-AUTH_SAM3_SEMANTIC_ASSET_QA_V1',
 'characterId':'p0_character_001',
 'sourceSHA256':sha(srcp),'inputSHA256':sha(D/'input-head-640.png'),
 'provider':'prithivMLmods/SAM3-Demo','authAttemptSucceeded':True,
 'maskClass':'front bangs hair fringe on forehead','masks':assets,
 'referenceP1574HairSHA256':sha(P/'p15-74-bangs-repair/hair.front.alpha-dedup.png'),
 'sourcePixelRGBPreserved':True,
 'resultsAreRawModelSemanticMasks':True,'hiddenUnderpaintGenerated':False,
 'realRestPoseExact':False,
 'formalArtMeshAccepted':False,'formalKeyframeAccepted':False,
 'visualGate':'SAM3_TEXT_MASK_RETURNED_BUT_REST_POSE_AND_SEMANTIC_QUALITY_PENDING',
}
(R/'evidence/p15-81-sam3-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(assets,ensure_ascii=False,indent=2))

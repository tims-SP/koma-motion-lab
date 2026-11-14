#!/usr/bin/env python3
"""Generate an honest full-area front hair matting candidate and expose missing underpaint."""
from PIL import Image,ImageDraw,ImageFilter,ImageChops
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-67-front-hair';D.mkdir(parents=True,exist_ok=True)
SRC=R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'
OLD=R/'private-assets/exports/p15-41-profile-candidate/layers/hair.front.png'
BG=R/'private-assets/exports/p15-63-masked-lama/underpaint-full.png'
EYE=R/'private-assets/exports/p15-65-eyelid-refinement/eye.near.refined-layer.png'
source=Image.open(SRC).convert('RGBA')
under=Image.open(BG).convert('RGBA')
old=Image.open(OLD).convert('RGBA')
eye=Image.open(EYE).convert('RGBA')
w,h=source.size
# Hand-drawn coarse semantic envelope is a *candidate* boundary; chroma classifier
# retains textured pink hair and excludes most exposed forehead and eye pixels.
envelope=[
 (445,106),(535,107),(616,115),(694,153),(742,218),(771,295),
 (790,376),(777,458),(754,537),(723,571),(693,573),(658,544),
 (628,537),(596,560),(556,548),(531,505),(503,460),(481,396),
 (454,340),(437,270),(435,193)
]
roi=Image.new('L',(w,h),0)
ImageDraw.Draw(roi).polygon(envelope,fill=255)
roip=roi.load();pix=source.load();mask=Image.new('L',(w,h),0);mp=mask.load()
for y in range(100,586):
 for x in range(425,795):
  if not roip[x,y]:continue
  r,g,b,a=pix[x,y]
  if a<32:continue
  chrom=b-g
  pink=r-g
  # Skin is typically blue <= green, whereas plum hair is blue > green.
  chrom_alpha=max(0,min(1,(chrom-4)/18))
  pink_alpha=max(0,min(1,(pink-14)/18))
  # Upper hair occupies many dark ink strands, not just its rosy interior.
  top_conf=0.95 if y<336 and x>480 else 0.0
  confidence=max(top_conf,chrom_alpha*pink_alpha)
  mp[x,y]=int(255*confidence*a/255)
# preserve gradual strand boundaries without hard-edged flat polygons
mask=mask.filter(ImageFilter.MedianFilter(3)).filter(ImageFilter.GaussianBlur(1.2))
layer=Image.new('RGBA',(w,h),(0,0,0,0))
layer.paste(source,(0,0),mask)
mask.save(D/'hair.front.full-area-mask.png')
layer.save(D/'hair.front.full-area-candidate.png')
# Failed attempted underpaint is evaluated by comparing original source to
# original after removing new foreground; no synthesized forehead is invented.
residual=Image.composite(Image.new('RGBA',(w,h)),source,mask)
residual.save(D/'remaining-visible-with-hair-hole.png')
# Compose the full-area front layer over old inpainted portrait and moving eye.
frames=[]
for dx in [0,9,18]:
 moved=Image.new('RGBA',(w,h));moved.alpha_composite(eye,(dx,0))
 base=Image.alpha_composite(under,moved)
 withhair=Image.alpha_composite(base,layer)
 withhair.save(D/f'eye-shift-{dx:02d}-full-hair.png')
 base.save(D/f'eye-shift-{dx:02d}-no-full-hair.png')
 withhair.crop((445,265,795,605)).resize((700,680),Image.Resampling.LANCZOS).save(D/f'eye-shift-{dx:02d}-face.png')
 frames.append({'shiftPx':dx,'fullHairFile':f'eye-shift-{dx:02d}-full-hair.png'})
# Composite the layer over original source; if independent hair is clean,
# it should not color-shift pixels at rest, but strong changes reveal contaminated edges.
recomp=Image.alpha_composite(source,layer)
difference=ImageChops.difference(recomp.convert('RGB'),source.convert('RGB')).convert('L')
changed=sum(i>7 for i in difference.getdata())
mask_a=layer.getchannel('A')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
report={
 'schema':'KOMA-P15-67-FULL_FRONT_HAIR_FEASIBILITY_V1',
 'characterId':'p0_character_001',
 'sourceSHA256':sha(SRC),'oldHairSHA256':sha(OLD),
 'underpaintSHA256':sha(BG),'eyeLayerSHA256':sha(EYE),
 'method':'HAND_ENVELOPE_CHROMA_MATTE_VISIBLE_PIXELS_ONLY',
 'fullHairCandidateSHA256':sha(D/'hair.front.full-area-candidate.png'),
 'maskSHA256':sha(D/'hair.front.full-area-mask.png'),
 'newLayerBBox':list(mask_a.getbbox()),
 'visiblePixels':sum(v>0 for v in mask_a.getdata()),
 'alphaPartials':sum(0<v<255 for v in mask_a.getdata()),
 'recomposeChangedPixelsOverSource':changed,
 'originalHiddenForeheadUnderpaintAvailable':False,
 'trueIndependentPaintedHair':False,'semanticHairPurityVerified':False,
 'candidateFrames':frames,
 'formalArtMeshAccepted':False,'formalKeyframeAccepted':False,
 'visualGate':'PENDING_DIRECT_INSPECTION'
}
(R/'evidence/p15-67-front-hair-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['newLayerBBox','visiblePixels','alphaPartials','recomposeChangedPixelsOverSource']}))

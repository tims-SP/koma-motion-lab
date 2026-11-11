#!/usr/bin/env python3
"""P15-69 diagnostic: split gold clip once, restore eye-less base; never mislabel full hair as accepted."""
import json,hashlib
from pathlib import Path
from PIL import Image,ImageChops,ImageFilter
R=Path(__file__).resolve().parents[1];P=R/'private-assets';D=P/'exports/p15-69-clip-separation';D.mkdir(parents=True,exist_ok=True)
src=P/'exports/p15-56-edge-matting/candidate-erode-2.png'
base68=P/'exports/p15-68-forehead/forehead-neural-underpaint.png'
clipfree=P/'exports/p15-55-registration/underlay--28.png'
eyeunder=P/'exports/p15-63-masked-lama/underpaint-full.png'
eyemask=P/'exports/p15-63-masked-lama/mask-full.png'
hairfile=P/'exports/p15-67-front-hair/hair.front.eye-excluded-v2.png'
eyefile=P/'exports/p15-65-eyelid-refinement/eye.near.refined-layer.png'
clipfile=P/'exports/p15-56-edge-matting/clip-erode-2.png'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
srcim=Image.open(src).convert('RGBA');b=Image.open(base68).convert('RGBA')
clean=Image.open(clipfree).convert('RGBA');eyebase=Image.open(eyeunder).convert('RGBA')
eye=Image.open(eyefile).convert('RGBA');hair=Image.open(hairfile).convert('RGBA')
clip=Image.open(clipfile).convert('RGBA')
# Gold clip fixture originally separately reconstructed P15-55. Dilate its alpha
# for a clean radius, then feather only to blend source underlay to inpainted base.
clipmask=clip.getchannel('A').point(lambda a:255 if a>14 else 0)
clipguard=clipmask.filter(ImageFilter.MaxFilter(35)).filter(ImageFilter.GaussianBlur(3))
clipguard.save(D/'clip-cleanup-guard.png')
# replace inherited partly removed gold clip in neural forehead base with the actual
# P15-55 hair underlay; the clip is drawn once at the very end.
b=Image.composite(clean,b,clipguard)
# Erase embedded eye in P15-68 base so moving eye doesn't duplicate static iris.
em=Image.open(eyemask).convert('L')
b=Image.composite(eyebase,b,em)
b.save(D/'clip-and-eye-free-underpaint.png')
# Prevent P15-67 hair candidate from carrying its own gold fixture pixels.
a=hair.getchannel('A')
newa=ImageChops.multiply(a,ImageChops.invert(clipguard.point(lambda v:255 if v>0 else 0)))
hair.putalpha(newa)
hair.save(D/'hair-front-no-gold-candidate.png')
# Transparent clip on its own, placed in highest depth.
clip.save(D/'hair-clip-gold-independent.png')
frames=[]
for dx in (0,9,18):
 moved=Image.new('RGBA',b.size);moved.alpha_composite(eye,(dx,0))
 image=Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(b,moved),hair),clip)
 name=f'eye-shift-{dx:02d}-clip-once.png'
 image.save(D/name)
 image.crop((445,265,795,605)).resize((700,680),Image.Resampling.LANCZOS).save(D/f'eye-shift-{dx:02d}-face.png')
 frames.append({'dx':dx,'file':name,'sha256':sha(D/name)})
# comparison P15-68 saved image
old=Image.open(P/'exports/p15-68-forehead/with-hair-eye-18.png').convert('RGBA')
for label,im in [('original',srcim),('old68',old),('new69',Image.open(D/'eye-shift-18-clip-once.png').convert('RGBA'))]:
 im.crop((630,245,800,445)).resize((510,600),Image.Resampling.LANCZOS).save(D/(label+'-clip-compare.png'))
 im.crop((445,265,795,605)).resize((700,680),Image.Resampling.LANCZOS).save(D/(label+'-face-compare.png'))
# Determine how much clip-like yellow remains in hair before/after:
def yellow_in(img):
 rgba=img.convert('RGBA'); pixels=rgba.crop((675,270,770,388)).getdata()
 return sum(a>100 and r>140 and g>95 and r>b*1.1 and g>b*1.15 for r,g,b,a in pixels)
prior=Image.open(hairfile).convert('RGBA')
oldyellow=yellow_in(prior);newyellow=yellow_in(hair)
# baseline inpainted eye mask no static iris: check exact pixel provenance within eye region
replaced_count=sum(v>0 for v in em.getdata())
report={'schema':'KOMA-P15-69-CLIP_SINGLE_DRAW_V1',
 'characterId':'p0_character_001',
 'sourceSHA256':sha(src),'foreheadBaseSHA256':sha(base68),
 'cleanClipUnderlaySHA256':sha(clipfree),'neuralEyeUnderpaintSHA256':sha(eyeunder),
 'nearEyeMaskSHA256':sha(eyemask),'rawHairSHA256':sha(hairfile),
 'independentClipSHA256':sha(clipfile),'eyeLayerSHA256':sha(eyefile),
 'clipGuardSHA256':sha(D/'clip-cleanup-guard.png'),
 'cleanedBackgroundSHA256':sha(D/'clip-and-eye-free-underpaint.png'),
 'cleanedHairSHA256':sha(D/'hair-front-no-gold-candidate.png'),
 'hairYellowPixelsBefore':oldyellow,'hairYellowPixelsAfter':newyellow,
 'eyeCleanupMaskPixels':replaced_count,
 'zOrder':['forehead_neural_base_with_clip_removed_and_eyeless_skin','moving_near_eye','color_derived_front_hair_clip_excluded','independent_gold_clip_once'],
 'frames':frames,'fullHairSemanticIdentityVerified':False,
 'originalHeadPaintingChanged':False,'formalArtMeshAccepted':False,'formalKeyframeAccepted':False,
 'visualGate':'PENDING_VISUAL_INSPECTION'}
assert oldyellow>newyellow
(R/'evidence/p15-69-clip-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'yellowBefore':oldyellow,'yellowAfter':newyellow,'eyeMaskPixels':replaced_count,'frames':[f['dx'] for f in frames]}))

#!/usr/bin/env python3
"""Local moving-pose occluder suppression; preserve exact rest pose, reject fake skin-paint patches."""
from pathlib import Path
from PIL import Image,ImageFilter,ImageDraw,ImageChops
import json,hashlib
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-75-eyebrow-seam';D.mkdir(parents=True,exist_ok=True)
srcp=P/'p15-56-edge-matting/candidate-erode-2.png'
basep=P/'p15-70-seam-repair/forehead-seam-repaired.png'
eyep=P/'p15-65-eyelid-refinement/eye.near.refined-layer.png'
hairp=P/'p15-74-bangs-repair/hair.front.alpha-dedup.png'
clipp=P/'p15-69-clip-separation/hair-clip-gold-independent.png'
src=Image.open(srcp).convert('RGBA');base=Image.open(basep).convert('RGBA')
eye=Image.open(eyep).convert('RGBA');hair=Image.open(hairp).convert('RGBA')
clip=Image.open(clipp).convert('RGBA')
old=Image.open(P/'p15-74-bangs-repair/eye-shift-18.png').convert('RGBA')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
# Only target the incorrectly copied near-eye/eyebrow patch inside the SAM hair layer.
# This guard is pose-dependent, not a new semantic hair layer.
pts=[(513,442),(541,419),(577,416),(604,432),(604,445),(560,461),(536,478),(513,467)]
guard=Image.new('L',src.size,0)
ImageDraw.Draw(guard).polygon(pts,fill=255)
guard=guard.filter(ImageFilter.GaussianBlur(5))
guard.save(D/'dynamic-suppression-guard.png')
# P15-74's eye-eroded alpha is reused; do not shift/repaint approved source identity.
frames=[]
for dx in (0,9,18):
 weight=dx/18
 active=guard.point(lambda x:int(x*weight))
 alpha=ImageChops.multiply(hair.getchannel('A'),ImageChops.invert(active))
 dynamic_hair=hair.copy();dynamic_hair.putalpha(alpha)
 dynamic_hair.save(D/f'hair.front.moving-{dx:02d}.png')
 eye_alpha=Image.open(P/f'p15-74-bangs-repair/eye.matte-{dx:02d}.png').convert('RGBA')
 move=Image.new('RGBA',src.size);move.alpha_composite(eye_alpha,(dx,0))
 output=Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(base,move),dynamic_hair),clip)
 outpath=D/f'eye-shift-{dx:02d}.png';output.save(outpath)
 output.crop((445,265,795,605)).resize((700,680),Image.Resampling.LANCZOS).save(D/f'eye-shift-{dx:02d}-face.png')
 output.crop((490,390,700,540)).resize((840,600),Image.Resampling.LANCZOS).save(D/f'eye-shift-{dx:02d}-detail.png')
 frames.append({'dx':dx,'sha256':sha(outpath),'hairSHA256':sha(D/f'hair.front.moving-{dx:02d}.png')})
assert ImageChops.difference(src,Image.open(D/'eye-shift-00.png').convert('RGBA')).getbbox() is None
old_crop=old.crop((490,390,700,540))
new_crop=Image.open(D/'eye-shift-18.png').convert('RGBA').crop((490,390,700,540))
old_crop.resize((840,600),Image.Resampling.LANCZOS).save(D/'p15-74-before-detail.png')
diff=ImageChops.difference(old_crop,new_crop)
diff.resize((840,600),Image.Resampling.LANCZOS).save(D/'delta-18-detail.png')
region=(510,425,685,530);holes={}
for dx in [0,9,18]:
 o=Image.open(D/f'eye-shift-{dx:02d}.png').convert('RGBA')
 holes[str(dx)]=sum(x>128 and y<32 for x,y in zip(src.getchannel('A').crop(region).getdata(),o.getchannel('A').crop(region).getdata()))
assert holes=={'0':0,'9':0,'18':0}
diff_pixels=sum(v>0 for v in diff.convert('L').getdata())
q={
 'schema':'KOMA-P15-75-MOVING-HAIR-SUPPRESSION-V1','characterId':'p0_character_001',
 'sourceSHA256':sha(srcp),'baseSHA256':sha(basep),'eyeSHA256':sha(eyep),
 'hairSHA256':sha(hairp),'clipSHA256':sha(clipp),
 'guardSHA256':sha(D/'dynamic-suppression-guard.png'),
 'method':'POSE_WEIGHTED_LOCAL_HAIR_ALPHA_SUPPRESSION_NOT_SEMANTIC_MATTE',
 'sourceUnchanged':True,'guardPolygon':pts,'guardBlurPx':5,
 'zeroPosePixelExact':True,'frameHashes':frames,
 'changedRGBOrAlphaPixelsAt18InDetail':diff_pixels,'transparentHoleCounts':holes,
 'rejectedCandidateExperiments':['solid_skin_color_patch_due_to_obvious_flat_polygon','overwide_hair_suppression_due_to_loss_of_real_strands'],
 'visualAssessment':'Moving-pose suppression reduces the broad reddish edge block at the eye outer corner and suppresses part of the dashed lash/forehead contamination. Remaining thin dotted marks and eye-to-bang seam are still visible at enlarged 18px, and the correction is not true semantic separation.',
 'visualGate':'LOCAL_MOVING_ARTIFACT_REDUCED_BUT_SEMANTIC_HAIR_VISUAL_FAIL',
 'formalArtMeshAccepted':False,'formalKeyframeAccepted':False,
 'next':'P15-76 obtain accurate isolated near-eye lash/eyebrow and bang overlap artwork; stop extending masks since remaining thin dashed contour is drawn inside source/base.'
}
(R/'evidence/p15-75-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'zeroPoseExact':True,'changedDetailPixels':diff_pixels,'holes':holes,'visualGate':q['visualGate']}))

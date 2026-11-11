from pathlib import Path
from PIL import Image,ImageFilter,ImageChops,ImageDraw
import hashlib,json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-80-front-hair';D.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
src=P/'p15-74-bangs-repair/hair.front.alpha-dedup.png'
hair=Image.open(src).convert('RGBA')
alpha=hair.getchannel('A')
# Restrict to erroneous SAM upper-fringe mask. This is a quality probe,
# NOT a semantic human-hair classifier.
roi=(605,370,740,470)
a=alpha.crop(roi)
variants={
 'median3':a.filter(ImageFilter.MedianFilter(3)),
 'opening3':a.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3)),
 'closing3':a.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))}
q={'schema':'KOMA-P15-80-MASK-QUALITY-PROBE-V1','sourceSHA256':sha(src),'roi':list(roi),'variants':{},'formalArtMeshAccepted':False,'formalKeyframeAccepted':False}
for name,new in variants.items():
 layer=hair.copy()
 edited_alpha=alpha.copy();edited_alpha.paste(new,(roi[0],roi[1]))
 layer.putalpha(edited_alpha)
 p=D/(name+'-hair.png');layer.save(p)
 changed=sum(x!=y for x,y in zip(a.tobytes(),new.tobytes()))
 # Count transparent pixels in ROI and independent nonopaque patterns.
 original_zeros=sum(v==0 for v in a.getdata())
 new_zeros=sum(v==0 for v in new.getdata())
 # Full real composite of moving eye while preserving the prior dynamic guard.
 guard=Image.open(P/'p15-75-eyebrow-seam/dynamic-suppression-guard.png').convert('L')
 base=Image.open(P/'p15-76-seam-source/hidden-skin-18.png').convert('RGBA')
 eye=Image.open(P/'p15-74-bangs-repair/eye.matte-18.png').convert('RGBA')
 clip=Image.open(P/'p15-69-clip-separation/hair-clip-gold-independent.png').convert('RGBA')
 edited_alpha=ImageChops.multiply(edited_alpha,ImageChops.invert(guard))
 layer.putalpha(edited_alpha)
 move=Image.new('RGBA',base.size);move.alpha_composite(eye,(18,0))
 frame=Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(base,move),layer),clip)
 frame.save(D/(name+'-18.png'))
 frame.crop((490,380,740,520)).resize((1000,560)).save(D/(name+'-18-detail.png'))
 q['variants'][name]={'changedAlphaPixels':changed,'zerosBefore':original_zeros,'zerosAfter':new_zeros,'hairSHA256':sha(p),'frameSHA256':sha(D/(name+'-18.png'))}
# Baseline uses P15-76 genuine underpaint and P15-75 dynamic hair.
old=Image.open(P/'p15-76-seam-source/eye-shift-18.png').convert('RGBA')
old.crop((490,380,740,520)).resize((1000,560)).save(D/'baseline-18-detail.png')
q['visualGate']='MORPHOLOGICAL_CANDIDATE_REQUIRES_VISUAL_INSPECTION'
(R/'evidence/p15-80-mask-probe.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(q['variants']))

#!/usr/bin/env python3
"""Preserve P15-56 at zero pose while eliminating duplicate outer alpha and evaluating eyelash edge."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageFilter,ImageChops,ImageDraw
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-74-bangs-repair';D.mkdir(parents=True,exist_ok=True)
srcp=P/'p15-56-edge-matting/candidate-erode-2.png'
basep=P/'p15-70-seam-repair/forehead-seam-repaired.png'
eyep=P/'p15-65-eyelid-refinement/eye.near.refined-layer.png'
hairp=P/'p15-73-interactive-sam/front-bangs-rgba.png'
clipp=P/'p15-69-clip-separation/hair-clip-gold-independent.png'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=Image.open(srcp).convert('RGBA')
base=Image.open(basep).convert('RGBA')
eye=Image.open(eyep).convert('RGBA')
hair=Image.open(hairp).convert('RGBA')
clip=Image.open(clipp).convert('RGBA')
# Only pixels in documented external translucent silhouette, with exactly
# identical source/background color+alpha, must not be drawn a second time.
m=hair.getchannel('A');pixels=m.load();sp=source.load();bp=base.load()
changed=[]
for y in range(270,400):
 for x in range(750,785):
  if 0<sp[x,y][3]<255 and sp[x,y]==bp[x,y] and pixels[x,y]>0:
   changed.append((x,y,pixels[x,y]))
   pixels[x,y]=0
assert len(changed)==95,len(changed)
hair.putalpha(m)
hair.save(D/'hair.front.alpha-dedup.png')
# Eroding only at moving poses helps eyelid halo, but remains a diagnostic and
# is blended in proportion to displacement to prevent hard jumping at pose 0.
ealpha=eye.getchannel('A')
eroded=ealpha.filter(ImageFilter.MinFilter(3))
frames=[]
original=Image.open(P/'p15-73-interactive-sam/p15-73-composite-18.png').convert('RGBA')
for dx in (0,9,18):
 t=dx/18
 target=ealpha if dx==0 else Image.blend(ealpha,eroded,t)
 e=eye.copy();e.putalpha(target)
 e.save(D/f'eye.matte-{dx:02d}.png')
 moved=Image.new('RGBA',base.size,(0,0,0,0));moved.alpha_composite(e,(dx,0))
 frame=Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(base,moved),hair),clip)
 name=f'eye-shift-{dx:02d}.png';frame.save(D/name)
 frame.crop((445,265,795,605)).resize((700,680),Image.Resampling.LANCZOS).save(D/f'eye-shift-{dx:02d}-face.png')
 frame.crop((495,405,685,525)).resize((950,600),Image.Resampling.LANCZOS).save(D/f'eye-shift-{dx:02d}-detail.png')
 frames.append({'dx':dx,'sha256':sha(D/name),'eyeMatteSHA256':sha(D/f'eye.matte-{dx:02d}.png')})
source_diff=ImageChops.difference(source,Image.open(D/'eye-shift-00.png').convert('RGBA'))
assert source_diff.getbbox() is None,'actual zero-pose composite differs from source'
# Separate the exact zero-rest gate from all actual moving-pose visual gates.
region=(510,425,685,530)
ref_alpha=source.getchannel('A').crop(region)
holes={}
for dx in (0,9,18):
 alpha=Image.open(D/f'eye-shift-{dx:02d}.png').convert('RGBA').getchannel('A').crop(region)
 holes[str(dx)]=sum(v>128 and w<32 for v,w in zip(ref_alpha.getdata(),alpha.getdata()))
assert holes=={'0':0,'9':0,'18':0}
before=Image.open(P/'p15-73-interactive-sam/p15-73-composite-00.png').convert('RGBA')
old_bbox=ImageChops.difference(source,before).getbbox()
after_bbox=source_diff.getbbox()
# Source-rest exactness alone does not imply semantic correctness when animating.
for name,im in [('original',source),('p15-73',original)]:
 im.crop((495,405,685,525)).resize((950,600),Image.Resampling.LANCZOS).save(D/f'{name}-detail.png')
sheet=Image.new('RGB',(1050,390),'#172638');dr=ImageDraw.Draw(sheet)
for i,dx in enumerate((0,9,18)):
 im=Image.open(D/f'eye-shift-{dx:02d}.png').convert('RGBA').crop((445,265,795,605)).resize((350,340))
 bg=Image.new('RGBA',im.size,(255,255,255,255));bg.alpha_composite(im)
 sheet.paste(bg.convert('RGB'),(i*350,30));dr.text((i*350+8,6),f'eye displacement {dx}px',fill='white')
sheet.save(D/'motion-contact.jpg',quality=92)
report={
 'schema':'KOMA-P15-74-ZERO_POSE_ALPHA_DEDUP_V1',
 'characterId':'p0_character_001',
 'sourceSHA256':sha(srcp),
 'baseSHA256':sha(basep),'eyeSourceSHA256':sha(eyep),'hairSourceSHA256':sha(hairp),'clipSHA256':sha(clipp),
 'repairedHairSHA256':sha(D/'hair.front.alpha-dedup.png'),
 'duplicateSemiTransparentPixelsRemoved':len(changed),
 'cleanedRegionBBox':[750,270,785,400],
 'beforeZeroPoseDiffBBox':list(old_bbox) if old_bbox else None,
 'afterZeroPoseDiffBBox':list(after_bbox) if after_bbox else None,
 'actualAnimationZeroPoseSourceExact':True,
 'frameHashes':frames,
 'motionEyeAlphaMethod':'P15-65 original at 0px, linearly blended toward 1px morphological matte erosion at 18px',
 'motionHoleCounts':holes,
 'eyeVisualAssessment':'At 18px the mild eye-alpha shrink reduces fringe around lower lid/outer lash compared to unshrunk sprite; enlarged images still show a dashed eyebrow/forehead remnant and reddish seam at left eye corner. Not anime-quality approved.',
 'hairVisualAssessment':'Only 95 semi-transparent pixels on far-right outer silhouette are deduplicated. Main SAM front-hair hair strands remain unchanged. No new art or source-semantic fix is claimed.',
 'sourceIdentityPreserved':True,'formalArtMeshAccepted':False,'formalKeyframeAccepted':False,
 'visualGate':'ZERO_POSE_PIXEL_GATE_PASS_DYNAMIC_EYELASH_HAIR_EDGE_VISUAL_FAIL',
 'next':'P15-75 repaint eyebrow/lash-underbang edge from genuine source layers or accurate guided semantic editing; only admit to VDD after dynamic detail is clean'
}
(R/'evidence/p15-74-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'dedupPixels':len(changed),'beforeBBox':report['beforeZeroPoseDiffBBox'],'afterBBox':report['afterZeroPoseDiffBBox'],'holes':holes,'visualGate':report['visualGate']}))

#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageChops
import hashlib,json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-80-front-hair'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
q=json.loads((R/'evidence/p15-80-mask-probe.json').read_text())
source=Image.open(P/'p15-56-edge-matting/candidate-erode-2.png').convert('RGBA')
roi=tuple(q['roi'])
clip=Image.open(P/'p15-69-clip-separation/hair-clip-gold-independent.png').convert('RGBA')
guard=Image.open(P/'p15-75-eyebrow-seam/dynamic-suppression-guard.png').convert('L')
orig=Image.open(P/'p15-74-bangs-repair/hair.front.alpha-dedup.png').convert('RGBA')
a0=orig.getchannel('A').crop(roi)
def zigzag_count(a):
 # alternating 2x2 alpha transitions, indicative of raster speckles, NOT semantic fidelity
 p=a.load();count=0
 for y in range(a.height-1):
  for x in range(a.width-1):
   a1=p[x,y]>127;b=p[x+1,y]>127;c=p[x,y+1]>127;d=p[x+1,y+1]>127
   if a1==d and b==c and a1!=b:count+=1
 return count
q['roiRasterZigzagOriginal']=zigzag_count(a0)
ref_dir=P/'p15-76-seam-source'
q['reviewFrames']={}
for name in ['median3','opening3','closing3']:
 h=Image.open(D/(name+'-hair.png')).convert('RGBA')
 aa=h.getchannel('A').crop(roi)
 q['variants'][name]['rasterZigzagCount']=zigzag_count(aa)
 q['variants'][name]['changedOutsideROI']=sum(x!=y for x,y in zip(
  ImageChops.difference(h.getchannel('A'),orig.getchannel('A')).getdata(),
  Image.new('L',h.size,0).getdata())) # overwritten below
 dif=ImageChops.difference(h.getchannel('A'),orig.getchannel('A'))
 dp=dif.load()
 q['variants'][name]['changedOutsideROI']=sum(dp[x,y]>0 for y in range(1024) for x in range(1024) if not (roi[0]<=x<roi[2] and roi[1]<=y<roi[3]))
 assert q['variants'][name]['changedOutsideROI']==0
# Choose median only as diagnostic; do not approve it as semantic layer.
h=Image.open(D/'median3-hair.png').convert('RGBA')
for dx in (0,9,18):
 if dx==0:out=source.copy()
 else:
  back=Image.open(ref_dir/f'hidden-skin-{dx:02d}.png').convert('RGBA')
  e=Image.open(P/f'p15-74-bangs-repair/eye.matte-{dx:02d}.png').convert('RGBA')
  move=Image.new('RGBA',back.size,(0,0,0,0));move.alpha_composite(e,(dx,0))
  weighted=guard.point(lambda x:int(x*dx/18))
  ha=ImageChops.multiply(h.getchannel('A'),ImageChops.invert(weighted))
  dynamic=h.copy();dynamic.putalpha(ha)
  out=Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(back,move),dynamic),clip)
 out.save(D/f'candidate-median3-{dx:02d}.png')
 out.crop((490,380,740,520)).resize((1000,560)).save(D/f'candidate-median3-{dx:02d}-detail.png')
 old=Image.open(ref_dir/f'eye-shift-{dx:02d}.png').convert('RGBA')
 face=(510,425,685,530)
 hole=sum(a>128 and b<32 for a,b in zip(source.getchannel('A').crop(face).getdata(),out.getchannel('A').crop(face).getdata()))
 q['reviewFrames'][str(dx)]={'sha256':sha(D/f'candidate-median3-{dx:02d}.png'),
   'changedAgainstBaselinePixels':sum(v>0 for v in ImageChops.difference(out,old).convert('L').getdata()),
   'transparentHoles':hole}
assert ImageChops.difference(source,Image.open(D/'candidate-median3-00.png').convert('RGBA')).getbbox() is None
assert all(f['transparentHoles']==0 for f in q['reviewFrames'].values())
q.update({'provisionalCandidate':'median3','zeroPoseSourceExact':True,
 'rasterEdgeCheck':'Zigzag count measures only local mask topology, not semantic correctness',
 'visualAssessment':'All three morphological variants change hundreds of alpha pixels but retain wrong skin/brow content inside the SAM hair mask. Median slightly reduces tiny holes; opening removes real strand tips and closing spreads skin-colored coverage. The visible eyebrow and outer-eye seam remains. Reject formal upgrade.',
 'visualGate':'FAIL_UNRESOLVED_FRONT_HAIR_SEMANTIC_LAYER',
 'formalArtMeshAccepted':False,'formalKeyframeAccepted':False,
 'next':'P15-81 acquire or create true same-pose isolated bangs artwork with explicit source/rest correspondence; stop morphological/threshold optimization'})
(R/'evidence/p15-80-mask-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'originalZigzag':q['roiRasterZigzagOriginal'],'variants':{k:{'changed':v['changedAlphaPixels'],'zigzag':v['rasterZigzagCount']} for k,v in q['variants'].items()},'frames':q['reviewFrames']}))

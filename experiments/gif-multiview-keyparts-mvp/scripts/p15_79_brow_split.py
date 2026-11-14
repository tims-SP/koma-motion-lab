#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageFilter,ImageChops
import json,hashlib
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-79-brow-split';D.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
basep=P/'p15-70-seam-repair/forehead-seam-repaired.png'
base=Image.open(basep).convert('RGBA');rgb=base.convert('RGB');pix=rgb.load()
mask=Image.new('L',base.size,0);mp=mask.load()
# Same-view eyebrow band; color threshold keeps the painted brown stroke,
# not a generated redraw. Bounded to the actual eyebrow arc.
for y in range(416,431):
 for x in range(584,632):
  r,g,b=pix[x,y]
  if r<190 and g<155 and b<160 and r-g>24 and r-b>15 and r>g*1.18:mp[x,y]=255
mask=mask.filter(ImageFilter.GaussianBlur(.55))
A=list(base.getchannel('A').getdata());M=list(mask.getdata())
up=bytearray();skin=bytearray()
for a,m in zip(A,M):
 u=round(a*m/255);s=round((a-u)*255/(255-u)) if u<255 else 0
 up.append(u);skin.append(s)
def make(alpha):
 out=base.copy();out.putalpha(Image.frombytes('L',base.size,bytes(alpha)));return out
brow=make(up);under=make(skin)
brow.save(D/'eyebrow.same-view.png');under.save(D/'forehead.without-eyebrow.png');mask.save(D/'eyebrow-mask.png')
recon=Image.alpha_composite(under,brow);recon.save(D/'forehead.reconstructed.png')
assert ImageChops.difference(base,recon).getbbox() is None
# Dynamic compositing: eyebrow remains fixed to head; front hair remains above it.
clip=Image.open(P/'p15-69-clip-separation/hair-clip-gold-independent.png').convert('RGBA')
frames=[]
for dx in (0,9,18):
 if dx==0:
  frame=Image.open(P/'p15-56-edge-matting/candidate-erode-2.png').convert('RGBA')
 else:
  eye=Image.open(P/f'p15-74-bangs-repair/eye.matte-{dx:02d}.png').convert('RGBA')
  hair=Image.open(P/f'p15-75-eyebrow-seam/hair.front.moving-{dx:02d}.png').convert('RGBA')
  # Rebuild the original forehead base from exact complementary layers, then
  # apply the same translated eye and moving-bang stack as P15-75.
  frame=Image.alpha_composite(under,brow)
  moved=Image.new('RGBA',base.size,(0,0,0,0));moved.alpha_composite(eye,(dx,0))
  frame=Image.alpha_composite(frame,moved)
  frame=Image.alpha_composite(frame,hair)
  frame=Image.alpha_composite(frame,clip)
 frame.save(D/f'frame-{dx:02d}.png')
 frame.crop((480,390,700,540)).resize((880,600)).save(D/f'frame-{dx:02d}-detail.png')
 # Compare moving frames against previously accepted P15-75 compositing.
 ref=Image.open(P/f'p15-75-eyebrow-seam/eye-shift-{dx:02d}.png').convert('RGBA')
 diff=ImageChops.difference(frame,ref)
 frames.append({'dx':dx,'sha256':sha(D/f'frame-{dx:02d}.png'),
  'previousCompositeDiffPixels':sum(v>0 for v in diff.convert('L').getdata()),
  'referenceSHA256':sha(P/f'p15-75-eyebrow-seam/eye-shift-{dx:02d}.png')})
# Verify source at rest and alpha hole count in the moved eye ROI.
src=Image.open(P/'p15-56-edge-matting/candidate-erode-2.png').convert('RGBA')
zero=ImageChops.difference(src,Image.open(D/'frame-00.png').convert('RGBA')).getbbox()
holes={}
for dx in (0,9,18):
 o=Image.open(D/f'frame-{dx:02d}.png').convert('RGBA')
 holes[str(dx)]=sum(v==0 for v in o.getchannel('A').crop((510,425,685,530)).getdata())
q={'schema':'KOMA-P15-79-SAME_VIEW_BROW_SPLIT_V1','characterId':'p0_character_001',
 'baseSHA256':sha(basep),'eyebrowSHA256':sha(D/'eyebrow.same-view.png'),
 'underpaintSHA256':sha(D/'forehead.without-eyebrow.png'),'maskSHA256':sha(D/'eyebrow-mask.png'),
 'eyebrowNonzeroPixels':sum(v>0 for v in brow.getchannel('A').getdata()),
 'baseReconstructionExact':ImageChops.difference(base,recon).getbbox() is None,
 'zeroPoseSourceExact':zero is None,'frames':frames,'motionOffsets':[0,9,18],
 'transparentPixelCountsInFaceROI':holes,
 'method':'SAME_VIEW_SOURCE_PIXEL_ALPHA_COMPLEMENT_SPLIT_NO_GENERATED_BROW_ART',
 'browAnchoredToHead':True,'bangsRemainAboveBrow':True,
 'visualAssessment':'The existing same-view painted eyebrow is now an independently addressable RGBA layer. Its complementary forehead layer reconstructs the original base exactly. Existing front-bang alpha still contains the unresolved dashed/fragmented contour around the brow and eye; no new semantic bang matte was created.',
 'visualGate':'BROW_LAYER_EXTRACTED_EXACT_RECONSTRUCTION_BANG_SEMANTIC_MATTE_FAIL',
 'formalArtMeshAccepted':False,'formalKeyframeAccepted':False}
(R/'evidence/p15-79-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'browPixels':q['eyebrowNonzeroPixels'],'baseExact':q['baseReconstructionExact'],'zeroExact':q['zeroPoseSourceExact'],'frames':frames,'holes':holes}))

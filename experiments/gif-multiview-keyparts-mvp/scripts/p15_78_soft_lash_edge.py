#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter,ImageChops
import json,hashlib
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-78-soft-lash';D.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
eye0=Image.open(P/'p15-65-eyelid-refinement/eye.near.refined-layer.png').convert('RGBA')
poly=[(519,454),(521,447),(529,437),(545,427),(561,423),(587,419),(610,419),(632,423),(645,430),(651,441),(654,451),(645,457),(633,449),(615,443),(593,439),(566,439),(547,447),(533,458),(525,463)]
hard=Image.new('L',eye0.size,0);ImageDraw.Draw(hard).polygon(poly,fill=255)
mask=hard.filter(ImageFilter.GaussianBlur(1.0))
A=list(eye0.getchannel('A').getdata());M=list(mask.getdata())
up=bytearray();lo=bytearray()
for a,m in zip(A,M):
 u=round(a*m/255);l=round((a-u)*255/(255-u)) if u<255 else 0
 up.append(u);lo.append(l)
def layer(alpha):
 out=eye0.copy();out.putalpha(Image.frombytes('L',eye0.size,bytes(alpha)));return out
upper=layer(up);lower=layer(lo)
recon=Image.alpha_composite(lower,upper)
diff=ImageChops.difference(eye0,recon)
assert diff.getbbox() is None, diff.getbbox()
upper.save(D/'eye.upper-lash.soft.png');lower.save(D/'eye.lower-eye.soft.png');mask.save(D/'lash-soft-mask.png')
# Source-derived layer frames with independent z-order. The 0px frame is
# exactly the original source; only moving poses use separated layers.
source=Image.open(P/'p15-56-edge-matting/candidate-erode-2.png').convert('RGBA')
clip=Image.open(P/'p15-69-clip-separation/hair-clip-gold-independent.png').convert('RGBA')
frames=[]
for dx in (0,9,18):
 if dx==0: 
  frame=source.copy()
 else:
  under=Image.open(P/f'p15-76-seam-source/hidden-skin-{dx:02d}.png').convert('RGBA')
  hair=Image.open(P/f'p15-75-eyebrow-seam/hair.front.moving-{dx:02d}.png').convert('RGBA')
  eye=Image.open(P/f'p15-74-bangs-repair/eye.matte-{dx:02d}.png').convert('RGBA')
  # Apply same source mask to translated eye; compute complementary alpha split.
  shifted_mask=Image.new('L',eye.size,0);shifted_mask.paste(mask,(dx,0))
  aa=list(eye.getchannel('A').getdata());mm=list(shifted_mask.getdata())
  ua=bytearray();la=bytearray()
  for a,m in zip(aa,mm):
   u=round(a*m/255);l=round((a-u)*255/(255-u)) if u<255 else 0
   ua.append(u);la.append(l)
  U=eye.copy();U.putalpha(Image.frombytes('L',eye.size,bytes(ua)))
  L=eye.copy();L.putalpha(Image.frombytes('L',eye.size,bytes(la)))
  frame=Image.alpha_composite(under,L)
  frame=Image.alpha_composite(frame,hair)
  frame=Image.alpha_composite(frame,U)
  frame=Image.alpha_composite(frame,clip)
 frame.save(D/f'frame-{dx:02d}.png')
 frame.crop((480,390,700,540)).resize((880,600),Image.Resampling.LANCZOS).save(D/f'frame-{dx:02d}-detail.png')
 frames.append({'dx':dx,'sha256':sha(D/f'frame-{dx:02d}.png')})
zero=ImageChops.difference(source,Image.open(D/'frame-00.png').convert('RGBA')).getbbox()
assert zero is None
report={'schema':'KOMA-P15-78-SOFT_LASH_BOUNDARY_V1','sourceEyeSHA256':sha(P/'p15-65-eyelid-refinement/eye.near.refined-layer.png'),
 'sourceSHA256':sha(P/'p15-56-edge-matting/candidate-erode-2.png'),
 'maskSHA256':sha(D/'lash-soft-mask.png'),'upperLashSHA256':sha(D/'eye.upper-lash.soft.png'),
 'lowerEyeSHA256':sha(D/'eye.lower-eye.soft.png'),'maskBlurRadius':1.0,
 'eyeReconstructionExact':True,'eyeReconstructionDiffBBox':None,
 'zeroPoseSourceExact':zero is None,'motionOffsets':[0,9,18],'frames':frames,
 'visualGate':'SOFT_EDGE_REDUCES_PIXEL_STAIRCASE_BUT_BROW_BANG_OCCLUSION_STILL_REQUIRES_REVIEW',
 'formalArtMeshAccepted':False,'formalKeyframeAccepted':False}
(R/'evidence/p15-78-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'eyeExact':True,'zeroExact':zero is None,'frames':frames}))

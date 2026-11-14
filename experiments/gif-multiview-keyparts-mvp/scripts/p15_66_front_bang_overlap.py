#!/usr/bin/env python3
"""Test a chroma-constrained local bang/eye occlusion matte, not a full hair ArtMesh."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageFilter,ImageChops
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-66-front-bang';D.mkdir(parents=True,exist_ok=True)
SRC=R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'
BG=R/'private-assets/exports/p15-63-masked-lama/underpaint-full.png'
EYE=R/'private-assets/exports/p15-65-eyelid-refinement/eye.near.refined-layer.png'
WORK=R/'private-assets/exports/p15-63-masked-lama/mask-full.png'
OLDHAIR=R/'private-assets/exports/p15-41-profile-candidate/layers/hair.front.png'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
S=Image.open(SRC).convert('RGBA');B=Image.open(BG).convert('RGBA')
E=Image.open(EYE).convert('RGBA');W=Image.open(WORK).convert('L')
assert S.size==B.size==E.size==(1024,1024)
def clamp(x):return max(0,min(1,x))
# Extract a small local pink front-strand footprint by its chroma, then restrict
# the foreground matte to the area hidden/repainted by P15-63 LaMa.
# This is a local dynamic occluder prototype, NOT an independent full bang.
mat=Image.new('L',S.size,0);src=S.load();m=mat.load()
for y in range(370,500):
 for x in range(610,686):
  r,g,b,a=src[x,y]
  chrom=clamp((b-g-12)/14)
  pink=clamp((r-g-24)/20)
  xpos=clamp((x-628)/13)
  ypos=clamp((488-y)/26)
  m[x,y]=round(255*chrom*pink*xpos*ypos*(a/255))
mat=mat.filter(ImageFilter.GaussianBlur(.65))
mat=ImageChops.multiply(mat,W)
hair=Image.new('RGBA',S.size)
hair.paste(S,(0,0),mat)
hair.save(D/'hair.front.eye-overlap.png')
mat.save(D/'hair.front.eye-overlap-mask.png')
# Explicitly hold front-strand overlap at highest layer depth, ahead of moving eye.
frames=[]
base_outputs={}
for dx in (0,9,18):
 moving=Image.new('RGBA',S.size,(0,0,0,0))
 moving.alpha_composite(E,(dx,0))
 nohair=Image.alpha_composite(B,moving)
 withhair=Image.alpha_composite(nohair,hair)
 stem=f'eye-shift-{dx:02d}'
 nohair.save(D/(stem+'-no-occlusion.png'))
 withhair.save(D/(stem+'-with-occlusion.png'))
 withhair.crop((470,390,760,660)).resize((870,810),Image.Resampling.LANCZOS).save(D/(stem+'-face.png'))
 px_diff=ImageChops.difference(nohair.convert('RGB'),withhair.convert('RGB')).convert('L')
 changed=sum(v>0 for v in px_diff.crop((600,400,695,485)).getdata())
 orig_a=S.getchannel('A').crop((510,400,690,545)).getdata()
 new_a=withhair.getchannel('A').crop((510,400,690,545)).getdata()
 holes=sum(a>128 and b<32 for a,b in zip(orig_a,new_a))
 frames.append({'dx':dx,'sha256':sha(D/(stem+'-with-occlusion.png')),
    'noOcclusionSHA256':sha(D/(stem+'-no-occlusion.png')),
    'changedRGBPixelsNearBang':changed,'transparentHolePixels':holes})
 base_outputs[dx]=nohair
assert all(f['transparentHolePixels']==0 for f in frames)
assert all(f['changedRGBPixelsNearBang']>0 for f in frames)
# Diagnostic source comparisons.
for name,p in [('source',SRC),('old45hair',OLDHAIR)]:
 Image.open(p).convert('RGBA').crop((470,390,760,660)).resize((870,810),Image.Resampling.LANCZOS).save(D/(name+'-face.png'))
# Half-tone/transparent areas are retained; no hard polygon cut around strand.
alpha=hair.getchannel('A')
nonzero=sum(v>0 for v in alpha.getdata())
partial=sum(0<v<255 for v in alpha.getdata())
old=Image.open(OLDHAIR).convert('RGBA')
report={
 'schema':'KOMA-P15-66-LOCAL_BANG_OCCLUSION_V1','characterId':'p0_character_001',
 'sourceSHA256':sha(SRC),'neuralUnderpaintSHA256':sha(BG),
 'eyeLayerSHA256':sha(EYE),'originalInpaintMaskSHA256':sha(WORK),
 'older45BangLayerSHA256':sha(OLDHAIR),
 'older45BangReusedAsNewArtwork':False,
 'chromaMethod':{'minimumBlueMinusGreen':12,'featherPx':0.65,'xLowerFadeStart':628,
   'mattedOnlyInsideOriginalNeuralInpaintMask':True,'purpose':'local front bang at near eye'},
 'localBangAlphaBBox':list(alpha.getbbox()),
 'localBangAlphaPixels':nonzero,'localBangPartialAlphaPixels':partial,
 'localBangSHA256':sha(D/'hair.front.eye-overlap.png'),
 'localBangMaskSHA256':sha(D/'hair.front.eye-overlap-mask.png'),
 'frames':frames,
 'zOrder':['neural_skin_underpaint','eye.near.refined-layer','hair.front.eye-overlap'],
 'fullIndependentFrontHairAvailable':False,
 'perStrandHairIdentityVerified':False,
 'visualAssessment':'The chroma matte avoids the straight polygon seams seen in P15-65 and restores a small foreground pink strand near the right eyelid; it only covers a tiny eye-overlap patch, not complete independent front hair. The eyelash and hair junction remains insufficient for full quality certification.',
 'visualGate':'LOCAL_OCCLUSION_DIAGNOSTIC_PASS_FULL_HAIR_ARTMESH_FAIL',
 'formalArtMeshAccepted':False,'formalKeyframeAccepted':False,
 'next':'P15-67 acquire clean full front-hair layer with transparent strand boundaries and recheck occlusion without relying on pixel-color heuristics.'
}
(R/'evidence/p15-66-front-bang-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'alphaBBox':report['localBangAlphaBBox'],'nonzero':nonzero,'partial':partial,'motion':frames,'formalArtMeshAccepted':False}))

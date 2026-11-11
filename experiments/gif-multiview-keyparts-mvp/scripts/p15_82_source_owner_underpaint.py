#!/usr/bin/env python3
"""Source-exact layered decomposition + *distinct* clean underpaint for moving near eye.
Each original pixel belongs to exactly one of clip, SAM3 bangs, eye, face.
Use raw RGBA equality, never Pillow getbbox on RGBA differences as the sole gate.
"""
from pathlib import Path
from PIL import Image,ImageChops,ImageFilter
import json,hashlib
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-82-rest-underpaint';D.mkdir(parents=True,exist_ok=True)
sp=P/'p15-56-edge-matting/candidate-erode-2.png'
bp=P/'p15-70-seam-repair/forehead-seam-repaired.png'
ep=P/'p15-65-eyelid-refinement/eye.near.refined-layer.png'
hp=P/'p15-81-image-layered/sam3-027-aligned-alpha.png'
cp=P/'p15-69-clip-separation/hair-clip-gold-independent.png'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=Image.open(sp).convert('RGBA');b=Image.open(bp).convert('RGBA')
e=Image.open(ep).convert('RGBA');hmask=Image.open(hp).convert('L')
c=Image.open(cp).convert('RGBA')
W,H=s.size;N=W*H
def binary(im):return im.point(lambda x:255 if x>0 else 0)
# Determine exclusive source-space pixel ownership. Clip has highest depth,
# then hair, then eye, then remaining base.
clip_m=binary(c.getchannel('A'))
hair_m=hmask.point(lambda x:255 if x>=128 else 0)
hair_m=ImageChops.multiply(hair_m,ImageChops.invert(clip_m))
eye_m=binary(e.getchannel('A')).filter(ImageFilter.MaxFilter(7))
eye_m=ImageChops.multiply(eye_m,ImageChops.invert(clip_m))
eye_m=ImageChops.multiply(eye_m,ImageChops.invert(hair_m))
base_m=ImageChops.invert(ImageChops.lighter(clip_m,ImageChops.lighter(hair_m,eye_m)))
masks={'clip':clip_m,'bangs':hair_m,'eye':eye_m,'face':base_m}
def extract(src,mask): 
 im=src.copy()
 im.putalpha(ImageChops.multiply(src.getchannel('A'),mask))
 return im
for name,mask in masks.items():
 mask.save(D/f'mask.owner-{name}.png')
 extract(s,mask).save(D/f'part.source-{name}.png')
parts={n:Image.open(D/f'part.source-{n}.png').convert('RGBA') for n in masks}
def combine(arr):
 o=Image.new('RGBA',s.size,(0,0,0,0))
 for i in arr:o=Image.alpha_composite(o,i)
 return o
# Real recomposition of all four independently addressable image files.
rest=combine([parts[n] for n in ['face','eye','bangs','clip']])
rest.save(D/'actual-rest-by-independent-parts.png')
source_bytes=s.tobytes();rest_bytes=rest.tobytes()
raw_differences=[i for i in range(N) if rest_bytes[4*i:4*i+4]!=source_bytes[4*i:4*i+4]]
visible_differences=[i for i in raw_differences if source_bytes[4*i+3]>0]
assert not visible_differences,('Visible source pixel differences',len(visible_differences))
assert all(rest_bytes[4*i+3]==source_bytes[4*i+3] for i in range(N))
# Transparent pixel RGB may encode discarded invisible colors (alpha=0)
# and standard alpha compositing normalizes those colors to RGB 0. Do not
# falsely claim raw-byte equality unless this is also identical.

# Actual source-matched hidden forehead: remove the source eye ownership
# from source face and fill with the prior image-free P15-70 underpaint.
# Inpainting region retains original neighboring skin instead of regenerating
# the entire face. The underpaint is not accepted as final artwork yet.
hole=eye_m
face_rest=parts['face']
painted=Image.alpha_composite(face_rest,extract(b,hole))
painted.save(D/'underpaint.clean-eye-region.png')
# Diagnose whether old source eye can be removed without leaving a source
# eyebrow/lash contour outside the ownership region.
under_behind=Image.alpha_composite(painted,parts['bangs'])
under_behind.save(D/'hidden-face-with-front-bangs.png')
frames={}
roi=(510,425,685,530)
reference_alpha=s.getchannel('A').crop(roi)
for dx in (0,9,18):
 # At rest compose source-exact independent layers, NOT direct source copy.
 # For motion use the true eye-free underpaint to reveal hidden face.
 if dx==0:
  frame=combine([parts[n] for n in ['face','eye','bangs','clip']])
 else:
  shifted=Image.new('RGBA',s.size)
  shifted.alpha_composite(parts['eye'],(dx,0))
  frame=combine([painted,shifted,parts['bangs'],parts['clip']])
 out=D/f'frame-{dx:02d}.png'
 frame.save(out)
 frame.crop((445,265,795,605)).resize((700,680),Image.Resampling.LANCZOS).save(D/f'frame-{dx:02d}-face.png')
 frame.crop((510,390,700,525)).resize((950,675),Image.Resampling.LANCZOS).save(D/f'frame-{dx:02d}-eye-detail.png')
 alpha=frame.getchannel('A').crop(roi)
 holes=sum(a>128 and z<32 for a,z in zip(reference_alpha.getdata(),alpha.getdata()))
 ref=Image.open(P/f'p15-76-seam-source/eye-shift-{dx:02d}.png').convert('RGBA')
 a=frame.tobytes();r=ref.tobytes()
 pixel_diff=sum(a[4*i:4*i+4]!=r[4*i:4*i+4] for i in range(N))
 frames[str(dx)]={'sha256':sha(out),'transparentHolesROI':holes,'changedPixelsVsP1576':pixel_diff}
# Visible rest proof cannot rely on a shortcut image: inspect independent layer
# masks and verify their union covers the entire valid source.
mask_bytes={n:m.tobytes() for n,m in masks.items()}
assert all(sum(mask_bytes[n][i]>0 for n in masks)==1 for i in range(N))
qa={
 'schema':'KOMA-P15-82-INDEPENDENT_SOURCE_PARTS_AND_HIDDEN_EYE_UNDERPAINT_V1',
 'sourceSHA256':sha(sp),'priorFaceSHA256':sha(bp),'priorEyeSHA256':sha(ep),
 'sam3AlphaSHA256':sha(hp),'priorClipSHA256':sha(cp),
 'sourceOwnedLayers':{n:{'maskSHA256':sha(D/f'mask.owner-{n}.png'),'layerSHA256':sha(D/f'part.source-{n}.png'),'nonzeroPixels':sum(v>0 for v in parts[n].getchannel('A').getdata())} for n in masks},
 'ownerPriority':['clip','bangs','eye','face'],
 'eyeSourceMaskExpansionPx':3,
 'underpaintSHA256':sha(D/'underpaint.clean-eye-region.png'),
 'underpaintMethod':'P15-70 authentic local clean skin/forehead in source eye-owned region; outside source pixels retained',
 'actualIndependentPartRestExactRGBA':rest_bytes==source_bytes,
 'actualIndependentPartRestVisuallyExact':not visible_differences,
 'actualIndependentPartRestAlphaExact':True,
 'transparentRGBOnlyDifferences':len(raw_differences),
 'zeroPoseGeneratedByCompositingIndependentParts':True,
 'frameQA':frames,
 'dynamicVisualGate':'PENDING_VISUAL_INSPECTION_NOT_FORMAL',
 'formalArtMeshAccepted':False,'formalKeyframeAccepted':False,
}
(R/'evidence/p15-82-source-decomposition-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'visibleRestExact':qa['actualIndependentPartRestVisuallyExact'],
 'rawByteExact':qa['actualIndependentPartRestExactRGBA'],
 'transparentRgbDifferences':qa['transparentRGBOnlyDifferences'],
 'parts':{k:v['nonzeroPixels'] for k,v in qa['sourceOwnedLayers'].items()},'frames':frames},ensure_ascii=False),flush=True)

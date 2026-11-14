#!/usr/bin/env python3
"""Use already-existing, clean same-view P15-70 occluded pixels for erroneously
stationary eyelash on P15-84 background. No new model/skin clone; preserve P15-82
true independent source-owned zero pose. Evaluate 9/18 dynamic separately."""
from PIL import Image, ImageChops, ImageDraw, ImageFilter
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-86-semantic-ownership';D.mkdir(parents=True,exist_ok=True)
paths={
 'source':P/'p15-56-edge-matting/candidate-erode-2.png',
 'base':P/'p15-84-clean-brow-inpaint/clean-hidden-face.png',
 'donor':P/'p15-70-seam-repair/forehead-seam-repaired.png',
 'sam':P/'p15-81-image-layered/sam3-027-aligned-alpha.png',
 'eyeSource':P/'p15-65-eyelid-refinement/eye.near.refined-layer.png',
 'hair':P/'p15-81-image-layered/sam3-027-hair-rgba.png',
 'clip':P/'p15-82-rest-underpaint/part.source-clip.png',
 'zero':P/'p15-82-rest-underpaint/candidate-00.png'}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
src=Image.open(paths['source']).convert('RGBA')
base=Image.open(paths['base']).convert('RGBA')
donor=Image.open(paths['donor']).convert('RGBA')
sam=Image.open(paths['sam']).convert('L')
eye=Image.open(paths['eyeSource']).convert('RGBA').getchannel('A')
hair=Image.open(paths['hair']).convert('RGBA')
clip=Image.open(paths['clip']).convert('RGBA')
# The semantically mislabeled stationary eyelash begins just outside the moving
# iris. Geometry is bounded to inspected source pixels, not a full skin patch.
area=[(515,445),(520,442),(532,442),(534,446),(534,455),(527,458),(516,456),(513,452)]
raw=Image.new('L',src.size,0)
ImageDraw.Draw(raw).polygon(area,fill=255)
# anti-aliased transition along existing clean source coordinates.
mask=raw.filter(ImageFilter.GaussianBlur(.6))
old_mask=Image.open(P/'p15-84-clean-brow-inpaint/mask-full.png').convert('L')
# Do not overwrite successful P15-84 inpainting.
mask=ImageChops.multiply(mask,ImageChops.invert(old_mask))
mask.save(D/'ownership-correction-mask.png')
corrected=Image.composite(donor,base,mask)
corrected.save(D/'corrected-hidden-face.png')
a=base.tobytes();b=corrected.tobytes();m=mask.tobytes()
modified=[i for i in range(src.width*src.height) if a[4*i:4*i+4]!=b[4*i:4*i+4]]
outside=sum(m[i]==0 for i in modified)
assert outside==0
# Verify the artifact belonged to old source eye: the darkest pixels had strong
# source eye alpha and/or direct overlap with the SAM3 hair classification.
sa=sam.tobytes();ea=eye.tobytes()
classified=sum(sa[i]>0 or ea[i]>0 for i in modified)
def composite(images):
 result=Image.new('RGBA',src.size,(0,0,0,0))
 for im in images:result=Image.alpha_composite(result,im)
 return result
frames={}
for dx in (0,9,18):
 if dx==0:
  result=Image.open(paths['zero']).convert('RGBA')
 else:
  im=Image.open(P/f'p15-74-bangs-repair/eye.matte-{dx:02d}.png').convert('RGBA')
  moved=Image.new('RGBA',src.size);moved.alpha_composite(im,(dx,0))
  result=composite([corrected,moved,hair,clip])
 p=D/f'frame-{dx:02d}.png';result.save(p)
 result.crop((445,265,795,605)).resize((700,680),Image.Resampling.LANCZOS).save(D/f'frame-{dx:02d}-face.png')
 result.crop((500,395,690,515)).resize((950,600),Image.Resampling.NEAREST).save(D/f'frame-{dx:02d}-detail.png')
 prev=Image.open(P/f'p15-84-clean-brow-inpaint/frame-{dx:02d}.png').convert('RGBA')
 bytes_a=result.tobytes();bytes_b=prev.tobytes()
 visible=sum(bytes_a[4*i:4*i+4]!=bytes_b[4*i:4*i+4] and (bytes_a[4*i+3]>0 or bytes_b[4*i+3]>0) for i in range(src.width*src.height))
 invisible=sum(bytes_a[4*i:4*i+4]!=bytes_b[4*i:4*i+4] and bytes_a[4*i+3]==0 and bytes_b[4*i+3]==0 for i in range(src.width*src.height))
 roi=(510,405,690,535)
 holes=sum(x>128 and y<32 for x,y in zip(src.getchannel('A').crop(roi).getdata(),result.getchannel('A').crop(roi).getdata()))
 frames[str(dx)]={'sha256':sha(p),'visibleChangedVsP1584':visible,'invisibleRGBChangedVsP1584':invisible,'newTransparentHolesROI':holes}
# Objective check against the actual source of stationary residual:
# dark, red-black line in x515..535 y442..458 when no foreground layers exist.
roi=(514,439,535,459)
def darkcount(im):
 return sum(r<120 and g<95 and b<110 and a>128 for r,g,b,a in im.crop(roi).getdata())
qa={
 'schema':'KOMA-P15-86-TRUE-SOURCE-SEMANTIC_OWNERSHIP_V1',
 'baseline':'P15-84','inputSHA256':{k:sha(v) for k,v in paths.items()},
 'correctionRegion':area,'correctionMaskSHA256':sha(D/'ownership-correction-mask.png'),
 'correctionMaskPixels':sum(v>0 for v in mask.getdata()),
 'changedInsideMaskPixels':len(modified),'changedOutsideMaskPixels':outside,
 'changedPixelsAtOriginalEyeOrSAMOwnership':classified,
 'preexistingCleanDonor':'P15-70 authentic same-view covered forehead',
 'newModelCalls':0,'cloningOrGenerativeFill':False,
 'correctedUnderpaintSHA256':sha(D/'corrected-hidden-face.png'),
 'sourceDarkPixelsOriginal':darkcount(src),
 'stationaryResidualDarkPixelsBefore':darkcount(base),
 'stationaryResidualDarkPixelsAfter':darkcount(corrected),
 'frameQA':frames,'zeroPoseUsesIndependentOriginalLayers':True,
 'formalArtMeshAccepted':False,'formalKeyframeAccepted':False,
 'visualGate':'PENDING_REAL_IMAGE_INSPECTION'
}
(R/'evidence/p15-86-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'changed':len(modified),'classified':classified,'darkBefore':qa['stationaryResidualDarkPixelsBefore'],'darkAfter':qa['stationaryResidualDarkPixelsAfter'],'frames':frames},ensure_ascii=False))

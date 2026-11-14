#!/usr/bin/env python3
"""P15-86: real source-owned eyelash correction and P15-70 clean hidden pixels.
The source eye owns eyelashes misclassified by SAM3; no new image generation."""
from PIL import Image,ImageDraw,ImageFilter,ImageChops
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-86-semantic-ownership';D.mkdir(exist_ok=True)
sha=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()
files={
 'source':P/'p15-56-edge-matting/candidate-erode-2.png',
 'oldUnderpaint':P/'p15-84-clean-brow-inpaint/clean-hidden-face.png',
 'cleanSameViewUnderpaint':P/'p15-70-seam-repair/forehead-seam-repaired.png',
 'oldSAM3Hair':P/'p15-81-image-layered/sam3-027-hair-rgba.png',
 'sourceEye':P/'p15-65-eyelid-refinement/eye.near.refined-layer.png',
 'oldSourceBangMask':P/'p15-82-rest-underpaint/mask.owner-bangs.png',
 'oldSourceEyeMask':P/'p15-82-rest-underpaint/mask.owner-eye.png',
 'oldSourceFaceMask':P/'p15-82-rest-underpaint/mask.owner-face.png',
 'oldSourceClipMask':P/'p15-82-rest-underpaint/mask.owner-clip.png',
 'sourceClip':P/'p15-82-rest-underpaint/part.source-clip.png',
 'priorInpaintMask':P/'p15-84-clean-brow-inpaint/mask-full.png'}
s=Image.open(files['source']).convert('RGBA')
under=Image.open(files['oldUnderpaint']).convert('RGBA')
clean=Image.open(files['cleanSameViewUnderpaint']).convert('RGBA')
hair=Image.open(files['oldSAM3Hair']).convert('RGBA')
clip=Image.open(files['sourceClip']).convert('RGBA')
# Inspection area includes false stationary eyelashes. This is a source-owner
# correction, not a global morphology pass. Protect the rest of the bangs.
polygon=[(514,441),(520,439),(531,440),(536,445),(536,457),(530,462),(517,459),(511,453)]
hard=Image.new('L',s.size,0);ImageDraw.Draw(hard).polygon(polygon,fill=255)
soft=hard.filter(ImageFilter.GaussianBlur(.7))
soft.save(D/'owner-correction-soft-mask.png')
hard.save(D/'owner-correction-binary-mask.png')
# Use P15-70 exact same-coordinate hidden pixels. No new inpainting, cloning
# or changed source geometry outside this small boundary.
under_new=Image.composite(clean,under,soft);under_new.save(D/'hidden-face.reassigned.png')
# False stationary eyelash must no longer be part of foreground front hair.
# Hair follows existing source RGB and only loses alpha at the misclassified area.
hm=hair.getchannel('A')
hairnew=hair.copy();hairnew.putalpha(ImageChops.multiply(hm,ImageChops.invert(soft)))
hairnew.save(D/'bangs.without-source-eyelash.png')
# Reallocate source OWNERSHIP to independent source eye for rest pose,
# without moving any original pixels. Old clip priority is preserved.
clipmask=Image.open(files['oldSourceClipMask']).convert('L')
oldbang=Image.open(files['oldSourceBangMask']).convert('L')
oldeye=Image.open(files['oldSourceEyeMask']).convert('L')
oldface=Image.open(files['oldSourceFaceMask']).convert('L')
# Use original hard semantic patch rather than fractional owner allocations
# so each original source pixel still belongs to exactly one part.
eyeoverlap=ImageChops.multiply(oldbang,hard)
eyemask=ImageChops.lighter(oldeye,eyeoverlap)
bangmask=ImageChops.multiply(oldbang,ImageChops.invert(eyeoverlap))
facemask=oldface
masks={'face':facemask,'eye':eyemask,'bangs':bangmask,'clip':clipmask}
parts={}
for name,m in masks.items():
 m.save(D/f'owner-{name}.png')
 im=s.copy();im.putalpha(ImageChops.multiply(s.getchannel('A'),m))
 im.save(D/f'part-{name}.png');parts[name]=im
def alpha_comp(parts):
 im=Image.new('RGBA',s.size)
 for p in parts:im=Image.alpha_composite(im,p)
 return im
rest=alpha_comp([parts[n] for n in ('face','eye','bangs','clip')])
rest.save(D/'rest-from-reassigned-ownership.png')
src=s.tobytes();rt=rest.tobytes()
visible_diff=sum(src[i*4:i*4+4]!=rt[i*4:i*4+4] and src[i*4+3]>0 for i in range(s.width*s.height))
alpha_diff=sum(src[i*4+3]!=rt[i*4+3] for i in range(s.width*s.height))
assert visible_diff==0 and alpha_diff==0
maskbytes=[m.tobytes() for m in masks.values()]
assert all(sum(a[i]>0 for a in maskbytes)==1 for i in range(s.width*s.height))
n=s.width*s.height
def delta(x,y):
 a=x.tobytes();b=y.tobytes()
 return sum(a[i*4:i*4+4]!=b[i*4:i*4+4] for i in range(n))
def visible_delta(x,y):
 a=x.tobytes();b=y.tobytes()
 return sum(a[i*4:i*4+4]!=b[i*4:i*4+4] and (a[i*4+3]>0 or b[i*4+3]>0) for i in range(n))
# 0px is actual source-owned compositing. Motion uses P15-74 original eye.
frames={}
for dx in (0,9,18):
 if dx==0:frame=rest
 else:
  eye=Image.open(P/f'p15-74-bangs-repair/eye.matte-{dx:02d}.png').convert('RGBA')
  moved=Image.new('RGBA',s.size);moved.alpha_composite(eye,(dx,0))
  frame=alpha_comp([under_new,moved,hairnew,clip])
 path=D/f'frame-reassigned-{dx:02d}.png';frame.save(path)
 frame.crop((445,265,795,605)).resize((700,680),Image.Resampling.LANCZOS).save(D/f'face-reassigned-{dx:02d}.png')
 frame.crop((500,395,690,515)).resize((950,600),Image.Resampling.NEAREST).save(D/f'detail-reassigned-{dx:02d}.png')
 ref=Image.open(P/f'p15-84-clean-brow-inpaint/frame-{dx:02d}.png').convert('RGBA')
 roi=(510,405,690,535)
 holes=sum(a>128 and b<32 for a,b in zip(s.getchannel('A').crop(roi).getdata(),frame.getchannel('A').crop(roi).getdata()))
 frames[str(dx)]={'sha256':sha(path),'visibleChangedFromP1584':visible_delta(frame,ref),'rgbaChangedFromP1584':delta(frame,ref),'faceHoles':holes}
# Compare true background-only + stationary hair overlay.
static_before=Image.alpha_composite(under,hair)
static_after=Image.alpha_composite(under_new,hairnew)
for name,im in [('old-stationary-no-eye',static_before),('new-stationary-no-eye',static_after),('new-underpaint-only',under_new)]:
 im.crop((510,430,550,468)).resize((640,608),Image.Resampling.NEAREST).save(D/f'{name}.png')
# Count dark original lash in source-eye overlap patch without skin-colored pixels.
def dark(im):
 return sum(r<150 and g<115 and b<130 and a>128 for r,g,b,a in im.crop((515,442,536,459)).getdata())
q={
 'schema':'KOMA-P15-86-LASH_BANG_OWNERSHIP_V1',
 'baselineGit':'ede2b4e24b86988e875ff6dc233b6c322de6b103',
 'inputSHA256':{k:sha(v) for k,v in files.items()},
 'correctionPolygon':polygon,'hardMaskSHA256':sha(D/'owner-correction-binary-mask.png'),
 'softMaskSHA256':sha(D/'owner-correction-soft-mask.png'),
 'hardMaskPixels':sum(v>0 for v in hard.getdata()),
 'transferredBangToEyePixels':sum(v>0 for v in eyeoverlap.getdata()),
 'originalEyeOwnerPixelCount':sum(v>0 for v in oldeye.getdata()),
 'newEyeOwnerPixelCount':sum(v>0 for v in eyemask.getdata()),
 'underpaintSHA256':sha(D/'hidden-face.reassigned.png'),
 'newHairSHA256':sha(D/'bangs.without-source-eyelash.png'),
 'sourcePartSHA256':{name:sha(D/f'part-{name}.png') for name in masks},
 'sourceMaskSHA256':{name:sha(D/f'owner-{name}.png') for name in masks},
 'underpaintChangedVsP1584':delta(under_new,under),
 'hairVisibleChangedVsP1584':visible_delta(hairnew,hair),
 'restVisiblePixelDiff':visible_diff,'restAlphaPixelDiff':alpha_diff,
 'restRawRGBAEqual':rt==src,
 'stationaryDarkPixelsBefore':dark(static_before),'stationaryDarkPixelsAfter':dark(static_after),
 'frameQA':frames,'newModelCalls':0,'newCloneOperations':0,
 'formalArtMeshAccepted':False,'formalKeyframeAccepted':False,
 'visualGate':'PENDING_RENDER_REVIEW'}
(R/'evidence/p15-86-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'ownerTransfer':q['transferredBangToEyePixels'],'staticDarkBefore':q['stationaryDarkPixelsBefore'],'staticDarkAfter':q['stationaryDarkPixelsAfter'],'restVisibleDiff':visible_diff,'frames':frames},ensure_ascii=False))

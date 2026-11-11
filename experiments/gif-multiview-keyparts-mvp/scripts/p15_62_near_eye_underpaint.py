#!/usr/bin/env python3
"""P15-62 local source-derived skin underpaint prototype; no generated or approved art implied."""
import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter,ImageChops
R=Path(__file__).resolve().parents[1];P=R/'private-assets'
D=P/'exports/p15-62-near-eye-underpaint';D.mkdir(parents=True,exist_ok=True)
SRC=P/'exports/p15-56-edge-matting/candidate-erode-2.png'
im=Image.open(SRC).convert('RGBA')
assert im.size==(1024,1024)
# Polygon isolates the visible eye and its lash silhouette. Avoid nearby fringe strands.
poly=[(522,449),(535,430),(565,420),(606,421),(637,436),(652,457),(650,480),(636,503),(613,516),(581,516),(552,505),(533,486)]
mask=Image.new('L',im.size,0);ImageDraw.Draw(mask).polygon(poly,fill=255)
# The underpaint is cloned from an adjacent clean cheek patch, not model-generated.
# Crop is selected away from nose/mouth and scaled to the eye footprint.
donor=im.crop((542,535,647,635)).resize((145,125),Image.Resampling.BICUBIC)
# Match donor's average RGB to the immediate skin ring around the removal mask.
import statistics
ring=mask.filter(ImageFilter.MaxFilter(31))
ring=ImageChops.subtract(ring,mask)
ring_pixels=[]
for y in range(400,545):
    for x in range(500,675):
        if ring.getpixel((x,y))>200:
            r,g,b,a=im.getpixel((x,y))
            if a>200 and r>180 and g>130 and b>130 and r-g<65:
                ring_pixels.append((r,g,b))
donor_pixels=list(donor.convert('RGB').getdata())
if not ring_pixels: raise AssertionError('No nearby skin ring for color matching')
means=[sum(v[i] for v in ring_pixels)/len(ring_pixels) for i in range(3)]
dmeans=[sum(v[i] for v in donor_pixels)/len(donor_pixels) for i in range(3)]
pix=[]
for r,g,b in donor_pixels:
    pix.extend([max(0,min(255,round(r+means[0]-dmeans[0]))),
                max(0,min(255,round(g+means[1]-dmeans[1]))),
                max(0,min(255,round(b+means[2]-dmeans[2])))])
donor=Image.frombytes('RGB',donor.size,bytes(pix)).convert('RGBA')
# Shift donor up; preserve candidate texture and local average skin color.
under=im.copy()
under.paste(donor,(515,412))
# Feather the fill edge; avoid modifying pixels outside the removal ROI.
soft=mask.filter(ImageFilter.GaussianBlur(8.0))
under=Image.composite(under,im,soft)
# Keep the source eye as a separately movable RGBA layer.
eye=Image.composite(im,Image.new('RGBA',im.size,(0,0,0,0)),mask)
eye.save(D/'eye.near.cutout.png')
under.save(D/'skin.underpaint.png')
# Shift eye 18px right over underpaint.
shifted=Image.new('RGBA',im.size,(0,0,0,0));shifted.alpha_composite(eye,(18,0))
preview=under.copy();preview.alpha_composite(shifted)
preview.save(D/'eye-shift-18px.png')
# Difference / coverage diagnostics.
# Mask's original opaque eye footprint must now be skin, with no alpha holes.
old_a=im.getchannel('A');new_a=preview.getchannel('A')
old_hole=sum(1 for a,b in zip(old_a.crop((515,410,675,535)).getdata(),new_a.crop((515,410,675,535)).getdata()) if a>128 and b<32)
# Confirm underpaint fully opaque within central eye footprint.
center=Image.new('L',im.size,0);ImageDraw.Draw(center).polygon(poly,fill=255)
coverage=ImageChops.multiply(center,new_a)
missing=sum(1 for m,a in zip(center.getdata(),new_a.getdata()) if m>0 and a<250)
# Measure source change strictly within removal ROI and outside unchanged area.
diff=ImageChops.difference(im,under)
outside=ImageChops.subtract(diff.getchannel('A'),mask)
outside_changed=sum(1 for v in outside.getdata() if v>0)
# Face comparison.
for name,x in [('source',im),('underpaint',under),('shifted',preview)]:
 x.crop((470,390,760,660)).resize((870,810),Image.Resampling.LANCZOS).save(D/f'{name}-face.png')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
q={'schema':'KOMA-P15-62-NEAR-EYE-UNDERPAINT-V1','characterId':'p0_character_001',
 'sourceSHA256':sha(SRC),'sourceMethod':'LOCAL_CHEEK_TEXTURE_CLONE_COLOR_MATCHED_AND_FEATHERED_NOT_AI_INPAINT',
 'donorRect':[542,535,647,635],'eyeMaskPolygon':poly,'eyeMovePx':[18,0],
 'eyeCutoutSHA256':sha(D/'eye.near.cutout.png'),'underpaintSHA256':sha(D/'skin.underpaint.png'),
 'shiftedPreviewSHA256':sha(D/'eye-shift-18px.png'),
 'transparentHolePixelsNearEyeROI':old_hole,'opaqueCoverageMissingPixelsInEyePolygon':missing,
 'outsideMaskChangedPixels':outside_changed,
 'sourceVisiblePixelExactOutsideMask':outside_changed==0,
 'hiddenSkinAuthenticallyReconstructed':False,'methodIsIndependentOriginalPainting':False,
 'visualGate':'PENDING_REVIEW','formalArtMeshAccepted':False,'formalKeyframeAccepted':False}
(R/'evidence/p15-62-near-eye-underpaint-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:q[k] for k in ['transparentHolePixelsNearEyeROI','opaqueCoverageMissingPixelsInEyePolygon','outsideMaskChangedPixels','sourceMethod']}))

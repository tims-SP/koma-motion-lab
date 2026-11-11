#!/usr/bin/env python3
"""Inspect semantic extraction feasibility on P15-56. Visible cutouts are NOT independently painted ArtMesh."""
import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageStat
R=Path(__file__).resolve().parents[1]
P=R/'private-assets';D=P/'exports/p15-61-semantic-feasibility';D.mkdir(parents=True,exist_ok=True)
SRC=P/'exports/p15-56-edge-matting/candidate-erode-2.png'
SOURCE45=P/'p5-see-through/yaw045/integrated/parts'
CLIP=P/'exports/p15-56-edge-matting/clip-erode-2.png'
UNDER=P/'exports/p15-55-registration/underlay--28.png'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
target=Image.open(SRC).convert('RGBA')
size=target.size
assert size==(1024,1024)
# Each manually scoped ROI is only a visible-pixel sample. The masks contain
# neighboring skin/hair, so do not label them as production segmentation.
polys={
 'eye.near':[(536,421),(561,411),(640,417),(661,464),(646,513),(567,525),(532,486)],
 'eye.far':[(691,430),(715,424),(745,438),(749,499),(716,517),(698,499)],
 'nose':[(687,503),(725,511),(739,550),(709,562),(685,545)],
 'mouth':[(645,569),(704,567),(722,600),(667,614),(643,594)],
 'hair.ahoge':[(438,12),(461,12),(484,36),(555,40),(611,58),(646,111),(625,157),(602,157),(575,122),(548,106),(513,112),(461,92),(429,56)],
}
# Compose samples as a priority-exclusive partition of the original RGBA.
# This guarantees exact endpoint reassembly, but not hidden underpaint.
roles=['hair.ahoge','eye.far','eye.near','nose','mouth']
occupied=Image.new('L',size,0)
cutouts={}
for role in roles:
    mask=Image.new('L',size,0);ImageDraw.Draw(mask).polygon(polys[role],fill=255)
    mask=ImageChops.subtract(mask,occupied)
    occupied=ImageChops.lighter(occupied,mask)
    im=Image.composite(target,Image.new('RGBA',size,(0,0,0,0)),mask)
    cutouts[role]=im;im.save(D/(role+'.visible.png'))
    origin=SOURCE45/(role+'.png')
    if origin.is_file():
        Image.open(origin).convert('RGBA').save(D/(role+'.source45.png'))
# Real registered clip alpha is independent, and has a reconstructed supporting underlay.
clip=Image.open(CLIP).convert('RGBA')
clip.save(D/'hair.clip.cross_gold.independent.png')
# Remaining original visible image excluding the five ROIs; includes hair, skin,
# ear and body fused together. It is NOT a separate clean underpaint for eyes.
residual=Image.composite(Image.new('RGBA',size,(0,0,0,0)),target,occupied)
residual.save(D/'remaining.visible.composite.png')
reconstructed=residual.copy()
for role in roles:
    reconstructed=Image.alpha_composite(reconstructed,cutouts[role])
reconstructed.save(D/'reconstructed.png')
assert ImageChops.difference(reconstructed,target).getbbox() is None
# The target clip remains in the residual, so it is not composited a second time;
# the independent clip + P15-55 underlay must be used as a different layer path.
real_clip_composite=Image.alpha_composite(Image.open(UNDER).convert('RGBA'),clip)
assert ImageChops.difference(real_clip_composite,target).getbbox() is None
# A moved near-eye visible cutout leaves a transparent hole, illustrating why visible
# ROIs are insufficient for view-dependent ArtMesh deformation.
moved=Image.new('RGBA',size,(0,0,0,0))
moved.alpha_composite(cutouts['eye.near'],(18,0))
preview=residual.copy()
for role in roles:
    preview=Image.alpha_composite(preview,moved if role=='eye.near' else cutouts[role])
preview.save(D/'eye-shift-with-hole.png')
# Region of missing source pixels in original near-eye crop where the layer moved.
hole_region=(536,410,661,529)
a=target.crop(hole_region).getchannel('A')
b=preview.crop(hole_region).getchannel('A')
holes=sum(1 for aa,bb in zip(a.getdata(),b.getdata()) if aa>128 and bb<32)
for n,im in [('source45',Image.open(P/'p2-views/whole/yaw045.png').convert('RGBA')),
             ('target65',target),('eye-shift-with-hole',preview)]:
    im.crop((425,320,820,700)).resize((592,570),Image.Resampling.LANCZOS).save(D/(n+'-face.png'))
stats=[]
for role in roles:
    im=cutouts[role]
    alpha=im.getchannel('A')
    stats.append({'role':role,'cutoutSHA256':sha(D/(role+'.visible.png')),
                  'alphaBBox':list(alpha.getbbox()),'pixelsVisible':sum(v>0 for v in alpha.getdata()),
                  'source45Available':(SOURCE45/(role+'.png')).is_file(),
                  'trueSemanticPurityVerified':False,'hiddenUnderpaintAvailable':False,
                  'cutoutIncludesBackgroundFeatures':True})
q={'schema':'KOMA-P15-61-SEMANTIC-FEASIBILITY-V1',
   'characterId':'p0_character_001',
   'candidateSHA256':sha(SRC),'canonical45SHA256':sha(P/'p2-views/whole/yaw045.png'),
   'realIndependentClipSHA256':sha(CLIP),'realClipReconstructionExact':True,
   'visibleROIroles':stats,'roiLayerCount':len(stats),
   'desiredRoleCount':13,'remainingFusedRoles':['hair.back','hair.front','hair.side','face.skin','ear.near','ear.far','body.reference'],
   'reconstruction':{'sha256':sha(D/'reconstructed.png'),'pixelExact':True,
       'meaning':'Only re-partitions currently visible pixels; exact reassembly does not imply independent ArtMesh'},
   'movingEye':{'offsetPx':[18,0],'transparentHolePixelsInNearEyeROI':holes,
      'previewSHA256':sha(D/'eye-shift-with-hole.png'),
      'finding':'Moving a visible ROI uncovers absent hidden skin and produces texture double edges'},
   'clipSeparableFromPriorWork':True,
   'independentUnderpaintForEyesAndFace':False,
   'semanticSeparationGate':'FAIL_VISIBLE_ROI_NOT_INDEPENDENT_PAINT',
   'viewDependentVDDGate':'FAIL_MISSING_UNDERPAINT_AND_ROLE_BOUNDARIES',
   'formalKeyframeAccepted':False,'formalArtMeshModified':False,
   'next':'Generate or paint hidden face and hair underlayers for the new relative +20-degree candidate and obtain clean eye/nose/mouth semantic masks before VDD warping.'}
assert holes>100
(R/'evidence/p15-61-semantic-feasibility-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'roiLayers':len(stats),'reassembledPixelExact':True,'eyeShiftHolePixels':holes,'semanticGate':q['semanticSeparationGate']}))

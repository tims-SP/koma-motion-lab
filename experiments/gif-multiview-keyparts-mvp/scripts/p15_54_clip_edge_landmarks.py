#!/usr/bin/env python3
"""Refine detached clip-edge remnants and document manual landmark comparison."""
import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-54-edge-landmark-review';D.mkdir(parents=True,exist_ok=True)
src=R/'private-assets/exports/p15-53-gold-clip-repair/candidate-gold-cross-restored.png'
im=Image.open(src).convert('RGBA')
# Only remove the detached pink fragment visible outside the right hair silhouette below the clip.
# This is a narrow, hand-reviewed polygon; it does not intersect the gold clip alpha mask.
mask=Image.new('L',im.size,0)
md=ImageDraw.Draw(mask)
md.polygon([(769,351),(783,350),(782,377),(772,378),(766,369)],fill=255)
clip=Image.open(R/'private-assets/exports/p15-53-gold-clip-repair/hair.clip.cross_gold.png').convert('RGBA')
# Protect any gold clip pixels if polygon overlaps anti-aliased edge.
clip_alpha=clip.getchannel('A')
remove=Image.eval(mask,lambda v:v)
pix=im.load();m=remove.load();ca=clip_alpha.load();removed=0
for y in range(350,379):
 for x in range(765,784):
  if m[x,y] and ca[x,y]<12:
   r,g,b,a=pix[x,y]
   if a:
    pix[x,y]=(r,g,b,0);removed+=1
im.save(D/'candidate-refined.png')
# Visual overlays. Manual estimates are explicit and have +-8px uncertainty, not machine vision.
landmarks=[
 {'name':'near_eye_iris','measured':[603,461],'expected':[604.739,460.617],'uncertainty_px':8,'source':'manual_visual_estimate'},
 {'name':'far_eye_iris','measured':[730,469],'expected':[729.373,469.040],'uncertainty_px':8,'source':'manual_visual_estimate'},
 {'name':'nose_tip','measured':[716,536],'expected':[716.341,535.644],'uncertainty_px':8,'source':'manual_visual_estimate'},
 {'name':'mouth_center','measured':[683,597],'expected':[684.097,596.867],'uncertainty_px':8,'source':'manual_visual_estimate'},
 {'name':'chin','measured':[637,661],'expected':[637.199,660.889],'uncertainty_px':8,'source':'manual_visual_estimate'},
 {'name':'gold_clip_center','measured':[753,323],'expected':[789.948,320.1],'uncertainty_px':8,'source':'manual_visual_estimate'}
]
annot=im.copy();d=ImageDraw.Draw(annot)
for item in landmarks:
 x,y=item['measured'];ex,ey=item['expected']
 d.ellipse((x-7,y-7,x+7,y+7),outline=(0,235,255,255),width=3)
 d.line((x-12,y,x+12,y),fill=(0,235,255,255),width=2);d.line((x,y-12,x,y+12),fill=(0,235,255,255),width=2)
 d.ellipse((ex-5,ey-5,ex+5,ey+5),outline=(255,50,160,255),width=2)
 d.line((x,y,ex,ey),fill=(255,220,0,255),width=2)
annot.save(D/'landmark-comparison.png')
# Crops, before/after and all-background previews
for n,p in [('before',Image.open(src).convert('RGBA')),('after',im)]:
 p.crop((690,255,825,400)).resize((810,870),Image.Resampling.LANCZOS).save(D/(n+'-clip-detail.png'))
for name,bg in [('light',(238,240,247,255)),('blue',(65,115,176,255)),('pink',(244,199,214,255))]:
 plate=Image.new('RGBA',im.size,bg);plate.alpha_composite(im);plate.convert('RGB').save(D/('preview-'+name+'.png'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for item in landmarks:
 x,y=item['measured'];ex,ey=item['expected']
 item['delta_px']=[round(x-ex,2),round(y-ey,2)]
 item['distance_px']=round(((x-ex)**2+(y-ey)**2)**.5,2)
qa={
 'schema':'KOMA-P15-54-EDGE-LANDMARK-QA-V1',
 'inputSHA256':sha(src),'outputSHA256':sha(D/'candidate-refined.png'),
 'refinedPixels':removed,'edgeCleanup':'manual narrow polygon below right clip, protects detached gold clip alpha',
 'landmarks':landmarks,
 'landmarkInterpretation':'Eye, nose, mouth and chin manually estimated and fall within 8px of projected anchor points. Hair clip center differs by about 37px. These anchor points include two-view extrapolation and orthographic proxy; this comparison is not calibrated camera yaw proof.',
 'cameraYaw65Verified':False,'formalKeyframeAccepted':False,'artMeshModified':False,
 'clipEdgeStatus':'IMPROVED_BUT_REQUIRES_VISUAL_REVIEW',
 'identityStatus':'FACE_LANDMARKS_CONSISTENT_WITH_PROXY; CLIP_ANCHOR_OFFSET_REMAINS_UNRESOLVED'
}
(R/'evidence/p15-54-edge-landmark-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'removedPixels':removed,'landmarks':[(x['name'],x['distance_px']) for x in landmarks],'sha':qa['outputSHA256']}))

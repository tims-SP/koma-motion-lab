#!/usr/bin/env python3
"""Authored correspondence prototypes over original independent P0 keyview canvases."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-98-anchor-review';D.mkdir(parents=True,exist_ok=True)
sources={
 '52p5':P/'p15-93-yaw0525-review/yaw052p5-registered.png',
 '60':P/'p15-92-angle-keyart/yaw060-registered.png',
 '75':P/'p15-92-angle-keyart/yaw075-registered.png'
}
# Landmarks are manually estimated visual proxies, NOT measured/artist-approved geometry.
# Coordinates refer to native 1024x1024 source space.
features={
 '52p5':{
  'eye.near.center':[573,458],'eye.near.outer':[511,449],'eye.near.inner':[622,455],
  'eye.far.center':[721,459],'eye.far.inner':[704,453],
  'brow.near':[570,384],'nose.bridge':[741,496],
  'nose.tip':[742,524],'mouth':[705,564],'chin':[684,636],
  'cheek':[607,555],'ear.center':[468,481],
  'hair.front.root':[679,319],'hair.front.tip':[699,457],
  'hair.clip':[765,350],'hair.crown':[601,202],
  'shoulder':[550,781]},
 '60':{
  'eye.near.center':[646,459],'eye.near.outer':[588,449],'eye.near.inner':[695,454],
  'eye.far.center':[736,459],'eye.far.inner':[724,452],
  'brow.near':[650,382],'nose.bridge':[757,488],
  'nose.tip':[772,527],'mouth':[729,563],'chin':[706,638],
  'cheek':[665,548],'ear.center':[486,492],
  'hair.front.root':[704,320],'hair.front.tip':[729,468],
  'hair.clip':[765,350],'hair.crown':[606,202],
  'shoulder':[552,781]},
 '75':{
  'eye.near.center':[688,455],'eye.near.outer':[646,450],'eye.near.inner':[724,454],
  'eye.far.center':[772,447],'eye.far.inner':[768,447],
  'brow.near':[686,376],'nose.bridge':[783,487],
  'nose.tip':[807,517],'mouth':[775,556],'chin':[745,633],
  'cheek':[710,559],'ear.center':[497,466],
  'hair.front.root':[734,324],'hair.front.tip':[764,473],
  'hair.clip':[766,346],'hair.crown':[621,204],
  'shoulder':[563,784]}
}
# Far-eye correspondence is a visibility proxy as far eye occludes near 75°.
selected=['eye.near.center','eye.near.outer','eye.near.inner','eye.far.center',
 'nose.bridge','nose.tip','mouth','chin','cheek','ear.center',
 'hair.front.root','hair.front.tip','hair.clip','hair.crown','shoulder']
background={'top-left':[15,15],'top-right':[1007,15],'bottom-left':[15,1007],'bottom-right':[1007,1007],
 'mid-left':[15,512],'mid-right':[1007,512],'top-mid':[512,15],'bottom-mid':[512,1007]}
q={'schema':'KOMA_P15_98_LANDMARK_PROXIES_V1','characterId':'p0_character_001',
 'coordinateSystem':'source RGBA 1024x1024','landmarkOrigin':'visual proxies for controlled hypothesis test',
 'geometryMeasured':False,'artistApproved':False,
 'sourceSHA256':{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in sources.items()},
 'viewLandmarks':features,'correspondenceRoles':selected,'fixedCanvasAnchors':background,
 'farEyeVisibleByView':{'52p5':True,'60':True,'75':False}}
(R/'evidence/p15-98-landmarks.json').write_text(json.dumps(q,indent=2,ensure_ascii=False)+'\n')
panel=Image.new('RGB',(512*3,540),'white');draw=ImageDraw.Draw(panel)
for index,(view,source) in enumerate(sources.items()):
 img=Image.open(source).convert('RGBA')
 white=Image.new('RGBA',img.size,'white');white.alpha_composite(img)
 tile=white.convert('RGB').resize((512,512),Image.Resampling.LANCZOS)
 panel.paste(tile,(index*512,25))
 draw.text((index*512+7,6),f'Yaw {view} landmark visual proxies',fill='black')
 for n,name in enumerate(selected):
  x,y=features[view][name]
  px=index*512+x//2;py=25+y//2
  color=(20,90,210) if name.startswith('eye') else (190,40,40) if name.startswith('hair') else (30,145,60)
  draw.ellipse([px-3,py-3,px+3,py+3],fill=color)
  if name in ('eye.near.center','eye.far.center','nose.tip','chin','hair.front.tip','hair.front.root'):
   draw.text((px+4,py-12),name.split('.')[-1],fill=color)
panel.save(D/'source-landmark-overview.jpg',quality=94)
print('LANDMARKS',len(selected),'VIEW',list(sources),'contact',D/'source-landmark-overview.jpg')

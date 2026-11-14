#!/usr/bin/env python3
"""Reviewable manual semantic correspondences for the 90–135° P0 rear arc.

Coordinates are first-pass inspection proposals, not ground-truth anatomical anchors.
Visibility is explicit; missing features are never represented as coordinate (0,0).
"""
import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from p15_129_ahoge_ownership import keyframes
ROOT=Path(__file__).resolve().parent.parent
P=ROOT/'private-assets';OUT=P/'exports/p15-131-semantic-landmarks'
E=ROOT/'evidence/p15-131-semantic-landmarks-qa.json'
# These are approximate initial image-space picks from actual 443×443 keyview paintings.
# Keep visibility distinct from geometry: an unseen eye/garment tip has no landmark.
POINTS={
 'hair.ahoge.root':{'90':[205,65],'112.5':[294,72],'135':[264,67]},
 'hair.ahoge.apex':{'90':[233,5],'112.5':[288,21],'135':[258,8]},
 'hair.crown':{'90':[229,57],'112.5':[254,67],'135':[250,63]},
 'hair.back.tip':{'90':[116,279],'112.5':[144,272],'135':[167,283]},
 'ear.center':{'90':[239,244],'112.5':[256,254],'135':[310,268]},
 'eye.near.center':{'90':[291,218],'112.5':[316,218],'135':None},
 'nose.tip':{'90':[340,248],'112.5':[325,251],'135':[329,273]},
 'chin':{'90':[289,299],'112.5':[307,282],'135':[305,287]},
 'collar.back.center':{'90':[208,332],'112.5':[215,322],'135':[221,320]},
 'shoulder.near.outer':{'90':[152,369],'112.5':[161,364],'135':[178,355]},
 'jacket.gold.trim':{'90':[159,365],'112.5':[200,341],'135':[217,336]},
 'bow.center':{'90':[251,369],'112.5':[271,362],'135':None}
}
MOTIONS={'hair.ahoge.root':'top-hair','hair.ahoge.apex':'top-hair','hair.crown':'head',
'hair.back.tip':'back-hair','ear.center':'face/hair boundary','eye.near.center':'face visibility',
'nose.tip':'face visibility','chin':'face visibility','collar.back.center':'neck-to-coat',
'shoulder.near.outer':'shoulder','jacket.gold.trim':'coat trim','bow.center':'front-to-back garment visibility'}

def source_hash(arr):return hashlib.sha256(arr.tobytes()).hexdigest()
def audit(save=True):
  sources=keyframes(); angles=[90,112.5,135]
  issues=[];motions={};entries={}
  for key,per_view in POINTS.items():
    vals=[]
    for angle in angles:
      p=per_view[str(angle)]
      if p is not None:
        x,y=p
        if not (0<=x<443 and 0<=y<443):issues.append({'role':key,'angle':angle,'issue':'off-canvas'})
        # A visible feature should be near source opacity. A radius tolerance is
        # diagnostic, not an assertion of anatomical identity.
        s=sources[float(angle)][...,3]
        x0,x1=max(0,x-12),min(443,x+13);y0,y1=max(0,y-12),min(443,y+13)
        nearby=int(s[y0:y1,x0:x1].max())
        if nearby<32:issues.append({'role':key,'angle':angle,'issue':'not-near-painted-foreground'})
      vals.append(p)
    entries[key]={'motionGroup':MOTIONS[key],'coordinates':{str(a):v for a,v in zip(angles,vals)},
                  'visible':[a for a,v in zip(angles,vals) if v is not None],
                  'classification':'proposed manual image-space landmark; artwork registration pending'}
    if vals[0] is not None and vals[1] is not None and vals[2] is not None:
      v0=np.asarray(vals[0],dtype=np.float32);vm=np.asarray(vals[1],dtype=np.float32);v1=np.asarray(vals[2],dtype=np.float32)
      deviation=float(np.linalg.norm(vm-(v0+v1)*.5))
      motions[key]={'midpointDeviationPx':round(deviation,3),
                    'segmentDistancesPx':[round(float(np.linalg.norm(vm-v0)),3),round(float(np.linalg.norm(v1-vm)),3)]}
  report={'schema':'KOMA_P15_131_SEMANTIC_LANDMARK_REVIEW_V1','characterId':'p0_character_001',
          'angles':angles,'coordinateSpace':'native reference 443×443 resized review raster',
          'nativeKeySHA256RGBA':{str(a):source_hash(sources[float(a)]) for a in angles},
          'landmarks':entries,'geometryDiagnostics':motions,'warnings':issues,
          'manualProposalsCount':len(entries),'threeViewVisibleCount':sum(all(per_view[str(a)] is not None for a in angles) for per_view in POINTS.values()),
          'artistVerifiedLandmarks':False,'physical3DAnchorVerified':False,
          'faceFeatureVisibilityMode':'explicit; missing far-side features marked null',
          'renderIntegrationAccepted':False,'visualAccepted':False,
          'next':'Correct highlighted art-space landmarks against source pixels; extract individually painted hair/ear/collar/shoulder masks and true underpaint for constrained ArtMesh VDD.'}
  if save:
    OUT.mkdir(parents=True,exist_ok=True)
    labels=list(POINTS)
    canvas=Image.new('RGB',(443*3,520),(37,43,53));d=ImageDraw.Draw(canvas)
    for i,angle in enumerate(angles):
      arr=sources[float(angle)]
      tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(arr,'RGBA'))
      canvas.paste(tile.convert('RGB'),(443*i,34))
      d.text((443*i+10,9),f'yaw {angle:g}° — landmark proposals',fill='white')
      for n,role in enumerate(labels):
        pos=POINTS[role][str(angle)]
        if pos is None:continue
        x,y=pos;xp=x+443*i
        color=(255,205,64) if 'hair' in role else ((97,225,238) if any(k in role for k in ('eye','nose','chin','ear')) else (148,242,160))
        d.ellipse((xp-3,y+34-3,xp+3,y+34+3),outline='black',fill=color,width=1)
        d.text((xp+5,y+34-6),str(n+1),fill=color,stroke_width=1,stroke_fill=(18,20,25))
    d.text((10,492),'1 ahoge root · 2 apex · 3 crown · 4 back tip · 5 ear · 6 eye · 7 nose · 8 chin · 9 collar · 10 shoulder · 11 trim · 12 bow',fill='white')
    canvas.save(OUT/'review.jpg',quality=94)
    (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 semantic anchor review</title><style>body{background:#202733;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>90° / 112.5° / 135° semantic correspondence proposals</h2><p>Numbers identify candidate landmarks. Eye and bow are explicitly absent where occluded. Coordinates need visual approval before deforming source art.</p><img src="review.jpg">')
    report['review']='private-assets/exports/p15-131-semantic-landmarks/index.html'
    E.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
  return report
if __name__=='__main__':
  q=audit();print(json.dumps({'roles':q['manualProposalsCount'],'allVisibleRoles':q['threeViewVisibleCount'],'warnings':q['warnings'],'deviations':{k:v['midpointDeviationPx'] for k,v in q['geometryDiagnostics'].items()}},indent=2))

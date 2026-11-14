#!/usr/bin/env python3
"""Evaluate bounded local landmark displacement on 90–135° inbetween render frames."""
import json,sys
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from p15_128_keyart_registration import jumps
from p15_129_ahoge_ownership import keyframes,KEYS,ANGLES
from p15_131_semantic_landmarks import POINTS
P=ROOT/'private-assets';OUT=P/'exports/p15-132-landmark-vdd';E=ROOT/'evidence/p15-132-landmark-vdd-qa.json'
ROLES=('hair.ahoge.root','hair.ahoge.apex','hair.crown','hair.back.tip','ear.center','nose.tip','chin','collar.back.center','shoulder.near.outer','jacket.gold.trim')

def key_name(angle):return f'yaw{angle:06.2f}'.replace('.','p')+'.png'
def baseline():
 return [np.asarray(Image.open(P/'exports/p15-129-ahoge-owner/nearest_key_owner'/key_name(a)).convert('RGBA')).copy() for a in ANGLES]
def remap_local(frame,angle,amount=0.5,radius=28,max_offset=10):
 if angle in KEYS:return frame.copy(),[]
 a,b=(90.,112.5) if angle<112.5 else (112.5,135.)
 t=(angle-a)/(b-a)
 h,w=frame.shape[:2];ys,xs=np.indices((h,w),dtype=np.float32)
 numerator_x=np.zeros((h,w),np.float32);numerator_y=np.zeros_like(numerator_x);denom=np.ones_like(numerator_x)
 used=[]
 for role in ROLES:
  pts=POINTS[role];p0=pts[f'{a:g}'];p1=pts[f'{b:g}']
  if p0 is None or p1 is None:continue
  start=np.array(p0,np.float32);end=np.array(p1,np.float32)
  # Source-owner position is a proxy: actual optical-flow tracked landmark is not available.
  owner=start if t<=0.5 else end
  goal=start*(1-t)+end*t
  delta=np.clip((goal-owner)*amount,-max_offset,max_offset)
  if float(np.linalg.norm(delta))<0.01:continue
  weight=np.exp(-((xs-goal[0])**2+(ys-goal[1])**2)/(2*radius*radius)).astype(np.float32)
  numerator_x+=weight*delta[0];numerator_y+=weight*delta[1];denom+=weight
  used.append({'role':role,'sourceXY':[float(v) for v in owner],'targetXY':[round(float(v),3) for v in goal],
               'offsetXY':[round(float(v),3) for v in delta]})
 dx=numerator_x/denom;dy=numerator_y/denom
 # Inverse warp for continuous pixel sampling; avoid changing pixels outside meaningful landmark neighborhoods.
 warped=cv2.remap(frame,xs-dx,ys-dy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
 return warped,used

def compare(save=True):
 source=baseline();keys=keyframes();variants={'source_owned':source};tracks={}
 for name,amount,radius in [('localized_025',.25,20),('localized_050',.5,28),('localized_075',.75,36)]:
  frames=[];trail=[]
  for angle,frame in zip(ANGLES,source):
   out,used=remap_local(frame,angle,amount,radius)
   frames.append(out);trail.append({'yaw':angle,'applied':used})
  variants[name]=frames;tracks[name]=trail
 scores={}
 for name,frames in variants.items():
  js=jumps(frames)
  scores[name]={'maxAdjacentCompositeRGBMAE':max(js),'adjacentCompositeRGBMAE':js,
               'nativeKeysPixelExact':all(np.array_equal(frames[ANGLES.index(a)],keys[a]) for a in KEYS)}
 result={'schema':'KOMA_P15_132_LANDMARK_VDD_ABLATION_V1','characterId':'p0_character_001',
         'angles':list(ANGLES),'anchorRoles':list(ROLES),'method':'localized bounded inverse displacement fields driven by 2D source-view landmark proposals',
         'methods':scores,'displacements':tracks,'sourceArtPreserved':True,'artistApprovedCorrespondence':False,
         'truePhysicalAnchorsVerified':False,'occludedUnderpaintAvailable':False,'visualAccepted':False,
         'review':'private-assets/exports/p15-132-landmark-vdd/index.html',
         'next':'Replace provisional point correspondences with verified per-part geometry and complete source-painted hidden surfaces; use actual face, hair and garment visibility control.'}
 if save:
  OUT.mkdir(parents=True,exist_ok=True)
  canvas=Image.new('RGB',(320*5,354*len(variants)),(35,41,49));draw=ImageDraw.Draw(canvas)
  for row,(name,frames) in enumerate(variants.items()):
   folder=OUT/name;folder.mkdir(exist_ok=True)
   for col,(angle,frame) in enumerate(zip(ANGLES,frames)):
    Image.fromarray(frame,'RGBA').save(folder/key_name(angle))
    tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
    canvas.paste(tile.convert('RGB').resize((315,315),Image.Resampling.LANCZOS),(col*320,row*354+29))
    draw.text((col*320+7,row*354+7),f'{name} / {angle:g}',fill='white')
  canvas.save(OUT/'comparison.jpg',quality=94)
  (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 semantic landmark local deformation</title><style>body{font:16px system-ui;background:#202832;color:#eee}img{max-width:100%}</style><h2>90–135° local landmark VDD diagnostic</h2><p>Source-owned baseline compared with bounded local displacement near provisional semantic landmarks. Physical correspondence and hidden art are still pending validation.</p><img src="comparison.jpg">')
  E.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
 return result
if __name__=='__main__':print(json.dumps(compare()['methods'],indent=2))

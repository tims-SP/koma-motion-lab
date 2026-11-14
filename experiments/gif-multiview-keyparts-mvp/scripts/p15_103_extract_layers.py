#!/usr/bin/env python3
"""Source-owned collar, bow, jewel and jacket ArtMesh candidates (60° / 75°).
One pixel has exactly one owner. Photometric bow detection is constrained to
its source-specific ROI; manual collar polygons encode layout, not true geometry.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import cv2,numpy as np,json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-103-parts';D.mkdir(exist_ok=True,parents=True)
S=1024
srcFiles={v:P/f'p15-97-multiview-motion/yaw{v}-frame-06.png' for v in ['60','75']}
# Artist-proxy garment boundaries on the source RGBA keyframe, not training labels.
collarPoly={
 '60':[(470,670),(585,676),(634,698),(702,669),(764,689),(779,741),(759,800),(686,843),(651,803),(591,809),(523,760)],
 '75':[(487,663),(593,668),(642,694),(708,675),(786,693),(795,752),(770,813),(699,849),(651,812),(592,811),(541,761)]
}
bowROI={'60':(500,751,768,961),'75':(527,748,780,974)}
jewelROI={'60':(595,770,679,860),'75':(608,770,686,857)}
# shoulder left/right outlines, 2D anchors; details separate from whole body.
shoulderProxy={'60':[(209,705),(330,686),(454,702),(497,746),(480,818),(399,859),(299,833)],
 '75':[(217,704),(330,690),(461,705),(516,746),(501,829),(405,870),(296,839)]}
sha=lambda x:sha256(Path(x).read_bytes()).hexdigest()
q={'schema':'KOMA_P15_103_SOURCE_OWNED_GARMENT_PARTS_V1',
   'characterId':'p0_character_001','segmentation':'HSV photometric seed + morphology + manual layout proxy',
   'sourceAngles':[60,75],'partOrder':['jacket','shoulder.left','collar','bow','jewel'],
   'sourceReassemblyExact':False,'partBoundariesArtistApproved':False,'views':{}}
def poly_mask(points):
 canvas=np.zeros((S,S),np.uint8)
 cv2.fillPoly(canvas,[np.asarray(points,dtype=np.int32)],255)
 return canvas
for view,f in srcFiles.items():
 src=np.asarray(Image.open(f).convert('RGBA'))
 opaque=src[:,:,3]>0
 hsv=cv2.cvtColor(src[:,:,:3],cv2.COLOR_RGB2HSV)
 # Native magenta cloth, 2 components at 60° / 1 at 75°, including shaded ribbons.
 x0,y0,x1,y1=bowROI[view]
 roi=np.zeros((S,S),np.uint8);roi[y0:y1,x0:x1]=255
 hue=hsv[:,:,0];sat=hsv[:,:,1];val=hsv[:,:,2]
 # Require a rose-red fabric hue, including darker folds.
 rose=((((hue>=142)&(hue<=179))|((hue<=7)&(sat>=65)))&(sat>45)&(val>38))
 rose=(rose&(roi>0)&opaque).astype(np.uint8)*255
 count,labels,stats,center=cv2.connectedComponentsWithStats(rose,8)
 chosen=np.zeros((S,S),np.uint8)
 for i in range(1,count):
  if stats[i,cv2.CC_STAT_AREA]>=65 and y0-5<center[i,1]<y1+5:
   chosen[labels==i]=255
 chosen=cv2.morphologyEx(chosen,cv2.MORPH_CLOSE,
                        cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(15,15)))
 chosen=cv2.dilate(chosen,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)))
 # Preserve voids in the ribbon while closing internal dark ink holes.
 num,lab,st,cent=cv2.connectedComponentsWithStats(chosen,8)
 valid=np.zeros((S,S),np.uint8)
 for i in range(1,num):
  if st[i,cv2.CC_STAT_AREA]>110:valid[lab==i]=255
 bow=valid.astype(bool)
 # Gold badge: HSV golden in a small ROI around measured x634 / x645, y811.
 goldROI=np.zeros((S,S),np.uint8)
 gx0,gy0,gx1,gy1=jewelROI[view];goldROI[gy0:gy1,gx0:gx1]=255
 gold=(((hue>=10)&(hue<=35))&(sat>=45)&(val>=45)&(goldROI>0)&opaque).astype(np.uint8)*255
 n,labels,stats,cent=cv2.connectedComponentsWithStats(gold,8)
 expected=np.array([634.46,810.55] if view=='60' else [644.12,807.09])
 options=[]
 for i in range(1,n):
  if stats[i,cv2.CC_STAT_AREA]>=40:
   options.append((float(np.linalg.norm(cent[i]-expected)),i))
 assert options,view
 ix=min(options)[1]
 gold=np.uint8(labels==ix)*255
 gold=cv2.dilate(gold,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(11,11)))
 jewel=gold>0
 # Collar region includes white upright collar, but not the bow or gold foreground.
 collar=(poly_mask(collarPoly[view])>0)&opaque
 shoulder=(poly_mask(shoulderProxy[view])>0)&opaque
 # Highest layer owns pixels; other jacket pixels become the base.
 ownership=np.zeros((S,S),np.uint8)
 for idx,mask in enumerate([shoulder,collar,bow,jewel],start=1):
  ownership[mask]=idx
 parts=q['partOrder']
 countBy={}
 out=D/f'yaw{view}';out.mkdir(exist_ok=True)
 restored=np.zeros_like(src)
 masks=[]
 for idx,role in enumerate(parts):
  condition=ownership==idx
  layer=np.zeros_like(src);layer[condition]=src[condition]
  # Preserve hidden transparent RGB by assigning every pixel exactly once.
  restored[condition]=layer[condition]
  mask=np.uint8(condition)*255
  partPath=out/f'{role.replace(".","_")}.png'
  maskPath=out/f'{role.replace(".","_")}-ownership.png'
  Image.fromarray(layer,'RGBA').save(partPath)
  Image.fromarray(mask).save(maskPath)
  countBy[role]={'pixels':int(condition.sum()),
     'opaquePixels':int(np.count_nonzero(condition&(src[:,:,3]>128))),
     'textureSHA256':sha(partPath),'maskSHA256':sha(maskPath)}
  masks.append(mask)
 reconstructed=out/'reconstructed.png'
 Image.fromarray(restored,'RGBA').save(reconstructed)
 assert np.array_equal(restored,src),'RGBA reconstruction mismatch'
 # Render compact source and layer previews.
 preview=Image.new('RGB',(320*len(parts),355),'white');draw=ImageDraw.Draw(preview)
 for idx,role in enumerate(parts):
  layer=Image.open(out/f'{role.replace(".","_")}.png').convert('RGBA')
  bg=Image.new('RGBA',layer.size,'white');bg.alpha_composite(layer)
  tile=bg.convert('RGB').crop((365,585,850,1015)).resize((320,328),Image.Resampling.LANCZOS)
  preview.paste(tile,(idx*320,26));draw.text((idx*320+6,4),f'{view} {role}',fill='black')
 preview.save(out/'parts-contact.jpg',quality=94)
 q['views'][view]={'sourceSHA256':sha(f),'sourceReconstructedPixelExact':True,
  'reconstructionSHA256':sha(reconstructed),'source':str(f.relative_to(R)),
  'partStats':countBy,
  'bowHSVBlobPx':int(np.count_nonzero(bow)),
  'jewelPx':int(np.count_nonzero(jewel)),
  'collarPolygon':collarPoly[view],'shoulderPolygon':shoulderProxy[view],
  'bowROI':bowROI[view],'jewelROI':jewelROI[view],
  'contact':str((out/'parts-contact.jpg').relative_to(R))}
 print(view,'parts', {k:v['opaquePixels'] for k,v in countBy.items()},flush=True)
q['sourceReassemblyExact']=True
(R/'evidence/p15-103-parts-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')

#!/usr/bin/env python3
"""Register native Codex 67.5° garment to the 1024-source character canvas.

Native 1254 PNG is preserved exactly. Registration uses *native real gold brooch*
centroid, not invented pose anchors. All spatial changes are measured and saved.
"""
from pathlib import Path
from hashlib import sha256
from PIL import Image,ImageDraw
import json,cv2,numpy as np
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
N=R/'private-assets/p15-105-yaw0675';D=P/'p15-105-middle-art';D.mkdir(parents=True,exist_ok=True)
sha=lambda p:sha256(Path(p).read_bytes()).hexdigest()
src=N/'yaw0675-garment-native.png'
j=json.loads((N/'generation-result.json').read_text())
assert j['actual_image_tool_used']=='image_gen.imagegen'
assert j['sha256']==sha(src)
original=Image.open(src)
assert original.mode=='RGBA' and original.size==(1254,1254)
native=np.asarray(original)
scaled=np.asarray(original.resize((1024,1024),Image.Resampling.LANCZOS)).copy()
hsv=cv2.cvtColor(scaled[:,:,:3],cv2.COLOR_RGB2HSV)
h,s,v=cv2.split(hsv)
opaque=scaled[:,:,3]>128
gold=np.uint8(((h>=9)&(h<=37)&(s>70)&(v>70)&opaque))*255
valid=np.zeros((1024,1024),np.uint8);valid[650:900,535:760]=255
gold=cv2.bitwise_and(gold,valid)
n,labels,stats,cent=cv2.connectedComponentsWithStats(gold,8)
choices=[]
for i in range(1,n):
 cx,cy=cent[i];area=int(stats[i,cv2.CC_STAT_AREA])
 if area<15:continue
 distance=np.linalg.norm([cx-642,cy-791])
 if distance>90:continue
 choices.append((area/(1+distance/32),i,area,float(distance),[float(cx),float(cy)]))
assert choices,'Unable to locate native golden brooch in garment artwork'
choices.sort(reverse=True);q=choices[0]
observed=np.asarray(q[4],dtype=np.float32)
target=np.asarray([639.29,808.82],dtype=np.float32)
delta=target-observed
assert max(np.abs(delta))<95,(observed,delta)
matrix=np.float32([[1,0,delta[0]],[0,1,delta[1]]])
registered=cv2.warpAffine(scaled,matrix,(1024,1024),flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
# Tiny alpha (<8) from native imagegen is not content and stays recorded as native QA.
registered[:,:,3][registered[:,:,3]<=8]=0
out=D/'yaw067p5-garment-registered.png'
Image.fromarray(registered,'RGBA').save(out)
# Alpha>128 must not put body into head pose region; upper neck can start >=600.
y,x=np.where(registered[:,:,3]>128)
assert len(x)>70000,('garment area',len(x))
bbox=[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]
upper=int((registered[:575,:,3]>128).sum())
assert upper==0,('garment overlaps face region',upper)
alpha=int(np.sum(registered[:,:,3]>128))
# Rose bow ink and gold trim still present in unique expected position.
HSV=cv2.cvtColor(registered[:,:,:3],cv2.COLOR_RGB2HSV)
hh,ss,vv=cv2.split(HSV)
roi=registered[680:970,495:820]
hh2=hh[680:970,495:820];ss2=ss[680:970,495:820];vv2=vv[680:970,495:820]
bowMask=((((hh2>=142)&(hh2<=179))|(hh2<=8))&(ss2>45)&(vv2>50)&(roi[:,:,3]>128))
bowPixels=int(bowMask.sum())
assert bowPixels>8000,('bow region missing',bowPixels)
# Three-source contact sheet in garment ROI, all white for display only.
sample=[
 ('60° original',P/'p15-97-multiview-motion/yaw60-frame-06.png'),
 ('67.5° new source',out),
 ('75° original',P/'p15-97-multiview-motion/yaw75-frame-06.png')
]
sheet=Image.new('RGB',(455*3,405),'white');draw=ImageDraw.Draw(sheet)
for idx,(label,path) in enumerate(sample):
 im=Image.open(path).convert('RGBA');bg=Image.new('RGBA',im.size,'white');bg.alpha_composite(im)
 crop=bg.convert('RGB').crop((335,615,865,1015)).resize((455,380),Image.Resampling.LANCZOS)
 sheet.paste(crop,(idx*455,25));draw.text((idx*455+8,4),label,fill='black')
sheet.save(D/'native-garment-contact.jpg',quality=94)
qa={'schema':'KOMA_P15_105_NATIVE_MIDDLE_GARMENT_QA_V1',
 'model':'Codex built-in image_gen.imagegen',
 'character':'p0_character_001','requestedAngle':67.5,
 'nativePath':str(src.relative_to(R)),'nativeSHA256':sha(src),
 'nativeDimensions':[1254,1254],'nativeRGBA':True,
 'registeredPath':str(out.relative_to(R)),'registeredSHA256':sha(out),
 'registeredDimensions':[1024,1024],
 'registration':'native golden brooch centroid to mean original source golden brooch',
 'nativeGoldMeasuredCanvas1024':observed.round(4).tolist(),
 'sourceTargetGoldCenter':target.tolist(),
 'translation1024':delta.round(3).tolist(),
 'goldSourceComponentArea':q[2],
 'sourceContentBBox':bbox,
 'registeredOpaquePixels':alpha,'bowHuePixels':bowPixels,
 'opaqueAboveFaceROI':upper,'nativeImagePreserved':True,
 'angleGeometricallyVerified':False,'artStyleArtistApproved':False,
 'visualObservations':['single source bow and gold brooch visible',
  'source garment registered by measured brooch centroid',
  'collar height and natural cloth folds must be evaluated in continuous sequence'],
 'contact':'private-assets/exports/p15-105-middle-art/native-garment-contact.jpg'}
(R/'evidence/p15-105-native-art-qa.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({k:qa[k] for k in ('nativeSHA256','nativeDimensions','nativeGoldMeasuredCanvas1024','translation1024','sourceContentBBox','registeredOpaquePixels','bowHuePixels','opaqueAboveFaceROI')},indent=2),flush=True)

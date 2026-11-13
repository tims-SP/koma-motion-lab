#!/usr/bin/env python3
"""Audit the actual Codex-generated 60/75 garment companion key art.

This is a source-image viability gate, not an artistic pose certification.
It preserves model-native bytes, registers only by image-derived golden brooch
center, and emits measurable geometry/color metadata and an unedited contact.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import numpy as np,cv2,json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-107-source-patches';D.mkdir(parents=True,exist_ok=True)
N=R/'private-assets/p15-107-codex-patches'
sha=lambda f:sha256(Path(f).read_bytes()).hexdigest()
models=['60','75']
target={'60':np.array([634.46,810.55]),'75':np.array([644.12,807.09])}
original={'60':P/'p15-97-multiview-motion/yaw60-frame-06.png','75':P/'p15-97-multiview-motion/yaw75-frame-06.png'}
report={'schema':'KOMA_P15_107_COMPANION_GARMENT_SOURCE_AUDIT_V1',
 'characterId':'p0_character_001','sourceReference':'P15-105 native 67.5 transparent garment',
 'generatedCompanions':{},'allDimensionsAndColorsValidated':False,
 'artisticApproved':False}
sheet=Image.new('RGB',(3*500,510),'white');draw=ImageDraw.Draw(sheet)
def preview(im,index,title):
 white=Image.new('RGBA',im.size,'white');white.alpha_composite(im)
 crop=white.convert('RGB').crop((345,620,865,1015)).resize((500,480),Image.Resampling.LANCZOS)
 sheet.paste(crop,(500*index,28));draw.text((500*index+5,8),title,fill='black')
for index,view in enumerate(models):
 file=N/f'yaw0{view}-consistent-native.png'
 assert file.is_file(),file
 with Image.open(file) as im:
  assert im.mode=='RGBA',('native color mode',im.mode)
  assert min(im.size)>=1000,im.size
  nativeSize=im.size
  native=np.asarray(im)
  # preserve native image unmodified; normalize only the registered derivative.
  normalized=np.asarray(im.resize((1024,1024),Image.Resampling.LANCZOS))
 hsv=cv2.cvtColor(normalized[:,:,:3],cv2.COLOR_RGB2HSV)
 h,s,v=cv2.split(hsv)
 alpha=normalized[:,:,3]
 roi=np.zeros((1024,1024),np.uint8)
 roi[675:905,525:770]=1
 gold=((h>=8)&(h<=36)&(s>70)&(v>58)&(alpha>120)&(roi>0))
 num,labels,stats,cent=cv2.connectedComponentsWithStats(gold.astype(np.uint8),8)
 options=[]
 for i in range(1,num):
  area=int(stats[i,cv2.CC_STAT_AREA])
  if area<30:continue
  point=cent[i]
  dist=float(np.linalg.norm(point-target[view]))
  if dist>120:continue
  options.append((area/(1+dist/30),i,area,point))
 assert options,('brooch missing',view)
 _,label,area,measured=max(options,key=lambda x:x[0])
 delta=target[view]-measured
 assert float(max(abs(delta)))<100,('brooch registration shift',view,delta)
 transform=np.float32([[1,0,delta[0]],[0,1,delta[1]]])
 reg=cv2.warpAffine(normalized,transform,(1024,1024),flags=cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
 reg[:,:,3][reg[:,:,3]<10]=0
 bb=np.where(reg[:,:,3]>120)
 if len(bb[0])==0:raise AssertionError(('empty RGBA',view))
 bbox=[int(bb[1].min()),int(bb[0].min()),int(bb[1].max()+1),int(bb[0].max()+1)]
 # Isolate native red bow and gold trim evidence for consistent fabric material.
 hsv2=cv2.cvtColor(reg[:,:,:3],cv2.COLOR_RGB2HSV)
 hh,ss,vv=cv2.split(hsv2)
 bow=((hh>=141)|(hh<=8))&(ss>55)&(vv>42)&(reg[:,:,3]>120)
 bowROI=bow[720:1015,490:800]
 golden=((hh>=8)&(hh<=38))&(ss>60)&(vv>48)&(reg[:,:,3]>120)
 goldROI=golden[695:1015,330:850]
 bowPixels=int(bowROI.sum());goldPixels=int(goldROI.sum())
 faceOverlap=int(np.count_nonzero(reg[:590,:,3]>120))
 # A generated garment can be used as a canvas source candidate if features are present.
 usable=(bowPixels>7000 and goldPixels>1000 and bbox[1]>=575 and faceOverlap==0)
 result=D/f'yaw{view}-registered.png'
 Image.fromarray(reg,'RGBA').save(result)
 preview(Image.fromarray(reg,'RGBA'),index,view+' regenerated garment candidate')
 report['generatedCompanions'][view]={
  'nativePath':str(file.relative_to(R)),'nativeSHA256':sha(file),
  'nativeDimensions':list(nativeSize),'nativeRGBA':True,
  'registeredPath':str(result.relative_to(R)),'registeredSHA256':sha(result),
  'measuredBrooch':[round(float(x),3) for x in measured],
  'registrationOffset':[round(float(x),3) for x in delta],
  'registeredAlphaBounds':bbox,'opaqueAbove590':faceOverlap,
  'bowHuePixels':bowPixels,'goldHuePixels':goldPixels,
  'geometryAndColorPrecheck':bool(usable),'artistApproved':False}
 print('AUDIT',view,'usable',usable,'bbox',bbox,'gold',area,'bowPixels',bowPixels,'delta',delta,flush=True)
center=np.asarray(Image.open(P/'p15-105-middle-art/yaw067p5-garment-registered.png').convert('RGBA'))
preview(Image.fromarray(center,'RGBA'),2,'67.5 original canonical garment')
sheet.save(D/'consistent-garment-contact.jpg',quality=94)
report['contact']='private-assets/exports/p15-107-source-patches/consistent-garment-contact.jpg'
report['allDimensionsAndColorsValidated']=all(x['geometryAndColorPrecheck'] for x in report['generatedCompanions'].values())
(R/'evidence/p15-107-patch-qa.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print('PATCH_PRECHECK',report['allDimensionsAndColorsValidated'])

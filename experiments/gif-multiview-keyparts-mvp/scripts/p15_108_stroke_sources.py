#!/usr/bin/env python3
"""Find candidate garment strokes and occlusion regions in real P0 three-view art.

Photometric extraction is only a PROXY to an artist's stroke IDs; record every
mask/descriptor and evidence, never silently promote candidates to true strokes.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import cv2,numpy as np,json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-108-stroke-sources';D.mkdir(parents=True,exist_ok=True)
A=json.loads((R/'evidence/p15-107-patch-qa.json').read_text())
M=json.loads((R/'evidence/p15-105-native-art-qa.json').read_text())
paths={'60':R/A['generatedCompanions']['60']['registeredPath'],
       '67.5':R/M['registeredPath'],
       '75':R/A['generatedCompanions']['75']['registeredPath']}
sha=lambda p:sha256(Path(p).read_bytes()).hexdigest()
angles=list(paths)
report={'schema':'KOMA_P15_108_SOURCE_GARMENT_STROKE_CANDIDATES_V1','angles':[60,67.5,75],
        'roleKinds':['bowFabric','bowInk','goldTrim','collarWhite','collarInk'],
        'identityAssignment':'relative anchors plus local ink contour candidates',
        'artistStrokeIdentityApproved':False,'views':{}}
canvas=Image.new('RGB',(500*3,560*5),'white');draw=ImageDraw.Draw(canvas)
for column,(view,path) in enumerate(paths.items()):
 src=np.asarray(Image.open(path).convert('RGBA'))
 hsv=cv2.cvtColor(src[:,:,:3],cv2.COLOR_RGB2HSV)
 h,s,v=cv2.split(hsv);alpha=src[:,:,3]>125
 goldCenter=np.asarray({'60':[634.46,810.55],'67.5':[639.29,808.82],'75':[644.12,807.09]}[view])
 X,Y=np.meshgrid(np.arange(1024),np.arange(1024))
 x=X-goldCenter[0];y=Y-goldCenter[1]
 roi=(x>-170)&(x<170)&(y>-102)&(y<207)
 rose=(((h>=160)|(h<=5))&(s>66)&(v>42)&alpha&roi)
 # Source-color rose region rather than manual bow rectangle.
 bow=cv2.morphologyEx(np.uint8(rose)*255,cv2.MORPH_CLOSE,np.ones((13,13),np.uint8))
 cnt,_=cv2.findContours(bow,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
 clean=np.zeros_like(bow)
 for c in cnt:
  if cv2.contourArea(c)>250:cv2.drawContours(clean,[c],-1,255,-1)
 bow=clean
 # Ink stroke-like lines are darker-than-local-color structures strictly inside fabric.
 lab=cv2.cvtColor(src[:,:,:3],cv2.COLOR_RGB2LAB)
 L=lab[:,:,0];blackhat=cv2.morphologyEx(L,cv2.MORPH_BLACKHAT,np.ones((19,19),np.uint8))
 interior=cv2.erode(bow,np.ones((5,5),np.uint8))
 ink=np.uint8((blackhat>18)&(interior>0)&(v<175))*255
 n,labels,stats,cent=cv2.connectedComponentsWithStats(ink,8)
 filtered=np.zeros_like(ink)
 kept=[]
 for i in range(1,n):
  area=int(stats[i,cv2.CC_STAT_AREA])
  if area<9 or area>2000:continue
  xx,yy,w,hh,_=stats[i]
  # Candidate line is at least mildly elongated.
  if max(w,hh)<6:continue
  filtered[labels==i]=255
  kept.append({'area':area,'bbox':[int(xx),int(yy),int(xx+w),int(yy+hh)],
               'center':[round(float(cent[i,0]),2),round(float(cent[i,1]),2)]})
 # Collar is a bright/low saturation component above the jewel.
 collarROI=(x>-165)&(x<165)&(y>-230)&(y<30)
 white=(s<75)&(v>153)&(alpha)&collarROI&(src[:,:,2]>=src[:,:,0]-12)
 whiteMask=np.uint8(white)*255
 whiteMask=cv2.morphologyEx(whiteMask,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
 gold=(h>=9)&(h<=38)&(s>72)&(v>62)&alpha&roi
 # Dense gold is trim or jewel; record both separately based on center proximity.
 trim=np.uint8(gold & (np.sqrt(x*x+y*y)>37))*255
 cInk=np.uint8((blackhat>23)&(whiteMask>0))*255
 masks={'bowFabric':bow,'bowInk':filtered,'goldTrim':trim,'collarWhite':whiteMask,'collarInk':cInk}
 outdir=D/('yaw'+view.replace('.','p'));outdir.mkdir(exist_ok=True)
 info={'source':str(path.relative_to(R)),'sourceSHA256':sha(path),'goldCenter':goldCenter.tolist(),'masks':{},'bowInkComponents':kept}
 for row,(name,mask) in enumerate(masks.items()):
  file=outdir/(name+'.png');Image.fromarray(mask,'L').save(file)
  info['masks'][name]={'path':str(file.relative_to(R)),'sha256':sha(file),'pixels':int(np.count_nonzero(mask))}
  im=Image.fromarray(src,'RGBA');bg=Image.new('RGBA',im.size,'white');bg.alpha_composite(im)
  display=np.asarray(bg.convert('RGB')).copy()
  col=(255,55,20) if 'Ink' in name else (15,180,245)
  display[mask>0]=np.uint8(.56*display[mask>0]+.44*np.array(col))
  cropped=Image.fromarray(display,'RGB').crop((330,620,860,1015)).resize((500,520),Image.Resampling.LANCZOS)
  canvas.paste(cropped,(column*500,row*560+28))
  draw.text((column*500+6,row*560+7),view+' '+name,fill='black')
 report['views'][view]=info
 print(view,{name:round(m['pixels']/1000,1) for name,m in info['masks'].items()},'components',len(kept),flush=True)
canvas.save(D/'source-stroke-ownership-contact.jpg',quality=94)
report['contact']=str((D/'source-stroke-ownership-contact.jpg').relative_to(R))
(R/'evidence/p15-108-source-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')

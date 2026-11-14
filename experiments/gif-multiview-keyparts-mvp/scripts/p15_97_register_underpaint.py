#!/usr/bin/env python3
"""Register actual Codex-native underpaint to each original independent keyview."""
from pathlib import Path
from PIL import Image,ImageDraw
import cv2,numpy as np,hashlib,json
R=Path(__file__).resolve().parents[1]
P=R/'private-assets'
sources={'52p5':P/'exports/p15-93-yaw0525-review/yaw052p5-registered.png',
         '75':P/'exports/p15-92-angle-keyart/yaw075-registered.png'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
summary=[]
for view,sourceFile in sources.items():
 D=P/('p15-97-underpaint-'+view)
 info=json.loads((D/'source-info.json').read_text())
 native=D/'model-native.png'
 meta=json.loads((D/'generation-result.json').read_text())
 assert meta['actual_image_tool_used'] and meta['tool']=='image_gen.imagegen'
 assert sha(native)==meta['sha256']
 croppedRef=cv2.imread(str(D/'closeup-reference.png'))
 nativeBGR=cv2.imread(str(native))
 assert nativeBGR.shape[:2]==(1254,1254),nativeBGR.shape
 gen=cv2.resize(nativeBGR,(1024,1024),interpolation=cv2.INTER_AREA)
 mask=cv2.imread(str(D/'closeup-mask.png'),cv2.IMREAD_GRAYSCALE)
 valid=(mask<4).astype(np.uint8)*255
 gray=lambda v:cv2.cvtColor(v,cv2.COLOR_BGR2GRAY)
 candidates=[('resized',gen,np.eye(2,3,dtype=np.float32),None)]
 try:
  score,warp=cv2.findTransformECC(gray(croppedRef),gray(gen),np.eye(2,3,dtype=np.float32),
     cv2.MOTION_TRANSLATION,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,80,1e-5),
     valid,5)
  aligned=cv2.warpAffine(gen,warp,(1024,1024),
    flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REFLECT)
  candidates.append(('translation',aligned,warp,score))
 except cv2.error as e:print(view,'ECC',str(e).splitlines()[0],flush=True)
 def mae(a,m):
  diff=np.abs(a.astype(np.float32)-croppedRef).mean(axis=2)
  return float(diff[m].mean()) if np.any(m) else float('nan')
 err=[]
 for name,img,warp,score in candidates:
  err.append((mae(img,mask<4),name,img,warp,score))
 err.sort(key=lambda x:x[0]);outside,name,best,warp,score=err[0]
 inside=mae(best,mask>160)
 cropped=Image.fromarray(cv2.cvtColor(best,cv2.COLOR_BGR2RGB))
 cropped.save(D/'model-registered-crop.png')
 box=tuple(info['cropBox'])
 size=(box[2]-box[0],box[3]-box[1])
 full=Image.open(sourceFile).convert('RGBA')
 target=cropped.resize(size,Image.Resampling.LANCZOS).convert('RGBA')
 full.paste(target,box[:2])
 # The source alpha channel is canonical: preserve original silhouette & transparency.
 with Image.open(sourceFile) as src:
  full.putalpha(src.convert('RGBA').getchannel('A'))
 full.save(D/'model-registered-source.png')
 q={'schema':'KOMA_P15_97_CODEX_NATIVE_UNDERPAINT_REGISTRATION_V1','view':view,
    'sourceSHA256':sha(sourceFile),'nativeModelSHA256':sha(native),
    'nativeDimensions':[1254,1254],'nativeTool':'Codex CLI image_gen.imagegen',
    'referenceSHA256':sha(D/'closeup-reference.png'),
    'registeredSourceSHA256':sha(D/'model-registered-source.png'),
    'registration':name,'warp':warp.tolist(),'score':None if score is None else float(score),
    'outsideMaskRGBMAE':round(outside,4),'insideMaskRGBMAE':round(inside,4),
    'pixelExactMaskedModelEdit':False,'formalKeyframeAccepted':False,
    'visualGate':'SOURCE_REGISTERED_FOR_MOTION_TEST_ONLY'}
 (R/'evidence'/('p15-97-underpaint-yaw'+view+'.json')).write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
 summary.append(q)
 print(view,'registration',name,'outsideMAE',round(outside,3),'inside',round(inside,3),flush=True)
# Left images are the original crop, right actual registered candidate.
review=Image.new('RGB',(390*4,420),'white');d=ImageDraw.Draw(review)
for i,(view,label,source) in enumerate([(v,t,P/('p15-97-underpaint-'+v)/f) for v in sources for t,f in [('source','closeup-reference.png'),('codex','model-registered-crop.png')]]):
 img=Image.open(source).convert('RGB').resize((390,390),Image.Resampling.LANCZOS)
 review.paste(img,(i*390,26));d.text((i*390+8,6),view+' '+label,fill='black')
path=P/'exports/p15-97-underpaint-alignment-contact.jpg';review.save(path,quality=92)

#!/usr/bin/env python3
"""Preserve authenticated SAM3 masks and source-owned cutouts for independent keyviews."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import hashlib,json,urllib.request,numpy as np
R=Path(__file__).resolve().parents[1]
P=R/'private-assets'
manifest=json.loads((P/'p15-97-space-outputs.json').read_text())
sources={'52p5':P/'exports/p15-93-yaw0525-review/yaw052p5-registered.png',
         '75':P/'exports/p15-92-angle-keyart/yaw075-registered.png'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for view,config in manifest['views'].items():
 d=P/'exports'/('p15-97-sam3-yaw'+view)
 d.mkdir(parents=True,exist_ok=True)
 source=Image.open(sources[view]).convert('RGBA')
 table=[]
 masks=[]
 for n,url in enumerate(config['urls']):
  if not url.lower().startswith('https://prithivmlmods-sam3-demo.hf.space/'):
   raise RuntimeError('Unexpected model response origin')
  dest=d/f'annotation-{n}.png'
  if not dest.exists():
   with urllib.request.urlopen(url,timeout=60) as response:
    dest.write_bytes(response.read())
  with Image.open(dest) as image:
   assert image.size==(640,640),image.size
   alpha=image.convert('RGBA').getchannel('A').resize((1024,1024),Image.Resampling.BILINEAR)
  out=d/f'mask-{n}-1024.png';alpha.save(out)
  cut=source.copy();cut.putalpha(ImageChops.multiply(source.getchannel('A'),alpha))
  cut.save(d/f'cutout-{n}.png')
  data=np.asarray(alpha)
  active=data>128
  yy,xx=np.where(active)
  record={'index':n,'label':config['labels'][n],'rawSHA256':sha(dest),
       'maskSHA256':sha(out),'cutoutSHA256':sha(d/f'cutout-{n}.png'),
       'areaAlpha128':int(active.sum()),
       'bboxAlpha128':[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]}
  table.append(record);masks.append(alpha)
 contact=Image.new('RGB',((len(masks)+1)*400,420),'white')
 dr=ImageDraw.Draw(contact)
 for i,(name,img) in enumerate([('Source',source)]+[(f'SAM3 annotation {n}',Image.open(d/f'cutout-{n}.png').convert('RGBA')) for n in range(len(masks))]):
  bg=Image.new('RGBA',source.size,'white');bg.alpha_composite(img)
  im=bg.convert('RGB').resize((400,390),Image.Resampling.LANCZOS)
  contact.paste(im,(i*400,26));dr.text((i*400+6,7),name,fill='black')
 contact.save(d/'mask-contact.jpg',quality=92)
 ev=R/'evidence'/('p15-97-sam3-yaw'+view+'.json')
 q={'schema':'KOMA_P15_97_REAL_SAM3_VIEW_V1','view':view,
    'sourceSHA256':sha(sources[view]),'model':'prithivMLmods/SAM3-Demo',
    'execution':'authenticated Hugging Face plugin Space invocation','providerAccountSlot':{'52p5':'secondary-1','75':'secondary-2'}[view],
    'prompt':manifest['prompt'],'status':'MODEL_RETURNED','annotationCount':len(table),
    'annotations':table,'sourceRGBPreserved':True,
    'semanticArtMeshApproved':False,'visualGate':'FRONT_BANG_ANNOTATIONS_FOR_REVIEW',
    'contact':str((d/'mask-contact.jpg').relative_to(P))}
 ev.write_text(json.dumps(q,indent=2,ensure_ascii=False)+'\n')
 print(view,json.dumps(table,ensure_ascii=False),flush=True)

#!/usr/bin/env python3
"""Acquire HF SAM3 ocular masks, classify by validated source view landmark boxes."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import hashlib,json,urllib.request
import numpy as np
R=Path(__file__).resolve().parents[1]
A=R/'private-assets'
D=A/'p15-99-sam3-eyes'
E=A/'exports/p15-99-topology'
E.mkdir(exist_ok=True,parents=True)
config=json.loads((D/'manifest.json').read_text())
guide=json.loads((R/'evidence/p15-98-landmarks.json').read_text())['viewLandmarks']
srcPaths={'60':A/'exports/p15-92-angle-keyart/yaw060-registered.png',
          '75':A/'exports/p15-92-angle-keyart/yaw075-registered.png'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
qa={'schema':'KOMA_P15_99_REAL_SAM3_EYE_MASK_QA_V1','model':config['model'],
    'prompt':config['prompt'],'actualExternalModelOutput':True,'viewResults':{},'approvedForFormalArtMesh':False}
for view in ('60','75'):
 src=Image.open(srcPaths[view]).convert('RGBA')
 out=E/f'yaw{view}';out.mkdir(exist_ok=True)
 candidates=[]
 for idx,hashname in enumerate(config[view]):
  url='https://prithivmlmods-sam3-demo.hf.space/--replicas/4tz4r/gradio_api/file=/tmp/gradio/'+hashname+'/image.png'
  raw=out/f'sam3-eye-annotation-{idx}.png'
  if not raw.exists():
   with urllib.request.urlopen(url,timeout=65) as resp:
    raw.write_bytes(resp.read())
  annot=Image.open(raw).convert('RGBA')
  assert annot.size==(640,640),(view,annot.size)
  alpha=annot.getchannel('A').resize((1024,1024),Image.Resampling.BILINEAR)
  mask=out/f'sam3-eye-mask-{idx}.png';alpha.save(mask)
  arr=np.asarray(alpha)
  area=arr>128
  yy,xx=np.where(area)
  if not len(xx):continue
  bbox=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]
  rec={'index':idx,'rawSHA256':sha(raw),'maskSHA256':sha(mask),
       'bbox':bbox,'area':int(area.sum())}
  # Eye identification uses location proximity and plausible area, rather than response order.
  for role,point in [('near',guide[view]['eye.near.center']),('far',guide[view]['eye.far.center'])]:
   cx,cy=map(int,point)
   region=area[max(0,cy-42):cy+43,max(0,cx-65):cx+66]
   rec[role+'BoxOverlapPx']=int(region.sum())
  candidates.append(rec)
 qa['viewResults'][view]={'sourceSHA256':sha(srcPaths[view]),'candidates':candidates}
 contact=Image.new('RGB',(330*(len(candidates)+1),385),'white');draw=ImageDraw.Draw(contact)
 for n in range(len(candidates)+1):
  if n==0:
   art=src;caption='source yaw '+view
  else:
   alpha=Image.open(out/f'sam3-eye-mask-{n-1}.png').convert('L')
   art=src.copy();art.putalpha(ImageChops.multiply(art.getchannel('A'),alpha))
   caption=f'eye candidate {n-1}'
  bg=Image.new('RGBA',art.size,'white');bg.alpha_composite(art)
  tile=bg.convert('RGB').crop((440,290,840,675)).resize((330,355),Image.Resampling.LANCZOS)
  contact.paste(tile,((n)*330,25));draw.text((n*330+7,5),caption,fill='black')
 contact.save(out/'eye-contact.jpg',quality=92)
 print('VIEW',view,[(x['index'],x['area'],x['bbox'],x['nearBoxOverlapPx'],x['farBoxOverlapPx']) for x in candidates],flush=True)
(R/'evidence/p15-99-eye-mask-qa.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')

#!/usr/bin/env python3
"""Recover actual SAM3 annotations and preserve mask provenance for yaw60 hair."""
from pathlib import Path
from PIL import Image
import hashlib,json,requests
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-94-sam3-yaw060'
raw=D/'raw-result.json'
qpath=R/'evidence/p15-94-sam3-provider-qa.json'
q=json.loads(qpath.read_text())
output=json.loads(raw.read_text())
obj=output[0] if isinstance(output,list) else output
assert isinstance(obj,dict) and 'image' in obj and 'annotations' in obj
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[]
def save_file(kind,idx,data,ext):
 url=data['url']
 if not url.startswith('https://prithivmlmods-sam3-demo.hf.space/'):
  raise ValueError('untrusted remote file origin')
 resp=requests.get(url,timeout=(20,60));resp.raise_for_status()
 file=D/(f'{kind}-{idx}.{ext}')
 file.write_bytes(resp.content)
 with Image.open(file) as im:
  im.load()
  extrema=im.getextrema()
  props={'dimensions':list(im.size),'mode':im.mode,'extrema':extrema,
         'alphaNonZero':sum(v>0 for v in im.getchannel('A').getdata()) if 'A' in im.getbands() else None}
 record={'role':kind,'index':idx,'path':str(file.relative_to(R)), 'sha256':sha(file),
    'bytes':file.stat().st_size,'image':props}
 files.append(record)
 print('downloaded',record,flush=True)
save_file('visual',0,obj['image'],'webp')
for idx,anno in enumerate(obj['annotations']):
 save_file('annotation',idx,anno['image'],'png')
 files[-1]['label']=anno.get('label')
q.update({'status':'MODEL_RETURNED','resultSHA256':sha(raw),
 'rawResult':str(raw.relative_to(R)),'outputs':files,'annotationCount':len(obj['annotations']),
 'modelMaskProven':False,'formalArtMeshAccepted':False,'visualGate':'SAM3_ANNOTATIONS_RETURNED_MASK_SEMANTICS_PENDING'})
q.pop('error',None)
qpath.write_text(json.dumps(q,indent=2,ensure_ascii=False)+'\n')
print('annotations',len(obj['annotations']), 'status',q['status'])

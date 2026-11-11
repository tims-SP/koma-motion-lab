#!/usr/bin/env python3
import json,requests,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-85-outer-eye-seam'
base='https://pg56714-inpaint-anything.hf.space';s=requests.Session()
def upload(p):
 with p.open('rb') as f:r=s.post(base+'/gradio_api/upload',files={'files':(p.name,f,'image/png')},timeout=60)
 r.raise_for_status();v=r.json()[0]
 return {'path':v,'orig_name':p.name,'meta':{'_type':'gradio.FileData'}}
try:
 image=upload(D/'input-512.png');mask=upload(D/'mask-512.png')
 print('UPLOAD_OK',flush=True)
 r=s.post(base+'/gradio_api/call/get_inpainted_img',json={'data':[image,mask,512]},timeout=50);r.raise_for_status()
 ev=r.json()['event_id'];print('EVENT',ev,flush=True)
 with s.get(base+'/gradio_api/call/get_inpainted_img/'+ev,timeout=(20,360),stream=True) as out:
  out.raise_for_status()
  for line in out.iter_lines(decode_unicode=True):
   if not line or not line.startswith('data: '):continue
   v=json.loads(line[6:])
   if isinstance(v,list):
    x=v[0];url=x.get('url') if isinstance(x,dict) else x
    if not url:url=base+'/gradio_api/file='+x['path']
    if url.startswith('/'):url=base+url
    rr=s.get(url,timeout=90);rr.raise_for_status()
    (D/'model-512.png').write_bytes(rr.content)
    print('MODEL_RECEIVED',len(rr.content),flush=True);sys.exit(0)
 raise RuntimeError('No image returned')
except Exception as e:print('INFERENCE_FAILED',repr(e),flush=True);sys.exit(2)

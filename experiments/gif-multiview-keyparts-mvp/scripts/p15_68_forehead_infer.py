#!/usr/bin/env python3
"""Actual CPU LaMa inference through Gradio, fixed inputs in the P15-68 review directory."""
import json,requests,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-68-forehead'
base='https://pg56714-inpaint-anything.hf.space';session=requests.Session()
def upload(path):
 with path.open('rb') as f:
  r=session.post(base+'/gradio_api/upload',files={'files':(path.name,f,'image/png')},timeout=50)
 r.raise_for_status()
 return {'path':r.json()[0],'orig_name':path.name,'meta':{'_type':'gradio.FileData'}}
try:
 files=[upload(D/n) for n in ('input-512.png','mask-512.png')]
 r=session.post(base+'/gradio_api/call/get_inpainted_img',json={'data':[files[0],files[1],512]},timeout=45)
 r.raise_for_status();eid=r.json()['event_id']
 print('LaMa CPU inference submitted',eid,flush=True)
 with session.get(base+'/gradio_api/call/get_inpainted_img/'+eid,timeout=(20,300),stream=True) as output:
  output.raise_for_status()
  for line in output.iter_lines(decode_unicode=True):
   if not line or not line.startswith('data: '):continue
   val=json.loads(line[6:])
   if isinstance(val,list):
    result=val[0]
    url=result.get('url') if isinstance(result,dict) else result
    if not url:url=base+'/gradio_api/file='+result['path']
    if url.startswith('/'):url=base+url
    rr=session.get(url,timeout=80);rr.raise_for_status()
    (D/'model-512.png').write_bytes(rr.content)
    print('MODEL_RECEIVED',len(rr.content),flush=True)
    sys.exit(0)
 raise RuntimeError('No model result')
except Exception as exc:
 print('INFERENCE_FAILED',type(exc).__name__,str(exc)[:500],flush=True)
 sys.exit(2)

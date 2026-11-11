#!/usr/bin/env python3
"""Try SAM3 text-grounded semantic segmentation on same P15-56 pose; no fake masks."""
from pathlib import Path
import requests,json,hashlib,sys
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-81-image-layered'
inp=D/'input-head-640.png';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
base='https://prithivmlmods-sam3-demo.hf.space'
q={'schema':'KOMA-P15-81-SAM3-TEXT_FRONT_HAIR_V1','inputSHA256':sha(inp),
   'model':'prithivMLmods/SAM3-Demo','prompt':'front bangs hair fringe on forehead',
   'conf_thresh':0.25,'status':'PENDING','formalArtMeshAccepted':False}
def save():(R/'evidence/p15-81-sam3-provider.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
save()
try:
 session=requests.Session()
 with inp.open('rb') as f:
  u=session.post(base+'/gradio_api/upload',files={'files':('input-head-640.png',f,'image/png')},timeout=60)
 u.raise_for_status()
 fd={'path':u.json()[0],'orig_name':'input-head-640.png','meta':{'_type':'gradio.FileData'}}
 print('UPLOADED',fd['path'],flush=True)
 r=session.post(base+'/gradio_api/call/run_image_segmentation',json={'data':[fd,q['prompt'],q['conf_thresh']]},timeout=40)
 print('CALL',r.status_code,r.text[:400],flush=True);r.raise_for_status()
 eid=r.json()['event_id']
 with session.get(base+'/gradio_api/call/run_image_segmentation/'+eid,stream=True,timeout=(30,180)) as stream:
  stream.raise_for_status();ev=''
  for line in stream.iter_lines(decode_unicode=True):
   if not line:continue
   if line.startswith('event:'):ev=line[6:].strip();print('EVENT',ev,flush=True)
   if line.startswith('data:'):
    v=line[5:].strip();print('DATA',v[:700],flush=True)
    if ev=='error':raise RuntimeError(v[:800])
    if ev=='complete':
     z=json.loads(v);obj=z[0] if isinstance(z,list) and z else z
     if isinstance(obj,dict):
      url=obj.get('url')
      if not url and obj.get('path'):url=base+'/gradio_api/file='+obj['path']
     else:url=obj if isinstance(obj,str) else None
     if not url:raise RuntimeError('No result URL '+str(z)[:250])
     if url.startswith('/'):url=base+url
     res=session.get(url,timeout=60);res.raise_for_status()
     out=D/'sam3-front-hair-segmentation.png';out.write_bytes(res.content)
     q.update({'status':'MODEL_RETURNED','outputSHA256':sha(out),'bytes':len(res.content)})
     save();print('SAVED',q['outputSHA256'],flush=True);sys.exit(0)
 raise RuntimeError('No completed inference event')
except Exception as e:
 q.update({'status':'FAILED','error':repr(e)[:900]});save()
 print('FAILED',repr(e),flush=True);sys.exit(2)

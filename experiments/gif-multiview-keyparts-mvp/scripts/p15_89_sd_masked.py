#!/usr/bin/env python3
"""Secondary genuinely masked text inpainting attempt (not LaMa cloning)."""
from pathlib import Path
import requests,json,hashlib,sys
from PIL import Image
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-89-masked-local-art'
HOST='https://pg56714-inpaint-anything.hf.space';s=requests.Session()
E=R/'evidence/p15-89-sd-masked-qa.json';qa={'schema':'KOMA-P15-89-SD-MASK-API-V1',
'modelService':HOST,'api':'/get_fill_img_with_sd','maskPassedAsTrueModelArgument':False,
'status':'PREPARED','modelOutputCreated':False,'formalArtMeshAccepted':False}
def save():E.write_text(json.dumps(qa,indent=2)+'\n')
save()
try:
 # SD service accepts up to 768px and internally rescales; keep full-frame coordinates.
 img=Image.open(D/'full-source-1024.png').convert('RGB')
 mask=Image.open(D/'local-mask-1024.png').convert('L')
 img=img.resize((768,768),Image.Resampling.LANCZOS)
 mask=mask.resize((768,768),Image.Resampling.LANCZOS)
 ip=D/'sd-full-source-768.png';mp=D/'sd-local-mask-768.png'
 img.save(ip);mask.save(mp)
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 qa.update(inputSHA256=sha(ip),maskSHA256=sha(mp),inputSize=[768,768],maskBBox=list(mask.getbbox()));save()
 def upload(path):
  with path.open('rb') as f:r=s.post(HOST+'/gradio_api/upload',files={'files':(path.name,f,'image/png')},timeout=60)
  r.raise_for_status()
  return {'path':r.json()[0],'orig_name':path.name,'meta':{'_type':'gradio.FileData'}}
 imgs=[upload(p) for p in (ip,mp)]
 prompt='Anime painting, clean mauve pink side fringe, tapered curved hair edge over naturally shaded smooth peach skin, no dislocated dark line, no old eyelash, exact same face geometry'
 qa['maskPassedAsTrueModelArgument']=True;qa['status']='MASK_SUBMITTED';save()
 r=s.post(HOST+'/gradio_api/call/get_fill_img_with_sd',json={'data':[imgs[0],imgs[1],768,prompt]},timeout=60)
 r.raise_for_status();eid=r.json()['event_id'];qa['eventId']=eid;qa['status']='QUEUED';save()
 print('QUEUED',eid,flush=True)
 with s.get(HOST+'/gradio_api/call/get_fill_img_with_sd/'+eid,stream=True,timeout=(30,350)) as resp:
  resp.raise_for_status();event=''
  for ln in resp.iter_lines(decode_unicode=True):
   if not ln:continue
   if ln.startswith('event:'):event=ln[6:].strip();print('EVENT',event,flush=True)
   if ln.startswith('data:'):
    value=ln[5:].strip()
    if event=='error':raise RuntimeError('model returned error '+value[:1100])
    if event=='complete':
     arr=json.loads(value)
     x=arr[0];url=x.get('url') if isinstance(x,dict) else x
     if not url and isinstance(x,dict):url=HOST+'/gradio_api/file='+x['path']
     if url.startswith('/'):url=HOST+url
     rr=s.get(url,timeout=90);rr.raise_for_status()
     dest=D/'sd-model-returned.png';dest.write_bytes(rr.content)
     qa.update(status='MODEL_RETURNED',modelOutputCreated=True,outputSHA256=sha(dest),outputBytes=dest.stat().st_size)
     save();print('MODEL_RETURNED',dest.stat().st_size,flush=True);sys.exit(0)
 raise RuntimeError('No model completion')
except Exception as e:
 qa.update(status='INFERENCE_FAILED',error=repr(e)[:1200]);save()
 print('INFERENCE_FAILED',repr(e),flush=True);sys.exit(2)

#!/usr/bin/env python3
"""Probe actual SAM2 click segmentation on the current same-view portrait, not a threshold heuristic."""
import json,uuid,requests,hashlib,sys
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-71-sam-semantic';D.mkdir(parents=True,exist_ok=True)
source=R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'
im=Image.open(source).convert('RGBA')
region=(350,125,862,637)
input_file=D/'input-512.png'
im.crop(region).convert('RGB').save(input_file)
base='https://premkishor0007-sam2-image-segmentation.hf.space'
session=requests.Session()
q={'schema':'KOMA-P15-71-SAM2-PROBE-V1','sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'cropBox':list(region),
 'space':'Premkishor0007/sam2-image-segmentation','model':'SAM2','operation':'on_image_select','sourceSameView':True,
 'status':'PENDING','formalArtMeshAccepted':False}
def save(): (R/'evidence/p15-71-sam-probe.json').write_text(json.dumps(q,indent=2,ensure_ascii=False)+'\n')
save()
try:
 with input_file.open('rb') as f:
  u=session.post(base+'/gradio_api/upload',files={'files':('input-512.png',f,'image/png')},timeout=50)
 u.raise_for_status()
 fd={'path':u.json()[0],'orig_name':input_file.name,'meta':{'_type':'gradio.FileData'}}
 print('UPLOADED',fd['path'],flush=True)
 # Event-data point chosen deep inside pink hair, not forehead or iris.
 args={'data':[fd,'Foreground (+)',None,None], 'event_data':{'index':[205,112]},
       'fn_index':1,'trigger_id':None,'session_hash':'p1571'+uuid.uuid4().hex[:10]}
 r=session.post(base+'/gradio_api/queue/join',json=args,timeout=35)
 print('JOIN',r.status_code,r.text[:600],flush=True)
 r.raise_for_status()
 with session.get(base+'/gradio_api/queue/data',params={'session_hash':args['session_hash']},stream=True,timeout=(20,180)) as ev:
  ev.raise_for_status();data=''
  for line in ev.iter_lines(decode_unicode=True):
   if line and line.startswith('data: '):
    data=line[6:]
    print('EVENT',data[:500],flush=True)
    try:j=json.loads(data)
    except:continue
    if j.get('msg')=='process_completed':
     if not j.get('success'):raise RuntimeError(str(j)[:700])
     result=j.get('output',{}).get('data',[])
     for i,obj in enumerate(result[:2]):
      if not isinstance(obj,dict):continue
      url=obj.get('url')
      if not url and obj.get('path'):url=base+'/gradio_api/file='+obj['path']
      if not url:continue
      if url.startswith('/'):url=base+url
      response=session.get(url,timeout=60);response.raise_for_status()
      (D/f'sam-output-{i}.png').write_bytes(response.content)
     q.update({'status':'MODEL_RETURNED','resultSlots':len(result),'modelOutputFiles':[p.name for p in D.glob('sam-output-*.png')]})
     save();print('SAVED',q['modelOutputFiles'],flush=True);sys.exit(0)
 raise RuntimeError('No completed event')
except Exception as e:
 q['status']='FAILED';q['error']=repr(e)[:900];save()
 print('SAM2_FAILED',repr(e),flush=True);sys.exit(2)

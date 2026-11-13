#!/usr/bin/env python3
"""Probe real SAM3 text-guided semantic extraction on Codex yaw60 source."""
from pathlib import Path
from PIL import Image
import requests,hashlib,json,sys,io
R=Path(__file__).resolve().parents[1]
A=R/'private-assets';D=A/'exports/p15-94-sam3-yaw060';D.mkdir(parents=True,exist_ok=True)
SOURCE=A/'exports/p15-92-angle-keyart/yaw060-registered.png'
ENDPOINT='https://prithivmlmods-sam3-demo.hf.space'
role='hair.front';prompt='front bangs hair over the forehead'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
src=Image.open(SOURCE).convert('RGBA')
assert src.size==(1024,1024)
bg=Image.new('RGBA',src.size,(255,255,255,255));bg.alpha_composite(src)
inp=D/'yaw060-head-640.png'
bg.convert('RGB').resize((640,640),Image.Resampling.LANCZOS).save(inp)
q={'schema':'KOMA-P15-94-SAM3_YAW60_SEMANTIC_SOURCE_V1',
  'characterId':'p0_character_001',
  'sourceSHA256':sha(SOURCE),'inputSHA256':sha(inp),
  'role':role,'model':'prithivMLmods/SAM3-Demo','prompt':prompt,
  'conf_thresh':0.25,'status':'PENDING',
  'modelMaskProven':False,'formalArtMeshAccepted':False}
evidence=R/'evidence/p15-94-sam3-provider-qa.json'
def persist():evidence.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
persist()
try:
 s=requests.Session()
 with inp.open('rb') as f:
  upload=s.post(ENDPOINT+'/gradio_api/upload',files={'files':('yaw060-head-640.png',f,'image/png')},timeout=(20,60))
 upload.raise_for_status()
 fdata={'path':upload.json()[0],'orig_name':inp.name,'meta':{'_type':'gradio.FileData'}}
 print('UPLOADED',str(fdata['path'])[:120],flush=True)
 api=s.post(ENDPOINT+'/gradio_api/call/run_image_segmentation',
      json={'data':[fdata,prompt,q['conf_thresh']]},timeout=(20,45))
 print('CALL',api.status_code,api.text[:240],flush=True);api.raise_for_status()
 eid=api.json()['event_id']
 with s.get(ENDPOINT+'/gradio_api/call/run_image_segmentation/'+eid,stream=True,timeout=(30,150)) as stream:
  stream.raise_for_status();ev=''
  for ln in stream.iter_lines(decode_unicode=True):
   if not ln:continue
   if ln.startswith('event:'):ev=ln[6:].strip();print('EVENT',ev,flush=True)
   if ln.startswith('data:'):
    value=ln[5:].strip()
    if ev=='error':raise RuntimeError(value[:600])
    if ev=='complete':
     z=json.loads(value)
     # Gradio outputs may be either an image file or annotation object; keep real raw result.
     (D/'raw-result.json').write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n')
     obj=z[0] if isinstance(z,list) and z else z
     if not isinstance(obj,dict) or not isinstance(obj.get('annotations'),list):
      raise RuntimeError('expected Gradio annotated image output')
     q.update({'status':'MODEL_METADATA_RETURNED','resultSHA256':sha(D/'raw-result.json'),
       'annotationCount':len(obj['annotations']),'modelMaskProven':False,
       'rawResult':str((D/'raw-result.json').relative_to(R)),
       'next':'Run p15_94_sam3_result.py to download actual annotation mask files'})
     persist();print('RESULT',q['status'],'annotations',q['annotationCount'],flush=True)
     sys.exit(0)
 raise RuntimeError('no completed inference event')
except Exception as exc:
 q.update({'status':'FAILED','error':repr(exc)[:900]})
 persist();print('FAILED',repr(exc),flush=True);sys.exit(2)

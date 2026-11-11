#!/usr/bin/env python3
import requests,json,hashlib,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-73-interactive-sam'
base='https://mar2ding-sam2long-demo.hf.space';s=requests.Session()
q={'schema':'KOMA-P15-73-INTERACTIVE-SAM-V1','provider':'Mar2Ding/SAM2Long-Demo',
 'source':'P15-56 same-view 512px crop','status':'PENDING'}
def save(): (R/'evidence/p15-73-interactive-sam-qa.json').write_text(json.dumps(q,indent=2,ensure_ascii=False)+'\n')
save()
try:
 with (D/'input.mp4').open('rb') as f:
  u=s.post(base+'/gradio_api/upload',files={'files':('input.mp4',f,'video/mp4')},timeout=60)
 u.raise_for_status();path=u.json()[0];print('UPLOAD',path,flush=True)
 payload={'data':[{'path':path,'orig_name':'input.mp4','meta':{'_type':'gradio.FileData'}}]}
 r=s.post(base+'/gradio_api/call/preprocess_video_in',json=payload,timeout=45);print('CALL',r.status_code,r.text[:300],flush=True);r.raise_for_status()
 event=r.json()['event_id'];out=[]
 with s.get(base+'/gradio_api/call/preprocess_video_in/'+event,stream=True,timeout=(30,180)) as rs:
  rs.raise_for_status()
  for line in rs.iter_lines(decode_unicode=True):
   if line and line.startswith('data: '):
    raw=line[6:];print('EVENT',raw[:1600],flush=True)
    try:out=json.loads(raw)
    except:continue
    if isinstance(out,list):
     q.update({'status':'VIDEO_PREPROCESSED','output':out});save();print('OUTPUT_COUNT',len(out),flush=True);sys.exit(0)
 raise RuntimeError('No preprocess output')
except Exception as e:
 q.update({'status':'FAILED','error':repr(e)[:1000]});save();print('FAILED',repr(e),flush=True);sys.exit(2)

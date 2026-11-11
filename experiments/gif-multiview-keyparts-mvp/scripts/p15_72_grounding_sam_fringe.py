#!/usr/bin/env python3
"""Invoke actual CPU GroundingDINO + SAM Space on P15-56 same-view image."""
from pathlib import Path
import requests,json,sys,hashlib
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-72-semantic-hair';D.mkdir(parents=True,exist_ok=True)
S=R/'private-assets/exports/p15-71-sam-semantic/input-512.png'
assert S.exists()
base='https://volkopat-segmentanythingxgroundingdino.hf.space'
sess=requests.Session()
q={'schema':'KOMA-P15-72-CPU-SEMANTIC-V1','sourceSHA256':hashlib.sha256(S.read_bytes()).hexdigest(),
   'provider':'Volkopat/SegmentAnythingxGroundingDINO','prompt':'front hair fringe bangs',
   'status':'PENDING','formalArtMeshAccepted':False}
def save(): (R/'evidence/p15-72-semantic-provider-fringe-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
save()
try:
 with S.open('rb') as f:
  resp=sess.post(base+'/gradio_api/upload',files={'files':('input-512.png',f,'image/png')},timeout=45)
 resp.raise_for_status();path=resp.json()[0]
 print('UPLOADED',path,flush=True)
 obj={'path':path,'orig_name':'input-512.png','meta':{'_type':'gradio.FileData'}}
 payload={'data':[obj,q['prompt'],True,False,'Crop']}
 r=sess.post(base+'/gradio_api/call/detect_objects',json=payload,timeout=40)
 print('CALL',r.status_code,r.text[:500],flush=True)
 r.raise_for_status();event=r.json()['event_id']
 with sess.get(base+'/gradio_api/call/detect_objects/'+event,stream=True,timeout=(30,230)) as rs:
  rs.raise_for_status()
  for line in rs.iter_lines(decode_unicode=True):
   if not line:continue
   if line.startswith('event: '):print(line[:150],flush=True)
   if line.startswith('data: '):
    print('DATA',line[:700],flush=True)
    data=json.loads(line[6:])
    if isinstance(data,list):
     val=data[0]
     url=val.get('url') if isinstance(val,dict) else val
     if not url and isinstance(val,dict):url=base+'/gradio_api/file='+val['path']
     if url.startswith('/'):url=base+url
     rr=sess.get(url,timeout=80);rr.raise_for_status()
     (D/'grounded-sam-fringe.png').write_bytes(rr.content)
     q.update({'status':'MODEL_RETURNED','outputBytes':len(rr.content),'outputSHA256':hashlib.sha256(rr.content).hexdigest()})
     save();print('MODEL_OUTPUT_SAVED',len(rr.content),flush=True);sys.exit(0)
 raise RuntimeError('No result')
except Exception as e:
 q.update({'status':'FAILED','error':str(e)[:800]});save()
 print('PROVIDER_FAILED',str(e)[:500],flush=True);sys.exit(2)

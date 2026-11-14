import requests,json,uuid,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-73-interactive-sam';base='https://mar2ding-sam2long-demo.hf.space';s=requests.Session()
with (D/'input-512.png').open('rb') as f:
 u=s.post(base+'/gradio_api/upload',files={'files':('input-512.png',f,'image/png')},timeout=45);u.raise_for_status()
fd={'path':u.json()[0],'orig_name':'input-512.png','meta':{'_type':'gradio.FileData'}}
for point in [[155,160],[240,330]]:
 sh='p1573'+uuid.uuid4().hex[:10]
 payload={'data':['include',[],[],fd],'event_data':{'index':point,'value':None,'row_value':None,'col_value':None},'fn_index':1,'trigger_id':None,'session_hash':sh}
 r=s.post(base+'/gradio_api/queue/join',json=payload,timeout=30);print('JOIN',r.status_code,r.text[:500],flush=True)
 if not r.ok:continue
 try:
  with s.get(base+'/gradio_api/queue/data',params={'session_hash':sh},stream=True,timeout=(20,120)) as rs:
   for line in rs.iter_lines(decode_unicode=True):
    if line and line.startswith('data: '):
     print('EVENT',line[:1200],flush=True)
     j=json.loads(line[6:])
     if j.get('msg')=='process_completed':print('COMPLETED',j.get('success'),flush=True);break
 except Exception as e:print('ERR',repr(e),flush=True)

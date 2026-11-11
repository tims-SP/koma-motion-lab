import requests,json,uuid,hashlib,sys,base64
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-73-interactive-sam';base='https://basimbashir-segment-anything-webui.hf.space';s=requests.Session()
q={'schema':'KOMA-P15-73-INTERACTIVE-POINT-SAM-V1','provider':'basimbashir/segment_anything_webui','model':'vit_b','device':'cpu','status':'PENDING','points':[]}
def save(): (R/'evidence/p15-73-interactive-sam-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
def run(fn,data,event_data=None):
 payload={'data':data,'fn_index':fn,'session_hash':sh}
 if event_data is not None:payload['event_data']=event_data
 r=s.post(base+'/run/predict',json=payload,timeout=240);r.raise_for_status();j=r.json()
 if j.get('error') is not None:raise RuntimeError(str(j['error']))
 return j.get('data')
try:
 src=D/'input-512.png';uri='data:image/png;base64,'+base64.b64encode(src.read_bytes()).decode();sh='p1573'+uuid.uuid4().hex[:12]
 out=run(3,[uri]);print('IMAGE_UPLOAD_STATE',out,flush=True);q['status']='IMAGE_READY'
 selected_points=[]
 points=[('foreground_point',[250,245]),('foreground_point',[300,220]),('foreground_point',[340,260]),('foreground_point',[205,270]),('background_point',[240,345]),('background_point',[250,415]),('background_point',[390,170]),('background_point',[400,390])]
 annotated=uri
 for kind,xy in points:
  out=run(4,[annotated,selected_points,kind],{'index':xy,'value':None,'row_value':None,'col_value':None})
  annotated=out[0]
  selected_points.append((xy,1 if kind=='foreground_point' else 0))
  q['points'].append({'type':kind,'xy':xy})
  print('POINT_OK',kind,xy,'returned',len(str(annotated)),flush=True)
  if isinstance(annotated,str) and annotated.startswith('data:image'):
   raw=base64.b64decode(annotated.split(',',1)[1]);(D/'annotated-points.png').write_bytes(raw)
 q['status']='POINTS_ANNOTATED';q['selectedPoints']=selected_points;save()
 args=['cpu','vit_b',16,0.88,0.95,0,1.0,0.7,0,0.7,0.1,uri,'',selected_points]
 print('SELECTED_POINTS',selected_points,flush=True)
 print('RUN_SAM',flush=True)
 out=run(6,args)
 print('SAM_RETURN',str(out)[:1400],flush=True)
 for i,x in enumerate(out or []):
  if isinstance(x,str) and x.startswith('data:image'):
   raw=base64.b64decode(x.split(',',1)[1]);name=f'sam-mask-{i}.png';(D/name).write_bytes(raw);q.setdefault('outputs',[]).append({'file':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
  elif isinstance(x,dict) and x.get('name'):
   p=x['name'];url=base+'/file='+p;rr=s.get(url,timeout=90);rr.raise_for_status();name=f'sam-mask-{i}.png';(D/name).write_bytes(rr.content);q.setdefault('outputs',[]).append({'file':name,'bytes':len(rr.content),'sha256':hashlib.sha256(rr.content).hexdigest()})
 q['status']='MODEL_RETURNED';q['outputCount']=len(out or []);save();print('DONE',q.get('outputs'),flush=True)
except Exception as e:q.update({'status':'FAILED','error':repr(e)[:1200]});save();print('FAILED',repr(e),flush=True);sys.exit(2)

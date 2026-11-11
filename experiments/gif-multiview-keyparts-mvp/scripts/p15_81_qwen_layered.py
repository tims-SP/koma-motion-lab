#!/usr/bin/env python3
"""Run official Qwen Image Layered on P15-56 true source; store actual model outputs."""
from pathlib import Path
from PIL import Image
import requests,hashlib,json,sys,time,zipfile,io
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-81-image-layered';D.mkdir(parents=True,exist_ok=True)
src=R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
original=Image.open(src).convert('RGBA')
# Anime face/head only, include full front/side hair to avoid trivial character/background split.
crop=(150,45,850,745)
image=original.crop(crop);image.thumbnail((640,640),Image.Resampling.LANCZOS)
input_file=D/'input-head-640.png';image.save(input_file)
base='https://qwen-qwen-image-layered.hf.space'
session=requests.Session()
q={'schema':'KOMA-P15-81-OFFICIAL-QWEN-LAYERED-V1',
   'sourceSHA256':sha(src),'inputSHA256':sha(input_file),
   'sourceCropBox':list(crop),'inputSize':list(image.size),
   'provider':'Qwen/Qwen-Image-Layered','modelOutputs':[],
   'formalArtMeshAccepted':False,'formalKeyframeAccepted':False,'status':'PENDING'}
def save(): (R/'evidence/p15-81-layered-provider.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
save()
try:
 with input_file.open('rb') as f:
  upload=session.post(base+'/gradio_api/upload',files={'files':('input-head-640.png',f,'image/png')},timeout=70)
 upload.raise_for_status()
 fd={'path':upload.json()[0],'orig_name':input_file.name,'meta':{'_type':'gradio.FileData'}}
 print('UPLOADED',str(fd['path'])[:160],flush=True)
 payload={'data':[fd,77,False,'',' ',4.0,28,6,True,True]}
 # The actual service supports predict through /call/infer_1 and may queue.
 res=session.post(base+'/gradio_api/call/infer_1',json=payload,timeout=50)
 print('CALL',res.status_code,res.text[:600],flush=True)
 res.raise_for_status()
 event_id=res.json()['event_id'];q['eventId']=event_id;q['status']='QUEUED';save()
 with session.get(base+'/gradio_api/call/infer_1/'+event_id,stream=True,timeout=(35,210)) as stream:
  stream.raise_for_status()
  event=''
  for ln in stream.iter_lines(decode_unicode=True):
   if not ln:continue
   if ln.startswith('event:'):event=ln[6:].strip();print('EVENT',event,flush=True)
   if ln.startswith('data:'):
    value=ln[5:].strip()
    print('DATA',value[:800],flush=True)
    if event=='error':raise RuntimeError(value[:1000])
    if event=='complete':
     data=json.loads(value)
     (D/'result.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
     gallery=data[0] if isinstance(data,list) and data else []
     for i,item in enumerate(gallery):
      entry=item[0] if isinstance(item,(list,tuple)) else item
      if isinstance(entry,dict):
       url=entry.get('url') or entry.get('path')
       if url and url.startswith('/'):url=base+url
       elif url and not url.startswith('http'):url=base+'/gradio_api/file='+url
      else:url=entry if isinstance(entry,str) else None
      if not url:continue
      response=session.get(url,timeout=70);response.raise_for_status()
      file=D/f'layer-{i:02d}.png';file.write_bytes(response.content)
      q['modelOutputs'].append({'path':file.name,'sha256':sha(file),'bytes':len(response.content)})
     for j,val in enumerate(data[1:3],start=1):
      if isinstance(val,dict):
       url=val.get('url')
       if not url and val.get('path'):url=base+'/gradio_api/file='+val['path']
       if url:
        out=session.get(url,timeout=70);out.raise_for_status()
        f=D/('layers-output.pptx' if j==1 else 'layers-output.zip');f.write_bytes(out.content)
        if j==2:
         with zipfile.ZipFile(io.BytesIO(out.content)) as z:
          q['zipMembers']=z.namelist()[:50]
     q['status']='MODEL_RETURNED';save()
     print('SAVED',q['modelOutputs'],flush=True);sys.exit(0)
 raise RuntimeError('No complete event')
except Exception as e:
 q['status']='FAILED';q['error']=repr(e)[:1200];save()
 print('FAILED',repr(e),flush=True);sys.exit(2)

#!/usr/bin/env python3
"""P15-89 genuine mask-conditioned Qwen ControlNet trial. Never auto-admit."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageOps
import requests,json,hashlib,sys,datetime
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-89-masked-local-art';D.mkdir(parents=True,exist_ok=True)
SRC=P/'p15-86-semantic-ownership/hidden-face.reassigned.png'
ref=P/'p15-56-edge-matting/candidate-erode-2.png'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
# Fully original 1024 canvas in same coordinates, masked around the actual
# left outer-eye fringe/skin junction exposed after the P15-86 correction.
under=Image.open(SRC).convert('RGBA')
identity=Image.open(ref).convert('RGBA')
bg=Image.new('RGBA',under.size,'white');bg.alpha_composite(under)
inp=D/'full-source-1024.png';bg.convert('RGB').save(inp)
# Only the broken exposed contour, not the iris or most of the eye.
polygon=[(505,430),(518,427),(532,430),(547,445),(549,462),(538,475),(515,470),(502,452)]
mask=Image.new('L',under.size,0);ImageDraw.Draw(mask).polygon(polygon,fill=255)
mask=mask.filter(ImageFilter.GaussianBlur(1.3))
mp=D/'local-mask-1024.png';mask.save(mp)
# The source is a structural control, not a separate regenerated whole head.
ctrl=D/'control-lineart-1024.png'
gray=ImageOps.grayscale(bg.convert('RGB'))
from PIL import ImageFilter,ImageChops
edges=gray.filter(ImageFilter.FIND_EDGES).point(lambda x:255 if x>28 else 0)
line=ImageOps.invert(edges).convert('RGB')
line.save(ctrl)
qa={'schema':'KOMA-P15-89-MASKED-CONTROL-V1','sourceSHA256':sha(SRC),'referenceSHA256':sha(ref),
    'inputSHA256':sha(inp),'controlSHA256':sha(ctrl),'maskSHA256':sha(mp),
    'maskBBox':list(mask.getbbox()),'maskActivePixels':sum(v>0 for v in mask.getdata()),
    'canvas':[1024,1024], 'maskPassedAsTrueModelArgument':False,
    'status':'PREPARED','modelOutputCreated':False,
    'candidateAccepted':False,'formalArtMeshAccepted':False,'formalKeyframeAccepted':False}
E=R/'evidence/p15-89-masked-inference-qa.json'
def save():E.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
save()
HOST='https://hugging-apps-qwen-image-2-1-controlnet-union-demo.hf.space'
s=requests.Session()
def upload(path):
 with path.open('rb') as f:
  r=s.post(HOST+'/gradio_api/upload',files={'files':(path.name,f,'image/png')},timeout=90)
 r.raise_for_status()
 return {'path':r.json()[0],'orig_name':path.name,'meta':{'_type':'gradio.FileData'}}
try:
 vals={k:upload(p) for k,p in [('control',ctrl),('source',inp),('mask',mp)]}
 print('UPLOAD_OK',list(vals),flush=True)
 prompt=('High quality original Japanese 2D anime painted hidden face under rose lavender bangs, '
  'repair only the small broken outer eye hair-to-skin boundary inside the explicit inpainting mask. '
  'Natural tapered lavender hair strand and contiguous peach skin shading. '
  'Preserve EXACT character, viewpoint and every facial feature outside the mask. '
  'No old stray eyelash, no vertical hard seam, no text.')
 payload=[prompt,vals['control'],'None (already a control map)',
  {'background':vals['source'],'layers':[],'composite':None},
  vals['mask'],1.0,1024,20,1589001,False,
  'extra eyes, altered camera, wrong pose, different character, extra clips, detached line',1.0]
 # Gradio input 4 is actual imageeditor; input 5 is explicit model inpaint mask.
 qa['maskPassedAsTrueModelArgument']=True;qa['model']='hugging-apps/Qwen-Image-2.1-ControlNet-Union-Demo'
 qa['api']='/gradio_api/call/generate';qa['seed']=1589001;qa['status']='UPLOADED_MASK_SUBMITTED';save()
 r=s.post(HOST+'/gradio_api/call/generate',json={'data':payload},timeout=90)
 print('SUBMIT_HTTP',r.status_code,r.text[:450],flush=True)
 r.raise_for_status();eid=r.json()['event_id'];qa['eventId']=eid;qa['status']='QUEUED';save()
 with s.get(HOST+'/gradio_api/call/generate/'+eid,stream=True,timeout=(35,420)) as stream:
  stream.raise_for_status()
  event=''
  for ln in stream.iter_lines(decode_unicode=True):
   if not ln:continue
   if ln.startswith('event:'):event=ln[6:].strip();print('EVENT',event,flush=True)
   if ln.startswith('data:'):
    data=ln[5:].strip()
    if event=='error':raise RuntimeError('model returned error '+data[:1200])
    if event=='complete':
     arr=json.loads(data)
     if not isinstance(arr,list) or not arr:raise RuntimeError('Unexpected model result '+data[:400])
     val=arr[0]
     url=val.get('url') if isinstance(val,dict) else val
     if not url and isinstance(val,dict):url=HOST+'/gradio_api/file='+val['path']
     if url.startswith('/'):url=HOST+url
     response=s.get(url,timeout=120);response.raise_for_status()
     op=D/'returned-model-1024.png';op.write_bytes(response.content)
     im=Image.open(op);assert im.size==(1024,1024),im.size
     qa.update(status='MODEL_RETURNED',modelOutputCreated=True,outputSHA256=sha(op),outputBytes=op.stat().st_size)
     save();print('MODEL_RETURNED',op.stat().st_size,qa['outputSHA256'],flush=True);sys.exit(0)
 raise RuntimeError('No complete event')
except Exception as e:
 qa.update(status='INFERENCE_FAILED',errorType=type(e).__name__,error=str(e)[:1500]);save()
 print('INFERENCE_FAILED',repr(e),flush=True);sys.exit(2)

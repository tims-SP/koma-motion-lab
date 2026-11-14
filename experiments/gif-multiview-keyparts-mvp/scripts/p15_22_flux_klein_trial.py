#!/usr/bin/env python3
"""Run independent new painting trial with FLUX.2 Klein fast image editing."""
import base64,hashlib,json
from pathlib import Path
from io import BytesIO
from PIL import Image
from gradio_client import Client
ROOT=Path(__file__).resolve().parent.parent
P=ROOT/'private-assets'
OUT=P/'p15-22-new-painting';OUT.mkdir(exist_ok=True)
A=P/'p2-views/whole/yaw045.png'
B=P/'p15-21-layered-anatomy/yaw60.png'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def reference(p):
 rgb=Image.open(p).convert('RGBA')
 bg=Image.new('RGBA',rgb.size,'white');bg.alpha_composite(rgb)
 buf=BytesIO();bg.convert('RGB').save(buf,'JPEG',quality=90)
 return 'data:image/jpeg;base64,'+base64.b64encode(buf.getvalue()).decode()
if __name__=='__main__':
 img=OUT/'yaw060-flux2-klein-source.png'
 if img.exists():raise FileExistsError(str(img))
 prompt=("Create a newly painted frame of the exact same anime girl, not just copy of pixels. "
 "Image 1 fixes the character identity including mauve neck-length bob haircut, side-swept fringe, single ahoge, "
 "gold crossed X barrette on the original same physical side, violet-pink eyes, navy school uniform with gold trim, burgundy bow. "
 "Image 2 fixes head yaw 60 degrees facing right, size and placement. Retain natural near violet eye and thin far iris partly "
 "covered by the nose bridge/bangs. Anatomically accurate profile transition, clean anime cel linework, consistent lighting, "
 "no extra eyes, no additional hairpin, gold crossed clip appears foreshortened, no mirror or costume changes, white background.")
 refs=json.dumps([reference(A),reference(B)])
 print(json.dumps({'event':'start','space':'prithivMLmods/Flux.2-Klein-Edit-Ultra-Fast','yaw':60,
   'sourceSHA256':[sha(A),sha(B)],'seed':602202}),flush=True)
 try:
  c=Client('prithivMLmods/Flux.2-Klein-Edit-Ultra-Fast',verbose=False)
  res=c.predict(refs,prompt,602202,False,768,768,4,1.0,api_name='/edit_image')
  if isinstance(res,(tuple,list)):res=res[0]
  data=base64.b64decode(res['image'].split('base64,')[-1])
  i=Image.open(BytesIO(data)).convert('RGB')
  i.save(img)
  record={'schema':'KOMA-P15-22-FLUX-KLEIN-NEW-PAINTING-V1','characterId':'p0_character_001',
   'model':'FLUX.2 Klein 4B','space':'prithivMLmods/Flux.2-Klein-Edit-Ultra-Fast',
   'seed':602202,'steps':4,'guidance':1.0,'prompt':prompt,'sourceSHA256':[sha(A),sha(B)],
   'path':str(img.relative_to(P)),'sha256':sha(img),'canvas':list(i.size),
   'artisticAcceptance':False,'independentSemanticLayersAccepted':0,
   'status':'NEW_RGB_PAINT_CANDIDATE_PENDING_IDENTITY_POSE_AND_LAYER_QA'}
  (OUT/'flux-trial-qa.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
  print(json.dumps({'event':'complete','sha256':sha(img),'size':list(i.size)}),flush=True)
 except Exception as exc:
  rec={'schema':'KOMA-P15-22-FLUX-INFERENCE-ATTEMPT-V1','attempted':True,
   'space':'prithivMLmods/Flux.2-Klein-Edit-Ultra-Fast','errorType':type(exc).__name__,
   'errorText':str(exc)[:1300],'modelOutputCreated':False}
  (OUT/'flux-attempt-qa.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n')
  print(json.dumps(rec),flush=True)
  raise

#!/usr/bin/env python3
"""Generate a fresh independent P0 intermediate-angle painting candidate.

This is a new model-generated source image, NOT a transparent semantic layer,
not admitted to VDD until source identity and pose review.
"""
import base64,hashlib,json,os
from pathlib import Path
from io import BytesIO
from PIL import Image
from gradio_client import Client
R=Path(__file__).resolve().parent.parent
A=R/'private-assets'
SPACE='akhaliq/Qwen-Image-Edit-2511-LoRAs-Fast'
D=A/'p15-22-new-painting';D.mkdir(exist_ok=True)
SOURCE=A/'p2-views/whole/yaw045.png'
POSE=A/'p15-21-layered-anatomy/yaw60.png'
OUT=D/'yaw060-new-painting-candidate.png'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
if __name__=='__main__':
 if OUT.exists():raise FileExistsError(str(OUT))
 def url(src):
  im=Image.open(src).convert('RGBA')
  matte=Image.new('RGBA',im.size,(255,255,255,255));matte.alpha_composite(im)
  buf=BytesIO();matte.convert('RGB').save(buf,'JPEG',quality=95)
  return 'data:image/jpeg;base64,'+base64.b64encode(buf.getvalue()).decode()
 input_data=json.dumps([url(POSE),url(SOURCE)])
 prompt=('Create a newly hand-painted anime keyframe at exactly the pose/scale of Image 1; use Image 2 ONLY to lock character identity. '
  'One original anime girl, head rotated 60 degrees to right profile (not facing viewer, not full side profile); '
  'near eye violet pink fully visible; far eye much narrower and partially concealed by bangs/nose bridge; coherent face outline, jaw and nose. '
  'Identity is the identical character from Image 2: neck length mauve pink bob with soft bangs, one thin upward ahoge, '
  'gold X-shaped crossed hairclip on the same physical hair side at the viewer right of the original reference. '
  'Keep X hairpin physically consistent and partially foreshortened, no additional ornaments. '
  'Preserve the navy school jacket with gold trim, white collar and burgundy bow. '
  'Clean original Japanese anime 2D cel-shaded hand-painted still with high quality precise linework, '
  'correct occlusion between separate hair locks, no double eyes, no fused hair pin, no extra hairpin, '
  'entire figure same location/scale as Image 1 on pure white background, no text or split panels. ')
 source={'yaw045':digest(SOURCE),'poseYaw60':digest(POSE)}
 print(json.dumps({'event':'start','space':SPACE,'model':'Qwen-Image-Edit-2511','seed':602201,'inputSHA256':source}),flush=True)
 try:
  c=Client(SPACE,verbose=False)
  data=c.predict(input_data,prompt,'Anime-V2',602201,False,1.0,4,api_name='/edit_image')
  if isinstance(data,list):data=data[0]
  raw=base64.b64decode(data['image'].split('base64,')[-1])
  im=Image.open(BytesIO(raw)).convert('RGB')
  if im.size!=(1024,1024):raise RuntimeError('unexpected canvas: '+str(im.size))
  im.save(OUT)
  d={'schema':'KOMA-P15-22-INDEPENDENT-PAINTING-TRIAL-V1','characterId':'p0_character_001',
     'model':'Qwen-Image-Edit-2511','adapter':'Anime-V2','seed':602201,'steps':4,'guidance':1.0,
     'inputSHA256':source,'prompt':prompt,'outputPath':str(OUT.relative_to(A)),
     'outputSHA256':digest(OUT),'canvas':[1024,1024],'type':'NEW_INDEPENDENT_RGB_PAINTING_CANDIDATE',
     'transparentLayersProduced':0,'semanticLayersAccepted':0,
     'artisticAcceptance':False,'status':'GENERATED_REQUIRES_INDEPENDENT_POSE_AND_IDENTITY_REVIEW'}
  (D/'trial-qa.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
  print(json.dumps({'event':'complete','sha256':digest(OUT),'bytes':OUT.stat().st_size,'accepted':0}),flush=True)
 except Exception as exc:
  d={'schema':'KOMA-P15-22-INFERENCE-ATTEMPT-V1','characterId':'p0_character_001','space':SPACE,
     'sourceSHA256':source,'attempted':True,'modelOutputCreated':False,
     'errorType':type(exc).__name__,'errorText':str(exc)[:1500],'status':'INFERENCE_UNAVAILABLE_NO_ART_GENERATED'}
  (D/'attempt-qa.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
  print(json.dumps(d,ensure_ascii=False),flush=True)
  raise

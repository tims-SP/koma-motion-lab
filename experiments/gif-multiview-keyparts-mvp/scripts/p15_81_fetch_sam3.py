from pathlib import Path
from PIL import Image
import requests,hashlib,json
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-81-image-layered';D.mkdir(parents=True,exist_ok=True)
urls=[
'https://prithivmlmods-sam3-demo.hf.space/--replicas/4tz4r/gradio_api/file=/tmp/gradio/5aa4053c77e73a01c1ffa7868d50f63cad7a96554969f50dacfe0e7adcd222b4/image.webp',
'https://prithivmlmods-sam3-demo.hf.space/--replicas/4tz4r/gradio_api/file=/tmp/gradio/c697b00663e64810facd9db547ee3fb48111afc7ee2db444bc9ad610d89a9bcb/image.png',
'https://prithivmlmods-sam3-demo.hf.space/--replicas/4tz4r/gradio_api/file=/tmp/gradio/8b93e50709350b0b654e3e911d0fbc2892c4ea14ee93f006fcb8010b4303f87d/image.png'
]
s=requests.Session();files=[]
for name,url in zip(['sam3-overlay.webp','sam3-mask-027.png','sam3-mask-083.png'],urls):
 r=s.get(url,timeout=40);print(name,r.status_code,len(r.content),r.headers.get('content-type'),flush=True)
 r.raise_for_status();p=D/name;p.write_bytes(r.content)
 im=Image.open(p);print('IM',im.mode,im.size,'bbox',im.getbbox(),flush=True)
 files.append({'name':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'mode':im.mode,'size':list(im.size)})
q={'schema':'KOMA-P15-81-SAM3-AUTHENTICATED-V1','provider':'prithivMLmods/SAM3-Demo',
 'prompt':'front bangs hair fringe on forehead','confidenceThreshold':0.25,
 'inferenceAuthenticated':True,'outputs':files,'status':'MODEL_RETURNED',
 'formalArtMeshAccepted':False,'formalKeyframeAccepted':False}
(R/'evidence/p15-81-sam3-authenticated.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')

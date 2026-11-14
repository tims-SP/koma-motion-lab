#!/usr/bin/env python3
"""P15-43 explicit camera-landmark and generated art comparison witness."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw

R=Path(__file__).resolve().parents[1]
P=R/'private-assets'
D=P/'exports/p15-43-camera-pose-review'
D.mkdir(parents=True,exist_ok=True)
Q=R/'evidence/p15-43-camera-pose-qa.json'
CAM=R/'evidence/p15-12-camera-proxy-qa.json'
cam=json.loads(CAM.read_text())
frame=next(x for x in cam['frames'] if x['yaw']==65)
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
sources={
  'p0-45.png':P/'p2-views/whole/yaw045.png',
  'registered-60.png':P/'p15-38-p0-registered-arc/yaw60/composite.png',
  'registered-65.png':P/'p15-38-p0-registered-arc/yaw65/composite.png',
  'independent-profile.png':P/'p15-41-profile-candidate/candidate.png',
  'pose-locked-candidate.png':P/'p15-43-structured-pose/yaw065-pose-controlled-account-3.png'
}
# P15-41 image is kept under exports, not private source asset root.
sources['independent-profile.png']=P/'exports/p15-41-profile-candidate/candidate.png'
rows=[]
for name,src in sources.items():
 if not src.is_file():raise FileNotFoundError(src)
 with Image.open(src) as im:
  if im.size!=(1024,1024):raise AssertionError((name,im.size))
  mode=im.mode
 (D/name).write_bytes(src.read_bytes())
 rows.append({'image':name,'source':str(src.relative_to(P)),'sha256':sha(src),'mode':mode})
# Camera landmarks already derived from source 0/45/90, draw into overlay of 65 registered proxy.
im=Image.open(sources['registered-65.png']).convert('RGBA')
canvas=Image.new('RGBA',(1024,1024),'white');canvas.alpha_composite(im)
canvas=canvas.convert('RGB');pen=ImageDraw.Draw(canvas)
labels=['eye.near.iris','eye.far.iris','nose','mouth','face.chin','hair.clip.center']
for k in labels:
 p=frame['anchors'][k]['xy']
 if p is None:continue
 x,y=p; color='#e92e3c' if 'eye.far' in k else '#1777d5'
 pen.ellipse([x-9,y-9,x+9,y+9],fill=color,outline='white',width=2)
 pen.text((x+12,y-20),k,fill='#142d46',stroke_width=2,stroke_fill='white')
canvas.save(D/'yaw65-anchor-overlay.png')
# Canvas alignment and pose comparison is visual, not automatically inferred from alpha bbox.
qa={'schema':'KOMA-P15-43-CAMERA-GUIDED-IMAGE-REVIEW-V1','characterId':'p0_character_001','nominalYaw':65,
 'cameraSourceSHA256':sha(CAM),'cameraModel':cam['model'],'cameraAnchors':{k:frame['anchors'][k] for k in labels},
 'inputRegistered65SHA256':sha(sources['registered-65.png']),'generatedSourceSHA256':sha(sources['pose-locked-candidate.png']),
 'sourceImages':rows,'overlaySHA256':sha(D/'yaw65-anchor-overlay.png'),
 'generation':{'model':'Qwen Image Edit 2511','space':'akhaliq/Qwen-Image-Edit-2511-LoRAs-Fast','seed':65431,
 'adapter':'Multiple-Angles','inputImages':['registered-65.png','p0-45.png'],'controlledPose':'65-degree right-facing, retain source 65 image-space camera'},
 'visualObservations':{'cameraDirection':'generated image faces screen-left, source faces screen-right',
 'farEye':'second eye absent from generated image','hairclip':'clip now at screen-left','hair':'additional back hair bunch differs from P0 identity'},
 'generatedPoseAccepted':False,'generatedIdentityAccepted':False,'new65KeyframeCommitted':False,
 'approvedHeroSHA256Verified':False,'artisticAcceptance':False}
Q.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-43 · 65° 相机锚点与原画审查</title><style>:root{color-scheme:dark;font:15px/1.5 system-ui;background:#152435;color:#eff4fc}body{max-width:1450px;margin:auto;padding:16px}h1{font-size:23px}p{color:#c5d3e2}nav{display:flex;gap:10px;margin:15px 0;flex-wrap:wrap}button{padding:9px 12px;border:1px solid #7393b4;border-radius:7px;background:#38536c;color:white}button[aria-pressed=true]{background:#5f7eab}section{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}article{background:#263b50;padding:10px;min-width:0}h3{font-size:15px;margin:0 0 10px}img{width:100%;object-fit:contain;aspect-ratio:1;background:repeating-conic-gradient(#d2dce7 0 25%,#f8fafc 0 50%) 50%/24px 24px}@media(max-width:800px){section{grid-template-columns:repeat(2,1fr)}}@media(max-width:500px){section{grid-template-columns:1fr}}</style><h1>P15-43 · 65° 结构化机位审查</h1><p>蓝色与红色标记来自 45°/90° 注册相机锚点。图像生成后的朝向、远眼与发夹必须逐项匹配才允许进入 13 层 ArtMesh。</p><nav><button data-mode="pose" aria-pressed="true">姿态与锚点</button><button data-mode="identity">身份对照</button></nav><section id="gallery"></section><p id="status" role="status"></p><script>
const modes={pose:[['registered-65.png','源注册 65°'],['yaw65-anchor-overlay.png','65° 结构化锚点'],['pose-locked-candidate.png','Qwen 双参考输出']],identity:[['p0-45.png','P0 原始 45°'],['registered-60.png','当前 60°'],['independent-profile.png','独立侧脸结构参考']]};
async function show(mode='pose'){document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===mode)));const g=document.getElementById('gallery');g.replaceChildren();const im=modes[mode].map(([f,label])=>{const a=document.createElement('article'),h=document.createElement('h3'),i=document.createElement('img');h.textContent=label;i.alt=label;i.src=f;a.append(h,i);g.append(a);return i});let r=await Promise.allSettled(im.map(i=>i.decode()));const ok=r.every(x=>x.status==='fulfilled')&&im.every(x=>x.naturalWidth===1024&&x.naturalHeight===1024);document.getElementById('status').textContent=ok?'来源与对照载入成功；机位与角色身份仍需独立准入':'来源载入失败';return ok}
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>show(b.dataset.mode));window.__KOMA_P15_43={show};show();</script>'''
(D/'index.html').write_text(html)
print(json.dumps({'images':len(rows),'anchors':len(labels),'generatedSource':qa['generatedSourceSHA256'],'review':str(D/'index.html')}))

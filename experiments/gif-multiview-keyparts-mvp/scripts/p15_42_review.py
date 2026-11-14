#!/usr/bin/env python3
"""P15-42: source-tracked image generation and 65-degree pose admission review."""
from pathlib import Path
from PIL import Image
import json,hashlib,shutil
R=Path(__file__).resolve().parents[1];A=R/'private-assets';O=A/'exports/p15-42-65-keyart-review';O.mkdir(parents=True,exist_ok=True)
Q=R/'evidence/p15-42-source-and-pose-qa.json'
files={
 'source-45.png':A/'p2-views/whole/yaw045.png',
 'source-60.png':A/'p15-38-p0-registered-arc/yaw60/composite.png',
 'source-65.png':A/'p15-38-p0-registered-arc/yaw65/composite.png',
 'candidate-1.png':A/'p15-42-65-original-candidates/yaw065-hf-account-2.png',
 'candidate-2.png':A/'p15-42-65-original-candidates/yaw065-dualref-65422.png',
 'candidate-3.png':A/'p15-42-65-original-candidates/yaw065-incremental-65423.png',
 'profile-reference.png':A/'p15-independent-candidates/yaw065-source-rgba.png'
}
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
rows=[]
for name,source in files.items():
 if not source.is_file():raise FileNotFoundError(source)
 with Image.open(source) as im:
  if im.size!=(1024,1024):raise ValueError(f'Wrong source canvas {source}: {im.size}')
  size=im.size;mode=im.mode
 (O/name).write_bytes(source.read_bytes())
 rows.append({'name':name,'sourcePath':str(source.relative_to(R)),'sha256':sha(source),'canvas':size,'mode':mode})
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-42 · 65° 关键原画准入审查</title><style>:root{color-scheme:dark;background:#172331;color:#f2f5fb;font:15px/1.5 system-ui}body{max-width:1450px;margin:auto;padding:16px}h1{font-size:24px}p{color:#b8c8dc}nav{display:flex;gap:9px;flex-wrap:wrap;margin:12px 0}button{background:#344b66;color:white;border:1px solid #7294b3;padding:9px;border-radius:7px;cursor:pointer}button[aria-pressed=true]{background:#6482ae}section{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}article{padding:10px;background:#293a50;min-width:0}h3{margin:0 0 8px;font-size:15px}img{width:100%;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#d3dfea 0 25%,#fafafa 0 50%) 50%/22px 22px}#status{margin:12px 0}@media(max-width:840px){section{grid-template-columns:repeat(2,1fr)}}@media(max-width:520px){section{grid-template-columns:1fr}}</style><main><h1>P15-42 · 65° 独立原画视觉审查</h1><p>所有画面均为真实生成或登记来源。候选 A/B/C 的姿态、远眼与发夹均需独立核对；三个生成候选尚未准入正式 65° VDD 关键帧。</p><nav><button data-mode="angle" aria-pressed="true">相机朝向</button><button data-mode="identity">身份细节</button></nav><section id="gallery"></section><p id="status" role="status"></p></main><script>
const modes={angle:[['source-60.png','P15-38 原注册 60°'],['candidate-1.png','新候选 A · 正向但近 90°'],['candidate-2.png','新候选 B · 反向侧面'],['candidate-3.png','新候选 C · 侧面发夹位置漂移']],identity:[['source-45.png','P0 原始 45°'],['source-65.png','P15-38 注册 65°'],['profile-reference.png','既有侧脸独立原画']]};
async function show(m='angle'){const g=document.getElementById('gallery');g.replaceChildren();document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===m)));const imgs=modes[m].map(([file,label])=>{const a=document.createElement('article'),h=document.createElement('h3'),img=document.createElement('img');h.textContent=label;img.alt=label;img.src=file;a.append(h,img);g.append(a);return img});const v=await Promise.allSettled(imgs.map(i=>i.decode()));const valid=v.every(x=>x.status==='fulfilled')&&imgs.every(i=>i.naturalWidth===1024&&i.naturalHeight===1024);document.getElementById('status').textContent=valid?'3 幅真实原画加载成功；姿态与艺术准入必须独立核对':'来源图像加载失败';return valid}document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>show(b.dataset.mode));window.__KOMA_P15_42={show,modes};show();</script>'''
(O/'index.html').write_text(html)
qa={'schema':'KOMA-P15-42-NEW-65-SOURCE-REVIEW-V1','characterId':'p0_character_001','frames':rows,'newModelPaintings':3,'source45Verified':True,'observations':[
 {'candidate':'candidate-1.png','cameraFacing':'right','angleFit':'approximately strict right-side profile rather than target 65','nearEye':'present','farEye':'not visible','goldClip':'edge-on','requested65PoseAccepted':False,'characterDesignAccepted':False},
 {'candidate':'candidate-2.png','cameraFacing':'left','angleFit':'opposite image-facing direction','nearEye':'present','farEye':'not visible','goldClip':'on image-left','hairIdentity':'extra ponytail','requested65PoseAccepted':False,'characterDesignAccepted':False},
 {'candidate':'candidate-3.png','cameraFacing':'right','angleFit':'near strict side profile','nearEye':'present','farEye':'not visible','goldClip':'shifted to image-left hair region','requested65PoseAccepted':False,'characterDesignAccepted':False}
 ],'newP0HeroSHA256Verified':False,'registeredArtMesh65Replaced':False,'newKeyframeAdmitted':False,'browserVerified':False,'visualApproval':False,'nextCriticalTask':'Produce right-facing 65-degree 2-visible-eyes key pose with consistent P0 character and transparent hidden layers'}
Q.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'sources':len(rows),'newPaintings':3,'poseAdmissions':0,'html':str(O/'index.html')}))

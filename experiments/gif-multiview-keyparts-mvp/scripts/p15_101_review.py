#!/usr/bin/env python3
"""Visual review of source-owned shared head, hair, and face UV correspondence."""
from pathlib import Path
from PIL import Image
import json,hashlib
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-101-head-render'
qpath=R/'evidence/p15-101-render-qa.json'
q=json.loads(qpath.read_text())
modes=list(q['methods']);angles=q['angles']
for mode,items in q['methods'].items():
 images=[]
 for angle in angles:
  path=R/items[f'{angle:g}']['relativePath']
  rgba=Image.open(path).convert('RGBA')
  bg=Image.new('RGBA',rgba.size,'white');bg.alpha_composite(rgba)
  images.append(bg.convert('RGB').resize((520,520),Image.Resampling.LANCZOS))
 seq=images+images[-2:0:-1]
 dest=D/(mode+'-yaw-loop.gif')
 seq[0].save(dest,save_all=True,append_images=seq[1:],duration=180,loop=0,optimize=False)
 q.setdefault('animations',{})[mode]={'relativePath':str(dest.relative_to(R)),
    'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
css="""body{font:15px/1.5 system-ui;background:#162639;color:#edf3fa;max-width:1480px;margin:15px auto;padding:0 16px}h1{font-size:23px}h2{font-size:18px}p,small{color:#bfcfdd}select,input{box-sizing:border-box;width:100%;padding:8px;margin:8px 0 14px}label{display:block;margin:12px 0}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{margin:0;padding:10px;border-radius:8px;background:#293f56}img{width:100%;display:block;object-fit:contain;background:white}figcaption{font-size:12px}@media(max-width:680px){.grid{grid-template-columns:1fr}}"""
options=''.join(f'<option value="{m}">{m.replace("_"," ")}</option>' for m in modes)
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 · Shared Head-Hair ArtMesh / View-Dependent UV Review</title><style>'''+css+'''</style></head><body>
<h1>P0 · 60°–75° 共用头部／头发网格验收</h1>
<p>沿用原始两端关键视角、P15-99 眼睛和头发蒙版、P15-100 脸部顶点。扩展后的头部与刘海采用同一组网格顶点、三角形索引及逐视角纹理坐标；中间画面来自真实连续渲染。面部隐藏内容与视角间变化仍须美术验收。</p>
<label for="method">头部合成与遮挡策略</label><select id="method">'''+options+'''</select>
<label for="yaw">视角角度：<b id="angle">60°</b></label><input id="yaw" type="range" min="0" max="8" step="1" value="0">
<div class="grid"><figure><img id="frame" src="head_alpha_blend-yaw60.png" alt="当前头部变形帧"><figcaption>全尺寸 1024×1024 原画／变形输出</figcaption></figure>
<figure><img id="motion" src="head_alpha_blend-yaw-loop.gif" alt="连续往返渲染动图"><figcaption>连续 60°–75° 动画</figcaption></figure></div>
<h2>原画共用头发网格</h2><div class="grid">
<figure><img src="../p15-101-shared-head-mesh/mesh-yaw60.png" alt="60度头部网格"><figcaption>60° 的头发、额头、耳、脸与下颌共享拓扑</figcaption></figure>
<figure><img src="../p15-101-shared-head-mesh/mesh-yaw75.png" alt="75度头部网格"><figcaption>75° 的独立源纹理与同索引网格</figcaption></figure></div>
<h2>全部候选对照</h2><figure><img src="head-hair-contact.jpg" alt="所有方法与角度的实际视觉对比"><figcaption>包含 P15-100 脸部局部网格基准</figcaption></figure>
<small>工程测试覆盖源图哈希、三角网格不翻面、纹理映射区域、实际渲染文件及交互功能；美术验收侧重重影、线稿连续性、遮挡和下颌轮廓。</small>
<script>
const modes='''+json.dumps(modes)+''',angles='''+json.dumps(angles)+''';
const method=document.querySelector('#method'),yaw=document.querySelector('#yaw'),frame=document.querySelector('#frame'),motion=document.querySelector('#motion'),label=document.querySelector('#angle');
function update(){const m=method.value,a=angles[Number(yaw.value)];label.textContent=a+'°';frame.src=m+'-yaw'+String(a).replace('.','p')+'.png';motion.src=m+'-yaw-loop.gif';}
method.addEventListener('change',update);yaw.addEventListener('input',update);
</script></body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
q['htmlReview']='private-assets/exports/p15-101-head-render/index.html'
qpath.write_text(json.dumps(q,indent=2,ensure_ascii=False)+'\n')
print('HTML',D/'index.html','modes',len(modes))

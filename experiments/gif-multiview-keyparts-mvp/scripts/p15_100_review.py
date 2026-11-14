#!/usr/bin/env python3
"""Source-owned P0 shared-face-mesh interactive VDD visual review."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports';D=P/'p15-100-mesh-vdd'
qaPath=R/'evidence/p15-100-render-qa.json'
qa=json.loads(qaPath.read_text())
methods=list(qa['methods']);angles=qa['interpolatedAngles']
for method,frames in qa['methods'].items():
 images=[]
 for angle in angles:
  p=R/frames[f'{angle:g}']['path']
  assert p.is_file()
  im=Image.open(p).convert('RGBA')
  bg=Image.new('RGBA',im.size,'white');bg.alpha_composite(im)
  images.append(bg.convert('RGB').crop((435,270,845,675)).resize((490,483),Image.Resampling.LANCZOS))
 animation=images+images[-2:0:-1]
 dest=D/f'{method}-yaw-loop.gif'
 animation[0].save(dest,save_all=True,append_images=animation[1:],duration=185,loop=0,optimize=False)
 qa.setdefault('animations',{})[method]={'relativePath':str(dest.relative_to(R)),
   'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
css="""body{font:15px/1.5 system-ui;background:#152638;color:#edf2f9;max-width:1460px;padding:0 15px;margin:13px auto}h1{font-size:24px}h2{font-size:18px}p,small{color:#bdcadb}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{margin:0;padding:11px;border-radius:8px;background:#283e56}img{display:block;object-fit:contain;width:100%;height:auto;background:white}figcaption{font-size:12px}select,input{box-sizing:border-box;width:100%;padding:8px;margin:7px 0 14px}label{display:block;margin-top:10px}.full{margin:12px 0}@media(max-width:690px){.grid{grid-template-columns:1fr}}"""
opts=''.join(f'<option value="{m}">{m.replace("_"," ")}</option>' for m in methods)
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 · Shared Face Mesh View-Dependent UV Study</title><style>'''+css+'''</style></head><body>
<h1>P0 · 60°–75° 共用脸部三角网格 / VDD 验收</h1>
<p>共用顶点、固定三角面索引与独立视角纹理坐标。面部控制由原始 P15-99 可见面分层与 P15-98 视觉锚点建立；展示实际渲染的独立关键帧和中间角度。网格几何与源像素可复现，连续视觉质量仍需评价。</p>
<label for="method">渲染方式</label><select id="method">'''+opts+'''</select>
<label for="yaw">转头角度：<b id="yaw-label">60°</b></label><input id="yaw" min="0" max="8" value="0" step="1" type="range">
<div class="grid">
<figure><img id="current" src="mesh_source_blend-yaw60.png" alt="网格映射后真实转头画面"><figcaption>单角度原尺寸 RGBA 渲染</figcaption></figure>
<figure><img id="motion" src="mesh_source_blend-yaw-loop.gif" alt="连续转头反复播放"><figcaption>正向与返程 GIF 对照</figcaption></figure></div>
<h2>全部角度和方案对照</h2><figure class="full"><img src="mesh-vdd-contact.jpg" alt="网格纹理融合与原分层的对照"><figcaption>与 P15-99 原分层基线并排比较</figcaption></figure>
<h2>原画坐标下的共用网格</h2><div class="grid">
<figure><img src="../p15-100-shared-face-mesh/mesh-yaw60.png" alt="60度脸部三角网格"><figcaption>60° 真实原画顶点和三角面</figcaption></figure>
<figure><img src="../p15-100-shared-face-mesh/mesh-yaw75.png" alt="75度脸部三角网格"><figcaption>75° 同顶点索引的投影和纹理坐标</figcaption></figure></div>
<small>22 个顶点、28 个有效三角面；视角和 UV 对应属于 2D 代理假设，并不等同于解出角色真实 3D 头部。</small>
<script>
const methods='''+json.dumps(methods)+''',angles='''+json.dumps(angles)+''';
const method=document.querySelector('#method'),yaw=document.querySelector('#yaw'),
current=document.querySelector('#current'),motion=document.querySelector('#motion'),label=document.querySelector('#yaw-label');
function refresh(){const m=method.value,a=angles[Number(yaw.value)];label.textContent=a+'°';current.src=m+'-yaw'+String(a).replace('.','p')+'.png';motion.src=m+'-yaw-loop.gif';}
method.addEventListener('change',refresh);yaw.addEventListener('input',refresh);
</script></body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
qa['htmlReview']='private-assets/exports/p15-100-mesh-vdd/index.html'
qaPath.write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')
print('REVIEW',D/'index.html','methods',len(methods),'angles',len(angles))

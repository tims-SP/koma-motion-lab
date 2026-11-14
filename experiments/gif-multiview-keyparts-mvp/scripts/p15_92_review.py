#!/usr/bin/env python3
"""HTML reviewer for 45–90 degree independent keyart and conditional VDD flow previews."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-92-angle-keyart'
q=json.loads((R/'evidence/p15-92-view-flow-qa.json').read_text())
angles=[45,52.5,60,67.5,75,82.5,90]
files=[]
for a in angles:
 path=Path(q['frames'][str(a)]['path']);assert (R/path).is_file(),path
 files.append(path.name)
identities=[('45°','yaw045-reference.png'),('60°','yaw060-registered.png')]
if (D/'yaw075-registered.png').is_file():identities.append(('75°','yaw075-registered.png'))
identities.append(('90°','yaw090-reference.png'))
css="""body{background:#162435;color:#f2f6fb;font:15px/1.5 system-ui;margin:12px auto;padding:0 15px;max-width:1550px}p{color:#b4c2d3}h1{font-size:23px}h2{font-size:19px}label{display:block;margin:10px 0}input{width:100%}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}figure{margin:0;border-radius:9px;padding:8px;background:#253952}img{width:100%;object-fit:contain;background:white;border-radius:3px}figcaption{font-size:13px;margin-top:5px}#pose-image{display:block;width:100%;max-width:680px;margin:0 auto}small{color:#b4c2d3}@media(max-width:750px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}"""
markup=''.join(f'<figure><img src="{f}" alt="{tag} character art"><figcaption>{tag} 独立参考原画</figcaption></figure>' for tag,f in identities)
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 · 独立视角原画与连续性审核</title><style>'''+css+'''</style></head><body>
<h1>P0 · 多视角独立原画与视角连续性审核</h1><p>原创角色 p0_character_001。生成模型负责绘制新的视角原画，现有 TypeScript/WebGL/VDD 研究流程继续负责语义层、深度和动态遮挡。当前角度为生成目标，正式身份及镜头几何仍待验收。</p>
<h2>已生成关键角度</h2><div class="grid">'''+markup+'''</div><h2>45°–90° 连续镜头诊断</h2>
<label for="angle">目标角度：<strong id="angle-label">45°</strong></label><input id="angle" type="range" min="0" max="6" step="1" value="0">
<figure><img id="pose-image" src="'''+files[0]+'''" alt="连续镜头角度候选"><figcaption id="pose-caption">已登记的独立关键帧</figcaption></figure>
<h2>七角度总览</h2><figure><img src="seven-angle-contact.jpg" alt="seven-angle view continuity"><figcaption>独立生成关键帧与插值候选对照</figcaption></figure>
<script>const angles='''+json.dumps(angles)+''',files='''+json.dumps(files)+''',keys=new Set('''+json.dumps(q['sourceAngles'])+''');const slider=document.getElementById('angle'),label=document.getElementById('angle-label'),image=document.getElementById('pose-image'),caption=document.getElementById('pose-caption');slider.addEventListener('input',()=>{const i=Number(slider.value);label.textContent=angles[i]+'°';image.src=files[i];caption.textContent=keys.has(angles[i])?'独立原画':'连续变形诊断候选';});</script></body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
print('HTML',D/'index.html')

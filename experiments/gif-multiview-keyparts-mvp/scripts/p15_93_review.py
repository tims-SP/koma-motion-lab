#!/usr/bin/env python3
"""Create interactive P0 yaw52.5 independent-keyart and interpolation review."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports/p15-93-yaw0525-review'
A=R/'private-assets/exports/p15-92-angle-keyart'
assert (P/'yaw052p5-registered.png').is_file()
paths=['../p15-92-angle-keyart/yaw045-reference.png','yaw48p75-blend.png','yaw052p5-registered.png','yaw56p25-blend.png','../p15-92-angle-keyart/yaw060-registered.png']
for p in paths:
 assert (P/p).is_file(),p
css="""body{background:#162435;color:#f4f7fd;font:15px/1.5 system-ui;margin:12px auto;padding:0 15px;max-width:1470px}h1{font-size:23px}h2{font-size:19px}p{color:#c4d2dd}label{display:block;margin:12px 0}input{width:100%}figure{margin:0;background:#263952;border-radius:7px;padding:10px}img{width:100%;height:auto;object-fit:contain;background:white}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figcaption{font-size:13px}#current{max-width:580px;margin:auto;display:block}@media(max-width:690px){.grid{grid-template-columns:1fr}}"""
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 · 52.5° independent keyart review</title><style>'''+css+'''</style></head><body>
<h1>P0 · 52.5° 独立原画与连续形变验收</h1>
<p>Codex 原生图像生成的新增关键原画与原有的 OpenCV DIS 52.5° 插值结果并列查看。新原画用于探索 45°→60° 的更短跨角度变形。模型目标角度及身份一致性待正式验证。</p>
<h2>新增视角对照</h2><div class="grid"><figure><img src="../p15-92-angle-keyart/yaw052p5.png" alt="DIS 原始 52.5 插值"><figcaption>旧的 52.5° 双向光流插值</figcaption></figure><figure><img src="yaw052p5-registered.png" alt="Codex 新绘 52.5 视角"><figcaption>Codex 独立生成的 52.5° 原画候选</figcaption></figure></div>
<h2>局部视角运动</h2><label for="angle">角度：<b id="pose">45</b>°</label><input id="angle" type="range" min="0" max="4" value="0" step="1">
<figure><img id="current" src="../p15-92-angle-keyart/yaw045-reference.png" alt="当前视角"><figcaption id="type">已存在原始参考关键帧</figcaption></figure>
<h2>五角度总览</h2><figure><img src="five-angle-contact.jpg" alt="45 to 60 independent and interpolation views"><figcaption>独立关键帧与短跨度插值分开标注</figcaption></figure>
<h2>插值方法对照</h2><figure><img src="../p15-93-flow-ablation/comparison.jpg" alt="three methods comparison"><figcaption>双向混合与单源变形的对比实验</figcaption></figure>
<script>const poses=[45,48.75,52.5,56.25,60],sources='''+__import__('json').dumps(paths)+''',keys=new Set([45,52.5,60]);const slider=document.getElementById('angle'),label=document.getElementById('pose'),im=document.getElementById('current'),desc=document.getElementById('type');slider.addEventListener('input',()=>{const n=Number(slider.value),a=poses[n];label.textContent=String(a);im.src=sources[n];desc.textContent=keys.has(a)?'独立原画':'短跨度光流插值候选';});</script></body></html>'''
(P/'index.html').write_text(html,encoding='utf-8')
print('HTML',P/'index.html')

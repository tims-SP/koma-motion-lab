#!/usr/bin/env python3
"""Build a reproducible visual comparison of P0 yaw60 SAM3 hair annotations."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-94-sam3-yaw060'
for f in ('hair-candidate-0-source-rgba.png','hair-candidate-1-source-rgba.png','semantic-mask-contact.jpg'):
 assert (D/f).is_file()
css="""body{font:15px/1.5 system-ui;background:#172535;color:#e9eef6;margin:15px auto;padding:0 15px;max-width:1450px}h1{font-size:23px}p{color:#b5c5d5}h2{font-size:18px}label{display:block;margin:12px 0}input{width:100%}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}figure{background:#283d55;padding:10px;margin:0;border-radius:8px}figure img{width:100%;object-fit:contain;background:white}figcaption{font-size:13px;color:#d3deea}@media(max-width:650px){.grid{grid-template-columns:1fr}}"""
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 · yaw60 SAM3 semantic hair masks</title><style>'''+css+'''</style></head><body><h1>P0 · yaw60 原画语义刘海分割</h1>
<p>使用 Hugging Face SAM3 的真实推理结果提取 60° 原画的头发可见像素。0 为正面刘海候选，1 为整体头发候选。蒙版来源和模型输出均可追溯；独立隐藏层与边缘质量尚待验证。</p>
<label for="choice">分割候选：<b id="name">前发（annotation 0）</b></label><input id="choice" type="range" min="0" max="1" step="1" value="0">
<div class="grid"><figure><img src="../p15-92-angle-keyart/yaw060-registered.png" alt="原始 60° RGBA 画稿"><figcaption>源原画</figcaption></figure>
<figure><img id="candidate" src="hair-candidate-0-source-rgba.png" alt="SAM3 实际分割来源像素"><figcaption>真实分割像素（原画 RGB 保留）</figcaption></figure></div>
<h2>模型分割范围</h2><figure><img src="semantic-mask-contact.jpg" alt="source and candidate masks"><figcaption>来自同一张原画的两种掩码范围对照</figcaption></figure>
<script>const slider=document.getElementById('choice'),text=document.getElementById('name'),image=document.getElementById('candidate');slider.addEventListener('input',()=>{const n=Number(slider.value);text.textContent=n===0?'前发（annotation 0）':'全头发（annotation 1）';image.src='hair-candidate-'+n+'-source-rgba.png';});</script></body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
print(D/'index.html')

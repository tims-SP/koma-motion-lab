#!/usr/bin/env python3
"""Build interactive HTML evidence for source-owned 0–18px P0 eye-contour motion."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-91-flow-transition'
for stem in ('blend-00.png','blend-09.png','blend-18.png','0-9-visual-contact.jpg'):
 assert (D/stem).is_file(),stem
css="""body{font-family:system-ui,sans-serif;margin:14px auto;max-width:1460px;padding:0 12px;background:#182536;color:#f2f6fc}h1{font-size:24px}p{color:#c3d0df}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{margin:0;padding:10px;border-radius:8px;background:#293d56}figure img{width:100%;object-fit:contain;background:#dddddd}figcaption{font-size:13px;margin-top:8px}label{display:block;margin:12px 0}input{width:100%}@media(max-width:670px){.grid{grid-template-columns:1fr}}"""
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-91 · P0 eye contour motion</title><style>'''+css+'''</style></head><body><h1>P15-91 · P0 刘海与眼部连续动作</h1>
<p>Codex 原生图像生成、原画空间对齐、刘海语义归属和双向光流插帧的局部验证。所有结果基于同一原创角色。0px 使用原始关键帧，9px 与 18px 使用修复后的关键帧。</p>
<label for="shift">水平眼部位移：<b id="pose">0</b> px</label><input id="shift" type="range" min="0" max="18" value="0" step="1">
<div class="grid"><figure><img id="baseline" src="../p15-91-temporal-motion/frame-00.png" alt="原分层插值"><figcaption>原分层连续运动</figcaption></figure>
<figure><img id="candidate" src="blend-00.png" alt="Codex 局部修复和光流连续运动"><figcaption>Codex 局部修复与光流混合</figcaption></figure></div>
<h2>连续关键帧比较</h2><figure><img src="0-9-visual-contact.jpg" alt="前 10 帧的连续运动对照"><figcaption>0→9px 原分层、双向光流混合和单源重投影对照</figcaption></figure>
<h2>原画修复细节</h2><figure><img src="../p15-91-hair-ownership/dynamic-contact.jpg" alt="刘海与眼部语义分层补绘比较"><figcaption>9px 与 18px 的局部刘海归属修复</figcaption></figure>
<script>const slider=document.getElementById('shift'),pose=document.getElementById('pose'),baseline=document.getElementById('baseline'),candidate=document.getElementById('candidate');slider.addEventListener('input',()=>{const id=String(slider.value).padStart(2,'0');pose.textContent=slider.value;baseline.src='../p15-91-temporal-motion/frame-'+id+'.png';candidate.src='blend-'+id+'.png';});</script>
</body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
print('HTML',D/'index.html')

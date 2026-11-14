#!/usr/bin/env python3
"""Create an interactive visual-review page for source-owned P0 underpaint."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-90-precision-mask'
q=json.loads((R/'evidence/p15-90-precision-mask-qa.json').read_text())
assert q['variants']['r4']['frames']['0']['changedPixels']==0
assert q['variants']['r4']['frames']['9']['outsideMask']==0
assert q['variants']['r4']['frames']['18']['outsideMask']==0
css="""body{font-family:system-ui,sans-serif;background:#152434;color:#f2f4fa;max-width:1440px;margin:16px auto;padding:0 12px}h1{font-size:23px}.sub{color:#c2cad2}section{margin:20px 0}label{display:block;margin:8px 0}input{width:100%}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{margin:0;background:#23354a;padding:12px;border-radius:8px}figcaption{margin-top:8px}img{width:100%;height:auto;object-fit:contain;background:#ddd}small{color:#aab6c7}"""
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 · Hidden Hair Edge Review</title><style>'''+css+'''</style></head><body>
<h1>P0 · 头发遮挡与眼部运动局部补绘</h1>
<p class="sub">已生成真实 See-through 分层 PSD 和 Qwen 局部蒙版图；仅采用 r4 的少量候选像素进行动态比较。原始 0px 姿态保持逐像素一致；视觉签收状态为待审。</p>
<section><label for="shift">移动眼部：<span id="pose">0</span>px</label><input id="shift" type="range" min="0" max="18" step="9" value="0">
<div class="grid">
<figure><img id="baseline" alt="原始姿态" src="../p15-86-semantic-ownership/frame-00.png"><figcaption>来源参考</figcaption></figure>
<figure><img id="candidate" alt="候选姿态" src="r4-00.png"><figcaption>模型局部补绘（r4）</figcaption></figure>
</div></section><section><h2>局部逐帧对照</h2>
<figure><img src="precision-contact.jpg" alt="9px 与 18px 三种修复半径对照"><figcaption>9/18px 细节与三种局部范围对照</figcaption></figure></section>
<section><h2>模型证据</h2>
<div class="grid">
<figure><img src="../p15-90-qwen-masked/masked-contact.jpg" alt="真实局部蒙版输入输出"><figcaption>Qwen 原图、完整输出及 Mask</figcaption></figure>
<figure><img src="../../p15-90-seethrough/layer-contact.jpg" alt="See-through 原生图层"><figcaption>See-through 18 个图层概览</figcaption></figure>
</div></section>
<script>
const step=document.querySelector('#shift'),pose=document.querySelector('#pose'),a=document.querySelector('#baseline'),b=document.querySelector('#candidate');
step.addEventListener('input',()=>{const n=String(step.value).padStart(2,'0');pose.textContent=step.value;a.src='../p15-86-semantic-ownership/frame-'+n+'.png';b.src='r4-'+n+'.png';});
</script></body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
print('HTML',D/'index.html')

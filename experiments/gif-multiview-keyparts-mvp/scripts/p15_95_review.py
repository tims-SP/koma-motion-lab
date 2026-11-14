#!/usr/bin/env python3
"""Create responsive P0 yaw60 underpaint/ArtMesh diagnostic for 0..12px front hair motion."""
from pathlib import Path
from PIL import Image
import json,hashlib
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports'
D=P/'p15-95-elastic-review'
qa=json.loads((R/'evidence/p15-95-elastic-qa.json').read_text())
source=P/'p15-92-angle-keyart/yaw060-registered.png'
assert source.is_file()
frames=[]
for dx in range(13):
 f=D/f'feather-2-{dx:02}.png'
 assert f.is_file(),f
 art=Image.open(f).convert('RGBA')
 bg=Image.new('RGBA',art.size,'white')
 bg.alpha_composite(art)
 frames.append(bg.convert('RGB').crop((485,290,835,670)).resize((420,456),Image.Resampling.LANCZOS))
gif=D/'underpaint-motion.gif'
frames[0].save(gif,save_all=True,append_images=frames[1:],duration=135,loop=0,optimize=False)
css="""body{font-family:system-ui,sans-serif;background:#152536;color:#edf4fa;margin:12px auto;padding:0 15px;max-width:1500px}h1{font-size:23px}h2{font-size:19px}p{color:#bdcbd7}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}figure{margin:0;padding:10px;background:#263b52;border-radius:8px}img{width:100%;height:auto;object-fit:contain;background:#fff}figcaption{font-size:12px;line-height:1.5}label{display:block;margin:10px 0}input{width:100%}.pair{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}@media(max-width:760px){.grid,.pair{grid-template-columns:1fr}}"""
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 · yaw60 hidden face underpaint diagnostic</title><style>'''+css+'''</style></head><body>
<h1>P0 · 60° 前发下的脸部底图与动态遮挡</h1>
<p>真实 Codex 生成底图经过原画配准；前发由 Hugging Face SAM3 的原始颜色与分割蒙版构成。此页面只用于评估 0–12px 位移、面部接缝和语义边缘，正式 ArtMesh 仍待视觉验收。</p>
<label for="pose">前发相对移动：<b id="step">0</b>px</label><input id="pose" min="0" max="3" value="0" step="1" type="range">
<div class="grid">
<figure><img id="source" src="../p15-92-angle-keyart/yaw060-registered.png" alt="真实独立原画"><figcaption>0px 原始身份基准，独立的 60° 原画</figcaption></figure>
<figure><img id="rigid" src="../p15-95-yaw060-motion/semantic-baseline-00.png" alt="原始刚性移动基线"><figcaption>未补绘的前发刚性位移</figcaption></figure>
<figure><img id="elastic" src="feather-2-00.png" alt="模型补绘和局部弹性变形"><figcaption>真实补绘底图 + 原画前发 + 局部弹性变形</figcaption></figure>
</div><h2>补绘来源与边界</h2><div class="pair">
<figure><img src="../p15-95-yaw060-motion/underpaint-source-contact.jpg" alt="源图、生成底图与限定蒙版"><figcaption>原画、模型生成内容与蒙版补绘对照</figcaption></figure>
<figure><img src="elastic-dynamic-contact.jpg" alt="多种羽化半径的动态比较"><figcaption>刚性/弹性变形比较与四个移动姿态</figcaption></figure>
</div><h2>底图生成方式对照</h2><figure><img src="../p15-95-inpaint-compare/inpaint-method-contact.jpg" alt="生成内容和 OpenCV 局部补绘对照"><figcaption>模型补绘、OpenCV 修补和混合底图均处于研究候选状态</figcaption></figure>
<script>
const positions=[0,4,8,12],slider=document.getElementById('pose'),label=document.getElementById('step'),rigid=document.getElementById('rigid'),elastic=document.getElementById('elastic');slider.addEventListener('input',()=>{const v=positions[Number(slider.value)],id=String(v).padStart(2,'0');label.textContent=String(v);rigid.src='../p15-95-yaw060-motion/semantic-baseline-'+id+'.png';elastic.src='feather-2-'+id+'.png';});
</script></body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
qpath=R/'evidence/p15-95-elastic-qa.json'
qa['animatedPreviewSHA256']=hashlib.sha256(gif.read_bytes()).hexdigest()
qa['htmlReview']='private-assets/exports/p15-95-elastic-review/index.html'
qa['visualGate']='FOREHEAD_TRIANGLE_SEAM_REQUIRES_SEMANTIC_UNDERDRAWING_VALIDATION'
qpath.write_text(json.dumps(qa,indent=2)+'\n')
print('HTML',D/'index.html','GIF',gif)

#!/usr/bin/env python3
"""HTML evidence for same-view masked forehead repair, with explicit visual rejection."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-68-forehead'
q=json.loads((R/'evidence/p15-68-forehead-qa.json').read_text())
tiles=[('source-face.png','原始右向原画'),('underpaint-face.png','LaMa 新补绘的额头/发根'),
('with-hair-eye-00-face.png','前发复合 · 近眼 0px'),('with-hair-eye-18-face.png','前发复合 · 近眼 18px'),
('input-512.png','神经模型原始输入'),('mask-512.png','额头遮罩'),
('model-512.png','LaMa 直接输出'),('forehead-neural-underpaint.png','强制遮罩后的整图')]
css='''body{background:#172635;color:#f0f4fb;max-width:1450px;margin:20px auto;padding:0 16px;font:15px/1.5 system-ui}h1{font-size:24px}.failure{color:#ffc59b}.pass{color:#afe6c7}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}figure,.panel{margin:0;background:#2b4054;padding:12px;border-radius:8px}img{width:100%;object-fit:contain;max-height:550px;background:repeating-conic-gradient(#ddd 0 25%,white 0 50%) 50%/24px 24px}figcaption{font-weight:600;margin-top:7px}input{width:100%}p{color:#d1dce8}'''
h='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-68 · 前发与隐藏额头验收</title><style>'+css+'</style><h1>P15-68 · 前发与隐藏额头局部重建</h1>'
h+='<p class="pass">CPU LaMa 神经生成成功：遮罩内 '+str(q['changedInsideMaskPixels'])+' 个像素发生变化，遮罩外 0 个 RGBA 像素变化。</p>'
h+='<p class="failure"><b>正式视觉门禁 FAIL：</b>前发 V2 无法作为真实独立语义层。复合图仍有发夹残影、额头补片的色调不连续与眼睛移动时的睫毛残影。局部补绘成功不等于整片前发动画已经完成。</p>'
h+='<div class="panel"><h2 id="offset">近眼位移 18px</h2><input id="shift" aria-label="近眼位移" type="range" min="0" max="18" step="9" value="18"><div class="grid"><figure><img id="whole" src="with-hair-eye-18.png" alt="全图"><figcaption>前发复合全图</figcaption></figure><figure><img id="face" src="with-hair-eye-18-face.png" alt="面部"><figcaption>放大面部</figcaption></figure></div></div><div class="grid">'
for file,title in tiles:
 assert (D/file).exists(),file
 h+=f'<figure><img src="{file}" alt="{title}"><figcaption>{title}</figcaption></figure>'
h+='</div><script>const s=document.getElementById("shift");s.addEventListener("input",()=>{let dx=String(Number(s.value)).padStart(2,"0");document.getElementById("whole").src="with-hair-eye-"+dx+".png";document.getElementById("face").src="with-hair-eye-"+dx+"-face.png";document.getElementById("offset").textContent="近眼位移 "+Number(s.value)+"px";});</script></html>'
(D/'index.html').write_text(h,encoding='utf8')

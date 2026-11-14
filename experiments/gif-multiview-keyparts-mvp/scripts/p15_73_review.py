#!/usr/bin/env python3
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-73-interactive-sam'
q=json.loads((R/'evidence/p15-73-mask-extraction-qa.json').read_text())
css='''body{font:15px/1.55 system-ui;background:#172737;color:#eff4fa;max-width:1500px;padding:0 16px;margin:16px auto}h1{font-size:25px}h2{font-size:18px}.good{color:#addcc3}.warn{color:#ffca9b}p{color:#d1dce8}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:14px}figure,.panel{margin:0;padding:12px;background:#293f54;border-radius:8px}img{width:100%;max-height:650px;object-fit:contain;background:repeating-conic-gradient(#ddd 0 25%,#fff 0 50%) 50%/24px 24px}figcaption{font-weight:600;margin-top:6px}input{width:100%}'''
h='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-73 · SAM 前发候选</title><style>'+css+'</style></head><body><h1>P15-73 · SAM 实例分割与近眼遮挡</h1>'
h+='<p class="good">真实 CPU SAM ViT-B 输出中选择独立实例，最大连通域 '+str(q['largestComponentPixels'])+' 像素，建立 '+str(q['hairLayerAlphaPixels'])+' 非透明像素的同视角前发候选。选定眼睛、脸颊及金色发夹锚点被排除。原合成 PNG 分割回组的 0px 逐像素重建无变化。</p>'
h+='<p class="warn"><b>正式 ArtMesh 仍不准入：</b>当前实例来自 SAM 自动分割后人工选择，并非真正正负点条件分割。边缘有零散像素、刘海内部混入额头线条，眼睛移动时的原画遮挡仍需局部视觉精修。利用原合成图互补分割得到的 0px 完全一致，不等于最终动画图层 0px 视觉合格；与现有前额底图和独立发夹复合时仍有局部差异。</p>'
h+='<div class="panel"><h2 id="offset">近眼移动 18px</h2><input type="range" id="shift" min="0" max="18" step="9" value="18" aria-label="近眼位移"><div class="grid"><figure><img id="whole" src="p15-73-composite-18.png" alt="完整画面"><figcaption>实际 ArtMesh 候选复合</figcaption></figure><figure><img id="face" src="p15-73-face-18.png" alt="面部放大"><figcaption>面部局部</figcaption></figure></div></div>'
tiles=[('mask-overlay.png','SAM 前发实例覆盖范围'),('front-bangs-checker.jpg','提取出的独立前发透明 PNG 棋盘格预览'),('front-bangs-rgba.png','候选 RGBA 图层'),('front-bangs-mask-largest.png','最大连通域 Alpha'),('sam-mask-1.png','SAM 自动实例原始标签'),('ui-point-mask-38-0.png','真实点提示：错误的整头掩码，不采用'),('p15-73-motion-contact.jpg','0/9/18px 三帧对照'),('p15-73-three-way-comparison.jpg','原图、候选与复合对照')]
h+='<h2>原始分割、失败分支与画质检查</h2><div class="grid">'
for f,caption in tiles:
 assert (D/f).is_file(),f
 h+=f'<figure><img src="{f}" alt="{caption}"><figcaption>{caption}</figcaption></figure>'
h+='</div><script>const s=document.querySelector("#shift");s.addEventListener("input",()=>{let n=String(+s.value).padStart(2,"0");document.querySelector("#whole").src="p15-73-composite-"+n+".png";document.querySelector("#face").src="p15-73-face-"+n+".png";document.querySelector("#offset").textContent="近眼移动 "+Number(s.value)+"px";});</script></body></html>'
(D/'index.html').write_text(h,encoding='utf8')
print('HTML',len(h))

#!/usr/bin/env python3
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-64-semantic-eye'
q=json.loads((R/'evidence/p15-64-semantic-eye-qa.json').read_text())
css='''body{max-width:1420px;margin:18px auto;padding:0 17px;background:#172636;color:#eff4fa;font:15px/1.5 system-ui}h1{font-size:24px}.warn{color:#ffca9b}.good{color:#a5e8c4}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}figure,.panel{margin:0;padding:12px;background:#2a3f54;border-radius:7px}img{width:100%;object-fit:contain;max-height:520px;background:repeating-conic-gradient(#dedede 0 25%,white 0 50%) 50%/24px 24px}figcaption{font-weight:600;margin-top:6px}p{color:#cad8e5}input{width:100%}'''
h='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-64 近眼语义遮罩改善</title><style>'+css+'</style><h1>P15-64 · 近眼语义边界与 18px 位移</h1>'
h+='<p class="good">复用已完成 LaMa 皮肤底图，不重复模型推理。近眼可见 ROI 从 11,457 像素缩减到 '+str(q['newVisibleCutoutPixels'])+' 像素；取消矩形刘海覆盖层，不再携带大块皮肤/发丝。位移后透明洞：0。</p>'
h+='<p class="warn">视觉评审：和 P15-63 相比明显改善，但放大仍有下眼睑灰色晕边和局部高光过渡问题，尚未达到正式日本动漫原画的 ArtMesh 门槛。</p>'
h+='<div class="panel"><h2 id="angle">近眼位移 18px</h2><input id="shift" aria-label="eye displacement" type="range" min="0" max="18" step="9" value="18"><div class="grid"><figure><img id="whole" src="near-eye-shift-18.png" alt="全图"><figcaption>完整透明候选</figcaption></figure><figure><img id="face" src="near-eye-shift-18-face.png" alt="放大面部"><figcaption>局部 3 倍检查</figcaption></figure></div></div>'
tiles=[('source-face.png','原始候选面部'),('previous-face.png','P15-63：旧 ROI 移动失败'),('near-eye-shift-18-face.png','P15-64：收紧边界移动 18px'),('eye.near.tight-layer.png','新独立近眼 RGBA 图层'),('eye.near.tight-mask.png','解剖外轮廓 Mask')]
h+='<div class="grid">'
for name,label in tiles:
 assert (D/name).exists()
 h+=f'<figure><img src="{name}" alt="{label}"><figcaption>{label}</figcaption></figure>'
h+='</div><script>const v=document.querySelector("#shift");v.addEventListener("input",()=>{const n=String(Number(v.value)).padStart(2,"0");document.querySelector("#whole").src="near-eye-shift-"+n+".png";document.querySelector("#face").src="near-eye-shift-"+n+"-face.png";document.querySelector("#angle").textContent="近眼位移 "+Number(v.value)+"px";});</script></html>'
(D/'index.html').write_text(h,encoding='utf8')
print('html visual tiles',len(tiles))

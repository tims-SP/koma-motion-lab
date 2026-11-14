from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-65-eyelid-refinement'
q=json.loads((R/'evidence/p15-65-eyelid-qa.json').read_text())
items=[('original-face.png','原始候选'),
('p15-64-shift18-face.png','P15-64：未修边的 18px 位移'),
('eye-shift-18-face.png','P15-65：选用下眼睑修边'),
('baseline-1p5.png','基线局部'),
('trim2-1p0.png','下眼睑收紧约 2px（选用）'),
('trim4-1p0.png','收紧约 4px（虹膜边缘削弱）'),
('trim6-1p0.png','收紧约 6px（过度裁剪）'),
('hairA-test.png','刘海覆盖 A：拼接线，不采纳'),
('hairB-test.png','刘海覆盖 B：拼接线，不采纳'),
('hairC-test.png','刘海覆盖 C：拼接线，不采纳'),
('eye.near.refined-layer.png','独立近眼 RGBA'),
('eye.near.refined-mask.png','独立近眼 Alpha')]
css='''body{font:15px/1.5 system-ui;max-width:1500px;background:#172637;color:#eff4fa;margin:18px auto;padding:0 16px}h1{font-size:24px}h2{font-size:18px}.good{color:#b3e8cb}.warn{color:#ffcc9f}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}figure,.panel{margin:0;background:#293e54;padding:12px;border-radius:7px}img{width:100%;object-fit:contain;max-height:600px;background:repeating-conic-gradient(#ddd 0 25%,#fff 0 50%) 50%/24px 24px}figcaption{margin-top:7px;font-weight:600}input{width:100%}p{color:#d3dce8}'''
s='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>P15-65 眼睑修边与刘海遮挡审查</title><style>'+css+'</style><h1>P15-65 · 近眼下眼睑修边及刘海遮挡</h1>'
s+='<p class="good">复用 P15-63 LaMa 皮肤底图，选用下眼睑收紧约 2px 的候选。眼部可见像素从 6995 降至 '+str(q['newLayerNonzeroAlphaPixels'])+'，0/9/18px 位移均无透明孔。</p>'
s+='<p class="warn">视觉准入尚未通过。虽然灰色晕边减轻，但与眼睛交叠的刘海缺少干净的独立层；三种多边形刘海覆盖均产生明显拼接线，均拒绝使用。没有修改正式 ArtMesh。</p>'
s+='<div class="panel"><h2 id="pos">眼睛位移 18px</h2><input type="range" id="shift" min="0" max="18" step="9" value="18"><div class="grid"><figure><img id="whole" src="eye-shift-18.png"><figcaption>全图</figcaption></figure><figure><img id="face" src="eye-shift-18-face.png"><figcaption>放大面部</figcaption></figure></div></div><h2>修边方案、被拒刘海及透明图层</h2><div class="grid">'
for filename,label in items:
 assert (D/filename).is_file(),filename
 s+=f'<figure><img src="{filename}" alt="{label}"><figcaption>{label}</figcaption></figure>'
s+='</div><script>const v=document.querySelector("#shift");v.addEventListener("input",()=>{const dx=String(+v.value).padStart(2,"0");document.querySelector("#whole").src="eye-shift-"+dx+".png";document.querySelector("#face").src="eye-shift-"+dx+"-face.png";document.querySelector("#pos").textContent="眼睛位移 "+Number(v.value)+"px";});</script></html>'
(D/'index.html').write_text(s,encoding='utf8')
print('html tiles',len(items))

from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-69-clip-separation'
q=json.loads((R/'evidence/p15-69-clip-qa.json').read_text())
css='''body{max-width:1480px;margin:18px auto;padding:0 17px;background:#172635;color:#f0f4fa;font:15px/1.5 system-ui}h1{font-size:24px}.good{color:#b4e8c7}.warn{color:#ffcb9c}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}figure,.panel{margin:0;background:#2b4054;padding:12px;border-radius:8px}img{width:100%;max-height:550px;object-fit:contain;background:repeating-conic-gradient(#ddd 0 25%,white 0 50%) 50%/22px 22px}figcaption{font-weight:600;margin-top:6px}p{color:#d4deea}input{width:100%}'''
images=[('old68-clip-compare.png','P15-68：发夹残影'),('new69-clip-compare.png','P15-69：发夹只绘制一次'),
('original-clip-compare.png','原始角色金色发夹'),('clip-and-eye-free-underpaint.png','删除发夹/近眼残影的底图'),
('hair-front-no-gold-candidate.png','原前发候选已去除发夹像素'),
('hair-clip-gold-independent.png','金色交叉发夹独立透明图层'),
('clip-cleanup-guard.png','发夹去重保护遮罩'),
('old68-face-compare.png','P15-68 面部失败对照'),('new69-face-compare.png','P15-69 面部新结果')]
h='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-69 发夹单层与眼部遮挡审查</title><style>'+css+'</style><h1>P15-69 · 发夹只绘制一次</h1>'
h+='<p class="good">发夹修复已通过局部视觉核查：将混入前发的黄色像素从 '+str(q['hairYellowPixelsBefore'])+' 降为 '+str(q['hairYellowPixelsAfter'])+'；独立发夹在最顶层只叠加一次，P15-68 的下方灰色 X 形残影消失。背景中的固定近眼也已替换为无遮挡皮肤。</p>'
h+='<p class="warn"><b>完整前发仍未正式通过：</b>当前前发仅是颜色筛选的透明候选，额头三角形补片及睫毛/刘海边界仍不自然。不能把发夹去重当成完整 VDD 验收。</p>'
h+='<div class="panel"><h2 id="frameLabel">眼部位移 18px</h2><input id="shift" type="range" min="0" max="18" step="9" value="18" aria-label="眼睛位移"><div class="grid"><figure><img id="whole" src="eye-shift-18-clip-once.png" alt="全图"><figcaption>全图</figcaption></figure><figure><img id="face" src="eye-shift-18-face.png" alt="面部细节"><figcaption>面部放大</figcaption></figure></div></div><div class="grid">'
for p,label in images:
 assert (D/p).exists(),p
 h+=f'<figure><img src="{p}" alt="{label}"><figcaption>{label}</figcaption></figure>'
h+='</div><script>const v=document.querySelector("#shift");v.addEventListener("input",()=>{const n=String(+v.value).padStart(2,"0");document.querySelector("#whole").src="eye-shift-"+n+"-clip-once.png";document.querySelector("#face").src="eye-shift-"+n+"-face.png";document.querySelector("#frameLabel").textContent="眼部位移 "+Number(v.value)+"px";});</script></html>'
(D/'index.html').write_text(h,encoding='utf8')

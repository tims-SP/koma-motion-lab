from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-67-front-hair'
q=json.loads((R/'evidence/p15-67-front-hair-qa.json').read_text())
css='''body{max-width:1450px;margin:16px auto;padding:0 17px;background:#172736;color:#eef3fa;font:15px/1.52 system-ui}h1{font-size:24px}h2{font-size:18px}.bad{color:#ffbf9b}p{color:#cbd8e8}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}figure,.panel{margin:0;background:#283e52;padding:12px;border-radius:8px}img{width:100%;object-fit:contain;max-height:600px;background:repeating-conic-gradient(#ddd 0 25%,#fff 0 50%) 50%/22px 22px}figcaption{font-weight:600;margin-top:6px}input{width:100%}'''
h='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-67 完整前发语义分层门禁</title><style>'+css+'</style><h1>P15-67 · 完整前发提取与动态遮挡审查</h1>'
h+='<p class="bad"><b>正式视觉门禁 FAIL：</b>当前原画只能提取外观上接近前发的可见像素，不足以形成独立可移动 ArtMesh。V1 混入眼睛，V2 排除眼睛后会剪掉真实的部分刘海；发顶左侧被粗边界截断，隐藏额头和发根也缺少补绘。</p>'
h+='<p>V1 的非透明候选像素：'+str(q['visiblePixels'])+'；V2：'+str(q['eyeExcludedNonzeroAlphaPixels'])+'。这些数字只说明提取面积，不能证明语义准确。P15-41 旧前发来自另一版本，不作当前身份的像素真值。</p>'
h+='<div class="panel"><h2 id="pose">眼睛位移 18px</h2><input id="shift" type="range" aria-label="眼睛位移" min="0" max="18" step="9" value="18"><div class="grid"><figure><img id="main" src="eye-shift-18-v2.png" alt="V2 组合"><figcaption>V2 全图</figcaption></figure><figure><img id="face" src="eye-shift-18-v2-face.png" alt="V2 面部细节"><figcaption>面部局部</figcaption></figure></div></div>'
h+='<h2>提取尝试与真实缺口</h2><div class="grid">'
tiles=[('hair.front.full-area-candidate.png','V1：混入眼部与截断发顶'),('hair.front.eye-excluded-v2.png','V2：眼部排除，但刘海遮挡亦受损'),('hair.front.full-area-mask.png','V1 Alpha 遮罩'),('hair.front.eye-excluded-mask.png','V2 Alpha 遮罩'),('remaining-visible-with-hair-hole.png','剩余可见素材：无真正隐藏额头'),('eye-shift-18-face.png','V1 18px 位移（眼睛残影）'),('eye-shift-18-v2-face.png','V2 18px 位移（失去刘海覆盖）')]
for file,title in tiles:
 assert (D/file).exists(),file
 h+=f'<figure><img src="{file}" alt="{title}"><figcaption>{title}</figcaption></figure>'
h+='</div><p>结论：需要对同一张右向原画进行真实发丝语义 Matting，独立补齐隐藏额头/发根，再做视角变形。当前两个候选均禁止进入正式 ArtMesh。</p>'
h+='<script>const s=document.querySelector("#shift");s.addEventListener("input",()=>{let n=String(Number(s.value)).padStart(2,"0");document.querySelector("#main").src="eye-shift-"+n+"-v2.png";document.querySelector("#face").src="eye-shift-"+n+"-v2-face.png";document.querySelector("#pose").textContent="眼睛位移 "+Number(s.value)+"px";});</script></html>'
(D/'index.html').write_text(h,encoding='utf8')
print('Review ready')

from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-70-seam-repair'
q=json.loads((R/'evidence/p15-70-seam-qa.json').read_text())
css='''body{background:#182839;color:#eff4fb;max-width:1450px;margin:18px auto;padding:0 16px;font:15px/1.5 system-ui}h1{font-size:24px}.good{color:#b6e9cb}.warn{color:#ffcc9c}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}.card{background:#293f54;padding:12px;border-radius:8px}figure{margin:0}img{width:100%;object-fit:contain;max-height:590px;background:repeating-conic-gradient(#ddd 0 25%,white 0 50%) 50%/24px 24px}figcaption{font-weight:600;margin-top:5px}input{width:100%}p{color:#d1dce9}'''
h='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-70 前额拼接修复</title><style>'+css+'</style></head><body><h1>P15-70 · 额头纹理接缝修复与前发门禁</h1>'
h+='<p class="good">本轮在旧 P15-55 原画参考中恢复额头上方皮肤/前发接缝，改变 '+str(q['changedRGBApixels'])+' 个像素；Mask 外变动 0。已生成 0 / 9 / 18px 眼部移动，透明洞 0。</p>'
h+='<p class="warn"><b>正式 ArtMesh 尚未通过：</b>三角形补片已经减少，但跨越额头的灰紫色线条仍被前发候选携带，睫毛和发丝边界仍然存在重影。当前颜色阈值提取不能替代完整独立前发原画。</p>'
h+='<div class="card"><h2 id="angle">眼睛位移 18px</h2><input id="shift" aria-label="眼睛位移" type="range" min="0" max="18" step="9" value="18"><div class="grid"><figure><img id="whole" src="eye-shift-18-seam-repaired.png" alt="全图"><figcaption>完整画面</figcaption></figure><figure><img id="face" src="eye-shift-18-face.png" alt="面部细节"><figcaption>面部细节放大</figcaption></figure></div></div>'
items=[('before-forehead.png','修复前：额头粉色接缝'),('after-forehead.png','修复后：参考原画融合'),('before-face.png','原 P15-69 面部'),('after-face.png','P15-70 面部'),('forehead-repair-mask.png','受控局部 Mask'),('forehead-seam-repaired.png','修复后的透明底图')]
h+='<h2>视觉前后对照及精确遮罩</h2><div class="grid">'
for file,caption in items:
 assert (D/file).is_file(),file
 h+=f'<figure class="card"><img src="{file}" alt="{caption}"><figcaption>{caption}</figcaption></figure>'
h+='</div><script>const s=document.querySelector("#shift");s.addEventListener("input",()=>{let n=String(+s.value).padStart(2,"0");document.querySelector("#whole").src="eye-shift-"+n+"-seam-repaired.png";document.querySelector("#face").src="eye-shift-"+n+"-face.png";document.querySelector("#angle").textContent="眼睛位移 "+Number(s.value)+"px";});</script></body></html>'
(D/'index.html').write_text(h,encoding='utf8')
print('HTML ready')

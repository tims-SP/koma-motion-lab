from pathlib import Path
D=Path(__file__).resolve().parents[1]/'private-assets/exports/p15-83-eye-seam'
css='''body{background:#172738;color:#edf4fb;max-width:1440px;margin:18px auto;padding:0 16px;font:15px/1.55 system-ui}h1{font-size:24px}h2{font-size:18px}p{color:#d4deeb}.pass{color:#b5e8c9}.fail{color:#ffd1a3}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}figure,.panel{background:#2b4054;padding:12px;margin:0;border-radius:8px}img{width:100%;max-height:580px;object-fit:contain;background:repeating-conic-gradient(#ddd 0 25%,#fff 0 50%) 50%/24px 24px}figcaption{font-weight:600;margin-top:6px}input{width:100%}'''
h='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-83 动态眉眼残影修复失败对照</title><style>'+css+'</style></head><body>'
h+='<h1>P15-83 · 眉睫毛与刘海交界源像素克隆验证</h1>'
h+='<p class="pass">实际使用 P15-70 隐藏额头的原像素，尝试三组局部形状，固定 28px 邻近取样，重新渲染 9/18px。已有 P15-82 四层 0px 回组不改，三组动态都无新增透明孔。</p>'
h+='<p class="fail"><b>全部视觉门禁 FAIL。</b>Slender 保留眉毛但残影仍在；Upper 明显削掉眉毛并留下肤色补片；Localized 仅改变局部，不能消除眼上方重复线条。不要把任何一组升级为正式 ArtMesh/VDD。</p>'
h+='<div class="panel"><h2 id="pose">位移 18px</h2><input id="shift" aria-label="近眼位移" type="range" min="9" max="18" step="9" value="18"><div class="grid">'
for k,t in [('slender','较窄区域：保留眉线但残影在'),('upper','过宽区域：眉毛被擦除'),('localized','局部区域：残留重复线条')]:
 h+=f'<figure><img id="{k}" src="candidate-{k}-18-detail.png" alt="{t}"><figcaption>{t}</figcaption></figure>'
h+='</div></div><h2>18px 实际对照</h2><div class="grid">'
for f,t in [('baseline.png','P15-82 原有残影'),('candidate-slender-18-detail.png','Slender · 与原帧不同 1,794 像素'),('candidate-upper-18-detail.png','Upper · 与原帧不同 2,900 像素'),('candidate-localized-18-detail.png','Localized · 与原帧不同 1,608 像素'),('mask-slender.png','Slender 羽化 Mask'),('mask-upper.png','Upper 羽化 Mask'),('mask-localized.png','Localized 羽化 Mask')]:
 assert (D/f).is_file(),f
 h+=f'<figure><img src="{f}" alt="{t}"><figcaption>{t}</figcaption></figure>'
h+='</div><script>let s=document.getElementById("shift");s.addEventListener("input",()=>{let n=String(+s.value).padStart(2,"0");for(let k of ["slender","upper","localized"])document.getElementById(k).src="candidate-"+k+"-"+n+"-detail.png";document.getElementById("pose").textContent="位移 "+Number(s.value)+"px";});</script></body></html>'
(D/'index.html').write_text(h,encoding='utf8')
print('P15-83 HTML ready')

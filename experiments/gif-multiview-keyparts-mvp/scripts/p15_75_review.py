from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-75-eyebrow-seam'
css='''body{background:#172738;color:#edf4fa;max-width:1440px;margin:16px auto;padding:0 16px;font:15px/1.5 system-ui}h1{font-size:24px}.good{color:#b1e3c7}.warn{color:#ffd09d}p{color:#d2deeb}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:14px}figure,.panel{margin:0;background:#293f53;padding:12px;border-radius:8px}img{width:100%;max-height:580px;object-fit:contain;background:repeating-conic-gradient(#ddd 0 25%,#fff 0 50%) 50%/24px 24px}figcaption{font-weight:600;margin-top:7px}input{width:100%}'''
h='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-75 前发与眉睫毛局部遮挡审核</title><style>'+css+'</style></head><body><h1>P15-75 · 前发与眉睫毛局部遮挡诊断</h1>'
h+='<p class="good"><b>0px 门禁保持通过：</b>未更改角色原画、金色发夹与已验收额头底图；0px 全 RGBA 与 P15-56 原稿逐像素相同。0/9/18px 均无透明破洞。</p>'
h+='<p class="warn"><b>正式视觉门禁未通过：</b>以动态遮罩降低前发中误含的近眼色块，使 18px 左眼角色块变小；但仍能看到眉毛上方虚线和发丝/睫毛接缝，且遮罩并非真正独立原画。纯肤色修补出现明显色块，已拒绝。</p>'
h+='<div class="panel"><h2 id="angle">近眼位移 18px</h2><input id="shift" type="range" min="0" max="18" step="9" value="18" aria-label="眼睛位移"><div class="grid"><figure><img id="whole" src="eye-shift-18.png"><figcaption>全图</figcaption></figure><figure><img id="face" src="eye-shift-18-face.png"><figcaption>局部面部</figcaption></figure><figure><img id="detail" src="eye-shift-18-detail.png"><figcaption>眉毛与睫毛交界</figcaption></figure></div></div>'
items=[('p15-74-before-detail.png','P15-74：移动眼角色块与虚线'),('eye-shift-18-detail.png','P15-75：局部色块减轻，虚线残留'),('delta-18-detail.png','18px 实际变化像素'),('dynamic-suppression-guard.png','局部遮挡抑制 Mask'),('combined-detail.png','对照：完整局部抑制'),('retouch2-detail.png','拒绝：纯肤色修补产生假色块'),('hair-diagnostic.png','原 SAM 前发图层：夹带眼部污染'),('base-diagnostic.png','旧底图：有细线残留')]
h+='<h2>缺陷来源与被拒方案</h2><div class="grid">'
for f,label in items:
 assert (D/f).exists(),f
 h+=f'<figure><img src="{f}" alt="{label}"><figcaption>{label}</figcaption></figure>'
h+='</div><script>const x=document.getElementById("shift");x.addEventListener("input",()=>{let n=String(+x.value).padStart(2,"0");document.querySelector("#whole").src="eye-shift-"+n+".png";document.querySelector("#face").src="eye-shift-"+n+"-face.png";document.querySelector("#detail").src="eye-shift-"+n+"-detail.png";document.querySelector("#angle").textContent="近眼位移 "+Number(x.value)+"px";});</script></body></html>'
(D/'index.html').write_text(h,encoding='utf8')
print('html ready')

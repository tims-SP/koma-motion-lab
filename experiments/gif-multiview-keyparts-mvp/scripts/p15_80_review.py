from pathlib import Path
D=Path(__file__).resolve().parents[1]/'private-assets/exports/p15-80-front-hair'
css='''body{max-width:1460px;margin:18px auto;padding:0 18px;background:#172738;color:#edf5fa;font:15px/1.55 system-ui}h1{font-size:24px}h2{font-size:18px}p{color:#d4dfeb}.warn{color:#ffcf9a}.pass{color:#b1e7c9}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}figure,.panel{background:#293f53;padding:12px;border-radius:8px;margin:0}img{width:100%;max-height:580px;object-fit:contain;background:repeating-conic-gradient(#ddd 0 25%,white 0 50%) 50%/24px 24px}figcaption{margin-top:6px;font-weight:600}input{width:100%}'''
h='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-80 刘海语义失败验收</title><style>'+css+'</style></head><body>'
h+='<h1>P15-80 · 刘海 Alpha 修复方案实测</h1><p class="pass">已实际对同视角 SAM 前发候选进行三个受限区域形态学实验，并渲染独立 0/9/18px 动态对照。0px 原图一致，动态无新增透明洞。</p>'
h+='<p class="warn"><b>正式视觉门禁 FAIL：</b>问题不是孤立噪点，SAM Mask 已把眉毛和皮肤当作刘海的一部分。Median/Opening/Closing 都不能生成真正的发丝层。所有变体已拒绝正式 ArtMesh/VDD 准入。</p>'
h+='<div class="panel"><h2 id="move">Median 诊断候选位移 18px</h2><input id="shift" type="range" min="0" max="18" step="9" value="18" aria-label="近眼移动"><div class="grid"><figure><img id="motion" src="candidate-median3-18.png"><figcaption>仅作诊断的 1024px 动画复合</figcaption></figure><figure><img id="detail" src="candidate-median3-18-detail.png"><figcaption>眉弓与外眼角放大</figcaption></figure></div></div>'
h+='<h2>三个真实 Mask 实验的失败对照</h2><div class="grid">'
for f,title in [('baseline-18-detail.png','基线 P15-76：错误刘海细纹'),('median3-18-detail.png','Median3：改变 375 像素，未消除污染'),('opening3-18-detail.png','Opening3：改变 735 像素，削掉细发丝'),('closing3-18-detail.png','Closing3：改变 586 像素，扩大错误覆盖'),('brow-hair-alpha.png','原始刘海 Mask：网格状漏选'),('brow-hair-rgba.png','SAM 候选含眉毛/肤色像素')]:
 assert (D/f).is_file(),f
 h+=f'<figure><img src="{f}" alt="{title}"><figcaption>{title}</figcaption></figure>'
h+='</div><script>const s=document.getElementById("shift");s.addEventListener("input",()=>{const n=String(+s.value).padStart(2,"0");document.getElementById("motion").src="candidate-median3-"+n+".png";document.getElementById("detail").src="candidate-median3-"+n+"-detail.png";document.getElementById("move").textContent="Median 诊断候选位移 "+Number(s.value)+"px";});</script></body></html>'
(D/'index.html').write_text(h,encoding='utf8')

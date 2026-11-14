from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-79-brow-split'
css='''body{background:#172737;color:#eff5fa;max-width:1440px;margin:18px auto;padding:0 16px;font:15px/1.5 system-ui}h1{font-size:24px}p{color:#d1deeb}.good{color:#b8e7cc}.warn{color:#ffd09d}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:14px}figure,.panel{margin:0;background:#293f53;padding:12px;border-radius:8px}img{width:100%;max-height:590px;object-fit:contain;background:repeating-conic-gradient(#ddd 0 25%,white 0 50%) 50%/24px 24px}figcaption{font-weight:600;margin-top:6px}input{width:100%}'''
s='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-79 同源眉毛分层验收</title><style>'+css+'</style></head><body><h1>P15-79 · 同视角眉毛像素独立分层</h1>'
s+='<p class="good">从 P15-70 原始同视角额头底图中提取眉弓像素，拆为独立 RGBA 眉毛和互补额头层。两层重组后与原始底图逐像素完全一致。9/18px 动态复合与既有 P15-75 帧逐像素一致。</p>'
s+='<p class="warn"><b>正式视觉门禁仍未通过：</b>提取证明眉毛可单独寻址，但刘海仍有碎片化/虚线状 Alpha 边缘；当前没有完成真正的刘海语义 Matte。没有将该候选晋升为正式 ArtMesh/VDD。</p>'
s+='<div class="panel"><h2 id="pose">眼睛位移 18px</h2><input id="shift" type="range" min="0" max="18" step="9" value="18" aria-label="眼睛位移"><div class="grid"><figure><img id="whole" src="frame-18.png"><figcaption>实际 1024px 全画面</figcaption></figure><figure><img id="detail" src="frame-18-detail.png"><figcaption>眉弓与刘海遮挡局部</figcaption></figure></div></div><h2>独立眉毛和额头底图</h2><div class="grid">'
for f,label in [('eyebrow-detail.png','从现有原画提取的眉毛透明层'),('forehead-without-brow-detail.png','去除眉毛后的互补额头底图'),('eyebrow-mask.png','眉毛像素选择 Mask'),('forehead.reconstructed.png','两层重组后的原始底图')]:
 s+=f'<figure><img src="{f}"><figcaption>{label}</figcaption></figure>'
s+='</div><script>let s=document.getElementById("shift");s.addEventListener("input",()=>{let n=String(+s.value).padStart(2,"0");document.getElementById("whole").src="frame-"+n+".png";document.getElementById("detail").src="frame-"+n+"-detail.png";document.getElementById("pose").textContent="眼睛位移 "+Number(s.value)+"px";});</script></body></html>'
(D/'index.html').write_text(s,encoding='utf8')

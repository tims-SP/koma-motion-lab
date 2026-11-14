from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-78-soft-lash'
css='''body{background:#172737;color:#eff5fa;max-width:1440px;margin:18px auto;padding:0 16px;font:15px/1.5 system-ui}h1{font-size:24px}p{color:#d1deeb}.good{color:#b8e7cc}.warn{color:#ffd09d}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:14px}figure,.panel{margin:0;background:#293f53;padding:12px;border-radius:8px}img{width:100%;max-height:590px;object-fit:contain;background:repeating-conic-gradient(#ddd 0 25%,white 0 50%) 50%/24px 24px}figcaption{font-weight:600;margin-top:6px}input{width:100%}'''
s='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-78 睫毛软边分层验收</title><style>'+css+'</style></head><body><h1>P15-78 · 上睫毛切缘软边修整</h1>'
s+='<p class="good">采用 1px Gaussian feather 和互补 Alpha 求解，拆分层重新合成与原近眼 RGBA 逐像素完全一致。0px 完整画面与 P15-56 原画 SHA 相同。</p>'
s+='<p class="warn"><b>正式视觉门禁仍未通过：</b>9/18px 的睫毛切缘锯齿明显减少，但额头眉线与刘海交界的灰色细线仍残留；当前只修整睫毛子层，不代表眉毛或前发语义图层已完成。</p>'
s+='<div class="panel"><h2 id="pose">眼睛位移 18px</h2><input id="shift" type="range" min="0" max="18" step="9" value="18" aria-label="眼睛位移"><div class="grid"><figure><img id="whole" src="frame-18.png"><figcaption>实际 1024px 全画面</figcaption></figure><figure><img id="detail" src="frame-18-detail.png"><figcaption>眉毛、刘海与睫毛局部</figcaption></figure></div></div><h2>同源睫毛分层</h2><div class="grid">'
for f,label in [('eye.upper-lash.soft.png','1px 羽化后的独立上睫毛'),('eye.lower-eye.soft.png','互补的虹膜/下眼层'),('lash-soft-mask.png','软边选择 Mask')]:
 s+=f'<figure><img src="{f}"><figcaption>{label}</figcaption></figure>'
s+='</div><script>let s=document.getElementById("shift");s.addEventListener("input",()=>{let n=String(+s.value).padStart(2,"0");document.getElementById("whole").src="frame-"+n+".png";document.getElementById("detail").src="frame-"+n+"-detail.png";document.getElementById("pose").textContent="眼睛位移 "+Number(s.value)+"px";});</script></body></html>'
(D/'index.html').write_text(s,encoding='utf8')

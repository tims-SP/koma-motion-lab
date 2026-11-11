from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-77-art-layer'
tiles=[
('source.png','当前 P15-56 身份原画'),('current-eye-source.png','当前 P15-65 近眼原图'),
('lash-close.png','新上睫毛独立层'),('iris-close.png','新虹膜与下眼层'),
('lash45-offset-55-8.png','拒绝：旧 45° 睫毛叠加'),('brow45-offset-55-8.png','拒绝：旧 45° 眉毛叠加'),
('lashFront-offset-55-8.png','拒绝：旧正面睫毛错位')]
css='''body{background:#172737;color:#ecf4fa;max-width:1460px;margin:20px auto;padding:0 16px;font:15px/1.5 system-ui}h1{font-size:24px}p{color:#d1deeb}.good{color:#b6e8cc}.warn{color:#ffd09d}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:14px}figure,.panel{margin:0;background:#293f54;padding:12px;border-radius:8px}img{width:100%;max-height:600px;object-fit:contain;background:repeating-conic-gradient(#ddd 0 25%,white 0 50%) 50%/24px 24px}figcaption{font-weight:600;margin-top:6px}input{width:100%}'''
s='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-77 同视角上睫毛独立分层</title><style>'+css+'</style></head><body><h1>P15-77 · 同源上睫毛图层与动态遮挡测试</h1>'
s+='<p class="good">新图层来自当前 P15-65 原画，拆分后重新合成与原独立近眼 RGBA 逐像素完全一致。真实动画 0px 仍保持 P15-56 原画逐像素一致。0/9/18px 分别测试了睫毛放在前发前方的层级。</p>'
s+='<p class="warn"><b>正式视觉门禁 FAIL：</b>这是按几何区域对原画的真实像素分层，不是人工修整后的发丝级描线。上睫毛切缘有锯齿，18px 眼尾仍存在细小残影。早期其他视角的眉睫毛不能直接复用。</p>'
s+='<div class="panel"><h2 id="offset">眼睛位移 18px</h2><input id="shift" type="range" aria-label="近眼位移" min="0" max="18" step="9" value="18"><div class="grid"><figure><img id="whole" src="depth-lash-18.png" alt="完整动作帧"><figcaption>新层级实际复合画面</figcaption></figure><figure><img id="face" src="depth-lash-18-detail.png" alt="眼部放大"><figcaption>眼缘和刘海细节</figcaption></figure></div></div><h2>同源原画和不匹配的旧素材</h2><div class="grid">'
for f,label in tiles:
 assert (D/f).exists(),f
 s+=f'<figure><img src="{f}" alt="{label}"><figcaption>{label}</figcaption></figure>'
s+='</div><script>let s=document.getElementById("shift");s.addEventListener("input",()=>{let n=String(Number(s.value)).padStart(2,"0");document.getElementById("whole").src="depth-lash-"+n+".png";document.getElementById("face").src="depth-lash-"+n+"-detail.png";document.getElementById("offset").textContent="眼睛位移 "+Number(s.value)+"px";});</script></body></html>'
(D/'index.html').write_text(s,encoding='utf8')
print('HTML_READY')

from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-76-seam-source'
tiles=[('before-detail.png','P15-75：未修复的隐藏眼角灰色斜线'),('after-detail.png','P15-76：取样真实皮肤后的 18px 结果'),
('hidden-skin-local-guard.png','局部修复范围和羽化'),('hidden-skin-clean-candidate.png','独立修复底图：候选'),
('clone-b-roi.png','拒绝：采样位置 B 的重复边缘'),('clone-c-roi.png','拒绝：采样位置 C 的不自然发丝复写'),
('clone-d-roi.png','拒绝：采样位置 D 消除了真实鬓角发丝'),('clone-e-roi.png','拒绝：采样位置 E 的过度平滑')]
css='''body{margin:16px auto;max-width:1450px;padding:0 16px;background:#172738;color:#eff4fa;font:15px/1.55 system-ui}h1{font-size:24px}.good{color:#b4e5c9}.warn{color:#ffd09d}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}figure,.panel{background:#293f53;padding:12px;border-radius:8px;margin:0}img{width:100%;max-height:590px;object-fit:contain;background:repeating-conic-gradient(#ddd 0 25%,#fff 0 50%) 50%/24px 24px}figcaption{font-weight:600;margin-top:6px}p{color:#d2deec}input{width:100%}'''
h='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-76 局部隐藏皮肤源像素修复</title><style>'+css+'</style></head><body><h1>P15-76 · 眉睫毛与刘海交界的隐藏皮肤修复</h1>'
h+='<p class="good"><b>0px 原画保真 PASS：</b>真实动画合成仍与 P15-56 原画逐像素完全一致；0/9/18px 均无透明孔。18px 画面中隐藏底图上的灰色斜线减弱。</p>'
h+='<p class="warn"><b>正式 ArtMesh 视觉门禁 FAIL：</b>本轮修复是从已知底图复制相邻皮肤纹理，并非全新眉毛、睫毛、前发独立语义绘画。额头纹理与局部发丝接缝仍残留，不能晋升正式 VDD。</p>'
h+='<div class="panel"><h2 id="pose">眼部位移 18px</h2><input id="shift" type="range" min="0" max="18" step="9" value="18" aria-label="近眼位移"><div class="grid"><figure><img id="whole" src="eye-shift-18.png" alt="全图"><figcaption>实际复合全图</figcaption></figure><figure><img id="face" src="eye-shift-18-face.png" alt="面部放大"><figcaption>面部局部</figcaption></figure><figure><img id="detail" src="eye-shift-18-detail.png" alt="近眼细节"><figcaption>眉毛/睫毛/前发细节</figcaption></figure></div></div><h2>源像素复绘方案及拒绝候选</h2><div class="grid">'
for file,label in tiles:
 assert (D/file).is_file(),file
 h+=f'<figure><img src="{file}" alt="{label}"><figcaption>{label}</figcaption></figure>'
h+='</div><script>const v=document.querySelector("#shift");v.addEventListener("input",()=>{const dx=String(+v.value).padStart(2,"0");document.querySelector("#whole").src="eye-shift-"+dx+".png";document.querySelector("#face").src="eye-shift-"+dx+"-face.png";document.querySelector("#detail").src="eye-shift-"+dx+"-detail.png";document.querySelector("#pose").textContent="眼部位移 "+Number(v.value)+"px";});</script></body></html>'
(D/'index.html').write_text(h,encoding='utf8')
print('P15-76 HTML ready')

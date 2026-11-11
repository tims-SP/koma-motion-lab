from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-82-rest-underpaint'
qa=json.loads((R/'evidence/p15-82-source-decomposition-qa.json').read_text())
css='''body{max-width:1480px;margin:16px auto;padding:0 16px;background:#172839;color:#f0f6fa;font:15px/1.5 system-ui}h1{font-size:24px}h2{font-size:18px}p{color:#d4dfeb}.ok{color:#b5e8ce}.bad{color:#ffcca0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:14px}figure,.panel{background:#283e51;padding:12px;margin:0;border-radius:9px}img{width:100%;max-height:580px;object-fit:contain;background:repeating-conic-gradient(#ddd 0 25%,#fff 0 50%) 50%/24px 24px}figcaption{font-weight:600;margin-top:8px}input{width:100%}code{background:#101b28;padding:3px 5px}'''
h='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-82 真实独立图层与隐藏底图验收</title><style>'+css+'</style></head><body><h1>P15-82 · SAM3 刘海、近眼和隐藏底图重组</h1>'
h+='<p class="ok"><b>可见 0px 画面：完全相同。</b>实际从四张独立 RGBA 文件重组，没有直接把 P15-56 源图作为最终帧。角色 0px 的所有可见 RGBA 像素与 P15-56 完全一致。</p>'
h+='<p class="bad"><b>原始 PNG 字节级验收：未通过。</b>原图 19,603 个 Alpha=0 但 RGB 非零的像素在标准 alpha_composite 中归零，不影响显示，但不能宣称全部 RGBA 字节一致。</p>'
h+='<p class="bad"><b>正式动态画质：FAIL。</b>9px/18px 没有新增眼部透明洞，使用 P15-70 的真实隐藏额头底图和 P15-74 原眼层比直接移动源像素眼图更干净，但眉眼边缘和刘海依旧有细残影。正式 ArtMesh/VDD 不予批准。</p>'
h+='<div class="panel"><h2 id="pose">眼睛位移：18px</h2><input type="range" id="shift" min="0" max="18" step="9" value="18" aria-label="近眼位移"><div class="grid"><figure><img id="full" src="candidate-18.png" alt="完整画面"><figcaption>真实动画合成 1024×1024</figcaption></figure><figure><img id="face" src="candidate-18-face.png" alt="面部"><figcaption>面部和金色发夹</figcaption></figure><figure><img id="eye" src="candidate-18-detail.png" alt="眼睫毛和刘海细节"><figcaption>近眼放大</figcaption></figure></div></div>'
h+='<h2>独立原画图层与失败对照</h2><div class="grid">'
items=[
 ('part.source-face.png','同源脸部/额头层（移除眼与刘海所有权）'),
 ('part.source-eye.png','同源近眼所有权图层'),
 ('part.source-bangs.png','SAM3 0.27 前发 RGBA'),
 ('part.source-clip.png','同源金色交叉发夹层'),
 ('underpaint.clean-eye-region.png','眼睛被遮挡处的已知皮肤底图'),
 ('actual-rest-by-independent-parts.png','四个独立文件合成的 0px 画面'),
 ('diagnose-diff-mask.png','P15-81 零姿态不一致差异'),
 ('frame-18-face.png','被拒方案：移动源像素眼睛，露出白边'),
 ('variant-native-eye-ownbase-18-face.png','方案对照：原有近眼与源像素底图'),
 ('variant-native-eye-brow-18-face.png','方案对照：增加原眉毛层造成残影'),
 ('candidate-18-face.png','最终候选：历史额头底图和独立眼层')]
for f,label in items:
 assert (D/f).is_file(),f
 h+=f'<figure><img src="{f}" alt="{label}"><figcaption>{label}</figcaption></figure>'
h+='</div><script>const s=document.getElementById("shift");s.addEventListener("input",()=>{const n=String(+s.value).padStart(2,"0");for(const [id,end] of [["full",""],["face","-face"],["eye","-detail"]])document.getElementById(id).src="candidate-"+n+end+".png";document.getElementById("pose").textContent="眼睛位移："+Number(s.value)+"px";});</script></body></html>'
(D/'index.html').write_text(h,encoding='utf-8')
print('REVIEW_READY')

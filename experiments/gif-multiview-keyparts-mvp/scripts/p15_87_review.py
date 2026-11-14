from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-87-hair-face-seam'
for n in (9,18):
 im=Image.open(P/f'p15-86-semantic-ownership/frame-reassigned-{n:02d}.png').convert('RGBA')
 im.crop((500,420,565,485)).resize((650,650),Image.Resampling.NEAREST).save(D/f'baseline-{n:02d}-detail.png')
css='''body{background:#172739;color:#f1f6fa;max-width:1460px;margin:18px auto;padding:0 16px;font:15px/1.5 system-ui}h1{font-size:24px}h2{font-size:18px}.good{color:#b6ebca}.bad{color:#ffd09d}p{color:#d7e1ec}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}figure,.panel{margin:0;padding:12px;background:#2a4053;border-radius:8px}img{width:100%;max-height:590px;object-fit:contain;background:repeating-conic-gradient(#ddd 0 25%,#fff 0 50%) 50%/24px 24px}figcaption{margin-top:6px;font-weight:600}input{width:100%}'''
h='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-87 前发侧缘真实连续性验收</title><style>'+css+'</style></head><body><h1>P15-87 · 同视角隐藏前发和脸部边缘质量门禁</h1>'
h+='<p class="good">P15-86 睫毛语义所有权保持不变，0px 从原始独立图层重组的可见像素和 Alpha 仍精确一致。未运行新模型、未修改正式 ArtMesh。</p>'
h+='<p class="bad"><b>正式视觉门禁 FAIL：</b>实际检查 P15-70 同视角隐藏素材时发现其在当前可动眼睛边界旁保留了深色发丝轮廓。仅用该素材替换 P15-86 的边缘遮罩，不能恢复正确的隐蔽发丝几何。三种多边形 × 两种羽化宽度均仍出现黑色断裂或平直补片。</p>'
h+='<div class="panel"><h2 id="pose">动态位移 9px</h2><input id="shift" type="range" min="9" max="18" step="9" value="9" aria-label="眼睛位移"><div class="grid">'
h+='<figure><img id="baseline" src="baseline-09-detail.png" alt="P15-86 基线"><figcaption>保留的 P15-86 基线</figcaption></figure>'
keys=['canonical-left-blur07','canonical-left-blur17','wide-left-blur07','wide-left-blur17','edge-taper-blur07','edge-taper-blur17']
for i,k in enumerate(keys):
 f=f'{k}-09-detail.png';assert (D/f).is_file(),f
 h+=f'<figure><img id="v{i}" src="{f}" alt="{k}"><figcaption>{k}</figcaption></figure>'
h+='</div></div><h2>源图结构与遮挡 Mask</h2><div class="grid">'
for f,label in [('diagnostic-source.png','原始角色睫毛与头发'),('diagnostic-under.png','P15-86 的眼后隐藏图层'),('diagnostic-hair.png','独立前发候选（含待修正边界）')]:
 assert (D/f).is_file(),f
 h+=f'<figure><img src="{f}" alt="{label}"><figcaption>{label}</figcaption></figure>'
h+='</div><script>document.getElementById("shift").addEventListener("input",e=>{let n=String(+e.target.value).padStart(2,"0");document.getElementById("baseline").src="baseline-"+n+"-detail.png";'+''.join('document.getElementById("v'+str(i)+'").src="'+k+'-"+n+"-detail.png";' for i,k in enumerate(keys))+'document.getElementById("pose").textContent="动态位移 "+Number(e.target.value)+"px";});</script></body></html>'
(D/'index.html').write_text(h,encoding='utf8')
print('html',len(keys)+4)

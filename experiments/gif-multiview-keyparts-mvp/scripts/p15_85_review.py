from pathlib import Path
D=Path(__file__).resolve().parents[1]/'private-assets/exports/p15-85-outer-eye-seam'
css='''body{background:#172738;color:#eef4fb;max-width:1420px;margin:18px auto;padding:0 16px;font:15px/1.55 system-ui}h1{font-size:24px}h2{font-size:18px}p{color:#d1dfeb}.ok{color:#b6e4c8}.bad{color:#ffcb9e}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(265px,1fr));gap:14px}figure,.panel{margin:0;background:#2c4155;padding:12px;border-radius:8px}img{width:100%;max-height:590px;object-fit:contain;background:repeating-conic-gradient(#ddd 0 25%,white 0 50%) 50%/24px 24px}figcaption{font-weight:600;margin-top:6px}input{width:100%}'''
h='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-85 眼缘细线来源和修复失败验收</title><style>'+css+'</style></head><body>'
h+='<h1>P15-85 · 外眼角残线溯源与真实 LaMa 修复试验</h1>'
h+='<p class="ok"><b>来源已定位：</b>在不叠加任何眼睛与 SAM3 刘海时，P15-84 隐藏底图已含原始眼睫毛的固定暗线。独立近眼 Alpha 与 SAM3 刘海 Mask 在该处交叉，造成原来的修复遮罩错误排除局部睫毛。</p>'
h+='<p class="bad"><b>正式视觉门禁 FAIL：</b>针对原眼睫毛误归属的 198 像素区域，真实 LaMa 推理返回一张 512×512 图，替换了 196 像素，遮罩外 0 变化。但深色残线未消除，局部深色像素反而增加。此结果仅保留为诊断证据，绝不替换 P15-84 正式候选。</p>'
h+='<p class="bad"><b>对比统计：</b>9/18px 与 P15-84 帧相比，全 RGBA 差异各 19,634 像素，其中 19,603 是透明 RGB 的合成归零，真正可见的差异仅 31 个像素。不可把 19,634 解释为画质改善。</p>'
h+='<div class="panel"><h2 id="shift-title">位移 9px：模型试验与 P15-84 原候选</h2><input type="range" id="shift" aria-label="近眼位移" min="9" max="18" value="9" step="9"><div class="grid"><figure><img id="trial" src="frame-09-detail.png"><figcaption>新 LaMa 试验 · 未批准</figcaption></figure><figure><img id="ref" src="previous-09-detail.png"><figcaption>P15-84 参考基线 · 保留</figcaption></figure></div></div>'
h+='<h2>来源分层与原始模型证据</h2><div class="grid">'
tiles=[('under_only-roi.png','无眼睛、无前发：固定细线已存在'),('eye_moved-roi.png','独立近眼（9px），非固定细线来源'),('under_hair-roi.png','仅前发与底图：细线仍在'),('original-line.png','原图局部：睫毛与前发交叠'),('underpaint-line.png','P15-84 底图残留的原始眼睫毛'),('hairmask-line.png','SAM3 前发 Mask 错误覆盖的区域'),('inpaintmask-line.png','P15-84 原修复 Mask 排除区域'),('residual-mask-preview.png','本轮仅 198px 的修复区域'),('model-512.png','真实 LaMa 返回结果'),('revised-underpaint-detail.png','试验后底图：残线变深'),('frame-18-detail.png','18px 动态试验')]
for f,t in tiles:
 assert (D/f).is_file(),f
 h+=f'<figure><img src="{f}" alt="{t}"><figcaption>{t}</figcaption></figure>'
h+='</div><script>document.getElementById("shift").addEventListener("input",e=>{const n=String(+e.target.value).padStart(2,"0");document.getElementById("trial").src="frame-"+n+"-detail.png";document.getElementById("ref").src="previous-"+n+"-detail.png";document.getElementById("shift-title").textContent="位移 "+Number(e.target.value)+"px：模型试验与 P15-84 原候选";});</script></body></html>'
(D/'index.html').write_text(h,encoding='utf8')
print('P15-85 HTML ready')

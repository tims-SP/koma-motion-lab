from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-81-image-layered'
q=json.loads((R/'evidence/p15-81-sam3-qa.json').read_text())
css='''body{max-width:1500px;margin:18px auto;padding:0 18px;background:#162636;color:#f1f6fb;font:15px/1.5 system-ui}h1{font-size:24px}h2{font-size:18px}.good{color:#a7e5c6}.warn{color:#ffce9e}p{color:#d1dfeb}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(265px,1fr));gap:14px}figure,.panel{margin:0;padding:12px;background:#2a4054;border-radius:8px}img{width:100%;max-height:590px;object-fit:contain;background:repeating-conic-gradient(#ddd 0 25%,white 0 50%) 50%/22px 22px}figcaption{font-weight:600;margin-top:7px}input{width:100%}table{border-collapse:collapse;width:100%}td,th{padding:8px;text-align:left;border-bottom:1px solid #486175}'''
h='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-81 真实 SAM3 前发分层候选验收</title><style>'+css+'</style></head><body>'
h+='<h1>P15-81 · 同视角 SAM3 真实前发语义候选</h1>'
h+='<p class="good">SAM3 以当前 P15-56 原画为输入，通过已连接 Hugging Face 账户真实返回两张 Mask。低置信结果定位到前侧刘海，眼球/脸颊/金色发夹测试点未被选中；模型分割不是手工多边形或颜色阈值。</p>'
h+='<p class="warn"><b>正式 ArtMesh 门禁 FAIL：</b>将新候选直接叠加到现有眼睛、隐藏底图和发夹时，0px 与 P15-56 仍有 8,409 个变化像素；在 9/18px 移动时原有隐藏眼缘/眉弓仍有残影。SAM3 只提供可用的分割候选，没有生成匹配的隐藏额头纹理。</p>'
h+='<p>官方 Qwen-Image-Layered 接收上传，但服务端运行返回错误，没有生成 RGBA 图层。SAM3 匿名调用遇到 ZeroGPU 额度，切换已连接账户后成功产出实际模型 Mask。</p>'
h+='<table><thead><tr><th>模型掩码</th><th>源像素区域</th><th>0px 变化</th><th>正式准入</th></tr></thead><tbody>'
for name,desc in [('027','前刘海局部'),('083','整头大范围')]:
 info=q['masks'][name]
 h+=f'<tr><td>{name} · {desc}</td><td>{info["alignedAlphaPixels"]:,} 非透明像素</td><td>{info["actualRestPoseChangedPixels"]:,}</td><td>未通过</td></tr>'
h+='</tbody></table>'
h+='<div class="panel"><h2 id="pose">Mask 0.27 · 位移 18px</h2><input id="shift" type="range" min="0" max="18" value="18" step="9" aria-label="近眼位移"><div class="grid"><figure><img id="whole" src="sam3-027-motion-18.png" alt="动态完整合成"><figcaption>新分层尝试：实际复合</figcaption></figure><figure><img id="face" src="sam3-027-motion-18-face.png" alt="脸部放大"><figcaption>眼睫毛、眉弓与刘海局部</figcaption></figure></div></div>'
items=[('sam3-027-overlay.png','SAM3 低阈值真实刘海范围'),('sam3-mask-027.png','原始前发分割 Mask，约 0.27'),('sam3-027-hair-rgba.png','同源像素独立刘海候选 RGBA'),('sam3-027-rest-face.png','实际 0px：不满足原画重组'),('sam3-083-overlay.png','SAM3 较宽 Mask 覆盖整头'),('sam3-mask-083.png','第二个原始模型 Mask，约 0.83'),('previous-sam-alpha-preview.png','P15-74 原 SAM 前发：网格漏选'),('previous-p15-76-18-face.png','旧系统 18px 对照'),('input-head-640.png','本次模型实际输入角色头部')]
h+='<h2>真实模型输出、源图、遮挡对照</h2><div class="grid">'
for f,label in items:
 assert (D/f).exists(),f
 h+=f'<figure><img src="{f}" alt="{label}"><figcaption>{label}</figcaption></figure>'
h+='</div>'
h+='<script>const s=document.querySelector("#shift");s.addEventListener("input",()=>{let n=String(Number(s.value)).padStart(2,"0");document.querySelector("#whole").src=n==="00"?"sam3-027-rest-composite.png":"sam3-027-motion-"+n+".png";document.querySelector("#face").src=n==="00"?"sam3-027-rest-face.png":"sam3-027-motion-"+n+"-face.png";document.querySelector("#pose").textContent="Mask 0.27 · 位移 "+Number(s.value)+"px";});</script></body></html>'
(D/'index.html').write_text(h,encoding='utf8')
print('HTML ready')

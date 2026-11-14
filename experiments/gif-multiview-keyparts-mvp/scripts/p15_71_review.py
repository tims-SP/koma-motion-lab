from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-71-sam-semantic'
q=json.loads((R/'evidence/p15-71-source-gate-qa.json').read_text())
css='''body{max-width:1450px;margin:18px auto;padding:0 16px;background:#172638;color:#eff3f9;font:15px/1.5 system-ui}h1{font-size:24px}h2{font-size:18px}.warning{color:#ffbf93}.good{color:#b5e4cd}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}figure,.panel{margin:0;background:#293f53;padding:12px;border-radius:8px}img{width:100%;object-fit:contain;max-height:600px;background:repeating-conic-gradient(#dce0e3 0 25%,#fff 0 50%) 50%/24px 24px}figcaption{font-weight:600;margin-top:5px}input{width:100%}p{color:#d3dfed}'''
s='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-71 前发语义资产准入核查</title><style>'+css+'</style><h1>P15-71 · 前发语义分层真值审查</h1>'
s+='<p class="warning"><b>正式门禁 FAIL：</b>旧 45° / 90° 前发虽然是独立透明 PNG，但与当前 P15-56 右向原画不是同一姿态和来源。直接叠加造成明显发丝、轮廓和眼部错位；P15-69 色彩提取层仍有额头横线与发丝丢失。</p>'
s+='<p>SAM2 真实接口已探测、上传当前 512px 角色图并调用。交互点分割返回后端失败；自动分割返回 ZeroGPU 使用配额耗尽。没有取得真实 SAM2 透明语义结果。旧数据与新数据没有被混为正式同视角 ArtMesh。</p>'
s+='<div class="panel"><h2>当前 P15-70 近眼位移复现</h2><input id="shift" type="range" aria-label="近眼位移" min="0" max="18" step="9" value="18"><p id="offset">当前位移 18px</p><figure><img id="motion" src="p15-70-composite.png" alt="P15-70 既有画面"><figcaption>此次没有产生新的独立前发，所以位移直接引用此前 P15-70 的候选画面</figcaption></figure></div>'
items=[('current-right-source.png','同视角 P15-56 原画（身份源）'),
 ('p15-69-color-layer.png','P15-69：颜色分离不是语义层'),
 ('prior-yaw045-layer.png','既有 45° 独立发图'),
 ('prior-yaw045-overlay.png','45° 发图直接套在新原画上：明显错位'),
 ('prior-yaw090-layer.png','既有 90° 独立发图'),
 ('prior-yaw090-overlay.png','90° 发图直接套在新原画上：明显错位'),
 ('prior-prior41-overlay.png','另一候选版本前发直接套用：不匹配'),
 ('input-512.png','实际提交给 SAM2 的原画裁切')]
s+='<h2>素材来源、错误覆盖与 SAM2 实际输入</h2><div class="grid">'
for f,label in items:
 assert (D/f).exists(),f
 s+=f'<figure><img src="{f}" alt="{label}"><figcaption>{label}</figcaption></figure>'
s+='</div><script>const slider=document.getElementById("shift");const names={0:"p15-70-eye-shift-00.png",9:"p15-70-eye-shift-09.png",18:"p15-70-composite.png"};slider.addEventListener("input",()=>{let n=Number(slider.value);document.querySelector("#motion").src=names[n];document.querySelector("#offset").textContent="当前位移 "+n+"px";});</script></html>'
for dx in (0,9,18):
 p=R/f'private-assets/exports/p15-70-seam-repair/eye-shift-{dx:02d}-seam-repaired.png'
 out=D/('p15-70-composite.png' if dx==18 else f'p15-70-eye-shift-{dx:02d}.png')
 from shutil import copyfile
 copyfile(p,out)
(D/'index.html').write_text(s,encoding='utf8')
print('P15-71 HTML ready')

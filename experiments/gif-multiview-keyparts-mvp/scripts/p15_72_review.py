from pathlib import Path
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-72-semantic-hair'
css='''body{max-width:1450px;margin:18px auto;padding:0 17px;background:#172636;color:#edf3fa;font:15px/1.5 system-ui}h1{font-size:24px}.warn{color:#ffcc9e}.good{color:#b5ead0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:15px}.panel,figure{background:#294054;padding:12px;border-radius:8px;margin:0}img{width:100%;max-height:570px;object-fit:contain;background:repeating-conic-gradient(#ddd 0 25%,#fff 0 50%) 50%/22px 22px}figcaption{margin-top:7px;font-weight:600}p{color:#d6e0eb}input{width:100%}'''
h='<!doctype html><html lang="zh-CN"><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-72 前发语义模型实测</title><style>'+css+'</style><h1>P15-72 · CPU GroundingDINO + SAM 前发分割实测</h1>'
h+='<p class="good">本轮真实提交同视角角色裁切，CPU 服务成功返回 2 个模型结果，不受上轮 ZeroGPU 配额限制。</p>'
h+='<p class="warn"><b>正式视觉门禁 FAIL：</b>两个结果均包含眼睛、脸颊和下脸，不能构成独立前发透明 Alpha。模型“检测到目标”不代表分割范围语义正确。</p>'
h+='<div class="grid">'
for file,label in [('reference-same-view.png','P15-56 原始 512px 同视角素材'),
('grounded-sam-output.png','模型结果 A：pink anime bangs hair（包括脸部）'),
('grounded-sam-fringe.png','模型结果 B：front hair fringe bangs（包括脸部）')]:
 h+=f'<figure><img src="{file}" alt="{label}"><figcaption>{label}</figcaption></figure>'
h+='</div><div class="panel"><h2 id="motion-label">既有 P15-70 近眼位移 18px</h2><input id="shift" type="range" min="0" max="18" step="9" value="18" aria-label="近眼位移"><figure><img id="motion" src="baseline-eye-18.png" alt="既有近眼位移"><figcaption>仅复用此前的 P15-70 对照帧；SAM 输出没有进入动画管线</figcaption></figure></div>'
h+='<p>下一步必须取得真正的同姿态发丝级语义层，先完成 0px 原图重组验收，再进行 9px / 18px 遮挡验证。</p>'
h+='<script>const s=document.querySelector("#shift");s.addEventListener("input",()=>{let n=String(Number(s.value)).padStart(2,"0");document.querySelector("#motion").src="baseline-eye-"+n+".png";document.querySelector("#motion-label").textContent="既有 P15-70 近眼位移 "+Number(s.value)+"px";});</script></html>'
(D/'index.html').write_text(h)
print('HTML',len(h))

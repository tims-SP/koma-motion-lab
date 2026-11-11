from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-84-clean-brow-inpaint'
q=json.loads((R/'evidence/p15-84-qa.json').read_text())
css='''body{max-width:1480px;margin:18px auto;padding:0 16px;background:#172738;color:#f0f6fb;font:15px/1.55 system-ui}h1{font-size:24px}h2{font-size:18px}p{color:#d5e0ea}.ok{color:#b7e8ce}.warn{color:#ffd1a2}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}figure,.panel{margin:0;padding:12px;background:#2a4054;border-radius:8px}img{width:100%;max-height:600px;object-fit:contain;background:repeating-conic-gradient(#ddd 0 25%,#fff 0 50%) 50%/24px 24px}figcaption{font-weight:600;margin-top:7px}input{width:100%}'''
h='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-84 真实隐藏眉眼 LaMa 修复</title><style>'+css+'</style></head><body><h1>P15-84 · 真实神经修复隐藏眉眼底图</h1>'
h+='<p class="ok"><b>真实模型成功：</b>调用 pg56714/Inpaint-Anything 的 LaMa CPU 推理。输入为原始 P15-56 同视角角色图，Mask 来自独立近眼与眉毛 Alpha 的并集扩张，排除 SAM3 前发区域。模型实际生成 512×512 隐藏底图；9/18px 使用生成底图与独立移动近眼、SAM3 刘海、金色发夹重新合成。</p>'
h+='<p class="warn"><b>正式 ArtMesh 暂不批准：</b>9/18px 主要重复眉线已被清除，眼周没有新增透明洞；但 9px 左侧仍有细小残线，眼睛外缘与前发交界仍需原画级精修。0px 继续使用 P15-82 四张独立图层的真实重组，不以 AI 重绘替换原画。</p>'
h+='<div class="panel"><h2 id="pose">眼睛位移 18px</h2><input id="shift" type="range" min="0" max="18" step="9" value="18" aria-label="近眼位移"><div class="grid"><figure><img id="full" src="frame-18.png" alt="完整角色"><figcaption>完整角色实际合成</figcaption></figure><figure><img id="face" src="frame-18-face.png" alt="面部放大"><figcaption>面部</figcaption></figure><figure><img id="detail" src="frame-18-detail.png" alt="眉眼细节"><figcaption>眉眼与刘海交界</figcaption></figure></div></div>'
h+='<h2>修复来源和模型证据</h2><div class="grid">'
for f,t in [('input-preview.png','真实模型输入（原画同视角）'),('mask-preview.png','近眼+眉毛语义区域 Mask，排除前发'),('model-512.png','LaMa 模型真实返回的修复结果'),('clean-hidden-face.png','映射回原图后的隐藏底图'),('frame-00-face.png','0px：P15-82 独立原画图层合成'),('frame-09-detail.png','9px：生成隐藏底图 + 独立近眼'),('frame-18-detail.png','18px：生成隐藏底图 + 独立近眼'),('frame-18-face.png','18px：全脸检查'),('previous-p15-83.png','P15-83 失败方案对照')]:
 assert (D/f).is_file(),f
 h+=f'<figure><img src="{f}" alt="{t}"><figcaption>{t}</figcaption></figure>'
h+='</div><script>document.getElementById("shift").addEventListener("input",e=>{let n=String(+e.target.value).padStart(2,"0");for(let [id,s] of [["full",""],["face","-face"],["detail","-detail"]])document.getElementById(id).src="frame-"+n+s+".png";document.getElementById("pose").textContent="眼睛位移 "+Number(e.target.value)+"px";});</script></body></html>'
(D/'index.html').write_text(h,encoding='utf8')
print('HTML_READY')

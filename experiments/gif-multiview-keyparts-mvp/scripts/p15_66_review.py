from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-66-front-bang'
q=json.loads((R/'evidence/p15-66-front-bang-qa.json').read_text())
css='''body{max-width:1460px;margin:16px auto;padding:0 16px;background:#182839;color:#eff4fa;font:15px/1.5 system-ui}h1{font-size:24px}h2{font-size:18px}.warn{color:#ffce9c}.good{color:#aee8c3}p{color:#d3ddea}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}figure,.panel{margin:0;background:#2a4054;padding:12px;border-radius:7px}img{width:100%;max-height:570px;object-fit:contain;background:repeating-conic-gradient(#dcdfe4 0 25%,#fff 0 50%) 50%/24px 24px}figcaption{margin-top:6px;font-weight:600}input{width:100%}'''
s='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-66 · 前发遮挡局部验证</title><style>'+css+'</style></head><body><h1>P15-66 · 前发与近眼局部遮挡</h1>'
s+='<p class="good">本轮复用 LaMa 隐藏皮肤和 P15-65 近眼原画。将紫粉色发丝的颜色特征与原 LaMa 修改区域相交，得到带柔和 Alpha 边缘的局部前发覆盖片（164 个非透明像素）；0/9/18px 三档均已实测，透明洞 0。</p>'
s+='<p class="warn"><b>完整前发 ArtMesh 仍失败：</b>该小图层仅能修复眼睛右缘的 17×24px 局部交叠，不是整片刘海，也不具有独立发丝绘制与遮挡后底图。旧 P15-41 的前发层属于另一个画面，身份及空间位置不吻合。不能作为正式 ArtMesh。</p>'
s+='<div class="panel"><h2 id="pos">眼睛位移：18px</h2><input type="range" id="shift" aria-label="eye displacement" min="0" max="18" step="9" value="18"><div class="grid"><figure><img id="whole" src="eye-shift-18-with-occlusion.png" alt="前发覆盖后的全图"><figcaption>本轮局部前发覆盖</figcaption></figure><figure><img id="face" src="eye-shift-18-face.png" alt="面部局部放大"><figcaption>局部放大</figcaption></figure><figure><img id="bare" src="eye-shift-18-no-occlusion.png" alt="无前发覆盖对照"><figcaption>同档无前发覆盖对照</figcaption></figure></div></div>'
tiles=[('hair.front.eye-overlap.png','透明的局部前发覆盖层'),('hair.front.eye-overlap-mask.png','局部 Alpha 遮罩'),('source-face.png','原始身份源面部'),('old45hair-face.png','旧 45° 发型图层：不能直接复用'),('a-face.png','全区域颜色遮罩：诊断'),('hairA-test.png','P15-65 硬多边形：拒绝')]
s+='<h2>源图、透明层和失败方式对照</h2><div class="grid">'
for p,title in tiles:
 src=D/p
 if not src.is_file():continue
 s+=f'<figure><img src="{p}" alt="{title}"><figcaption>{title}</figcaption></figure>'
s+='</div><script>const control=document.getElementById("shift");control.addEventListener("input",()=>{const n=String(Number(control.value)).padStart(2,"0");document.getElementById("pos").textContent="眼睛位移："+Number(control.value)+"px";document.getElementById("whole").src="eye-shift-"+n+"-with-occlusion.png";document.getElementById("face").src="eye-shift-"+n+"-face.png";document.getElementById("bare").src="eye-shift-"+n+"-no-occlusion.png";});</script></body></html>'
(D/'index.html').write_text(s,encoding='utf8')
print('HTML READY')

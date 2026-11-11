from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-74-bangs-repair'
q=json.loads((R/'evidence/p15-74-qa.json').read_text())
css='''body{max-width:1450px;margin:16px auto;padding:0 16px;background:#172738;color:#eff5fc;font:15px/1.5 system-ui}h1{font-size:24px}.pass{color:#a9e4c4}.warn{color:#ffca9f}p{color:#d2deec}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}figure,.panel{margin:0;background:#293f54;padding:12px;border-radius:8px}img{width:100%;max-height:590px;object-fit:contain;background:repeating-conic-gradient(#dcdcdc 0 25%,white 0 50%) 50%/24px 24px}figcaption{margin-top:7px;font-weight:600}input{width:100%}'''
h='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-74 动画 0px 像素精确回组验收</title><style>'+css+'</style></head><body><h1>P15-74 · 前发外轮廓 Alpha 去重与近眼位移</h1>'
h+='<p class="pass"><b>动画管线 0px 像素门禁已通过：</b>清理发层右外轮廓 '+str(q['duplicateSemiTransparentPixelsRemoved'])+' 个重复 Alpha 像素，正式原画 P15-56 与新的 0px 动画复合逐像素相同；三档没有新增透明孔。</p>'
h+='<p class="warn"><b>动态画质仍 FAIL：</b>9/18px 眼部移动后仍可见眉毛/刘海交界的虚线和左眼角色块。睫毛边缘收缩 1px 只减轻局部晕边，不能替代真正发丝与眉睫毛语义分层。没有批准正式 ArtMesh/VDD。</p>'
h+='<div class="panel"><h2 id="shiftTitle">近眼位移 18px</h2><input type="range" min="0" max="18" step="9" value="18" id="shift" aria-label="近眼位移"><div class="grid"><figure><img id="whole" src="eye-shift-18.png" alt="完整姿态"><figcaption>候选姿态全图</figcaption></figure><figure><img id="face" src="eye-shift-18-face.png" alt="放大面部"><figcaption>面部细节</figcaption></figure><figure><img id="detail" src="eye-shift-18-detail.png" alt="近眼边界细节"><figcaption>睫毛、前发、眉毛边缘放大</figcaption></figure></div></div>'
items=[('original-detail.png','P15-56 原始眼部局部'),('p15-73-detail.png','旧 P15-73 18px 对照'),('hair.front.alpha-dedup.png','修复后的前发 RGBA 层'),('motion-contact.jpg','三档位移联系表'),('eye-original-18-detail.png','旧睫毛边界'),('eye-erode1-18-detail.png','1px 收缩实验（本轮选用）'),('eye-erode2-18-detail.png','2px 收缩损伤眼缘（拒绝）'),('eye-smooth-18-detail.png','羽化对照')]
h+='<h2>源图、局部实验与失败模式</h2><div class="grid">'
for f,label in items:
 assert (D/f).is_file(),f
 h+=f'<figure><img src="{f}" alt="{label}"><figcaption>{label}</figcaption></figure>'
h+='</div><script>const s=document.querySelector("#shift");s.addEventListener("input",()=>{const dx=String(+s.value).padStart(2,"0");document.querySelector("#whole").src="eye-shift-"+dx+".png";document.querySelector("#face").src="eye-shift-"+dx+"-face.png";document.querySelector("#detail").src="eye-shift-"+dx+"-detail.png";document.querySelector("#shiftTitle").textContent="近眼位移 "+Number(s.value)+"px";});</script></body></html>'
(D/'index.html').write_text(h,encoding='utf8')
print('html ready')

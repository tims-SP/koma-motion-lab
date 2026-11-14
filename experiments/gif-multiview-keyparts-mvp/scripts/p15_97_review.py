#!/usr/bin/env python3
"""P0 three-angle, source-owned front-hair motion visual review."""
from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-97-multiview-motion'
q=json.loads((R/'evidence/p15-97-multiview-motion-qa.json').read_text())
views=['52p5','60','75']
assert list(q['views'])==views
ref={'52p5':'../p15-93-yaw0525-review/yaw052p5-registered.png',
     '60':'../p15-92-angle-keyart/yaw060-registered.png',
     '75':'../p15-92-angle-keyart/yaw075-registered.png'}
for name in views:
 for dx in range(13):assert (D/f'yaw{name}-frame-{dx:02}.png').is_file()
# Animation synchronized across view changes: visualizes a single normalized dynamic control.
frames=[]
for dx in range(13):
 canvas=Image.new('RGB',(360*3,415),'white')
 draw=ImageDraw.Draw(canvas)
 for idx,view in enumerate(views):
  art=Image.open(D/f'yaw{view}-frame-{dx:02}.png').convert('RGBA')
  white=Image.new('RGBA',art.size,'white');white.alpha_composite(art)
  crop=white.convert('RGB').crop((500,285,825,615)).resize((360,388),Image.Resampling.LANCZOS)
  canvas.paste(crop,(idx*360,26))
  draw.text((idx*360+8,7),f'yaw {view}, bangs {dx}px',fill='black')
 frames.append(canvas)
gif=D/'three-view-motion.gif'
frames[0].save(gif,save_all=True,append_images=frames[1:],duration=150,loop=0,optimize=False)
q['animatedPreviewSHA256']=hashlib.sha256(gif.read_bytes()).hexdigest()
q['browserEntry']='private-assets/exports/p15-97-multiview-motion/index.html'
css="""body{font:15px/1.55 system-ui,sans-serif;background:#162638;color:#eef4fa;max-width:1450px;margin:12px auto;padding:0 14px}h1{font-size:23px}h2{font-size:18px}p{color:#bdc9d7}label{display:block;margin:9px 0}input{width:100%;margin-bottom:14px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{background:#2a4057;border-radius:8px;padding:9px;margin:0}img{display:block;width:100%;height:auto;object-fit:contain;background:white}figcaption{font-size:12px;color:#e1e6eb;padding-top:6px}.full{margin:15px 0}@media(max-width:700px){.grid{grid-template-columns:1fr}}"""
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>P0 · 52.5°–75° 前发语义动态验收</title><style>'''+css+'''</style></head><body>
<h1>P0 · 52.5°、60°、75° 前发锚点与局部运动</h1>
<p>独立原画 + SAM3 头发语义源像素 + Codex 生成的隐藏脸部底图。三个视角共用 hairTipOffsetPx 参数；60° 保留既有验收帧。原画身份与静态画面逐像素保留，当前验收范围是局部发梢运动，不等于跨视角连续转头通过。</p>
<label for="angle">视角：<b id="angle-label">52.5°</b></label>
<input id="angle" type="range" min="0" max="2" value="0" step="1">
<label for="offset">局部发梢位移：<b id="offset-label">0px</b></label>
<input id="offset" type="range" min="0" max="12" value="0" step="1">
<div class="grid">
<figure><img id="source" src="'''+ref['52p5']+'''" alt="当前视角的原始身份图"><figcaption>独立原画（像素保真基准）</figcaption></figure>
<figure><img id="candidate" src="yaw52p5-frame-00.png" alt="动态前发画面"><figcaption>根部锚定、发梢局部形变与隐藏底图</figcaption></figure>
</div><h2>三个视角的同步运动</h2>
<figure class="full"><img src="view-coupled-contact.jpg" alt="全部视角原画与发梢位移对照"><figcaption>三个视角、四种位移的静态对照</figcaption></figure>
<figure class="full"><img src="three-view-motion.gif" alt="三视角同步动作 GIF"><figcaption>39 张逐帧源文件组成的同步 13 帧 GIF</figcaption></figure>
<h2>语义分割源</h2><div class="grid">
<figure><img src="../p15-97-sam3-yaw52p5/mask-contact.jpg" alt="52.5度SAM3分割"><figcaption>52.5° 的实际 SAM3 原画分割结果</figcaption></figure>
<figure><img src="../p15-97-sam3-yaw75/mask-contact.jpg" alt="75度SAM3分割"><figcaption>75° 的实际 SAM3 原画分割结果</figcaption></figure></div>
<script>
const views=['52p5','60','75'];
const refs={'52p5':'../p15-93-yaw0525-review/yaw052p5-registered.png','60':'../p15-92-angle-keyart/yaw060-registered.png','75':'../p15-92-angle-keyart/yaw075-registered.png'};
const angle=document.querySelector('#angle'),offset=document.querySelector('#offset'),src=document.querySelector('#source'),art=document.querySelector('#candidate'),angleLabel=document.querySelector('#angle-label'),offsetLabel=document.querySelector('#offset-label');
function update(){const yaw=views[Number(angle.value)],dx=String(offset.value).padStart(2,'0');angleLabel.textContent=yaw.replace('p','.')+'°';offsetLabel.textContent=offset.value+'px';src.src=refs[yaw];art.src='yaw'+yaw+'-frame-'+dx+'.png'}
angle.addEventListener('input',update);offset.addEventListener('input',update);
</script></body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
(R/'evidence/p15-97-multiview-motion-qa.json').write_text(json.dumps(q,indent=2,ensure_ascii=False)+'\n')
print('review',D/'index.html','animated',q['animatedPreviewSHA256'])

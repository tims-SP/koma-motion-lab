#!/usr/bin/env python3
"""Interactive evidence: real native 67.5° garment and three-key VDD ablation."""
from pathlib import Path
from PIL import Image
from hashlib import sha256
import os,json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-105-three-key-vdd'
qaPath=R/'evidence/p15-105-render-qa.json'
q=json.loads(qaPath.read_text());native=json.loads((R/'evidence/p15-105-native-art-qa.json').read_text())
prior=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
angles=q['renderedAngles']
sources={'P15-101-baseline':prior['methods']['head_alpha_blend']}
sources.update(q['methods'])
frames={}
animations={}
for method,info in sources.items():
 frames[method]={}
 shots=[]
 for a in angles:
  k=f'{a:g}';imgPath=R/info[k]['relativePath'];frames[method][k]=os.path.relpath(imgPath,D)
  im=Image.open(imgPath).convert('RGBA');back=Image.new('RGBA',im.size,'white');back.alpha_composite(im)
  shots.append(back.convert('RGB').resize((460,460),Image.Resampling.LANCZOS))
 sequence=shots+shots[-2:0:-1]
 gif=D/(method+'-loop.gif')
 sequence[0].save(gif,save_all=True,append_images=sequence[1:],duration=190,loop=0,optimize=False)
 animations[method]={'path':str(gif.relative_to(R)),'sha256':sha256(gif.read_bytes()).hexdigest()}
css="""body{font:15px/1.54 system-ui;background:#172739;color:#edf3fa;max-width:1460px;margin:14px auto;padding:0 16px}h1{font-size:23px}h2{font-size:18px}p,small{color:#bfcfdf}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{background:#293e54;padding:10px;border-radius:8px;margin:0}img{display:block;width:100%;height:auto;object-fit:contain;background:#fff}figcaption{font-size:12px}select,input{width:100%;box-sizing:border-box;padding:8px;margin:6px 0 14px}label{display:block;margin:12px 0}@media(max-width:690px){.grid{grid-template-columns:1fr}}"""
options=''.join(f'<option value="{m}">{m.replace("_"," ")}</option>' for m in frames)
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 · Native 67.5° Garment Source Three-Key VDD</title><style>'''+css+'''</style></head><body>
<h1>P0 · 60° → 67.5° → 75° 三关键视角服装动画</h1>
<p>新增 67.5° 服装独立原生绘图来自 Codex 内置 image_gen。60°、75° 继续使用原生角色原画；头部复用 P15-101 共用头发／脸部网格。下方对比三种分段服装采样与原有 P15-101 连续融合。</p>
<label for="method">方法选择</label><select id="method">'''+options+'''</select>
<label for="yaw">视角：<b id="yaw-label">60°</b></label><input id="yaw" type="range" min="0" max="8" step="1" value="0">
<div class="grid">
<figure><img id="current" src="../p15-101-head-render/head_alpha_blend-yaw60.png" alt="当前实际渲染帧"><figcaption>RGBA 原图与实际中间转头画面</figcaption></figure>
<figure><img id="motion" src="P15-101-baseline-loop.gif" alt="当前方法的 GIF"><figcaption>九角度正向和逆向连续动画</figcaption></figure>
</div>
<h2>67.5° 独立服装原画与两端来源</h2>
<figure><img src="../p15-105-middle-art/native-garment-contact.jpg" alt="60、原生67.5、75度服装外观并列"><figcaption>67.5° 原生模型源经过饰件中心配准，仅用于比较；原生 1254×1254 PNG 另行保留</figcaption></figure>
<h2>各角度画面对照</h2>
<figure><img src="three-key-garment-contact.jpg" alt="原基准以及三种分段 VDD 方法"><figcaption>九个角度比较，检查金色饰件、蝴蝶结线稿、下颌和衣领衔接</figcaption></figure>
<small>来源验证包括原生图片 SHA256、透明区域、饰件注册和两端关键帧逐像素保真。中间关键帧真实美术质量和三关键帧转头的流畅性分开验收。</small>
<script>
const frames='''+json.dumps(frames,separators=(',',':'))+''',angles='''+json.dumps(angles)+''';
const method=document.querySelector('#method'),yaw=document.querySelector('#yaw'),current=document.querySelector('#current'),motion=document.querySelector('#motion'),label=document.querySelector('#yaw-label');
function update(){const m=method.value,a=String(angles[Number(yaw.value)]);label.textContent=a+'°';current.src=frames[m][a];motion.src=m+'-loop.gif';}
method.addEventListener('change',update);yaw.addEventListener('input',update);
</script></body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
report={'schema':'KOMA_P15_105_THREE_KEY_REVIEW_V1',
 'sourceAngles':[60,67.5,75],'renderAngles':angles,
 'nativeMiddleSource':native['nativePath'],'nativeImageSHA256':native['nativeSHA256'],
 'frameFiles':frames,'animations':animations,
 'entry':'private-assets/exports/p15-105-three-key-vdd/index.html',
 'modelMiddleArtAccepted':False,'continuousAnimationAccepted':False}
(R/'evidence/p15-105-review-qa.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print('REVIEW',report['entry'],'modes',len(frames),'angles',len(angles),flush=True)

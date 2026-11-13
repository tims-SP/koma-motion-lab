#!/usr/bin/env python3
"""P15-111 P0 six native underpaint sources with 3-view compositing comparison."""
from pathlib import Path
from PIL import Image
from hashlib import sha256
import os,json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-111-layered-render'
q=json.loads((R/'evidence/p15-111-render-qa.json').read_text())
s=json.loads((R/'evidence/p15-111-source-qa.json').read_text())
comp=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
old=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
angles=q['renderAngles']
sources={
 'P15-101-baseline':{k:r['relativePath'] for k,r in old['methods']['head_alpha_blend'].items()},
 'P15-107-three-native':{k:r['relativePath'] for k,r in comp['methods']['companion_direct_native_keys'].items()}}
sources.update({m:{k:rec['path'] for k,rec in z.items()} for m,z in q['methods'].items()})
frames={};loops={}
for name,items in sources.items():
 frames[name]={};seq=[]
 for angle in angles:
  key=f'{angle:g}'
  path=R/items[key]
  frames[name][key]=os.path.relpath(path,D)
  im=Image.open(path).convert('RGBA')
  bg=Image.new('RGBA',im.size,'white');bg.alpha_composite(im)
  seq.append(bg.convert('RGB').resize((450,450),Image.Resampling.LANCZOS))
 cycle=seq+seq[-2:0:-1]
 gif=D/(name+'-loop.gif')
 cycle[0].save(gif,save_all=True,append_images=cycle[1:],duration=175,loop=0,optimize=False)
 loops[name]={'path':str(gif.relative_to(R)),'sha256':sha256(gif.read_bytes()).hexdigest()}
css="""body{font:15px/1.55 system-ui;background:#192b3e;color:#edf4fb;max-width:1480px;padding:0 16px;margin:12px auto}h1{font-size:23px}h2{font-size:18px}p,small{color:#bfcedd}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{margin:0;background:#304459;padding:10px;border-radius:8px}img{display:block;width:100%;background:#fff}figcaption{font-size:12px}select,input{box-sizing:border-box;width:100%;padding:8px;margin:7px 0 14px}label{display:block;margin:12px 0}@media(max-width:690px){.grid{grid-template-columns:1fr}}"""
options=''.join(f'<option value="{name}">{name.replace("_"," ")}</option>' for name in frames)
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 · Three-View Hidden Garment Underpaint</title><style>'''+css+'''</style></head><body>
<h1>P0 · 60°–75° 隐藏面原画与可见性分层</h1>
<p>三视角生成两类各自独立的透明原画：衣领/衬衫持续隐藏在前景蝴蝶结之后，蝴蝶结内层隐藏在金色饰件后方。采用原生 P0 服装和分层掩码限定绘图范围，在连续转头时分别比较线性分层、金饰单源、蝴蝶结单源以及既有基准。</p>
<label for="method">渲染方式</label><select id="method">'''+options+'''</select>
<label for="yaw">视角：<b id="angle">60°</b></label><input id="yaw" type="range" min="0" max="8" step="1" value="0">
<div class="grid">
<figure><img id="frame" src="../p15-101-head-render/head_alpha_blend-yaw60.png" alt="实际1024角色画面"><figcaption>完整角色与透明服装实际 RGBA 帧</figcaption></figure>
<figure><img id="motion" src="P15-101-baseline-loop.gif" alt="当前方法九角度GIF"><figcaption>九角度双向 GIF</figcaption></figure></div>
<h2>三视角透明隐藏面原画</h2>
<figure><img src="../p15-111-hidden-registered/underpaint-source-contact.jpg" alt="三视角原画及隐藏衣领、蝴蝶结及遮挡揭示"><figcaption>从左至右：真实原画、衣领补全、蝴蝶结补全、仅供验证的遮挡揭示。原生图片 SHA256 保留。</figcaption></figure>
<h2>完整动画对照</h2>
<figure><img src="hidden-material-layer-contact.jpg" alt="五种渲染方式的九角度画面对比"><figcaption>对比真实前景遮挡与隐藏面素材的独立分层</figcaption></figure>
<small>新隐藏面是模型根据可见原画推断的候选绘图，并非有观察证据的背面实物。验收分为原生文件、来源分层、隐藏区域覆盖率、关键帧保真、浏览器功能及实际动画视觉质量。</small>
<script>
const frames='''+json.dumps(frames,separators=(',',':'))+''',angles='''+json.dumps(angles)+''';
const method=document.querySelector('#method'),yaw=document.querySelector('#yaw'),
 frame=document.querySelector('#frame'),motion=document.querySelector('#motion'),label=document.querySelector('#angle');
function update(){const m=method.value,a=String(angles[Number(yaw.value)]);label.textContent=a+'°';frame.src=frames[m][a];motion.src=m+'-loop.gif';}
method.addEventListener('change',update);yaw.addEventListener('input',update);
</script></body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
review={'schema':'KOMA_P15_111_HIDDEN_MATERIAL_REVIEW_V1',
 'sourceAngles':[60,67.5,75],'renderAngles':angles,
 'methodFrames':frames,'animations':loops,
 'nativeGeneratedLayerCount':6,'registeredViewCount':3,
 'sourceArtifactSHA256':sha256((R/'evidence/p15-111-source-qa.json').read_bytes()).hexdigest(),
 'entry':str((D/'index.html').relative_to(R)),
 'nativeHiddenArtArtistApproved':False,'fullYawVisualAccepted':False}
(R/'evidence/p15-111-review-qa.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
print('REVIEW',review['entry'],'methods',len(frames),'angles',len(angles),flush=True)

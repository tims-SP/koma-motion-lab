#!/usr/bin/env python3
"""Visual comparison of source-consistent 67.5° garment ink transport."""
from pathlib import Path
from PIL import Image
from hashlib import sha256
import json,os
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-107-canonical-ink'
qa=json.loads((R/'evidence/p15-107-ink-qa.json').read_text())
P101=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
P105=json.loads((R/'evidence/p15-105-render-qa.json').read_text())
angles=qa['angles']
sources={
 'P15-101-baseline':{k:v['relativePath'] for k,v in P101['methods']['head_alpha_blend'].items()},
 'P15-105-native-middle':{k:v['relativePath'] for k,v in P105['methods']['three_key_direct'].items()}}
sources.update({m:{k:v['path'] for k,v in frames.items()} for m,frames in qa['methods'].items()})
paths={};gifs={}
for method,refs in sources.items():
 pics=[];paths[method]={}
 for a in angles:
  f=R/refs[f'{a:g}']
  paths[method][f'{a:g}']=os.path.relpath(f,D)
  rgba=Image.open(f).convert('RGBA')
  white=Image.new('RGBA',rgba.size,'white')
  white.alpha_composite(rgba)
  pics.append(white.convert('RGB').resize((475,475),Image.Resampling.LANCZOS))
 sequence=pics+pics[-2:0:-1]
 dest=D/(method+'-loop.gif')
 sequence[0].save(dest,save_all=True,append_images=sequence[1:],duration=190,loop=0,optimize=False)
 gifs[method]={'relativePath':str(dest.relative_to(R)),'sha256':sha256(dest.read_bytes()).hexdigest()}
css="""body{font:15px/1.55 system-ui;background:#16283b;color:#f2f5fb;margin:12px auto;padding:0 16px;max-width:1500px}h1{font-size:23px}h2{font-size:18px}p,small{color:#c0d0de}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{margin:0;padding:10px;border-radius:8px;background:#2b4259}img{display:block;width:100%;object-fit:contain;background:#fff}figcaption{font-size:12px}label{display:block;margin:12px 0}select,input{width:100%;box-sizing:border-box;padding:8px;margin:6px 0 14px}@media(max-width:700px){.grid{grid-template-columns:1fr}}"""
options=''.join(f'<option value="{m}">{m.replace("_"," ")}</option>' for m in sources)
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 · Source-Owned Garment Ink Correspondence</title><style>'''+css+'''</style></head><body>
<h1>P0 · 60°–75° 单一原画线稿与三视角对应验证</h1>
<p>以现有 67.5° 原画为统一纹理来源，通过 P15-106 语义锚点拟合二维 TPS，将整件服装或蝴蝶结贴图连续映射到目标视角；与旧两视角原画融合及三关键视角融合对照。两端 60°、75° 仍采用原始角色像素。</p>
<label for="method">真实渲染方案</label><select id="method">'''+options+'''</select>
<label for="yaw">目标视角：<b id="angle">60°</b></label><input id="yaw" type="range" min="0" max="8" step="1" value="0">
<div class="grid">
<figure><img id="frame" src="../p15-101-head-render/head_alpha_blend-yaw60.png" alt="实际全尺寸帧"><figcaption>原画关键视角与中间渲染</figcaption></figure>
<figure><img id="motion" src="P15-101-baseline-loop.gif" alt="当前方案的完整动画循环"><figcaption>九角度往返 GIF</figcaption></figure>
</div>
<h2>原画与角色一致性</h2>
<figure><img src="../p15-105-middle-art/native-garment-contact.jpg" alt="60 67.5 75度来源原画"><figcaption>三张真实服装原画及 67.5° 原图注册基准</figcaption></figure>
<h2>实际连续转头对照</h2>
<figure><img src="single-source-ink-contact.jpg" alt="所有方法九角度服装转头对照"><figcaption>来源所有权、肩线、衣领和蝴蝶结的连续线稿</figcaption></figure>
<small>工程验收覆盖原生素材哈希、非折叠 TPS、实际帧和可交互浏览器。视觉指标与关键视角跳变分别审查。</small>
<script>
const files='''+json.dumps(paths,separators=(',',':'))+''',angles='''+json.dumps(angles)+''';
const method=document.querySelector('#method'),yaw=document.querySelector('#yaw'),frame=document.querySelector('#frame'),motion=document.querySelector('#motion'),label=document.querySelector('#angle');
function update(){let m=method.value,a=String(angles[Number(yaw.value)]);label.textContent=a+'°';frame.src=files[m][a];motion.src=m+'-loop.gif';}
method.addEventListener('change',update);yaw.addEventListener('input',update);
</script></body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
review={'schema':'KOMA_P15_107_SOURCE_INK_REVIEW_V1',
 'renderedAngles':angles,'methods':paths,'gifs':gifs,
 'entry':'private-assets/exports/p15-107-canonical-ink/index.html',
 'sourceContinuityApproved':False}
(R/'evidence/p15-107-review-qa.json').write_text(json.dumps(review,indent=2,ensure_ascii=False)+'\n')
print('REVIEW',review['entry'],'methodCount',len(paths))

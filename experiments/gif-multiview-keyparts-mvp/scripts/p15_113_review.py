#!/usr/bin/env python3
"""P15-113 unified source textile UV and geometry-mesh visual inspection."""
from pathlib import Path
from PIL import Image
from hashlib import sha256
import os,json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-113-canonical-topology'
render=json.loads((R/'evidence/p15-113-render-qa.json').read_text())
top=json.loads((R/'evidence/p15-113-topology-qa.json').read_text())
p101=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
p107=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
p112=json.loads((R/'evidence/p15-112-render-qa.json').read_text())
angles=render['angles']
methods={
 'P15-101-original':{k:r['relativePath'] for k,r in p101['methods']['head_alpha_blend'].items()},
 'P15-107-native':{k:r['relativePath'] for k,r in p107['methods']['companion_direct_native_keys'].items()},
 'P15-112-edgeGuard':{k:r['path'] for k,r in p112['methods']['edge_guard'].items()},
 **{m:{k:r['path'] for k,r in frames.items()} for m,frames in render['methods'].items()}}
paths={};animations={}
for method,refs in methods.items():
 imgs=[];paths[method]={}
 for angle in angles:
  key=f'{angle:g}'
  path=R/refs[key]
  paths[method][key]=os.path.relpath(path,D)
  im=Image.open(path).convert('RGBA')
  white=Image.new('RGBA',im.size,'white');white.alpha_composite(im)
  imgs.append(white.convert('RGB').resize((450,450),Image.Resampling.LANCZOS))
 reverse=imgs+imgs[-2:0:-1]
 gif=D/(method+'-loop.gif')
 reverse[0].save(gif,save_all=True,append_images=reverse[1:],duration=195,loop=0,optimize=False)
 animations[method]={'path':str(gif.relative_to(R)),'sha256':sha256(gif.read_bytes()).hexdigest()}
css="""body{font:15px/1.55 system-ui;background:#172b3c;color:#eff4fa;max-width:1460px;margin:12px auto;padding:0 16px}h1{font-size:23px}h2{font-size:18px}p,small{color:#bfcdde}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{margin:0;background:#30485c;border-radius:8px;padding:10px}img{display:block;width:100%;height:auto;background:white}figcaption{font-size:12px}label{display:block;margin:10px 0}select,input{padding:8px;width:100%;box-sizing:border-box;margin:6px 0 14px}table{border-collapse:collapse;width:100%;max-width:680px;margin:12px 0 20px}td,th{padding:8px;border-bottom:1px solid #52718a;text-align:left}@media(max-width:680px){.grid{grid-template-columns:1fr}}"""
opts=''.join(f'<option value="{m}">{m.replace("_"," ")}</option>' for m in paths)
rows=''.join('<tr><th>'+name+'</th><td>'+str(top['actualTargetMaskIoU'][name]['60']['IoU'])+'</td><td>'+str(top['actualTargetMaskIoU'][name]['75']['IoU'])+'</td></tr>' for name in ('bow','collar','jewel'))
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 · Unified Three-View Garment ArtMesh</title><style>'''+css+'''</style></head><body>
<h1>P0 · 三视角服装统一拓扑与真实原画对照</h1>
<p>67.5° 原生服装为蝴蝶结与金饰提供唯一可复用纹理；完整统一方案同时使用同源衣领及金边，另设原生三视角衣领与背景对照。既有每部件 33 顶点、48 三角形的共享 ArtMesh 在 60°–75° 插值。所有原生 P0 素材独立保存。</p>
<label for="method">实际渲染方式</label><select id="method">'''+opts+'''</select>
<label for="yaw">目标角度：<b id="angle">60°</b></label><input id="yaw" type="range" min="0" max="8" step="1" value="0">
<div class="grid">
<figure><img id="frame" src="../p15-101-head-render/head_alpha_blend-yaw60.png" alt="完整角色实际渲染帧"><figcaption>1024×1024 角色渲染</figcaption></figure>
<figure><img id="loop" src="P15-101-original-loop.gif" alt="九角度双向循环GIF"><figcaption>完整动画双向循环</figcaption></figure>
</div>
<h2>目标轮廓匹配程度</h2>
<p>固定一套拓扑不等于三张原画天然一致；以下是单源 UV 投影与目标视角真实图层像素的 IoU。</p>
<table><thead><tr><th>物理部件</th><th>60°</th><th>75°</th></tr></thead><tbody>'''+rows+'''</tbody></table>
<h2>真实三视角服装原画</h2>
<figure><img src="../p15-107-source-patches/consistent-garment-contact.jpg" alt="原始三张服装原画"><figcaption>60°、67.5°、75° 源图</figcaption></figure>
<h2>源素材与统一网格对照</h2>
<figure><img src="canonical-garment-contact.jpg" alt="统一拓扑与原始来源真实帧的连续对照"><figcaption>统一 ArtMesh、同源 UV、原生衣领与不同背景归属策略的九帧对比</figcaption></figure>
<small>工程检查覆盖拓扑身份、非翻折三角形、实际纹理来源、轮廓 IoU、逐帧浏览器和画面指标。原画质量、衣领轮廓及完整转头由独立视觉门禁判定。</small>
<script>
const frames='''+json.dumps(paths,separators=(',',':'))+''',angles='''+json.dumps(angles)+''';
const method=document.querySelector('#method'),yaw=document.querySelector('#yaw'),frame=document.querySelector('#frame'),loop=document.querySelector('#loop'),label=document.querySelector('#angle');
function update(){const m=method.value,a=String(angles[Number(yaw.value)]);label.textContent=a+'°';frame.src=frames[m][a];loop.src=m+'-loop.gif';}
method.addEventListener('change',update);yaw.addEventListener('input',update);
</script></body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
report={'schema':'KOMA_P15_113_CANONICAL_GARMENT_REVIEW_V1','characterId':'p0_character_001',
 'sourceViews':[60,67.5,75],'renderedAngles':angles,'methodFrames':paths,
 'animations':animations,'entry':str((D/'index.html').relative_to(R)),
 'topologySourceSHA256':sha256((R/'evidence/p15-113-topology-qa.json').read_bytes()).hexdigest(),
 'fullYawArtistApproved':False}
(R/'evidence/p15-113-review-qa.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print('REVIEW',report['entry'],'methods',len(paths),'frames',len(angles),flush=True)

#!/usr/bin/env python3
"""Interactive P0 native-garment registration + bounded patch comparisons."""
from pathlib import Path
from PIL import Image
from hashlib import sha256
import json,os
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-115-review';D.mkdir(parents=True,exist_ok=True)
q=json.loads((R/'evidence/p15-115-render-qa.json').read_text())
local=json.loads((R/'evidence/p15-115-local-qa.json').read_text())
reg=json.loads((R/'evidence/p15-115-source-qa.json').read_text())
b101=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
b107=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
b114=json.loads((R/'evidence/p15-114-render-qa.json').read_text())
angles=q['angles']
refs={
 'P15-101-original':{k:v['relativePath'] for k,v in b101['methods']['head_alpha_blend'].items()},
 'P15-107-native':{k:v['relativePath'] for k,v in b107['methods']['companion_direct_native_keys'].items()},
 'P15-114-collar':{k:v['path'] for k,v in b114['methods']['source_collar_continuous'].items()},
 **{name:{k:v['path'] for k,v in frames.items()} for name,frames in q['methods'].items()},
 **{name:{k:v['path'] for k,v in frames.items()} for name,frames in local['methods'].items()}}
paths={};gifs={}
for method,files in refs.items():
 paths[method]={};imgs=[]
 for a in angles:
  k=f'{a:g}';fp=R/files[k]
  paths[method][k]=os.path.relpath(fp,D)
  art=Image.open(fp).convert('RGBA')
  white=Image.new('RGBA',art.size,'white');white.alpha_composite(art)
  imgs.append(white.convert('RGB').resize((450,450),Image.Resampling.LANCZOS))
 frames=imgs+imgs[-2:0:-1]
 gif=D/(method+'-loop.gif')
 frames[0].save(gif,save_all=True,append_images=frames[1:],duration=190,loop=0,optimize=False)
 gifs[method]={'path':str(gif.relative_to(R)),'sha256':sha256(gif.read_bytes()).hexdigest()}
css="""body{font:15px/1.55 system-ui;background:#172b3c;color:#edf4fa;max-width:1480px;margin:12px auto;padding:0 16px}h1{font-size:23px}h2{font-size:18px}p,small{color:#c1cddd}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{margin:0;padding:10px;background:#2d4458;border-radius:8px}img{width:100%;display:block;background:white}figcaption{font-size:12px}label{display:block;margin:10px 0}select,input{width:100%;box-sizing:border-box;padding:8px;margin:6px 0 14px}table{border-collapse:collapse;width:100%}td,th{padding:7px;border-bottom:1px solid #4a7085}@media(max-width:700px){.grid{grid-template-columns:1fr}}"""
opts=''.join(f'<option value="{m}">{m.replace("_"," ")}</option>' for m in paths)
rows=''.join(f'<tr><td>{role}</td><td>{reg["registered"][role]["60"]["sourceToNativeMaskIoU"]:.3f}</td><td>{reg["registered"][role]["75"]["sourceToNativeMaskIoU"]:.3f}</td><td>{reg["registered"][role]["75"]["sourceOwner"]}</td></tr>' for role in reg['roles'])
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 · Canonical Bow and Lapel Source Ownership</title><style>'''+css+'''</style></head><body>
<h1>P0 · 蝴蝶结／金边原画配准与分部件归属</h1>
<p>对真实 60°、67.5°、75° 原画进行独立部件注册：红色蝴蝶结与金饰使用 67.5° 单源纹理，左肩金边按形状配准，75° 右襟金边根据原画可见性使用该角度原生素材。对比完整分层合成、限制原生轮廓与仅在完整角色局部替换纹理三种处理策略。</p>
<label for="method">实际渲染策略</label><select id="method">'''+opts+'''</select>
<label for="yaw">旋转角度：<b id="angle">60°</b></label><input id="yaw" type="range" min="0" max="8" step="1" value="0">
<div class="grid"><figure><img id="frame" src="../p15-101-head-render/head_alpha_blend-yaw60.png" alt="P0真实1024 RGBA帧"><figcaption>完整角色源图与实际候选帧</figcaption></figure>
<figure><img id="loop" src="P15-101-original-loop.gif" alt="双向转头GIF"><figcaption>九角度往返循环 GIF</figcaption></figure></div>
<h2>真实轮廓对应（IoU）</h2>
<table><thead><tr><th>部件</th><th>60°</th><th>75°</th><th>75° 纹理归属</th></tr></thead><tbody>'''+rows+'''</tbody></table>
<h2>原画注册与分层</h2>
<figure><img src="../p15-115-component-art/component-registration-contact.jpg" alt="注册在三视角原画的蝴蝶结和金饰金边透明部件"><figcaption>同源原画逐视角注册，右襟原生素材独立归属</figcaption></figure>
<h2>九帧画面对照</h2>
<figure><img src="../p15-115-component-render/component-yaw-contact.jpg" alt="完整服装重组帧对照"><figcaption>完整分层合成与基准对照</figcaption></figure>
<figure><img src="../p15-115-local-patch/localized-garment-contact.jpg" alt="局部覆盖帧对照"><figcaption>原生完整角色画面上的局部纹理替换</figcaption></figure>
<small>结构上已验证原画来源、配准几何和图层归属。跨视角动画的视觉连贯性尚需单独判定，尤其肩部金边和蝴蝶结轮廓。</small>
<script>
const files='''+json.dumps(paths,separators=(',',':'))+''',angles='''+json.dumps(angles)+''';
const method=document.querySelector('#method'),yaw=document.querySelector('#yaw'),frame=document.querySelector('#frame'),loop=document.querySelector('#loop'),label=document.querySelector('#angle');
function update(){let m=method.value,a=String(angles[Number(yaw.value)]);label.textContent=a+'°';frame.src=files[m][a];loop.src=m+'-loop.gif';}
method.addEventListener('change',update);yaw.addEventListener('input',update);
</script></body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
review={'schema':'KOMA_P15_115_COMPONENT_REVIEW_V1','characterId':'p0_character_001',
 'angles':angles,'methodFrames':paths,'animations':gifs,
 'sourceRegistrationSHA256':sha256((R/'evidence/p15-115-source-qa.json').read_bytes()).hexdigest(),
 'entry':str((D/'index.html').relative_to(R)),
 'fullYawVisualApproved':False}
(R/'evidence/p15-115-review-qa.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
print('REVIEW',review['entry'],'methods',len(paths),'frames',len(angles),flush=True)

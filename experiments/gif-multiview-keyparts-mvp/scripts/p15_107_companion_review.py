#!/usr/bin/env python3
"""Native three-source companion garments, full-character visual review and GIFs."""
from pathlib import Path
from PIL import Image
from hashlib import sha256
import os,json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-107-companion-render'
q=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
aud=json.loads((R/'evidence/p15-107-patch-qa.json').read_text())
ref=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
prior=json.loads((R/'evidence/p15-105-render-qa.json').read_text())
angles=q['angles']
sources={
 'P15-101-baseline':{k:v['relativePath'] for k,v in ref['methods']['head_alpha_blend'].items()},
 'P15-105-three_key_direct':{k:v['relativePath'] for k,v in prior['methods']['three_key_direct'].items()}}
sources.update({method:{k:v['relativePath'] for k,v in frames.items()} for method,frames in q['methods'].items()})
frames={};gifs={}
for mode,refs in sources.items():
 frames[mode]={};pics=[]
 for angle in angles:
  k=f'{angle:g}';path=R/refs[k];frames[mode][k]=os.path.relpath(path,D)
  art=Image.open(path).convert('RGBA');white=Image.new('RGBA',art.size,'white');white.alpha_composite(art)
  pics.append(white.convert('RGB').resize((440,440),Image.Resampling.LANCZOS))
 seq=pics+pics[-2:0:-1];f=D/(mode+'-loop.gif')
 seq[0].save(f,save_all=True,append_images=seq[1:],duration=170,loop=0,optimize=False)
 gifs[mode]={'path':str(f.relative_to(R)),'sha256':sha256(f.read_bytes()).hexdigest()}
css="""body{font:15px/1.53 system-ui;background:#162838;color:#f0f4f9;max-width:1460px;margin:13px auto;padding:0 16px}h1{font-size:23px}h2{font-size:18px}p,small{color:#c1cedb}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{margin:0;padding:10px;border-radius:8px;background:#304355}img{display:block;width:100%;object-fit:contain;background:white}figcaption{font-size:12px}label{display:block;margin:10px 0}select,input{width:100%;box-sizing:border-box;padding:8px;margin:6px 0 14px}@media(max-width:680px){.grid{grid-template-columns:1fr}}"""
options=''.join(f'<option value="{method}">{method.replace("_"," ")}</option>' for method in frames)
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 · Consistent Three-View Garment Keyart</title><style>'''+css+'''</style></head><body>
<h1>P0 · 三视角一致服装原画与 VDD 验收</h1>
<p>对 60°、67.5°、75° 三张独立服装原画采用统一角色身份和衣领、蝴蝶结、金色饰件设计。60° 与 75° 由 Codex 内置原画生成工具真实重新绘制；与既有 P15-101 以及 P15-105 方案比较，分别验证保留原画端点与使用整套新服装关键帧两种交付模式。</p>
<label for="method">方法选择</label><select id="method">'''+options+'''</select>
<label for="yaw">角度：<b id="angle">60°</b></label><input id="yaw" type="range" min="0" max="8" step="1" value="0">
<div class="grid">
<figure><img id="frame" src="../p15-101-head-render/head_alpha_blend-yaw60.png" alt="实际逐帧渲染"><figcaption>真实 1024×1024 RGBA 角色动画</figcaption></figure>
<figure><img id="loop" src="P15-101-baseline-loop.gif" alt="当前方法 GIF"><figcaption>九角度往返动画</figcaption></figure></div>
<h2>原画来源</h2>
<figure><img src="../p15-107-source-patches/consistent-garment-contact.jpg" alt="原生60/67.5/75度统一服装设计"><figcaption>原生两张新角色服装及 67.5° 参考图</figcaption></figure>
<h2>完整连续帧视觉对照</h2>
<figure><img src="companion-garment-contact.jpg" alt="各种原画采用模式的逐帧对照"><figcaption>两端像素保真、三视角统一素材、直接融合及光流的画面对照</figcaption></figure>
<small>来源 RGBA、模型原生图片哈希与透明图层结构分别验证。完整角色画面、服装比例、线稿和遮挡质量仍以动画美术验收为准。</small>
<script>
const files='''+json.dumps(frames,separators=(',',':'))+''',angles='''+json.dumps(angles)+''';
const method=document.querySelector('#method'),yaw=document.querySelector('#yaw'),frame=document.querySelector('#frame'),loop=document.querySelector('#loop'),label=document.querySelector('#angle');
function update(){const m=method.value,a=String(angles[Number(yaw.value)]);label.textContent=a+'°';frame.src=files[m][a];loop.src=m+'-loop.gif';}
method.addEventListener('change',update);yaw.addEventListener('input',update);
</script></body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
evidence={'schema':'KOMA_P15_107_COMPANION_REVIEW_V1',
 'renderedAngles':angles,'methods':frames,'animations':gifs,
 'entry':'private-assets/exports/p15-107-companion-render/index.html',
 'allSourcesRegAndOriginalSHA':{view:rec['registeredSHA256'] for view,rec in aud['generatedCompanions'].items()},
 'visualAccepted':False}
(R/'evidence/p15-107-companion-review-qa.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+'\n')
print('REVIEW',evidence['entry'],'methods',len(frames),'frames',len(angles),flush=True)

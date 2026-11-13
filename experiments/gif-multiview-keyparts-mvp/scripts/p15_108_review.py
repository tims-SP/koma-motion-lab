#!/usr/bin/env python3
"""HTML and GIF inspection of real P0 three-view garment stroke correspondence."""
from pathlib import Path
from PIL import Image
from hashlib import sha256
import os,json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-108-stroke-render'
q=json.loads((R/'evidence/p15-108-render-qa.json').read_text())
qaSource=json.loads((R/'evidence/p15-108-source-qa.json').read_text())
native=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
bench=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
angles=q['renderedAngles']
files={
 'P15-101-original':{k:v['relativePath'] for k,v in bench['methods']['head_alpha_blend'].items()},
 'P15-107-native':{k:v['relativePath'] for k,v in native['methods']['companion_direct_native_keys'].items()}}
files.update({name:{k:r['path'] for k,r in frames.items()} for name,frames in q['methods'].items()})
mapping={};animations={}
for name,refs in files.items():
 mapping[name]={};images=[]
 for a in angles:
  k=f'{a:g}';file=R/refs[k]
  mapping[name][k]=os.path.relpath(file,D)
  art=Image.open(file).convert('RGBA')
  white=Image.new('RGBA',art.size,'white');white.alpha_composite(art)
  images.append(white.convert('RGB').resize((450,450),Image.Resampling.LANCZOS))
 sequence=images+images[-2:0:-1]
 gif=D/(name+'-loop.gif')
 sequence[0].save(gif,save_all=True,append_images=sequence[1:],duration=185,loop=0,optimize=False)
 animations[name]={'path':str(gif.relative_to(R)),'sha256':sha256(gif.read_bytes()).hexdigest()}
css="""body{font:15px/1.57 system-ui;background:#18293a;color:#edf3fa;max-width:1450px;padding:0 16px;margin:12px auto}h1{font-size:23px}h2{font-size:18px}p,small{color:#bccddd}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{margin:0;padding:10px;background:#304459;border-radius:7px}figure img{display:block;width:100%;height:auto;object-fit:contain;background:white}figcaption{font-size:12px}label{display:block;margin:12px 0}select,input{box-sizing:border-box;width:100%;padding:8px;margin:6px 0 14px}@media(max-width:700px){.grid{grid-template-columns:1fr}}"""
choices=''.join(f'<option value="{s}">{s.replace("_"," ")}</option>' for s in mapping)
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 · Garment Stroke Roles and Occlusion</title><style>'''+css+'''</style></head><body>
<h1>P0 · 60°–75° 服装笔画身份与分层遮挡验证</h1>
<p>真实服装原画：独立 60°、67.5°、75° 三视角。自动识别蝴蝶结左右褶皱、左右飘带、衣领两侧线稿的六个候选身份，采用有符号距离场对应生成单组墨线并在蝴蝶结／衣领素材区域内绘制；中央金色饰件使用单一前景归属。保留 P15-101 和 P15-107 基准。</p>
<label for="method">渲染方式</label><select id="method">'''+choices+'''</select>
<label for="yaw">角度：<b id="angle">60°</b></label><input id="yaw" type="range" min="0" max="8" value="0" step="1">
<div class="grid">
<figure><img id="frame" src="../p15-101-head-render/head_alpha_blend-yaw60.png" alt="实际角色转头帧"><figcaption>真实 1024×1024 RGBA 动画帧</figcaption></figure>
<figure><img id="loop" src="P15-101-original-loop.gif" alt="双向循环预览"><figcaption>九角度往返动画 GIF</figcaption></figure></div>
<h2>原始素材逐笔画候选与遮挡区域</h2>
<figure><img src="../p15-108-stroke-sources/source-stroke-ownership-contact.jpg" alt="三视角真实原画候选笔画色域和衣领金边"><figcaption>三视角颜色选区与候选线稿提取；身份需进一步确认</figcaption></figure>
<h2>三视角部件源图</h2>
<figure><img src="../p15-107-source-patches/consistent-garment-contact.jpg" alt="三张真实原生服装原画"><figcaption>同一角色的 60°、67.5°、75° 服装来源</figcaption></figure>
<h2>逐帧对照</h2>
<figure><img src="stroke-sdf-occlusion-contact.jpg" alt="不同笔画、遮挡插值方法的逐帧图像"><figcaption>基准、三视角直接合成、距离场笔画与单源蝴蝶结</figcaption></figure>
<small>端点像素保持、层归属及图像交互通过工程检查；自动提取的笔画角色、真实遮挡几何与完整人物转头质量仍按独立艺术门禁判断。</small>
<script>
const frames='''+json.dumps(mapping,separators=(',',':'))+''',angles='''+json.dumps(angles)+''';
const method=document.querySelector('#method'),yaw=document.querySelector('#yaw'),
 frame=document.querySelector('#frame'),loop=document.querySelector('#loop'),label=document.querySelector('#angle');
function update(){const m=method.value,a=String(angles[Number(yaw.value)]);label.textContent=a+'°';frame.src=frames[m][a];loop.src=m+'-loop.gif';}
method.addEventListener('change',update);yaw.addEventListener('input',update);
</script></body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
review={'schema':'KOMA_P15_108_STROKE_OCCLUSION_REVIEW_V1','sourceAngles':[60,67.5,75],
        'renderAngles':angles,'methodFrames':mapping,'gifs':animations,
        'entry':str((D/'index.html').relative_to(R)),
        'automaticStrokeIdentityArtistApproved':False,
        'fullVisualContinuityAccepted':False}
(R/'evidence/p15-108-review-qa.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
print('REVIEW',review['entry'],'methods',len(mapping),'angles',len(angles),flush=True)

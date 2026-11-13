#!/usr/bin/env python3
"""Interactive P0 collar source-registered art and complete garment yaw review."""
from pathlib import Path
from PIL import Image
from hashlib import sha256
import os,json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-114-collar-render'
r=json.loads((R/'evidence/p15-114-render-qa.json').read_text())
s=json.loads((R/'evidence/p15-114-source-qa.json').read_text())
b101=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
b107=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
b113=json.loads((R/'evidence/p15-113-render-qa.json').read_text())
angles=r['renderedAngles']
inputs={
 'P15-101-original':{k:x['relativePath'] for k,x in b101['methods']['head_alpha_blend'].items()},
 'P15-107-native':{k:x['relativePath'] for k,x in b107['methods']['companion_direct_native_keys'].items()},
 'P15-113-unified':{k:x['path'] for k,x in b113['methods']['canonical_full'].items()},
 **{m:{k:x['path'] for k,x in frames.items()} for m,frames in r['methods'].items()}}
files={};loops={}
for mode,frames in inputs.items():
 files[mode]={};images=[]
 for a in angles:
  k=f'{a:g}';fp=R/frames[k]
  files[mode][k]=os.path.relpath(fp,D)
  art=Image.open(fp).convert('RGBA')
  white=Image.new('RGBA',art.size,'white');white.alpha_composite(art)
  images.append(white.convert('RGB').resize((450,450),Image.Resampling.LANCZOS))
 seq=images+images[-2:0:-1]
 gif=D/(mode+'-loop.gif')
 seq[0].save(gif,save_all=True,append_images=seq[1:],duration=180,loop=0,optimize=False)
 loops[mode]={'path':str(gif.relative_to(R)),'sha256':sha256(gif.read_bytes()).hexdigest()}
css="""body{font:15px/1.55 system-ui;background:#172c40;color:#eef5fb;max-width:1480px;margin:14px auto;padding:0 16px}h1{font-size:23px}h2{font-size:18px}p,small{color:#c4d1dd}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{margin:0;padding:10px;background:#32485c;border-radius:8px}img{width:100%;display:block;background:white}figcaption{font-size:12px}label{display:block;margin:10px 0}select,input{width:100%;box-sizing:border-box;margin:7px 0 14px;padding:8px}table{border-collapse:collapse}td,th{padding:7px 10px;border-bottom:1px solid #4d7086}@media(max-width:690px){.grid{grid-template-columns:1fr}}"""
opts=''.join(f'<option value="{k}">{k.replace("_"," ")}</option>' for k in files)
rows=''.join(f'<tr><th>{v}°</th><td>{q["mappedNativeTargetIoU"]:.3f}</td><td>{q["nativeObservedSeamDrift"]["collar.left_inner_edge"]["meanSourceLineDriftPx"]:.2f}px</td><td>{q["nativeObservedSeamDrift"]["collar.right_inner_edge"]["meanSourceLineDriftPx"]:.2f}px</td></tr>' for v,q in s['views'].items())
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 · Collar Source Art Correspondence</title><style>'''+css+'''</style></head><body>
<h1>P0 · 三视角衣领原画与统一笔画对应</h1>
<p>来自真实 67.5° 衣领的单一源纹理与内外折线，在 60° 和 75° 使用原画掩码进行仿射配准。左右衣领折线保持同一源图像素及材质身份；其它服装图层和头发继续使用现有来源。单独对照原生视角、统一衣领形变和全角色实际转头。</p>
<label for="method">真实渲染策略</label><select id="method">'''+opts+'''</select>
<label for="yaw">旋转角度：<b id="angle">60°</b></label><input id="yaw" type="range" min="0" max="8" step="1" value="0">
<div class="grid"><figure><img id="frame" src="../p15-101-head-render/head_alpha_blend-yaw60.png" alt="真实角色渲染帧"><figcaption>1024×1024 RGBA 完整角色</figcaption></figure>
<figure><img id="loop" src="P15-101-original-loop.gif" alt="九角度GIF"><figcaption>九角度双向动画</figcaption></figure></div>
<h2>衣领原画对应结果</h2>
<table><thead><tr><th>角度</th><th>轮廓 IoU</th><th>左侧折线偏差</th><th>右侧折线偏差</th></tr></thead><tbody>'''+rows+'''</tbody></table>
<figure><img src="../p15-114-collar-art/collar-registration-contact.jpg" alt="独立原画与统一衣领图层逐视角对照"><figcaption>真实三视角原画衣领、统一原画投影、原生轮廓约束</figcaption></figure>
<h2>九帧动画对照</h2>
<figure><img src="single-source-collar-yaw-contact.jpg" alt="原画基准与衣领连续变形真实帧"><figcaption>对照源原画、共用拓扑及连续衣领候选</figcaption></figure>
<small>几何配准和原画身份可由测试复现；动画的完整画面质量仍以独立视觉验收结果为准。</small>
<script>
const frames='''+json.dumps(files,separators=(',',':'))+''',angles='''+json.dumps(angles)+''';
const method=document.querySelector('#method'),yaw=document.querySelector('#yaw'),frame=document.querySelector('#frame'),loop=document.querySelector('#loop'),label=document.querySelector('#angle');
function update(){const m=method.value,a=String(angles[Number(yaw.value)]);label.textContent=a+'°';frame.src=frames[m][a];loop.src=m+'-loop.gif';}
method.addEventListener('change',update);yaw.addEventListener('input',update);
</script></body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
review={'schema':'KOMA_P15_114_COLLAR_REVIEW_V1','characterId':'p0_character_001','sourceAngles':[60,67.5,75],
 'renderAngles':angles,'methodFrames':files,'animations':loops,
 'sourceQASHA256':sha256((R/'evidence/p15-114-source-qa.json').read_bytes()).hexdigest(),
 'entry':str((D/'index.html').relative_to(R)),'artistVisualApproved':False}
(R/'evidence/p15-114-review-qa.json').write_text(json.dumps(review,indent=2,ensure_ascii=False)+'\n')
print('REVIEW',review['entry'],'methods',len(files),'angles',len(angles))

#!/usr/bin/env python3
"""Interactive visual review: native garment layers and local flow ablations."""
from pathlib import Path
from PIL import Image
from hashlib import sha256
import os,json
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-103-render'
baseline=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
garment=json.loads((R/'evidence/p15-103-render-qa.json').read_text())
flow=json.loads((R/'evidence/p15-103-flow-qa.json').read_text())
angles=garment['angles']
frameFiles={'P15-101-baseline':{k:os.path.relpath(R/v['relativePath'],D)
                               for k,v in baseline['methods']['head_alpha_blend'].items()}}
for report in (garment,flow):
 for method,frames in report['methods'].items():
  frameFiles[method]={k:os.path.relpath(R/item['relativePath'],D) for k,item in frames.items()}
animations={}
for name,frames in frameFiles.items():
 pictures=[]
 for a in angles:
  rgba=Image.open(D/frames[f'{a:g}']).convert('RGBA')
  white=Image.new('RGBA',rgba.size,'white');white.alpha_composite(rgba)
  pictures.append(white.convert('RGB').resize((450,450),Image.Resampling.LANCZOS))
 frameset=pictures+pictures[-2:0:-1]
 dest=D/(name+'-loop.gif')
 frameset[0].save(dest,save_all=True,append_images=frameset[1:],duration=155,loop=0,optimize=False)
 animations[name]={'path':str(dest.relative_to(R)),'sha256':sha256(dest.read_bytes()).hexdigest()}
css="""body{font:15px/1.55 system-ui;background:#182839;color:#eef3f9;max-width:1510px;margin:14px auto;padding:0 16px}h1{font-size:23px}h2{font-size:18px}p,small{color:#c0d1df}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{margin:0;padding:10px;background:#2b435a;border-radius:8px}img{display:block;width:100%;height:auto;object-fit:contain;background:white}figcaption{font-size:12px}label{display:block;margin:10px 0}select,input{box-sizing:border-box;padding:8px;width:100%;margin:5px 0 12px}@media(max-width:680px){.grid{grid-template-columns:1fr}}"""
opts=''.join(f'<option value="{name}">{name.replace("_"," ")}</option>' for name in frameFiles)
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 · Source Garment ArtMesh Correspondence Review</title><style>'''+css+'''</style></head><body>
<h1>P0 · 60°–75° 衣领／蝴蝶结／饰件／肩线语义对应</h1>
<p>依据原始 P0 原画，为衣领、蝴蝶结、中央金色饰件及肩线建立相同三角拓扑和每视角独立 UV。使用 P15-101 已验证的头部合成作为基准，并比较几何配准、部件单源归属、可见轮廓联合及局部 DIS 光流。两端关键帧保持像素一致，所有结果均为真实渲染。</p>
<label for="method">候选方法</label><select id="method">'''+opts+'''</select>
<label for="yaw">目标角度：<b id="yaw-label">60°</b></label>
<input id="yaw" type="range" min="0" max="8" step="1" value="0">
<div class="grid">
<figure><img id="current" src="../p15-101-head-render/head_alpha_blend-yaw60.png" alt="当前帧"><figcaption>1024 × 1024 实际渲染</figcaption></figure>
<figure><img id="loop" src="P15-101-baseline-loop.gif" alt="当前方法的连续转头"><figcaption>60°–75° 往返循环 GIF</figcaption></figure>
</div>
<h2>独立原画部件</h2>
<div class="grid">
<figure><img src="../p15-103-parts/yaw60/parts-contact.jpg" alt="60度服装分层"><figcaption>60° 原画像素归属与独立部件</figcaption></figure>
<figure><img src="../p15-103-parts/yaw75/parts-contact.jpg" alt="75度服装分层"><figcaption>75° 原画像素归属与独立部件</figcaption></figure></div>
<h2>全角度对照</h2>
<figure><img src="garment-contact.jpg" alt="五种基于网格的服装纹理实验"><figcaption>基于共享 ArtMesh 的纹理/遮挡策略</figcaption></figure>
<figure><img src="bow-flow-contact.jpg" alt="两种局部光流对应实验"><figcaption>语义部件局部 DIS 光流对照</figcaption></figure>
<small>验收区分源图分层重建、网格与 UV 几何正确性、浏览器交互、连续性指标和实际美术质量。分层及虚拟纹理对应仍需美术审核。</small>
<script>
const files='''+json.dumps(frameFiles,separators=(',',':'))+''',angles='''+json.dumps(angles)+''';
const method=document.querySelector('#method'),yaw=document.querySelector('#yaw'),current=document.querySelector('#current'),loop=document.querySelector('#loop'),label=document.querySelector('#yaw-label');
function change(){const m=method.value,a=String(angles[Number(yaw.value)]);label.textContent=a+'°';current.src=files[m][a];loop.src=m+'-loop.gif';}
method.addEventListener('change',change);yaw.addEventListener('input',change);
</script></body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
evidence={'schema':'KOMA_P15_103_REVIEW_V1','frameFiles':frameFiles,'angles':angles,
 'animations':animations,'entry':'private-assets/exports/p15-103-render/index.html',
 'visualAccepted':False}
(R/'evidence/p15-103-review-qa.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+'\n')
print('REVIEW',evidence['entry'],'methods',len(frameFiles),'angles',len(angles),flush=True)

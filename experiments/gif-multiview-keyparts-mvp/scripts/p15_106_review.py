#!/usr/bin/env python3
"""P0 native three-view shared radial garment ArtMesh HTML/GIF review."""
from pathlib import Path
from PIL import Image
from hashlib import sha256
import json,os
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-106-three-key-render'
qaPath=R/'evidence/p15-106-render-qa.json'
qa=json.loads(qaPath.read_text());old=json.loads((R/'evidence/p15-105-render-qa.json').read_text())
original=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
angles=qa['renderAngles']
sources={
 'P15-101-baseline':{k:v['relativePath'] for k,v in original['methods']['head_alpha_blend'].items()},
 'P15-105-direct':{k:v['relativePath'] for k,v in old['methods']['three_key_direct'].items()}}
for method,frames in qa['methods'].items():
 sources[method]={k:rec['path'] for k,rec in frames.items()}
mapping={};gifs={}
for method,files in sources.items():
 mapping[method]={}
 pictures=[]
 for angle in angles:
  key=f'{angle:g}'
  path=R/files[key]
  mapping[method][key]=os.path.relpath(path,D)
  im=Image.open(path).convert('RGBA');bg=Image.new('RGBA',im.size,'white');bg.alpha_composite(im)
  pictures.append(bg.convert('RGB').resize((440,440),Image.Resampling.LANCZOS))
 seq=pictures+pictures[-2:0:-1]
 gif=D/(method+'-loop.gif')
 seq[0].save(gif,save_all=True,append_images=seq[1:],duration=160,loop=0,optimize=False)
 gifs[method]={'path':str(gif.relative_to(R)),'sha256':sha256(gif.read_bytes()).hexdigest()}
css="""body{font:15px/1.5 system-ui;background:#172638;color:#eff4fa;max-width:1450px;margin:14px auto;padding:0 16px}h1{font-size:23px}h2{font-size:18px}p,small{color:#c1d0dc}label{display:block;margin:12px 0}select,input{box-sizing:border-box;width:100%;padding:8px;margin:6px 0 14px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{margin:0;padding:10px;background:#2b4257;border-radius:8px}img{display:block;width:100%;height:auto;object-fit:contain;background:white}figcaption{font-size:12px}@media(max-width:680px){.grid{grid-template-columns:1fr}}"""
options=''.join(f'<option value="{name}">{name.replace("_"," ")}</option>' for name in mapping)
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 · Three-View Shared Garment ArtMesh</title><style>'''+css+'''</style></head><body>
<h1>P0 · 60°–75° 三视角部件对应网格验收</h1>
<p>基于原生 60°、独立生成 67.5°、原生 75° 服装，使用相同的服装中心、轮廓径向控制点、固定三角索引及各视角 UV。对比蝴蝶结／金色饰件共用几何、全部服装部件共用几何及已有两轮连续转头基准。</p>
<label for="method">渲染方法</label><select id="method">'''+options+'''</select>
<label for="yaw">视角：<b id="angle">60°</b></label><input id="yaw" type="range" min="0" max="8" value="0" step="1">
<div class="grid">
<figure><img id="frame" src="../p15-101-head-render/head_alpha_blend-yaw60.png" alt="实际转头帧"><figcaption>1024×1024 原生端点与中间渲染 RGBA</figcaption></figure>
<figure><img id="loop" src="P15-101-baseline-loop.gif" alt="往返转头动画"><figcaption>九角度双向循环 GIF</figcaption></figure></div>
<h2>服装三视角共用 ArtMesh</h2>
<div class="grid">
<figure><img src="../p15-106-three-key-mesh/bow-yaw60.png" alt="60度蝴蝶结网格"><figcaption>60° 源轮廓与金饰中心</figcaption></figure>
<figure><img src="../p15-106-three-key-mesh/bow-yaw67p5.png" alt="67.5度蝴蝶结网格"><figcaption>67.5° 独立原画及对应 UV</figcaption></figure>
<figure><img src="../p15-106-three-key-mesh/bow-yaw75.png" alt="75度蝴蝶结网格"><figcaption>75° 相同拓扑</figcaption></figure>
<figure><img src="../p15-105-middle-art/native-garment-contact.jpg" alt="原生三个服装视角"><figcaption>实际源服装原画对比</figcaption></figure>
</div>
<h2>完整连续性对照</h2>
<figure><img src="three-view-artmesh-contact.jpg" alt="多方法九视角对应画面对照"><figcaption>原有 P15-101、P15-105 与三种共用部件策略</figcaption></figure>
<small>结构验证包括源 RGBA、三视角共同拓扑、网格不翻面、端点像素保真、源关键帧与浏览器交互。艺术质量独立验收，包括领口、肩部、蝴蝶结的纹理和遮挡连续性。</small>
<script>
const frames='''+json.dumps(mapping,separators=(',',':'))+''',angles='''+json.dumps(angles)+''';
const method=document.querySelector('#method'),yaw=document.querySelector('#yaw'),
 frame=document.querySelector('#frame'),loop=document.querySelector('#loop'),label=document.querySelector('#angle');
function change(){const m=method.value,a=String(angles[Number(yaw.value)]);label.textContent=a+'°';frame.src=frames[m][a];loop.src=m+'-loop.gif';}
method.addEventListener('change',change);yaw.addEventListener('input',change);
</script></body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
review={'schema':'KOMA_P15_106_THREE_KEY_REVIEW_V1','sourceAngles':[60,67.5,75],
 'renderAngles':angles,'frameFiles':mapping,'animations':gifs,
 'entry':'private-assets/exports/p15-106-three-key-render/index.html',
 'continuousVisualAccepted':False,'formalArtMeshArtistApproved':False}
(R/'evidence/p15-106-review-qa.json').write_text(json.dumps(review,indent=2,ensure_ascii=False)+'\n')
print('REVIEW',review['entry'],'methods',len(mapping),'angles',len(angles),flush=True)

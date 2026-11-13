#!/usr/bin/env python3
"""P15-112 interactive yaw and moving-occluder proof on actual P0 source art."""
from pathlib import Path
from PIL import Image
import json,os,hashlib
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-112-visibility-vdd'
geo=json.loads((R/'evidence/p15-112-render-qa.json').read_text())
probe=json.loads((R/'evidence/p15-112-reveal-qa.json').read_text())
p101=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
p107=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
p111=json.loads((R/'evidence/p15-111-render-qa.json').read_text())
angles=geo['angles']
models={
 'P15-101-original':{k:v['relativePath'] for k,v in p101['methods']['head_alpha_blend'].items()},
 'P15-107-native':{k:v['relativePath'] for k,v in p107['methods']['companion_direct_native_keys'].items()},
 'P15-111-layered':{k:v['path'] for k,v in p111['methods']['layered_full'].items()},
 **{k:{a:rec['path'] for a,rec in z.items()} for k,z in geo['methods'].items()}
}
frames={};gifs={}
for method,refs in models.items():
 seq=[];frames[method]={}
 for a in angles:
  key=f'{a:g}';path=R/refs[key]
  frames[method][key]=os.path.relpath(path,D)
  rgba=Image.open(path).convert('RGBA')
  white=Image.new('RGBA',rgba.size,'white');white.alpha_composite(rgba)
  seq.append(white.convert('RGB').resize((450,450),Image.Resampling.LANCZOS))
 loop=seq+seq[-2:0:-1]
 f=D/(method+'-loop.gif')
 loop[0].save(f,save_all=True,append_images=loop[1:],duration=185,loop=0,optimize=False)
 gifs[method]={'path':str(f.relative_to(R)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
reveals={}
for view,rec in probe['viewRecords'].items():
 reveals[view]={}
 for pose,items in rec['files'].items():
  reveals[view][pose]={name:os.path.relpath(R/z['path'],D) for name,z in items.items()}
css="""body{font:15px/1.55 system-ui;background:#192d3f;color:#edf3f9;max-width:1480px;margin:14px auto;padding:0 16px}h1{font-size:23px}h2{font-size:18px}p,small{color:#c2cedc}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{margin:0;padding:10px;background:#304659;border-radius:8px}img{display:block;width:100%;background:white}figcaption{font-size:12px}label{display:block;margin:8px 0}select,input{box-sizing:border-box;padding:8px;width:100%;margin:6px 0 12px}.controls{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:15px}@media(max-width:700px){.grid,.controls{grid-template-columns:1fr}}"""
methods=''.join(f'<option value="{name}">{name.replace("_"," ")}</option>' for name in models)
views=''.join(f'<option value="{view}">{view}°</option>' for view in reveals)
poses=''.join(f'<option value="{pose}">{pose.replace("_"," ")}</option>' for pose in probe['poseLabels'])
page='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 · Geometric Visibility and Source Underpaint</title><style>'''+css+'''</style></head><body>
<h1>P0 · 服装几何与隐藏面可见性验证</h1>
<p>三张原生 60°、67.5°、75° 服装原画；四条来源可追溯的蝴蝶结轮廓路径；同一目标形状的前景归属和实际生成的隐藏衣领／金饰下方布料。上方比较实际角色九角度转头，下方独立检验原生像素上移开蝴蝶结或金饰的遮挡揭示。</p>
<h2>一、角色转头连续性</h2>
<label for="method">来源／变形策略</label><select id="method">'''+methods+'''</select>
<label for="yaw">目标角度：<b id="angle">60°</b></label><input id="yaw" type="range" min="0" max="8" value="0" step="1">
<div class="grid">
<figure><img id="frame" src="../p15-101-head-render/head_alpha_blend-yaw60.png" alt="真实1024角色帧"><figcaption>原尺寸完整角色 PNG</figcaption></figure>
<figure><img id="motion" src="P15-101-original-loop.gif" alt="连续往返GIF"><figcaption>九角度双向循环 GIF</figcaption></figure></div>
<h2>二、金饰和蝴蝶结的隐藏面揭示</h2>
<div class="controls">
<div><label for="sourceView">原画视角</label><select id="sourceView">'''+views+'''</select></div>
<div><label for="pose">前景物件偏移</label><select id="pose">'''+poses+'''</select></div>
</div>
<div class="grid">
<figure><img id="revealOff" src="../p15-112-occlusion-probe/yaw60-neutral-source_matte.png" alt="源图遮挡移动后缺失区域"><figcaption>源图前景移动</figcaption></figure>
<figure><img id="revealOn" src="../p15-112-occlusion-probe/yaw60-neutral-with_underpaint.png" alt="源图遮挡移动加隐藏面填充"><figcaption>新增隐藏原画参与合成</figcaption></figure></div>
<h2>三、实际来源与九帧对照</h2>
<figure><img src="../p15-112-occlusion-probe/three-view-occlusion-reveal-contact.jpg" alt="三视角金饰及蝴蝶结遮挡移动对照"><figcaption>原画纹理、背景与隐藏面两种结果对照</figcaption></figure>
<figure><img src="visibility-geometry-contact.jpg" alt="来源ArtMesh与完整转头逐帧对照"><figcaption>前景几何、单墨线归属和基准原画的完整转头对照</figcaption></figure>
<small>原生图层、来源归属、像素遮挡覆盖和几何非翻折有机器验收。隐藏面仍是按可见画面推断的原画；转头的美术质量需单独通过。</small>
<script>
const frames='''+json.dumps(frames,separators=(',',':'))+''',angles='''+json.dumps(angles)+''',reveals='''+json.dumps(reveals,separators=(',',':'))+''';
const method=document.querySelector('#method'),yaw=document.querySelector('#yaw'),frame=document.querySelector('#frame'),motion=document.querySelector('#motion'),angle=document.querySelector('#angle'),sourceView=document.querySelector('#sourceView'),pose=document.querySelector('#pose'),off=document.querySelector('#revealOff'),on=document.querySelector('#revealOn');
function updateYaw(){let m=method.value,a=String(angles[Number(yaw.value)]);angle.textContent=a+'°';frame.src=frames[m][a];motion.src=m+'-loop.gif';}
function updateReveal(){const v=sourceView.value,p=pose.value;off.src=reveals[v][p].source_matte;on.src=reveals[v][p].with_underpaint;}
method.addEventListener('change',updateYaw);yaw.addEventListener('input',updateYaw);
sourceView.addEventListener('change',updateReveal);pose.addEventListener('change',updateReveal);
</script></body></html>'''
(D/'index.html').write_text(page,encoding='utf-8')
review={'schema':'KOMA_P15_112_GEOMETRY_OCCLUSION_REVIEW_V1',
 'entry':str((D/'index.html').relative_to(R)),
 'angles':angles,'renderMethods':frames,'animations':gifs,
 'revealSourceViews':['60','67.5','75'],'revealPoses':probe['poseLabels'],
 'revealImageSources':reveals,
 'artistCorrespondenceAccepted':False,'fullYawVisualAccepted':False}
(R/'evidence/p15-112-review-qa.json').write_text(json.dumps(review,indent=2,ensure_ascii=False)+'\n')
print('REVIEW',review['entry'],'methods',len(frames),'reveal combinations',sum(len(x) for x in reveals.values()),flush=True)

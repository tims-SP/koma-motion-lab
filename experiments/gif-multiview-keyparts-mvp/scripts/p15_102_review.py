#!/usr/bin/env python3
"""P0 source-owned head/neck/eye and emblem correspondence interactive review."""
from pathlib import Path
from PIL import Image
from hashlib import sha256
import json,os
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-102-neck-eye-profile';D.mkdir(parents=True,exist_ok=True)
p1=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
p2=json.loads((R/'evidence/p15-102-render-qa.json').read_text())
p3=json.loads((R/'evidence/p15-102-jewel-qa.json').read_text())
angles=p2['angles']
allMethods={'baseline_head':{k:os.path.relpath(R/v['relativePath'],D) for k,v in p1['methods']['head_alpha_blend'].items()}}
allMethods.update({m:{k:os.path.relpath(R/v['relativePath'],D) for k,v in vals.items()} for m,vals in p2['methods'].items()})
allMethods.update({m:{k:os.path.relpath(R/v['relativePath'],D) for k,v in vals.items()} for m,vals in p3['methods'].items()})
assert len(allMethods)==8
animations={}
for method,frames in allMethods.items():
 images=[]
 for angle in angles:
  img=Image.open((D/frames[f'{angle:g}']).resolve()).convert('RGBA')
  bg=Image.new('RGBA',img.size,'white');bg.alpha_composite(img)
  images.append(bg.convert('RGB').resize((430,430),Image.Resampling.LANCZOS))
 seq=images+images[-2:0:-1]
 out=D/f'{method}-loop.gif'
 seq[0].save(out,save_all=True,append_images=seq[1:],duration=160,loop=0,optimize=False)
 animations[method]={'path':str(out.relative_to(R)),'sha256':sha256(out.read_bytes()).hexdigest()}
css="""body{font:15px/1.55 system-ui;background:#162637;color:#edf3fb;max-width:1480px;margin:15px auto;padding:0 16px}h1{font-size:23px}h2{font-size:18px}p,small{color:#becfde}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{margin:0;padding:10px;border-radius:8px;background:#293e57}img{display:block;width:100%;height:auto;object-fit:contain;background:white}figcaption{font-size:12px}label{display:block;margin:12px 0}select,input{box-sizing:border-box;width:100%;padding:8px;margin:6px 0 13px}@media(max-width:710px){.grid{grid-template-columns:1fr}}"""
opts=''.join(f'<option value="{m}">{m.replace("_"," ")}</option>' for m in allMethods)
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 · Neck / Eye / Nose / Garment Correspondence</title><style>'''+css+'''</style></head><body>
<h1>P0 · 60°–75° 颈肩、眼部、鼻侧和服装对应研究</h1>
<p>将 P15-101 共用头部网格与颈肩网格、源像素眼部遮挡、鼻侧轮廓和真实金色饰件配准进行对照。所有两端关键原画像素一致。中间角度为几何、纹理和可见性研究候选，连续视觉质量仍需审核。</p>
<label for="method">方案选择</label><select id="method">'''+opts+'''</select>
<label for="yaw">角度：<b id="angle">60°</b></label><input id="yaw" type="range" min="0" max="8" step="1" value="0">
<div class="grid">
<figure><img id="frame" src="../p15-101-head-render/head_alpha_blend-yaw60.png" alt="当前真实候选渲染"><figcaption>原尺寸 1024×1024 RGBA 帧</figcaption></figure>
<figure><img id="motion" src="baseline_head-loop.gif" alt="动态转头循环"><figcaption>同步角度的实际 GIF</figcaption></figure></div>
<h2>颈肩视角对应网格</h2><div class="grid">
<figure><img src="../p15-102-neck-shoulder-mesh/mesh-yaw60.png" alt="60度颈肩网格"><figcaption>60° 领口／肩线／胸饰锚点</figcaption></figure>
<figure><img src="../p15-102-neck-shoulder-mesh/mesh-yaw75.png" alt="75度颈肩网格"><figcaption>75° 同拓扑与独立源 UV</figcaption></figure></div>
<h2>运动与纹理归属对照</h2>
<figure><img src="neck-eye-profile-contact.jpg" alt="基准和颈肩、眼部、鼻侧组合实验"><figcaption>颈肩、眼睛和鼻侧遮挡对照</figcaption></figure>
<figure><img src="jewel-ownership-contact.jpg" alt="蝴蝶结金色饰件独立来源对应"><figcaption>实际金色饰件归属和颈肩位移对照</figcaption></figure>
<small>工程层面分别校验三角形索引、UV 范围、来源像素、逐帧输出和浏览器交互。视觉结论独立于上述验证。</small>
<script>
const frames='''+json.dumps(allMethods,separators=(',',':'))+''',angles='''+json.dumps(angles)+''';
const method=document.querySelector('#method'),yaw=document.querySelector('#yaw'),frame=document.querySelector('#frame'),motion=document.querySelector('#motion'),angle=document.querySelector('#angle');
function update(){const m=method.value,a=String(angles[Number(yaw.value)]);angle.textContent=a+'°';frame.src=frames[m][a];motion.src=m+'-loop.gif';}
method.addEventListener('change',update);yaw.addEventListener('input',update);
</script></body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
summary={'schema':'KOMA_P15_102_INTERACTIVE_REVIEW_V1','angles':angles,'methods':allMethods,
 'animations':animations,'entry':'private-assets/exports/p15-102-neck-eye-profile/index.html',
 'continuousVisualAccepted':False}
(R/'evidence/p15-102-review-qa.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
print('REVIEW',summary['entry'],'methods',len(allMethods),'angles',len(angles),flush=True)

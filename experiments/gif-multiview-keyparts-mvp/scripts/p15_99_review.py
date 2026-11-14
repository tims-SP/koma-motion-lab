#!/usr/bin/env python3
"""P0 semantic topology cross-view research: GIF, HTML and provenance."""
from pathlib import Path
from PIL import Image
import json,hashlib
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports'
D=P/'p15-99-vdd-review'
qa=json.loads((R/'evidence/p15-99-topology-vdd-qa.json').read_text())
angles=qa['angles'];methods=list(qa['methods'])
for method in methods:
 frames=[]
 for angle in angles:
  fp=R/qa['methods'][method][f'{angle:g}']['file']
  assert fp.is_file(),fp
  art=Image.open(fp).convert('RGBA')
  bg=Image.new('RGBA',art.size,'white');bg.alpha_composite(art)
  frames.append(bg.convert('RGB').crop((405,245,845,685)).resize((480,480),Image.Resampling.LANCZOS))
 anim=frames+frames[-2:0:-1]
 dest=D/(method+'-yaw-motion.gif')
 anim[0].save(dest,save_all=True,append_images=anim[1:],duration=145,loop=0,optimize=False)
 qa.setdefault('animations',{})[method]={'path':str(dest.relative_to(R)),
     'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
css="""body{font:15px/1.55 system-ui;background:#152637;color:#edf5fb;max-width:1500px;margin:14px auto;padding:0 15px}h1{font-size:23px}h2{font-size:18px}p,small{color:#bfcedd}label{display:block;margin:10px 0}select,input{width:100%;box-sizing:border-box;margin:5px 0 12px;padding:8px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{margin:0;background:#293e55;padding:10px;border-radius:8px}figure img{width:100%;height:auto;object-fit:contain;background:white}figcaption{font-size:12px}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:8px;border-bottom:1px solid #344b61}@media(max-width:690px){.grid{grid-template-columns:1fr}}"""
options=''.join(f'<option value="{m}">{m.replace("_"," ")}</option>' for m in methods)
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 · 跨视角语义拓扑与遮挡层</title><style>'''+css+'''</style></head><body>
<h1>P0 · 60°–75° 语义部件拓扑与连续转头研究</h1>
<p>真实 SAM3 近眼／远眼及前景头发蒙版、独立原画、隐藏脸部底图和视觉锚点构成明确分层。两端角色原画逐像素保真；中间角度是连续视角研究候选，并非已签收的高质量动画。</p>
<label for="method">跨视角合成策略</label><select id="method">'''+options+'''</select>
<label for="yaw">镜头目标角度：<b id="yaw-label">60°</b></label><input id="yaw" type="range" min="0" max="8" step="1" value="0">
<div class="grid">
<figure><img id="current" src="topology_nearest-yaw60.png" alt="实际跨视角输出"><figcaption>当前角度实际渲染帧</figcaption></figure>
<figure><img id="animated" src="topology_nearest-yaw-motion.gif" alt="当前策略的往返动画"><figcaption>连续往返预览</figcaption></figure>
</div>
<h2>四种合成策略的视觉对照</h2><figure><img src="topology-vdd-contact.jpg" alt="语义深度和眼部遮挡处理的连续帧对照"><figcaption>分层重建与多视角重投影对照</figcaption></figure>
<h2>源原画分层检查</h2><div class="grid">
<figure><img src="../p15-99-topology/yaw60/topology-contact.jpg" alt="60°语义原画拆分"><figcaption>60°：近眼、远眼、轮廓和前景头发</figcaption></figure>
<figure><img src="../p15-99-topology/yaw75/topology-contact.jpg" alt="75°语义原画拆分"><figcaption>75°：近眼可见、远眼遮挡与前景头发</figcaption></figure>
</div>
<small>源蒙版含 SAM3 模型结果和可重复生成的手工视觉几何代理。角色身份在各独立源视角保真；完整 ArtMesh 拓扑和连续视觉质量须进一步审核。</small>
<script>
const methods='''+json.dumps(methods)+''',angles='''+json.dumps(angles)+''';
const method=document.querySelector('#method'),yaw=document.querySelector('#yaw'),
current=document.querySelector('#current'),animated=document.querySelector('#animated'),label=document.querySelector('#yaw-label');
function update(){const m=method.value,a=angles[Number(yaw.value)];label.textContent=a+'°';current.src=m+'-yaw'+String(a).replace('.','p')+'.png';animated.src=m+'-yaw-motion.gif';}
method.addEventListener('change',update);yaw.addEventListener('input',update);
</script></body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
qa['reviewPage']='private-assets/exports/p15-99-vdd-review/index.html'
(R/'evidence/p15-99-topology-vdd-qa.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')
print('P15-99 HTML',D/'index.html','methods',len(methods),'angles',len(angles))

#!/usr/bin/env python3
"""Build an offline P15-27 review, retaining source full-frame baseline."""
from pathlib import Path
import hashlib,json,shutil,zipfile
R=Path(__file__).resolve().parent.parent;P=R/'private-assets'
Q=json.loads((R/'evidence/p15-27-occlusion-audit.json').read_text())
O=P/'exports/p15-27-occlusion-review';O.mkdir(parents=True,exist_ok=True)
data=[]
for f in Q['frames']:
 angle=f['yaw'];n='yaw'+(str(int(angle)) if angle%1==0 else str(angle).replace('.','p'))
 d=O/n;d.mkdir(exist_ok=True)
 files={}
 for k,v in f['paths'].items():
  src=P/v['path'];target=d/(k+'.png')
  shutil.copy2(src,target);files[k]=n+'/'+target.name
 base=P/'p15-21-layered-anatomy'/(n+'.png')
 shutil.copy2(base,d/'p15-21-baseline.png')
 files['baseline']=n+'/p15-21-baseline.png'
 data.append({'yaw':angle,'files':files,'metrics':f['metrics']})
shutil.copy2(R/'evidence/p15-27-occlusion-audit.json',O/'qa.json')
html='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-27 远眼和发夹遮挡</title>
<style>
body{margin:0;background:#151b25;color:#eff3fb;padding:16px;font:15px system-ui}
main{max-width:1280px;margin:auto}h1{font-size:24px}.desc{line-height:1.55;color:#bdc8d7}.warn{color:#efc086}
select{padding:9px;border-radius:6px;background:#2c394b;color:white;border:1px solid #6a7b90}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
.card{background:#212d3c;padding:9px;border:1px solid #435267;border-radius:8px;min-width:0}
img{width:100%;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#4a5767 0 25%,#293643 0 50%) 50%/24px 24px}
small{color:#b1c2d5} .metrics{font-variant-numeric:tabular-nums}
@media(max-width:950px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:550px){.grid{grid-template-columns:1fr}}
</style><main><h1>P15-27 · 远眼遮挡与发夹附着审查</h1>
<p class="desc">使用原始 P15-21 图层计算逐像素覆盖：远眼原画 = 可见部分 + 被刘海/鼻部覆盖的原画。未把远眼整体降低透明度冒充几何遮挡，也未修改正式 VDD。</p>
<p class="warn">这些图层是算法分解结果，不等于已经绘制新隐藏原画；发夹覆盖刘海不代表确定其物理侧正确。</p>
<label>视角 <select id="angle"></select></label><p id="metric" class="metrics"></p>
<div class="grid" id="grid"></div>
</main><script>
const D=__DATA__,sel=document.querySelector('#angle'),grid=document.querySelector('#grid');
const K=[['baseline','完整 P15-21 基线'],['eye-underpaint-original','远眼完整原画（保留隐藏像素）'],
['eye-visible','远眼实际可见'],['eye-hidden-paint','被遮挡远眼像素'],
['eye-occluder-bangs','刘海遮挡交集'],['eye-occluder-nose','鼻部遮挡交集'],
['clip-over-hair','发夹与刘海/侧发重叠'],['clip-unmounted','发夹不与头发重叠部分']];
D.forEach((v,i)=>{let o=document.createElement('option');o.value=i;o.textContent=v.yaw+'°';sel.append(o)});
function render(){const v=D[Number(sel.value)],m=v.metrics;grid.replaceChildren();
for(const [key,title] of K){const section=document.createElement('section'),h=document.createElement('h3'),img=document.createElement('img');section.className='card';h.textContent=title;img.src=v.files[key];img.alt=title;section.append(h,img);grid.append(section)}
document.querySelector('#metric').textContent='远眼可见占原图 Alpha：'+(100*m.visibleEyeFraction).toFixed(2)+'% · 发夹与头发重叠：'+(100*m.clipMountCoverageFraction).toFixed(2)+'%';}
sel.onchange=render;render()</script></html>'''
(O/'index.html').write_text(html.replace('__DATA__',json.dumps(data,ensure_ascii=False)))
Z=P/'exports/p15-27-occlusion-review.zip'
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for file in sorted(O.rglob('*')):
  if file.is_file():z.write(file,file.relative_to(O))
with zipfile.ZipFile(Z) as z:assert z.testzip() is None;files=len(z.namelist())
print(json.dumps({'entries':files,'bytes':Z.stat().st_size,'sha256':hashlib.sha256(Z.read_bytes()).hexdigest()}))

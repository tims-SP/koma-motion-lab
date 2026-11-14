#!/usr/bin/env python3
"""Build P15-23 review for model-generated source component cutouts."""
import hashlib,json,shutil,zipfile
from pathlib import Path
R=Path(__file__).resolve().parent.parent
P=R/'private-assets'
Q=json.loads((R/'evidence/p15-23-model-generated-keypart-qa.json').read_text())
OUT=P/'exports/p15-23-model-keyparts-review'
OUT.mkdir(parents=True,exist_ok=True)
rows=[]
for part in Q['parts']:
 slug=part['role'].replace('.','-')
 dest=OUT/slug
 dest.mkdir(exist_ok=True)
 files={}
 for mode,key in [('source','source'),('isolated','isolated'),('registered','registered')]:
  src=P/part[key];target=dest/(mode+src.suffix)
  shutil.copy2(src,target)
  files[mode]=str(target.relative_to(OUT))
 rows.append({'role':part['role'],'files':files,'alphaIoUWithVDD':part['alphaIoUWithVDD'],
  'sourceBoundingBox':part['sourceBBox'],'registeredBoundingBox':part['registeredTargetBBox'],
  'nontransparentPixels':part['nontransparentPixels']})
comp=OUT/'diagnostic-composite.png'
shutil.copy2(P/Q['diagnosticComposite'],comp)
base=OUT/'p15-21-baseline.png'
shutil.copy2(P/'p15-21-layered-anatomy/yaw60.png',base)
alt=P/'p15-23-hf-independent-parts/clip-flux-isolated-raw.webp'
if alt.is_file():shutil.copy2(alt,OUT/'clip-alternate-flux.webp')
shutil.copy2(R/'evidence/p15-23-model-generated-keypart-qa.json',OUT/'qa.json')
html='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>P15-23 · 新生成部件原画提取候选</title>
<style>body{font:15px system-ui;margin:0;padding:18px;background:#171c26;color:#eaf0f7}main{max-width:1320px;margin:auto}
h1{font-size:24px}.warn{color:#efbf8f}.desc{color:#b4c0ce;line-height:1.55}
.panel{padding:12px;background:#242d3b;border:1px solid #435266;border-radius:10px;min-width:0}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.two{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
img{width:100%;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#4b5767 0 25%,#2d3745 0 50%) 50%/24px 24px}
select{padding:9px;border-radius:6px;color:white;background:#263545;border:1px solid #5b6d80}small{color:#b8c5d5}
@media(max-width:750px){.grid,.two{grid-template-columns:1fr}}
</style><main><h1>P15-23 · 新模型图像 → 部件 RGBA 候选</h1>
<p class="warn">模型未严格遵循“一张图一个部件”，实际输出中带有完整头部/面部。这里使用新生成图的像素颜色和轮廓，按 P15-21 定位框缩放平移，仅供候选审查。没有通过角色身份、独立原画或隐藏补绘验收。</p>
<label>角色 <select id="role"></select></label><p class="desc" id="metric"></p>
<section id="compare" class="grid"></section>
<h2>60° 整体画面对照</h2><section class="two">
<div class="panel"><h3>P15-21 原始 VDD 工程基线</h3><img src="p15-21-baseline.png" alt="baseline"/></div>
<div class="panel"><h3>替换 4 个新候选部件后的实验画面</h3><img src="diagnostic-composite.png" alt="experimental candidate"/></div>
</section></main><script>
const data=__DATA__,sel=document.getElementById('role'),compare=document.getElementById('compare');
data.forEach((x,i)=>{const op=document.createElement('option');op.value=i;op.textContent=x.role;sel.append(op)});
function render(){const p=data[Number(sel.value)];compare.replaceChildren();
for(const [key,label] of [['source','模型原图（有背景）'],['isolated','模型颜色/独立像素轮廓'],['registered','定位至 60° ArtMesh']]){
 const d=document.createElement('article');d.className='panel';const h=document.createElement('h3'),im=document.createElement('img');
 h.textContent=label;im.src=p.files[key];im.alt=p.role+' '+key;d.append(h,im);compare.append(d)}
document.getElementById('metric').textContent='独立提取轮廓与原 VDD Alpha IoU: '+p.alphaIoUWithVDD+
'; 独立可见像素 '+p.nontransparentPixels+'；原图头部/面部混入：未通过。'}
sel.onchange=render;render();</script></html>'''
(OUT/'index.html').write_text(html.replace('__DATA__',json.dumps(rows,ensure_ascii=False)))
ZIP=P/'exports/p15-23-model-keyparts-review.zip'
with zipfile.ZipFile(ZIP,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in sorted(OUT.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(OUT))
with zipfile.ZipFile(ZIP) as z:
 assert z.testzip() is None;n=len(z.namelist())
print(json.dumps({'files':n,'bytes':ZIP.stat().st_size,'sha256':hashlib.sha256(ZIP.read_bytes()).hexdigest()},ensure_ascii=False))

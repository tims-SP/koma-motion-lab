#!/usr/bin/env python3
"""P15-24 P0 guided gold-cross-clip: offline HTML art QA."""
from pathlib import Path
import hashlib,json,zipfile,shutil
R=Path(__file__).resolve().parent.parent
P=R/'private-assets'
Q=json.loads((R/'evidence/p15-24-vector-cross-clip-qa.json').read_text())
D=P/'exports/p15-24-cross-clip-review'
D.mkdir(parents=True,exist_ok=True)
source=P/'p15-20-canonical-source-views/yaw045/hair.clip.cross_gold.png'
shutil.copy2(source,D/'p0-original-clip-45.png')
rows=[]
for frame in Q['results']:
 a=frame['angle'];slug='yaw'+(str(int(a)) if a%1==0 else str(a).replace('.','p'))
 folder=D/slug;folder.mkdir(exist_ok=True)
 f=P/frame['path'];dest=folder/'new-paint-clip.png';shutil.copy2(f,dest)
 b=P/frame['diagnostic'];shutil.copy2(b,folder/'candidate-composite.png')
 source=P/'p15-21-layered-anatomy'/(slug+'.png')
 shutil.copy2(source,folder/'original-vdd-frame.png')
 orig=P/'p15-21-intermediate-components'/slug/'hair.clip.cross_gold.png'
 shutil.copy2(orig,folder/'original-vdd-clip.png')
 rows.append({'angle':a,'clip':'%s/new-paint-clip.png'%slug,'source':'%s/original-vdd-clip.png'%slug,
  'candidate':'%s/candidate-composite.png'%slug,'baseline':'%s/original-vdd-frame.png'%slug,
  'iou':frame['clipAlphaIoUWithVDD']})
shutil.copy2(R/'evidence/p15-24-vector-cross-clip-qa.json',D/'qa.json')
html='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-24 · 金色交叉发夹五角度原画对照</title>
<style>
body{background:#161c26;color:#edf3f8;font:15px system-ui;padding:20px;margin:0}main{max-width:1300px;margin:auto}
.note{color:#b6c3d2;line-height:1.6}.warn{color:#e8bd86}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.box{border:1px solid #425268;background:#222c3a;border-radius:9px;padding:10px;min-width:0}
.box img{width:100%;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#4c5766 0 25%,#2c3644 0 50%) 50%/25px 25px}
.small{max-width:250px}select{padding:9px;border:1px solid #728296;border-radius:7px;background:#2c3a4c;color:white}
@media(max-width:700px){.grid{grid-template-columns:1fr}body{padding:12px}}
</style><main><h1>P15-24 · P0 发夹参考 / 新笔画</h1>
<p class="warn">这是参考 P0 原始发夹配色与交叉方向、新程序化绘制的 60° 附近透明资产。Qwen 图像编辑配额不足，未完成模型参考图生成。艺术验收和隐藏补绘尚未通过。</p>
<p class="note">左上保留原 VDD 全画面，右上是替换单个金色发夹后的诊断对照；下方可比较旧发夹与新透明像素图。所有其它部件均沿用 P15-21。</p>
<label>视角 <select id="angle"></select></label><p id="metrics"></p>
<div class="grid" id="grid"></div><h2>P0 45° 发夹身份参考</h2><div class="box small"><img src="p0-original-clip-45.png" alt="canonical 45 gold clip"/></div>
</main><script>
const data=__DATA__,selector=document.getElementById('angle'),grid=document.getElementById('grid');
data.forEach((x,i)=>{const o=document.createElement('option');o.value=i;o.textContent=x.angle+'°';selector.append(o)});
function render(){const x=data[Number(selector.value)];grid.replaceChildren();
for(const [name,url] of [['原始 VDD 基准',x.baseline],['更换新发夹后的对照',x.candidate],['旧发夹透明图',x.source],['新绘制发夹透明图',x.clip]]){
 const div=document.createElement('section'),h=document.createElement('h3'),img=document.createElement('img');div.className='box';h.textContent=name;img.src=url;img.alt=name;div.append(h,img);grid.append(div)}
document.getElementById('metrics').textContent='新旧发夹 Alpha IoU：'+x.iou+'；这是差异而不是艺术质量分数。'}
selector.onchange=render;render();
</script>'''
(D/'index.html').write_text(html.replace('__DATA__',json.dumps(rows,ensure_ascii=False)))
Z=P/'exports/p15-24-cross-clip-review.zip'
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in sorted(D.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(D))
with zipfile.ZipFile(Z) as z:assert z.testzip() is None;count=len(z.namelist())
print(json.dumps({'entries':count,'bytes':Z.stat().st_size,'sha256':hashlib.sha256(Z.read_bytes()).hexdigest()}))

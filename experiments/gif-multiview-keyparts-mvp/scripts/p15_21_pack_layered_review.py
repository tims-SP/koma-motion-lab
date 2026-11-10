#!/usr/bin/env python3
"""Produce standalone editable P15-21 review (source-derived, not new painting)."""
import hashlib,json,shutil,zipfile
from pathlib import Path
R=Path(__file__).resolve().parent.parent
A=R/'private-assets'
QA=R/'evidence/p15-21-intermediate-components-qa.json'
OUT=A/'exports/p15-21-layered-review'
D=json.loads(QA.read_text())
OUT.mkdir(parents=True,exist_ok=True)
frames=[]
for frame in D['frames']:
 yaw=frame['yaw']
 slug='yaw'+(str(int(yaw)) if float(yaw).is_integer() else str(yaw).replace('.','p'))
 folder=OUT/slug
 folder.mkdir(exist_ok=True)
 roles=[]
 for role in frame['roles']:
  src=A/role['path']
  dest=folder/(role['role']+'.png')
  shutil.copy2(src,dest)
  roles.append({'role':role['role'],'image':str(dest.relative_to(OUT)),
    'visiblePixels':role['visiblePixels'],
    'sourceStatus':role['sourceStatus'],
    'coveredPixels':frame['hiddenOccludedPixelInstances'][role['role']]})
 original=A/frame['whole']
 dest=folder/'whole.png';shutil.copy2(original,dest)
 frames.append({'yaw':yaw,'roles':roles,'whole':str(dest.relative_to(OUT)),
  'exactRoundtrip':frame['nativeRoundtripMaxPixelDelta']==0})
shutil.copy2(QA,OUT/'source-qa.json')
html='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>P15-21 · 五视角 ArtMesh 透明分层</title>
<style>
body{margin:0;padding:18px;background:#151923;color:#e6edf5;font:15px system-ui}
main{max-width:1300px;margin:auto}h1{font-size:24px}.note{color:#bac5d3;line-height:1.5}
.controls{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:12px 0}
select,button{border:1px solid #667486;background:#263444;color:#edf3fa;padding:9px;border-radius:6px}
.columns{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr) 290px;gap:12px}
.panel{background:#202a36;border:1px solid #3b495c;border-radius:9px;padding:10px;min-width:0}
.panel h2{font-size:17px}.stage{position:relative;width:100%;aspect-ratio:1;background:repeating-conic-gradient(#485360 0 25%,#28313b 0 50%) 50%/22px 22px;overflow:hidden}
.stage img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain}.stage.single img{position:static}
#layers{max-height:66vh;overflow:auto}#layers label{display:flex;gap:7px;align-items:center;padding:7px 0;border-bottom:1px solid #3f4b5b;font-size:12px}
#layers small{color:#b7c4d1}#warning{color:#e8c38a}
@media(max-width:1000px){.columns{grid-template-columns:1fr 1fr}.panel:nth-child(3){grid-column:span 2}}
@media(max-width:600px){.columns{grid-template-columns:1fr}.panel:nth-child(3){grid-column:auto}}
</style><main><h1>P15-21 · 原始 ArtMesh 形变部件</h1>
<p class="note">五个角度，每角度 13 个透明 PNG。左侧按深度合成，右侧为 P12 原始整帧。勾选任意部件查看遮挡关系；透明槽表示当前视角该部件不可见。<strong>这些是原画变形部件，不是独立补绘原画。</strong></p>
<div class="controls"><label>角度 <select id="yaw"></select></label>
<button id="all">全部显示</button><button id="none">隐藏全部</button>
<span id="warning"></span></div>
<div class="columns"><section class="panel"><h2>透明 ArtMesh 分层</h2><div class="stage" id="composed"></div></section>
<section class="panel"><h2>未经修改的 P12 基准</h2><div class="stage single"><img id="source" alt="baseline VDD frame"/></div></section>
<section class="panel"><h2>13 个部件</h2><div id="layers"></div></section></div>
</main><script>
const DATA=__DATA__;
const picker=document.querySelector('#yaw'),layers=document.querySelector('#layers'),view=document.querySelector('#composed'),source=document.querySelector('#source');
DATA.forEach((x,i)=>{let o=document.createElement('option');o.value=i;o.textContent=x.yaw+'°';picker.append(o)});
let controls=[];
function redraw(){const f=DATA[Number(picker.value)];source.src=f.whole;view.replaceChildren();layers.replaceChildren();controls=[];
 for(const r of f.roles){const img=document.createElement('img');img.src=r.image;img.alt=r.role;view.append(img);
 const line=document.createElement('label'),checkbox=document.createElement('input'),txt=document.createElement('span');
 checkbox.type='checkbox';checkbox.checked=true;checkbox.addEventListener('change',()=>img.style.display=checkbox.checked?'block':'none');
 txt.textContent=r.role+' · '+r.visiblePixels+' px · 遮挡候选 '+r.coveredPixels+' px';
 line.append(checkbox,txt);layers.append(line);controls.push({checkbox,img});}
 document.querySelector('#warning').textContent=f.exactRoundtrip?'原生分层重组：像素完全一致':'重组不一致';}
picker.addEventListener('change',redraw);
document.querySelector('#all').onclick=()=>controls.forEach(({checkbox,img})=>{checkbox.checked=true;img.style.display='block'});
document.querySelector('#none').onclick=()=>controls.forEach(({checkbox,img})=>{checkbox.checked=false;img.style.display='none'});
redraw();
</script></html>'''
(OUT/'index.html').write_text(html.replace('__DATA__',json.dumps(frames,ensure_ascii=False)))
ZIP=A/'exports/p15-21-layered-review.zip'
with zipfile.ZipFile(ZIP,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in sorted(OUT.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(OUT))
with zipfile.ZipFile(ZIP) as z:
 assert z.testzip() is None
 count=len(z.namelist())
print(json.dumps({'zip':str(ZIP),'size':ZIP.stat().st_size,'entries':count,
 'sha256':hashlib.sha256(ZIP.read_bytes()).hexdigest(),
 'frames':len(frames),'perFrameRoles':[len(x['roles']) for x in frames]},ensure_ascii=False))

#!/usr/bin/env python3
"""Bundle the existing independent-paint RGB candidates and derived-alpha parts."""
from pathlib import Path
import hashlib,json,shutil,zipfile
R=Path(__file__).resolve().parent.parent
P=R/'private-assets'
QA=R/'evidence/p15-22-painted-rgb-candidate-qa.json'
D=json.loads(QA.read_text())
OUT=P/'exports/p15-22-painted-rgb-review'
OUT.mkdir(parents=True,exist_ok=True)
views=[]
for view in D['views']:
 angle=view['yaw']
 slug='yaw57p5' if angle==57.5 else 'yaw60'
 target=OUT/slug
 target.mkdir(exist_ok=True)
 files={}
 for key,src in [('independent-source',view['sourceImage']),('derived-composite',view['compositePath'])]:
  dest=target/(key+'.png');shutil.copy2(P/src,dest);files[key]=str(dest.relative_to(OUT))
 baseline=P/'p15-21-layered-anatomy'/('yaw57p5.png' if angle==57.5 else 'yaw60.png')
 dest=target/'baseline-vdd.png';shutil.copy2(baseline,dest);files['baseline']=str(dest.relative_to(OUT))
 roles=[]
 for row in view['roles']:
  src=P/row['path'];dest=target/(row['role']+'.png');shutil.copy2(src,dest)
  roles.append({'role':row['role'],'src':str(dest.relative_to(OUT)),
     'paintRisk':row['whiteBackgroundRiskRatio'],'pixels':row['visiblePixels'],
     'independentColor':row['independentRgb'],'independentGeometry':row['independentSilhouette']})
 views.append({'yaw':angle,'files':files,'roles':roles,
  'overlap':view['sourceForegroundIoUWithSourceDerivedAlpha'],
  'keyRisks':view['keyRoleRisks']})
(OUT/'qa.json').write_text(json.dumps(D,ensure_ascii=False,indent=2)+'\n')
html='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-22 独立绘画颜色分层候选</title>
<style>body{background:#161c27;color:#f0f5fb;margin:0;padding:16px;font:15px system-ui}main{max-width:1300px;margin:auto}h1{font-size:25px}.hint{color:#c0c9d8;line-height:1.55}.warn{color:#e8b785}select,button{background:#273444;color:#f0f3fa;border:1px solid #647287;padding:9px;border-radius:7px}
.boxes{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.card{background:#232d3c;border:1px solid #455468;border-radius:9px;padding:9px;min-width:0}
.card img{width:100%;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#4d5968 0 25%,#2a3441 0 50%) 50%/24px 24px}
#parts{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}small{color:#c1cbd6}
@media(max-width:900px){#parts{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:680px){.boxes{grid-template-columns:1fr}#parts{grid-template-columns:repeat(2,minmax(0,1fr))}}
</style><main><h1>P15-22 · 独立绘画 RGB / ArtMesh 透明层</h1>
<p class="warn">独立生成图只有 RGB；各部件透明轮廓来自 P15-21 原画 VDD，并非新画的独立部件。源原画曾在姿态验收中失败，当前只是诊断候选，不可入库。</p>
<label>角度 <select id="angle"></select></label><p id="metric" class="hint"></p>
<section class="boxes" id="overview"></section><h2>13 个部件 · 白底污染风险</h2><section id="parts"></section>
<script>const D=__DATA__,pick=document.querySelector('#angle'),overview=document.querySelector('#overview'),parts=document.querySelector('#parts');
D.forEach((x,i)=>{const o=document.createElement('option');o.value=i;o.textContent=x.yaw+'°';pick.append(o)});
function card(name,path,desc){const c=document.createElement('article');c.className='card';const h=document.createElement('h3');h.textContent=name;const img=document.createElement('img');img.src=path;img.alt=name;const s=document.createElement('small');s.textContent=desc||'';c.append(h,img,s);return c}
function render(){const v=D[Number(pick.value)];overview.replaceChildren();parts.replaceChildren();
overview.append(card('旧独立绘画原图',v.files['independent-source'],'无透明分层'));
overview.append(card('RGB 独立绘制 + VDD Alpha',v.files['derived-composite'],'非独立形状'));
overview.append(card('P15-21 VDD 原始合成',v.files.baseline,'保留原始身份基线'));
for(const r of v.roles)parts.append(card(r.role,r.src,'白底污染风险：'+(r.paintRisk*100).toFixed(2)+'% · 原画形状独立：否'));
document.querySelector('#metric').textContent='独立原图前景与 VDD Alpha IoU：'+v.overlap+'。白色污染率是启发式指标，仍需目视确认。';
}pick.onchange=render;render();</script></main>'''
(OUT/'index.html').write_text(html.replace('__DATA__',json.dumps(views,ensure_ascii=False)))
Z=P/'exports/p15-22-painted-rgb-review.zip'
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in sorted(OUT.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(OUT))
with zipfile.ZipFile(Z) as z:
 assert z.testzip() is None
 entries=len(z.namelist())
print(json.dumps({'entries':entries,'size':Z.stat().st_size,'sha256':hashlib.sha256(Z.read_bytes()).hexdigest()},ensure_ascii=False))

#!/usr/bin/env python3
import json,zipfile,hashlib,shutil
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent.parent;P=R/'private-assets'
Q=json.loads((R/'evidence/p15-32-mesh-vdd-qa.json').read_text())
B=json.loads((R/'evidence/p15-31-native-vdd-qa.json').read_text())
O=P/'exports/p15-32-mesh-vdd-review';O.mkdir(parents=True,exist_ok=True)
roles=['eye.far','hair.clip.cross_gold','hair.side'];records=[]
for f in Q['angles']:
 y=f['yaw'];name='yaw'+(str(int(y)) if float(y).is_integer() else str(y).replace('.','p'))
 d=O/name;d.mkdir(parents=True,exist_ok=True)
 shutil.copy2(P/'p15-32-mesh-vdd'/name/'composite.png',d/'mesh-composite.png') if (P/'p15-32-mesh-vdd'/name/'composite.png').exists() else None
 if f['kind']=='exact-keyframe':
  srcf=next(x for x in B['frames'] if x['yaw']==y)
  shutil.copy2(P/srcf['composite'],d/'p15-31-reference.png')
 else:
  srcf=next(x for x in B['frames'] if x['yaw']==y)
  shutil.copy2(P/srcf['composite'],d/'p15-31-reference.png')
 if not (d/'mesh-composite.png').exists():
  shutil.copy2(P/'p15-32-mesh-vdd'/name/'composite.png',d/'mesh-composite.png')
 a=np.asarray(Image.open(d/'mesh-composite.png').convert('RGBA'),dtype=np.int16)
 b=np.asarray(Image.open(d/'p15-31-reference.png').convert('RGBA'),dtype=np.int16)
 diff=np.clip(np.abs(a-b)*5,0,255).astype('uint8');diff[:,:,3]=255
 Image.fromarray(diff,'RGBA').save(d/'difference-x5.png')
 for role in roles:shutil.copy2(P/'p15-32-mesh-vdd'/name/(role+'.png'),d/(role+'.png'))
 rec={'yaw':y,'kind':f['kind'],'dir':name,
  'changedPixels':int(np.count_nonzero(np.any(a!=b,axis=2))),
  'meanAbsDelta':round(float(np.abs(a-b).mean()),5),
  'mesh':f.get('meshDiagnostics',{})}
 records.append(rec)
qa={'schema':'KOMA-P15-32-MESH-REVIEW-V1','frames':records,
 'meshIs2DOpticalFlowDriven':True,'physical3DClaim':False,'artisticApproval':False}
(O/'qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
html='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-32 Mesh VDD Review</title><style>
body{margin:0;padding:16px;background:#151b26;color:#edf2f8;font:15px system-ui}main{max-width:1400px;margin:auto}h1{font-size:23px}.note{line-height:1.55;color:#b9c7d6}.warn{color:#e8b78c}.ctrl{padding:12px;background:#222d3b;border-radius:8px}select{padding:8px;background:#2b394b;color:white}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.card{min-width:0;padding:9px;border:1px solid #405168;border-radius:8px;background:#222d3b}.card h3{font-size:13px}.card img{width:100%;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#4a5765 0 25%,#283543 0 50%) 50%/24px 24px}@media(max-width:650px){.grid{grid-template-columns:1fr}}
</style><main><h1>P15-32 · 2D Piecewise-Affine Mesh VDD</h1>
<p class="note">55°–65° 五个关键帧与四个中间帧。远眼、金色交叉发夹、侧发分别使用 7×7 网格（72 个三角形）和 Farneback 光流估计位移，端点纹理向中间角度独立网格变形，再进行合成。</p>
<p class="warn">这是从现有二维图像估计的网格形变，不是真实三维头部表面或经批准的独立原画。鼻梁遮挡与发夹物理连接尚未通过验收。</p>
<div class="ctrl"><label>视角 <select id="angle"></select></label><input id="slider" type="range" min="0" max="8" step="1" value="0" style="width:100%"><p id="stats"></p></div>
<h2>完整画面对照</h2><div class="grid" id="comps"></div><h2>独立网格部件</h2><div class="grid" id="parts"></div></main>
<script>const F=__DATA__,a=document.querySelector('#angle'),s=document.querySelector('#slider'),c=document.querySelector('#comps'),p=document.querySelector('#parts');
F.forEach((f,i)=>{let o=document.createElement('option');o.value=i;o.textContent=f.yaw+'°';a.append(o)});
function show(){let f=F[+a.value],d=f.dir;c.replaceChildren();p.replaceChildren();
for(let [file,title] of [['mesh-composite.png','P15-32 网格形变结果'],['p15-31-reference.png','P15-31 原插值结果'],['difference-x5.png','画面差异 ×5']]){let e=document.createElement('section');e.className='card';let h=document.createElement('h3'),im=document.createElement('img');h.textContent=title;im.src=d+'/'+file;e.append(h,im);c.append(e)}
for(let role of ['eye.far','hair.clip.cross_gold','hair.side']){let e=document.createElement('section');e.className='card';let h=document.createElement('h3'),im=document.createElement('img');h.textContent=role;im.src=d+'/'+role+'.png';e.append(h,im);p.append(e)}
let m=f.mesh||{};document.querySelector('#stats').textContent=f.yaw+'° · '+f.kind+' · 画面差异像素 '+f.changedPixels+' · '+(Object.keys(m).length?'三个部件均为 7×7 mesh':'关键帧原样保留')}
a.onchange=()=>{s.value=a.value;show()};s.oninput=()=>{a.value=s.value;show()};show();</script></main>'''
(O/'index.html').write_text(html.replace('__DATA__',json.dumps(records,ensure_ascii=False)))
Z=P/'exports/p15-32-mesh-vdd-review.zip'
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for x in sorted(O.rglob('*')):
  if x.is_file():z.write(x,x.relative_to(O))
with zipfile.ZipFile(Z) as z:assert z.testzip() is None;cnt=len(z.namelist())
print(json.dumps({'frames':len(records),'entries':cnt,'zipBytes':Z.stat().st_size,
 'midpointChangedPixels':[x['changedPixels'] for x in records if x['kind']!='exact-keyframe'],
 'sha256':hashlib.sha256(Z.read_bytes()).hexdigest()}))

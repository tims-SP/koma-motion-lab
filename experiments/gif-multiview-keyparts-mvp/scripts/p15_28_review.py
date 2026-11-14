#!/usr/bin/env python3
import json,zipfile,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parent.parent;P=R/'private-assets'
Q=json.loads((R/'evidence/p15-28-physical-occlusion-qa.json').read_text())
O=P/'exports/p15-28-physical-occlusion-review';O.mkdir(parents=True,exist_ok=True)
data=[]
for f in Q['frames']:
 n='yaw'+(str(int(f['yaw'])) if f['yaw']%1==0 else str(f['yaw']).replace('.','p'))
 d=O/n;d.mkdir(exist_ok=True);paths={}
 for k,v in f['files'].items():
  src=P/v['path'];dst=d/(k+'.png');shutil.copy2(src,dst);paths[k]=n+'/'+dst.name
 for k in ('composite','baseline'):
  src=R/f[k];dst=d/(k+'.png');shutil.copy2(src,dst);paths[k]=n+'/'+dst.name
 data.append({'yaw':f['yaw'],'paths':paths,'fraction':f['eyeVisibleFraction'],'changed':f['changedCompositePixels443']})
shutil.copy2(R/'evidence/p15-28-physical-occlusion-qa.json',O/'qa.json')
html='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-28 物理 Alpha 遮挡</title>
<style>body{background:#161c26;color:#edf2f9;font:15px system-ui;margin:0;padding:16px}main{max-width:1200px;margin:auto}.note{color:#bec8d7;line-height:1.55}.warn{color:#efc28a}select{padding:9px;background:#2b394b;color:white}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.card{background:#222d3b;padding:10px;border:1px solid #47596d;border-radius:8px;min-width:0}img{width:100%;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#4a5767 0 25%,#293643 0 50%) 50%/24px 24px}small{color:#b7c4d4}@media(max-width:750px){.grid{grid-template-columns:1fr}}</style>
<main><h1>P15-28 · 远眼真实图层 Alpha 合成候选</h1><p class="note">沿用 P15-21 的源图层，不增加整体透明度衰减。远眼保留完整隐藏底稿，按现有 hair.front 与 nose 的 RGBA Alpha 做遮挡，再按已登记 depthOrder 合成。</p><p class="warn">注意：输入 eye.far 图层可能已继承上游 P8 隐藏窗口的透明度。此候选只是不再添加新的整体淡出，不代表已恢复未经淡出的原始眼睛，也没有创造新的面部遮挡几何。当前遮挡覆盖仍不足，不能签收。</p><label>角度 <select id="angle"></select></label><p id="metric"></p><div class="grid" id="grid"></div></main>
<script>const D=__DATA__,s=document.querySelector('#angle'),g=document.querySelector('#grid'),K=[['baseline','P15-21 原始合成'],['composite','P15-28 物理 Alpha 遮挡'],['eye-original-full','完整远眼原画（含隐藏部分）'],['eye-visible','实际可见远眼'],['eye-hidden-underpaint','被遮挡远眼底稿'],['eye-front-hair-occlusion','刘海遮挡交集'],['eye-nose-occlusion','鼻部遮挡交集']];D.forEach((x,i)=>{let o=document.createElement('option');o.value=i;o.textContent=x.yaw+'°';s.append(o)});function draw(){let x=D[+s.value];g.replaceChildren();for(let [k,t] of K){let c=document.createElement('section'),h=document.createElement('h3'),im=document.createElement('img');c.className='card';h.textContent=t;im.src=x.paths[k];im.alt=t;c.append(h,im);g.append(c)}document.querySelector('#metric').textContent='远眼 Alpha 可见比例 '+(x.fraction*100).toFixed(2)+'% · 完整合成变化像素 '+x.changed;}s.onchange=draw;draw();</script></html>'''
(O/'index.html').write_text(html.replace('__DATA__',json.dumps(data,ensure_ascii=False)))
Z=P/'exports/p15-28-physical-occlusion-review.zip'
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in sorted(O.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(O))
with zipfile.ZipFile(Z) as z:assert z.testzip() is None;cnt=len(z.namelist())
print(json.dumps({'entries':cnt,'bytes':Z.stat().st_size,'sha256':hashlib.sha256(Z.read_bytes()).hexdigest()}))

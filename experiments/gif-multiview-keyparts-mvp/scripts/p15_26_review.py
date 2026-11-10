#!/usr/bin/env python3
import json,hashlib,zipfile,shutil
from pathlib import Path
R=Path(__file__).resolve().parent.parent;P=R/'private-assets'
Q=json.loads((R/'evidence/p15-26-local-repair-qa.json').read_text())
OUT=P/'exports/p15-26-local-repair-review';OUT.mkdir(parents=True,exist_ok=True)
data=[]
for f in Q['frames']:
 a=f['angle'];name='yaw'+(str(int(a)) if a%1==0 else str(a).replace('.','p'))
 dest=OUT/name;dest.mkdir(exist_ok=True)
 roles=[]
 for role in f['roles']:
  source=P/role['path'];dst=dest/(role['role']+'.png');shutil.copy2(source,dst)
  roles.append({'name':role['role'],'src':name+'/'+dst.name,
    'changedRGB':role['rgbChangedPixels'],'changedAlpha':role['alphaChangedPixels']})
 base=P/'p15-21-layered-anatomy'/(name+'.png')
 shutil.copy2(base,dest/'baseline.png')
 shutil.copy2(P/f['diagnostic'],dest/'local-repair.png')
 data.append({'yaw':a,'base':name+'/baseline.png','candidate':name+'/local-repair.png',
 'parts':roles,'iou':f['compositeAlphaIoU'],'rgbChange':f['rgbChangedPixelsVsBaseline']})
shutil.copy2(R/'evidence/p15-26-local-repair-qa.json',OUT/'qa.json')
old=P/'p15-25-procedural-paint/compare-yaw60-tiny.jpg'
if old.is_file():shutil.copy2(old,OUT/'prior-p15-25-visual-fail.jpg')
html='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-26 · 原始纹理局部修复</title>
<style>body{margin:0;padding:16px;background:#161c26;color:#ecf0f8;font:15px system-ui}main{max-width:1300px;margin:auto}.hint{color:#b9c4d3;line-height:1.5}.warn{color:#e8c088}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.parts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.card{border:1px solid #47576d;background:#222c3b;padding:10px;border-radius:10px;min-width:0}.card img{width:100%;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#4a5668 0 25%,#2c3543 0 50%) 50%/24px 24px}select{padding:9px;background:#2c394a;color:white;border:1px solid #65788f;border-radius:7px}@media(max-width:760px){.grid,.parts{grid-template-columns:1fr}}</style>
<main><h1>P15-26 · 保留原始 ArtMesh 纹理的局部修复</h1><p class="hint">将 P15-25 的整块重绘撤回，恢复 P15-21 原有侧发与远眼身份；仅添加受限的侧发高光、呆毛 Alpha 微调整及远眼鼻侧渐变。均为派生素材，不是独立原画。</p>
<p class="warn">工程对照候选；真正的遮挡补绘和原画验收尚未通过。请直接对比两张完整画面，避免将 Alpha IoU 当画质分数。</p>
<label>角度 <select id="angle"></select></label><p id="stat" class="hint"></p><div class="grid"><section class="card"><h3>P15-21 原始基线</h3><img id="baseline"></section><section class="card"><h3>P15-26 微调候选</h3><img id="candidate"></section></div><h2>实际修改的透明层</h2><div class="parts" id="parts"></div>
<h2>上一阶段大面积替换失败示意</h2><img style="max-width:600px;width:100%" src="prior-p15-25-visual-fail.jpg" alt="P15-25 fail"/>
</main><script>const v=__DATA__,s=document.querySelector('#angle'),parts=document.querySelector('#parts');v.forEach((x,i)=>{let o=document.createElement('option');o.value=i;o.textContent=x.yaw+'°';s.append(o)});
function draw(){let x=v[Number(s.value)];document.querySelector('#baseline').src=x.base;document.querySelector('#candidate').src=x.candidate;
document.querySelector('#stat').textContent='整帧 Alpha IoU '+x.iou+' · RGB 改变像素 '+x.rgbChange+'（不代表画质评价）';
parts.replaceChildren();for(let r of x.parts){let div=document.createElement('section');div.className='card';let h=document.createElement('h3');h.textContent=r.name;let im=document.createElement('img');im.src=r.src;im.alt=r.name;let small=document.createElement('small');small.textContent='RGB变化 '+r.changedRGB+' / Alpha变化 '+r.changedAlpha;div.append(h,im,small);parts.append(div)}}s.onchange=draw;draw()</script></html>'''
(OUT/'index.html').write_text(html.replace('__DATA__',json.dumps(data,ensure_ascii=False)))
archive=P/'exports/p15-26-local-repair-review.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in sorted(OUT.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(OUT))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None;count=len(z.namelist())
print(json.dumps({'entries':count,'size':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}))

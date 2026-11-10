import json,zipfile,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent.parent
P=R/'private-assets';D=P/'p15-20-canonical-source-views'
q=json.loads((D/'qa.json').read_text())
html='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-20 原始部件源恢复</title>
<style>body{margin:0;padding:16px;background:#151b25;color:#edf2f8;font:14px system-ui}main{max-width:1450px;margin:auto}h1{font-size:24px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.cell{background:#222d3b;border:1px solid #45546a;border-radius:8px;padding:8px;min-width:0}.views{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:5px}.views img{width:100%;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#45505e 0 25%,#29323d 0 50%) 50%/20px 20px}.views small{display:block;text-align:center;color:#b7c4d2}.muted{color:#adbac9}.flag{color:#e8c18d}@media(max-width:760px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}</style>
<main><h1>P15-20 · P0 原始 ArtMesh 部件恢复</h1><p class="muted">仅从已登记 P1 / P2 源清单逐字节复制；不是新绘制，不做镜像、缩放或补绘。每列一个角度，每行一个语义部件。</p><p class="flag">90° 远眼、远耳、发夹透明是源清单标记的预期遮挡，不是丢失素材。</p><div class="grid" id="grid"></div></main>
<script>const D=__DATA__,root=document.querySelector('#grid');for(const role of D.semanticSlots){const c=document.createElement('section');c.className='cell';const h=document.createElement('b');h.textContent=role;c.append(h);const row=document.createElement('div');row.className='views';for(const v of D.views){const p=v.parts.find(x=>x.semanticId===role);const box=document.createElement('div'),im=document.createElement('img'),s=document.createElement('small');im.src=p.path.split('/').slice(-2).join('/');im.alt=v.yaw+' '+role;s.textContent=v.yaw+'° · '+p.alphaPixelsGt16+' px';box.append(im,s);row.append(box)}c.append(row);root.append(c)}</script></main></html>'''
# image URLs relative to html, assets live in yaw directories
(D/'index.html').write_text(html.replace('__DATA__',json.dumps(q,ensure_ascii=False)))
zip_path=P/'exports/p15-20-canonical-source-views.zip';zip_path.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in sorted(D.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(D))
with zipfile.ZipFile(zip_path) as z:assert z.testzip() is None;count=len(z.namelist())
print(json.dumps({'archive':str(zip_path),'files':count,'bytes':zip_path.stat().st_size,'sha256':hashlib.sha256(zip_path.read_bytes()).hexdigest()}))

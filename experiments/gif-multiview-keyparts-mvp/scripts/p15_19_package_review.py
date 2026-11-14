#!/usr/bin/env python3
"""Make offline pixel-comparison review without promoting unapproved art."""
import json,hashlib,zipfile,shutil
from pathlib import Path
R=Path(__file__).resolve().parent.parent
P=R/"private-assets"
QA=R/"evidence/p15-19-quality-region-qa.json"
OUT=P/"exports/p15-19-quality-review"
q=json.loads(QA.read_text())
data=[]
for v in q["views"]:
 records=[]
 for item in v["rois"]:
  records.append({"role":item["roi"],"center":item["center"],
   "files":item["files"],"edge":item["difference"]["edgeDisagreementPercent"],
   "changed":item["difference"]["changedRgbPixels"],
   "oldVisible":item["sourceP15_10PartVisiblePixels"]})
 data.append({"angle":v["yaw"],"rois":records})
html=r'''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>P15-19 局部纹理审查</title>
<style>
body{background:#141a22;color:#eff3fa;font:15px system-ui;margin:0;padding:18px}
main{max-width:1300px;margin:auto}h1{font-size:25px}p{color:#aeb9c7;line-height:1.5}
select{background:#283342;color:white;border:1px solid #5d6c80;padding:9px;border-radius:6px}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:15px}
.card{background:#202a37;border:1px solid #3f5065;padding:10px;border-radius:9px;min-width:0}
.three{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
figure{margin:0;min-width:0}img{width:100%;aspect-ratio:1;object-fit:contain;image-rendering:auto;background:repeating-conic-gradient(#465363 0 25%,#27303a 0 50%) 50%/22px 22px}
figcaption{color:#aeb9c7;text-align:center;font-size:12px}
small{color:#e3b682} .warn{border-left:3px solid #e3b682;padding-left:12px}
@media(max-width:800px){.grid{grid-template-columns:1fr}body{padding:9px}}
</style><main><h1>P15-19 · 原始 ArtMesh 局部纹理审查</h1>
<p class="warn">原始 anatomy / stroke-wide / 4× RGB 差异。P5 锚点仅用于选择截图区域。
旧 P15-10 部件像素数来自另一渲染链路，不代表当前 P12 可见性；本阶段没有艺术签收。</p>
<label>目标角度：<select id="angle"></select></label><p id="summary"></p><section id="grid" class="grid"></section>
</main><script>
const data=__DATA__;
const picker=document.getElementById('angle'),grid=document.getElementById('grid'),summary=document.getElementById('summary');
data.forEach((v,i)=>{const o=document.createElement('option');o.value=i;o.textContent=v.angle+'°';picker.appendChild(o)});
function render(){let v=data[Number(picker.value)];grid.replaceChildren();
v.rois.forEach(r=>{
 const card=document.createElement('article');card.className='card';
 const title=document.createElement('h3');title.textContent=r.role+' · P5 '+r.center.join(', ');
 const imgs=document.createElement('div');imgs.className='three';
 for(const [key,label] of [['anatomy','基准'],['stroke-wide','笔画增强'],['rgb-delta-x4','RGB 差异 ×4']]){
  const fig=document.createElement('figure'),img=document.createElement('img'),cap=document.createElement('figcaption');
  img.src=r.files[key];img.alt=r.role+' '+label;cap.textContent=label;fig.append(img,cap);imgs.append(fig);
 }
 const note=document.createElement('small');note.textContent='变化像素 '+r.changed+' · 边缘差异 '+r.edge+'% · 旧P15-10部件像素 '+r.oldVisible;
 card.append(title,imgs,note);grid.append(card);
});
summary.textContent='当前角度 '+v.angle+'° · 6 个区域 × 3 个对照';
}
picker.addEventListener('change',render);render();
</script></html>'''
(OUT/"index.html").write_text(html.replace("__DATA__",json.dumps(data,ensure_ascii=False)))
shutil.copy2(QA,OUT/"qa.json")
zip_path=P/"exports/p15-19-quality-review.zip"
with zipfile.ZipFile(zip_path,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for file in sorted(OUT.iterdir()):
  if file.is_file():z.write(file,file.name)
with zipfile.ZipFile(zip_path) as z:
 assert z.testzip() is None
 n=len(z.namelist())
print(json.dumps({"archive":str(zip_path),"files":n,"bytes":zip_path.stat().st_size,
 "sha256":hashlib.sha256(zip_path.read_bytes()).hexdigest()},ensure_ascii=False))

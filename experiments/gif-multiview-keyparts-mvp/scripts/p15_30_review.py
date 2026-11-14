#!/usr/bin/env python3
"""Review and diagnostic continuity frames for P15-30 tracked P0 roles."""
import json,zipfile,hashlib,shutil
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent.parent;P=R/'private-assets'
Q=json.loads((R/'evidence/p15-30-tracked-qa.json').read_text())
SOURCE=P/'p15-30-camera-tracked';OUT=P/'exports/p15-30-tracked-review'
OUT.mkdir(parents=True,exist_ok=True)
views=[]
for frame in Q['frames']:
 yaw=frame['yaw'];slug='yaw'+(str(int(yaw)) if yaw%1==0 else str(yaw).replace('.','p'))
 dest=OUT/slug;dest.mkdir(exist_ok=True)
 for key in ['eye-tracked','clip-tracked','eye-tracked-bridge-proxy',
             'whole-tracked','eye-only','clip-only']:
  shutil.copy2(SOURCE/slug/(key+'.png'),dest/(key+'.png'))
 shutil.copy2(P/'p15-21-layered-anatomy'/(slug+'.png'),dest/'baseline.png')
 views.append({'yaw':yaw,'slug':slug,'clipBefore':frame['clipCentroidErrorBefore'],
  'clipAfter':frame['clipCentroidErrorAfter'],'eyeError':frame['eyeRelativeMotionErrorPx'],
  'alphaIoU':frame['wholeFrameAlphaIoUToP15_21']})
# Produce 4 intermediate frames by LINEAR RGBA interpolation of the already
# composited five checkpoint images. This is not VDD part-level interpolation.
timeline=[]
for i,v in enumerate(views):
 timeline.append({'yaw':v['yaw'],'src':v['slug']+'/whole-tracked.png','mode':'key'})
 if i+1<len(views):
  nxt=views[i+1]
  a=np.asarray(Image.open(SOURCE/v['slug']/'whole-tracked.png').convert('RGBA'),dtype=np.float32)
  b=np.asarray(Image.open(SOURCE/nxt['slug']/'whole-tracked.png').convert('RGBA'),dtype=np.float32)
  mid=(a+b)*.5
  y=round((v['yaw']+nxt['yaw'])/2,3)
  path=OUT/('interpolated-'+str(y).replace('.','p')+'.png')
  Image.fromarray(np.rint(mid).astype(np.uint8),'RGBA').save(path)
  timeline.append({'yaw':y,'src':path.name,'mode':'diagnostic-linear-full-frame'})
(OuT if False else OUT/'qa.json').write_text(json.dumps({'characterId':'p0_character_001',
 'views':views,'timeline':timeline,'productionVddModified':False,
 'visualAcceptance':False,'intermediateFramesAreTrueVdd':False,
 'notes':'Four midframes are full-RGBA crossfades, NOT independent ArtMesh interpolation'},ensure_ascii=False,indent=2)+'\n')
html='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-30 相机锚点配准与连续帧</title>
<style>
body{margin:0;background:#151b25;color:#eef3fa;padding:18px;font:15px system-ui}main{max-width:1310px;margin:auto}
h1{font-size:24px}.hint{color:#b7c3d4;line-height:1.55}.warn{color:#edc08c}
select,input[type=range]{accent-color:#889fc8}select{padding:10px;background:#263446;color:white;border:1px solid #6c7c91;border-radius:6px}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.card{min-width:0;background:#222d3b;border:1px solid #45576f;border-radius:9px;padding:10px}
.card img{width:100%;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#4a5665 0 25%,#2a3644 0 50%) 50%/24px 24px}
.card h3{font-size:15px;margin:5px 0 10px}.control{padding:11px;background:#222d3b;margin:14px 0;border-radius:10px}
input[type=range]{width:100%}@media(max-width:780px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:540px){.grid{grid-template-columns:1fr}body{padding:11px}}
</style><main><h1>P15-30 · P0 远眼及发夹相机锚点配准</h1>
<p class="hint">五个相机关键角度按 P15-12 锚点进行像素位移。远眼使用相对于 55° 的虹膜锚点位移；发夹 Alpha 中心被平移到发夹锚点。</p>
<p class="warn">这是像素配准工程候选。鼻梁仍为 P15-29 二维代理，发夹穿插和侧发真实遮挡未被 3D 验证。中间帧为全画面线性 RGBA 诊断插值，不是正式的部件级 VDD。</p>
<label>关键视角 <select id="angle"></select></label><p id="metrics" class="hint"></p><div class="grid" id="comparison"></div>
<section class="control"><h2>连续预览：55°–65°</h2><input id="timeline" type="range" min="0" max="8" step="1" value="0">
<p id="timelineLabel"></p><div class="card" style="max-width:650px"><img id="timelineImage"></div></section>
</main><script>
const views=__VIEWS__,tl=__TIMELINE__,sel=document.querySelector('#angle'),comp=document.querySelector('#comparison'),slider=document.querySelector('#timeline');
views.forEach((v,i)=>{let op=document.createElement('option');op.value=i;op.textContent=v.yaw+'°';sel.append(op)});
function draw(){const v=views[+sel.value],s=v.slug;comp.replaceChildren();
for(let [t,p] of [['P15-21 原始基线','baseline.png'],['仅远眼配准','eye-only.png'],['仅发夹配准','clip-only.png'],['远眼与发夹均配准','whole-tracked.png'],['远眼透明候选','eye-tracked-bridge-proxy.png'],['发夹透明候选','clip-tracked.png']]){
let c=document.createElement('section');c.className='card';let h=document.createElement('h3');h.textContent=t;let img=document.createElement('img');img.src=s+'/'+p;img.alt=t;c.append(h,img);comp.append(c)}
document.querySelector('#metrics').textContent='发夹锚点误差 '+v.clipBefore.toFixed(2)+'px → '+v.clipAfter.toFixed(3)+'px；远眼相对位移误差 '+v.eyeError.toFixed(3)+'px；全帧 Alpha IoU '+v.alphaIoU;}
function frame(){const t=tl[+slider.value];document.querySelector('#timelineImage').src=t.src;document.querySelector('#timelineLabel').textContent=t.yaw+'°  '+(t.mode==='key'?'关键帧':'线性全帧诊断插值（非正式 VDD）');}
sel.onchange=draw;slider.oninput=frame;draw();frame();
</script>'''
(OUT/'index.html').write_text(html.replace('__VIEWS__',json.dumps(views,ensure_ascii=False)).replace('__TIMELINE__',json.dumps(timeline)))
ARCH=P/'exports/p15-30-tracked-review.zip'
with zipfile.ZipFile(ARCH,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(OUT.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(OUT))
with zipfile.ZipFile(ARCH) as z:assert z.testzip() is None;entries=len(z.namelist())
print(json.dumps({'views':len(views),'timelineFrames':len(timeline),'entries':entries,'bytes':ARCH.stat().st_size,
 'sha256':hashlib.sha256(ARCH.read_bytes()).hexdigest()}))

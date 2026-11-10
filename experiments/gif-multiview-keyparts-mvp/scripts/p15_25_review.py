#!/usr/bin/env python3
"""P15-25 layered painting review: combine 3 new brush roles + P15-24 clip."""
import hashlib,json,shutil,zipfile
from pathlib import Path
import numpy as np
from PIL import Image
from p1_front_semantic import alpha_over
R=Path(__file__).resolve().parent.parent;P=R/'private-assets'
Q=json.loads((R/'evidence/p15-25-original-keypart-paint-qa.json').read_text())
L=json.loads((R/'evidence/p15-21-intermediate-components-qa.json').read_text())
D=P/'exports/p15-25-four-role-review';D.mkdir(parents=True,exist_ok=True)
views=[]
for frame in Q['frames']:
 yaw=frame['angle'];slug='yaw'+(str(int(yaw)) if yaw%1==0 else str(yaw).replace('.','p'))
 out=D/slug;out.mkdir(exist_ok=True)
 f21=next(f for f in L['frames'] if f['yaw']==yaw)
 candidates={x['role']:P/x['path'] for x in frame['parts']}
 candidates['hair.clip.cross_gold']=P/'p15-24-reference-conditioned'/slug/'hair.clip.cross_gold.png'
 for role,path in candidates.items():
  shutil.copy2(path,out/(role+'.png'))
 raw=np.zeros((443,443,4),np.uint8)
 baseline=np.zeros_like(raw)
 for row in f21['roles']:
  a=np.asarray(Image.open(P/row['native']).convert('RGBA'))
  baseline=alpha_over(baseline,a)
  if row['role'] in candidates:
   new=np.asarray(Image.open(candidates[row['role']]).convert('RGBA'))
   a=np.asarray(Image.fromarray(new,'RGBA').resize((443,443),Image.Resampling.LANCZOS))
  raw=alpha_over(raw,a)
 full=Image.fromarray(raw,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
 gold=P/'p15-21-layered-anatomy'/(slug+'.png')
 reconstructed=np.asarray(Image.fromarray(baseline,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS))
 if not np.array_equal(reconstructed,np.asarray(Image.open(gold).convert('RGBA'))):
  raise AssertionError('Baseline byte pixels differ '+slug)
 full.save(out/'four-role-diagnostic.png')
 shutil.copy2(gold,out/'p15-21-baseline.png')
 a=np.asarray(full)[:,:,3]>16;b=np.asarray(Image.open(gold).convert('RGBA'))[:,:,3]>16
 iou=round(np.count_nonzero(a&b)/max(1,np.count_nonzero(a|b)),5)
 views.append({'yaw':yaw,'slug':slug,'alphaIoU':iou,
   'roles':[{ 'role':role,'file':slug+'/'+role+'.png'} for role in candidates],
   'whole':slug+'/four-role-diagnostic.png','baseline':slug+'/p15-21-baseline.png'})
shutil.copy2(R/'evidence/p15-25-original-keypart-paint-qa.json',D/'art-quality-qa.json')
preview=P/'p15-25-procedural-paint/compare-yaw60-tiny.jpg'
if preview.is_file():shutil.copy2(preview,D/'visual-fail-yaw60-preview.jpg')
(D/'qa.json').write_text(json.dumps({'sourceEvidence':'evidence/p15-25-original-keypart-paint-qa.json',
 'characterId':'p0_character_001','views':views,'formalArtApproval':False,
 'productionVddUnchanged':True},ensure_ascii=False,indent=2)+'\n')
html='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>P15-25 · 四部件新绘画对照</title><style>
body{background:#141b26;color:#e9f0f8;font:15px system-ui;margin:0;padding:18px}
main{max-width:1250px;margin:auto}.desc{color:#b6c3d1;line-height:1.5}.warn{color:#efc18d}
select{background:#273447;color:white;border:1px solid #65778c;border-radius:7px;padding:9px}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.box{padding:9px;border:1px solid #40516a;background:#222c3a;border-radius:10px;min-width:0}
.box img{width:100%;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#48596b 0 25%,#283542 0 50%) 50%/24px 24px}
.parts{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
@media(max-width:850px){.parts{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:650px){.grid{grid-template-columns:1fr}body{padding:10px}}
</style><main>
<h1>P15-25 · P0 引导新笔画 / 五角度诊断</h1>
<p class="warn">侧发、呆毛、远眼为新程序化笔画，发夹沿用 P15-24 新笔画。底图仍是已批准角色的 P15-21 ArtMesh，但这些新角色本身未经正式原画批准；远眼的隐藏补绘和真正的遮挡关系仍待人工检查。</p>
<label>角度：<select id="angle"></select></label><p id="numbers" class="desc"></p>
<div class="grid"><section class="box"><h3>原始 P15-21 基线</h3><img id="baseline"></section>
<section class="box"><h3>四部件替换后</h3><img id="candidate"></section></div>
<h2>四张独立透明候选部件</h2><div class="parts" id="parts"></div>
</main><script>
const data=__DATA__,select=document.querySelector('#angle'),parts=document.querySelector('#parts');
data.forEach((v,i)=>{const o=document.createElement('option');o.value=i;o.textContent=v.yaw+'°';select.append(o)});
function render(){const v=data[Number(select.value)];document.querySelector('#baseline').src=v.baseline;
document.querySelector('#candidate').src=v.whole;document.querySelector('#numbers').textContent=
'新旧整帧 Alpha IoU: '+v.alphaIoU+'，不代表艺术质量通过。';
parts.replaceChildren();for(const r of v.roles){const b=document.createElement('section'),h=document.createElement('h4'),im=document.createElement('img');
b.className='box';h.textContent=r.role;im.src=r.file;im.alt=r.role;b.append(h,im);parts.append(b)}}
select.onchange=render;render();
</script>'''
(D/'index.html').write_text(html.replace('__DATA__',json.dumps(views,ensure_ascii=False)))
archive=P/'exports/p15-25-four-role-review.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in sorted(D.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(D))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None;n=len(z.namelist())
print(json.dumps({'angles':len(views),'combinedAlphaIoU':[v['alphaIoU'] for v in views],
 'archiveFiles':n,'zipBytes':archive.stat().st_size,
 'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}))

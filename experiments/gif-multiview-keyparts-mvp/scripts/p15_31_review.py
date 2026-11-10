#!/usr/bin/env python3
"""P15-31 offline review comparing per-role interpolation to whole-frame fade."""
import json,zipfile,hashlib,shutil
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent.parent
P=R/'private-assets'
Q=json.loads((R/'evidence/p15-31-native-vdd-qa.json').read_text())
O=P/'exports/p15-31-native-artmesh-review';O.mkdir(parents=True,exist_ok=True)
OLD=P/'exports/p15-30-tracked-review'
frames=[]
for f in Q['frames']:
 yaw=f['yaw'];name='yaw'+(str(int(yaw)) if float(yaw).is_integer() else str(yaw).replace('.','p'))
 directory=O/name;directory.mkdir(parents=True,exist_ok=True)
 shutil.copy2(P/f['composite'],directory/'role-composite.png')
 key=abs(yaw-round(yaw/2.5)*2.5)<1.e-5
 if key:
  old=OLD/name/'whole-tracked.png'
 else:
  old=OLD/('interpolated-'+str(yaw).replace('.','p')+'.png')
 shutil.copy2(old,directory/'old-full-frame.png')
 arr=np.asarray(Image.open(directory/'role-composite.png').convert('RGBA'),dtype=np.int16)
 prev=np.asarray(Image.open(directory/'old-full-frame.png').convert('RGBA'),dtype=np.int16)
 changed=int(np.count_nonzero(np.any(np.abs(arr-prev)>2,axis=2)))
 mean=float(np.abs(arr-prev).mean())
 difference=np.clip(np.abs(arr-prev)*5,0,255).astype(np.uint8)
 difference[:,:,3]=255
 Image.fromarray(difference,'RGBA').save(directory/'enhanced-diff.png')
 if f['kind']=='tracked-keyframe' and changed:raise AssertionError('Keyframe changed in review')
 frame={'yaw':yaw,'key':key,'mode':f['kind'],'dir':name,
   'changedVsFullFrame':changed,'meanDiff':round(mean,5),
   'parts':[{'role':p['role'],'src':str(p['role'])+'.png'} for p in f['parts'] if p['role'] in ('eye.far','hair.clip.cross_gold','hair.side','hair.front','face.skin')]}
 # Include independently rendered eye and clip parts plus representative
 # side hair, face and bangs on native 443px.
 for role in ['eye.far','hair.clip.cross_gold','hair.side','hair.front','face.skin']:
  source=P/next(x['path'] for x in f['parts'] if x['role']==role)
  shutil.copy2(source,directory/(role+'.png'))
 frames.append(frame)
(O/'qa.json').write_text(json.dumps({
 'schema':'KOMA-P15-31-VISUAL-REVIEW-V1','frames':frames,
 'truePerRoleAlphaInterpolation':True,'fullFrameCrossfadeUsedForNewCandidates':False,
 'fullFrameCrossfadeIncludedOnlyAsReference':True,'meshVertexVDDCompleted':False,
 'artisticallyApproved':False,'productionVddModified':False},ensure_ascii=False,indent=2)+'\n')
html='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>P15-31 · 逐部件 ArtMesh 与整帧交叉淡入淡出对照</title>
<style>
body{margin:0;background:#151b26;color:#e9f0f8;font:15px system-ui;padding:16px}
main{max-width:1320px;margin:auto}h1{font-size:23px}
.note{color:#b8c5d4;line-height:1.55}.warn{color:#e8b888}
select,input[type=range]{padding:8px;accent-color:#91a9da}select{background:#2a394b;color:white;border:1px solid #6b7c95}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
.parts{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px}
.card{min-width:0;border:1px solid #405168;background:#222d3b;border-radius:8px;padding:9px}
.card img{width:100%;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#4a5765 0 25%,#283543 0 50%) 50%/24px 24px}
.card h3{font-size:13px}.controls{background:#222d3b;padding:12px;border-radius:8px}
@media(max-width:900px){.parts{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:650px){.grid{grid-template-columns:1fr}.parts{grid-template-columns:repeat(2,minmax(0,1fr))}}
</style><main><h1>P15-31 · 逐部件透明 RGBA 连续插值</h1>
<p class="note">五个关键角度 55°–65° 与四个新增中间角度。每张新帧由 13 个 ArtMesh 独立预乘 Alpha 插值后按层合成。下方对比 P15-30 的旧整帧交叉淡入淡出及差异图（放大五倍）。</p>
<p class="warn">注意：完成了逐部件插值，但尚无顶点网格 VDD 与独立 60° 原画。鼻梁还是二维代理；发夹正确物理穿插尚未验收。此为工程实验，不是最终动漫画质。</p>
<div class="controls"><label>视角 <select id="angle"></select></label>
<p><input style="width:100%" type="range" id="slider" min="0" max="8" value="0" step="1"></p><p id="stat"></p></div>
<h2>全帧对照</h2><div class="grid" id="comps"></div>
<h2>五种透明 ArtMesh 部件（443×443）</h2><div class="parts" id="parts"></div></main>
<script>
const F=__DATA__,a=document.querySelector('#angle'),s=document.querySelector('#slider'),c=document.querySelector('#comps'),parts=document.querySelector('#parts');
F.forEach((f,i)=>{let opt=document.createElement('option');opt.value=i;opt.textContent=f.yaw+'°';a.append(opt)});
function show(){let f=F[Number(a.value)],prefix=f.dir;
c.replaceChildren();for(let [file,title] of [['role-composite.png','新逐部件 ArtMesh 合成'],['old-full-frame.png','旧整帧交叉淡入淡出'],['enhanced-diff.png','RGB 差异 ×5']]){
let section=document.createElement('section');section.className='card';let h=document.createElement('h3'),img=document.createElement('img');h.textContent=title;img.src=prefix+'/'+file;img.alt=title;section.append(h,img);c.append(section)}
parts.replaceChildren();for(let x of f.parts){let section=document.createElement('section');section.className='card';let h=document.createElement('h3'),img=document.createElement('img');h.textContent=x.role;img.src=prefix+'/'+x.src;img.alt=x.role;section.append(h,img);parts.append(section)}
document.querySelector('#stat').textContent=f.yaw+'° · '+(f.key?'原始关键帧':'独立中间帧')+
' · 与旧整帧交叉淡入淡出差异像素 '+f.changedVsFullFrame+' · 平均差异 '+f.meanDiff}
a.onchange=()=>{s.value=a.value;show()};s.oninput=()=>{a.value=s.value;show()};show();
</script>'''
(O/'index.html').write_text(html.replace('__DATA__',json.dumps(frames,ensure_ascii=False)))
Z=P/'exports/p15-31-native-artmesh-review.zip'
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(O.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(O))
with zipfile.ZipFile(Z) as z:assert z.testzip() is None;count=len(z.namelist())
print(json.dumps({'frames':len(frames),'midFrameDifferentPixels':[x['changedVsFullFrame'] for x in frames if not x['key']],
 'bundleEntries':count,'zipBytes':Z.stat().st_size,'sha256':hashlib.sha256(Z.read_bytes()).hexdigest()}))

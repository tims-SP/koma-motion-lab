#!/usr/bin/env python3
import hashlib,json,shutil,zipfile
from pathlib import Path
R=Path(__file__).resolve().parent.parent
P=R/'private-assets'
QA=json.loads((R/'evidence/p15-16-physical-identity-qa.json').read_text())
OUT=P/'exports/p15-16-physical-eye-review'
OUT.mkdir(parents=True,exist_ok=True)
cells=[]
for view in QA['views']:
 if view['view']!='yaw045':continue
 for role in ['eye.near','eye.far','ear.near','ear.far']:
  record=next(x for x in view['roles'] if x['role']==role)
  path=P/record['path'];target=OUT/(role+'.png')
  shutil.copy2(path,target)
  cells.append({'name':role,'path':target.name,'pixels':record['pixels'],'status':record['roleIdentityStatus']})
frames=[]
for name in ['yaw55','yaw57p5','yaw60','yaw62p5','yaw65']:
 src=P/'p15-10-semantic-pose/arc'/(name+'.png')
 dest=OUT/(name+'.png')
 shutil.copy2(src,dest)
 frames.append({'name':name,'path':dest.name})
html='''<!DOCTYPE html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>P15-16 · 物理身份与转头不连续诊断</title>
<style>body{font:16px system-ui;background:#141922;color:#e8eff7;margin:0;padding:20px}
main{max-width:1050px;margin:auto}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.card{border:1px solid #354253;padding:12px;border-radius:10px;background:#222937}
img{width:100%;max-width:440px;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#485361 0 25%,#26303c 0 50%) 50%/22px 22px}
strong{color:#ffc47b}p{color:#adb7c5}
@media(max-width:650px){.grid{grid-template-columns:1fr}}
</style><main><h1>P15-16 · 物理身份与转头诊断</h1>
<p>45° P5 锚点：近眼和近耳位于画面左侧；此前的 P15-15 角色分配方向相反。57.5°→60° 仍有明显轮廓跳变。</p>
<strong>本页不是正式原画通过记录。PSD 中的隐藏补绘仍未通过视觉验收。</strong>
<h2>45° 物理身份角色</h2><section class="grid" id="roles"></section><h2>55°–65° 原有 VDD 比较</h2>
<section class="grid" id="frames"></section></main><script>
const roleData=__ROLES__,frameData=__FRAMES__;
function cards(id,data){const parent=document.getElementById(id);
for(const entry of data){const card=document.createElement('div');card.className='card';
const name=document.createElement('h3');name.textContent=entry.name;const im=document.createElement('img');
im.src=entry.path;im.alt=entry.name;const desc=document.createElement('p');desc.textContent=entry.status||('可见像素：'+entry.pixels);
card.append(name,im,desc);parent.append(card);}}
cards('roles',roleData);cards('frames',frameData);
</script>'''
(OUT/'index.html').write_text(html.replace('__ROLES__',json.dumps(cells,ensure_ascii=False)).replace('__FRAMES__',json.dumps(frames,ensure_ascii=False)))
shutil.copy2(R/'evidence/p15-16-physical-identity-qa.json',OUT/'qa.json')
zipfile_path=P/'exports/p15-16-physical-eye-review.zip'
with zipfile.ZipFile(zipfile_path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for path in sorted(OUT.iterdir()):
  if path.is_file():z.write(path,path.name)
with zipfile.ZipFile(zipfile_path) as z:
 assert z.testzip() is None
 entries=len(z.namelist())
print(json.dumps({'bytes':zipfile_path.stat().st_size,'entries':entries,'sha256':hashlib.sha256(zipfile_path.read_bytes()).hexdigest()}))

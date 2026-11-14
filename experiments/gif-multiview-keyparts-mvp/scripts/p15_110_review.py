#!/usr/bin/env python3
"""Interactive actual source annotations and four real render-method comparisons."""
from pathlib import Path
from PIL import Image
import hashlib,json,os
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-110-path-vdd'
qa=json.loads((R/'evidence/p15-110-render-qa.json').read_text())
old=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
base=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
vqa=json.loads((R/'evidence/p15-110-vision-qa.json').read_text())
angles=qa['renderAngles']
methods={
 'P15-101-original':{k:r['relativePath'] for k,r in base['methods']['head_alpha_blend'].items()},
 'P15-107-native':{k:r['relativePath'] for k,r in old['methods']['companion_direct_native_keys'].items()}}
methods.update({m:{k:r['path'] for k,r in frames.items()} for m,frames in qa['methods'].items()})
frames={};gifs={}
for m,paths in methods.items():
 frames[m]={};preview=[]
 for a in angles:
  k=f'{a:g}';path=R/paths[k]
  frames[m][k]=os.path.relpath(path,D)
  art=Image.open(path).convert('RGBA')
  back=Image.new('RGBA',art.size,'white');back.alpha_composite(art)
  preview.append(back.convert('RGB').resize((450,450),Image.Resampling.LANCZOS))
 loop=preview+preview[-2:0:-1]
 gif=D/(m+'-loop.gif')
 loop[0].save(gif,save_all=True,append_images=loop[1:],duration=180,loop=0,optimize=False)
 gifs[m]={'path':str(gif.relative_to(R)),'sha256':hashlib.sha256(gif.read_bytes()).hexdigest()}
css="""body{font:15px/1.5 system-ui;background:#192e42;color:#ecf2f9;max-width:1460px;margin:12px auto;padding:0 16px}h1{font-size:23px}h2{font-size:18px}p,small{color:#c2d0db}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{margin:0;padding:10px;border-radius:8px;background:#2c445b}img{width:100%;height:auto;display:block;background:white}figcaption{font-size:12px}label{display:block;margin:12px 0}select,input{padding:8px;box-sizing:border-box;width:100%;margin:6px 0 14px}@media(max-width:680px){.grid{grid-template-columns:1fr}}"""
opts=''.join(f'<option value="{m}">{m.replace("_"," ")}</option>' for m in frames)
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 · Three-View Vision Stroke Correspondence</title><style>'''+css+'''</style></head><body>
<h1>P0 · 60°–75° 服装真实笔画身份与遮挡验证</h1>
<p>基于 Codex 图像阅读对三张独立服装原画进行同名墨线跟踪，所有路径都绑定原图坐标、来源 SHA256、模型置信度及实际边缘距离。仅将同时满足三源可见性与几何约束的线条应用于局部双向变形；对照 P15-101 与 P15-107 完整角色基准。</p>
<label for="method">实际渲染方式</label><select id="method">'''+opts+'''</select>
<label for="yaw">角度：<b id="angle">60°</b></label><input id="yaw" type="range" min="0" max="8" step="1" value="0">
<div class="grid">
<figure><img id="frame" src="../p15-101-head-render/head_alpha_blend-yaw60.png" alt="真实1024动画帧"><figcaption>真实 P0 角色 1024×1024 RGBA</figcaption></figure>
<figure><img id="motion" src="P15-101-original-loop.gif" alt="九角度GIF循环"><figcaption>九角度双向循环</figcaption></figure></div>
<h2>源原画上直接标注的笔画</h2>
<div class="grid">
<figure><img src="../p15-110-vision-validated/yaw60-model-paths.jpg" alt="60度墨线路径"><figcaption>60° 原生服装源笔画</figcaption></figure>
<figure><img src="../p15-110-vision-validated/yaw67p5-model-paths.jpg" alt="67.5度墨线路径"><figcaption>67.5° 原生服装源笔画</figcaption></figure>
<figure><img src="../p15-110-vision-validated/yaw75-model-paths.jpg" alt="75度墨线路径"><figcaption>75° 原生服装源笔画</figcaption></figure>
<figure><img src="../p15-107-source-patches/consistent-garment-contact.jpg" alt="三张真实原画"><figcaption>三源独立服装原画</figcaption></figure>
</div>
<h2>真实服装变形对照</h2>
<figure><img src="vision-matched-bow-contact.jpg" alt="原画路径对照真实逐帧图"><figcaption>保留原画与源墨线对应的两种空间变形方法，九角度对照</figcaption></figure>
<small>可确认的是源原画中可见线的候选身份。隐藏面与内部笔画在其他视角没有可观察来源时，仍需要单独原画资产；原生角色完整转头的美术质量尚未通过。</small>
<script>
const frames='''+json.dumps(frames,separators=(',',':'))+''',angles='''+json.dumps(angles)+''';
const method=document.querySelector('#method'),yaw=document.querySelector('#yaw'),frame=document.querySelector('#frame'),motion=document.querySelector('#motion'),label=document.querySelector('#angle');
function update(){const m=method.value,a=String(angles[Number(yaw.value)]);label.textContent=a+'°';frame.src=frames[m][a];motion.src=m+'-loop.gif';}
method.addEventListener('change',update);yaw.addEventListener('input',update);
</script></body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
review={'schema':'KOMA_P15_110_VISION_PATH_REVIEW_V1','sourceAngles':[60,67.5,75],
 'renderedAngles':angles,'methodFrames':frames,'animations':gifs,
 'acceptedObservedStrokeRoles':vqa['experimentAcceptedRoles'],
 'entry':str((D/'index.html').relative_to(R)),
 'sourceInkArtistApproved':False,'fullYawVisualAccepted':False}
(R/'evidence/p15-110-review-qa.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
print('REVIEW',review['entry'],'methods',len(frames),'angles',len(angles),flush=True)

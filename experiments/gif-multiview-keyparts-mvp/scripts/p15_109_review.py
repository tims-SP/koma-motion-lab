#!/usr/bin/env python3
"""P0 source-observed garment stroke path evidence and full-frame preview."""
from pathlib import Path
from PIL import Image
from hashlib import sha256
import os,json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-109-collar-render'
report=json.loads((R/'evidence/p15-109-render-qa.json').read_text())
ref=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
ref101=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
angles=ref['angles']
inputFrames={
 'P15-101-original':{k:r['relativePath'] for k,r in ref101['methods']['head_alpha_blend'].items()},
 'P15-107-native':{k:r['relativePath'] for k,r in ref['methods']['companion_direct_native_keys'].items()}}
inputFrames.update({name:{k:item['path'] for k,item in data.items()} for name,data in report['methods'].items()})
gifs={};files={}
for method,frames in inputFrames.items():
 imgs=[];files[method]={}
 for angle in angles:
  k=f'{angle:g}';path=R/frames[k]
  files[method][k]=os.path.relpath(path,D)
  art=Image.open(path).convert('RGBA')
  back=Image.new('RGBA',art.size,'white');back.alpha_composite(art)
  imgs.append(back.convert('RGB').resize((440,440),Image.Resampling.LANCZOS))
 seq=imgs+imgs[-2:0:-1]
 f=D/(method+'-loop.gif')
 seq[0].save(f,save_all=True,append_images=seq[1:],duration=190,loop=0,optimize=False)
 gifs[method]={'path':str(f.relative_to(R)),'sha256':sha256(f.read_bytes()).hexdigest()}
css="""body{font:15px/1.55 system-ui;background:#192d3d;color:#edf3fa;max-width:1460px;margin:14px auto;padding:0 16px}h1{font-size:23px}h2{font-size:18px}p,small{color:#c4d2e0}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{margin:0;background:#2d465b;border-radius:8px;padding:10px}figure img{width:100%;display:block;background:#fff}figcaption{font-size:12px}label{display:block;margin:10px 0}select,input{box-sizing:border-box;width:100%;padding:8px;margin:5px 0 12px}@media(max-width:690px){.grid{grid-template-columns:1fr}}"""
opts=''.join(f'<option value="{x}">{x.replace("_"," ")}</option>' for x in inputFrames)
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 · Garment Stroke Correspondence Study</title><style>'''+css+'''</style></head><body>
<h1>P0 · 60°–75° 原画笔画对应验证</h1>
<p>三视角原画的可观测笔画路径均附有来源与位置证据。六组服装候选中，衣领左侧折线符合连续路径、归一化位置和长度约束。仅将有证据支持的路径应用于局部衣领纹理替换；头发和原始关键帧继续保留已确认的角色素材。</p>
<label for="method">实际渲染方法</label><select id="method">'''+opts+'''</select>
<label for="yaw">角度：<b id="angle">60°</b></label><input id="yaw" type="range" min="0" max="8" value="0" step="1">
<div class="grid">
<figure><img id="frame" src="../p15-101-head-render/head_alpha_blend-yaw60.png" alt="真实转头画面"><figcaption>1024×1024 角色动画帧</figcaption></figure>
<figure><img id="loop" src="P15-101-original-loop.gif" alt="实际九角度往返GIF"><figcaption>九角度双向循环 GIF</figcaption></figure></div>
<h2>三视角源图折线路径</h2>
<div class="grid">
<figure><img src="../p15-109-stroke-paths/yaw60-stroke-paths.png" alt="60度的真实墨线路径"><figcaption>60° 真正采样的原画路径</figcaption></figure>
<figure><img src="../p15-109-stroke-paths/yaw67p5-stroke-paths.png" alt="67.5度的真实墨线路径"><figcaption>67.5° 真实原画路径</figcaption></figure>
<figure><img src="../p15-109-stroke-paths/yaw75-stroke-paths.png" alt="75度的真实墨线路径"><figcaption>75° 真实原画路径</figcaption></figure>
<figure><img src="../p15-107-source-patches/consistent-garment-contact.jpg" alt="三视角素材颜色服装"><figcaption>三张独立原生服装图</figcaption></figure></div>
<h2>动画帧对照</h2>
<figure><img src="collar-path-contact.jpg" alt="局部折线路径重建的真实连续画面"><figcaption>现有基准与局部路径重建的九帧对照</figcaption></figure>
<small>此实验只验证来源可追踪的二维笔画对应、局部遮挡和渲染质量。对原画中缺失或误匹配的笔画保持独立审查。</small>
<script>
const files='''+json.dumps(files,separators=(',',':'))+''',angles='''+json.dumps(angles)+''';
const method=document.querySelector('#method'),yaw=document.querySelector('#yaw'),frame=document.querySelector('#frame'),loop=document.querySelector('#loop'),label=document.querySelector('#angle');
function update(){const m=method.value,a=String(angles[Number(yaw.value)]);label.textContent=a+'°';frame.src=files[m][a];loop.src=m+'-loop.gif';}
method.addEventListener('change',update);yaw.addEventListener('input',update);
</script></body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
review={'schema':'KOMA_P15_109_STROKE_PATH_REVIEW_V1','renderedAngles':angles,
 'methods':files,'animations':gifs,
 'entry':str((D/'index.html').relative_to(R)),
 'formalArtPathApproved':False,'continuousVisualAccepted':False}
(R/'evidence/p15-109-review-qa.json').write_text(json.dumps(review,indent=2,ensure_ascii=False)+'\n')
print('REVIEW',review['entry'],'methods',len(files),'angles',len(angles))

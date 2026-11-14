#!/usr/bin/env python3
"""Interactive actual source masks, corrected jacket trim, and yaw comparisons."""
from pathlib import Path
from hashlib import sha256
from PIL import Image,ImageDraw
import json,os,numpy as np
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-116-visibility-repair'
render=json.loads((R/'evidence/p15-116-render-qa.json').read_text())
src=json.loads((R/'evidence/p15-115-source-qa.json').read_text())
base=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
base101=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
base115=json.loads((R/'evidence/p15-115-local-qa.json').read_text())
angles=render['renderAngles']
refs={'P15-101-original':{k:z['relativePath'] for k,z in base101['methods']['head_alpha_blend'].items()},
      'P15-107-native':{k:z['relativePath'] for k,z in base['methods']['companion_direct_native_keys'].items()},
      'P15-115-inkCore':{k:z['path'] for k,z in base115['methods']['ink_core'].items()},
      **{m:{k:z['path'] for k,z in fs.items()} for m,fs in render['models'].items()}}
paths={};gifs={}
for method,files in refs.items():
 paths[method]={};seq=[]
 for angle in angles:
  key=f'{angle:g}';f=R/files[key]
  paths[method][key]=os.path.relpath(f,D)
  img=Image.open(f).convert('RGBA')
  white=Image.new('RGBA',img.size,'white');white.alpha_composite(img)
  seq.append(white.convert('RGB').resize((450,450),Image.Resampling.LANCZOS))
 loop=seq+seq[-2:0:-1]
 gif=D/(method+'-loop.gif')
 loop[0].save(gif,save_all=True,append_images=loop[1:],duration=190,loop=0,optimize=False)
 gifs[method]={'path':str(gif.relative_to(R)),'sha256':sha256(gif.read_bytes()).hexdigest()}
sheet=Image.new('RGB',(350*len(angles),3*302),'white');draw=ImageDraw.Draw(sheet)
for col,angle in enumerate(angles):
 key=f'{angle:g}'
 a=Image.open(R/refs['P15-107-native'][key]).convert('RGBA')
 b=Image.open(R/refs['trim_matte'][key]).convert('RGBA')
 def white(im):
  bg=Image.new('RGBA',im.size,'white');bg.alpha_composite(im);return bg.convert('RGB')
 aa=np.asarray(white(a)).astype(np.float32)
 bb=np.asarray(white(b)).astype(np.float32)
 difference=np.uint8(np.minimum(np.abs(aa-bb)*5,255))
 for row,im in enumerate((Image.fromarray(np.uint8(aa)),Image.fromarray(np.uint8(bb)),Image.fromarray(difference))):
  sheet.paste(im.crop((390,700,860,1015)).resize((350,280),Image.Resampling.LANCZOS),(col*350,row*302+22))
  draw.text((col*350+4,row*302+3),['native P0','source owned trim','absolute RGB x5'][row]+f' {angle:g}',fill='black')
sheet.save(D/'trim-reference-difference.jpg',quality=93)
css="""body{background:#172b40;color:#eef5fa;max-width:1500px;padding:0 16px;margin:14px auto;font:15px/1.5 system-ui}h1{font-size:22px}h2{font-size:18px}p,small{color:#c1d0de}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{margin:0;background:#30465c;padding:10px;border-radius:8px}img{display:block;width:100%;background:white}figcaption{font-size:12px}select,input{width:100%;padding:8px;box-sizing:border-box;margin:6px 0 13px}label{display:block;margin:10px 0}@media(max-width:700px){.grid{grid-template-columns:1fr}}"""
options=''.join(f'<option value="{method}">{method.replace("_"," ")}</option>' for method in paths)
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 · Source-Owned Visibility Boundaries</title><style>'''+css+'''</style></head><body>
<h1>P0 · 衣襟可见性与源纹理局部修正</h1>
<p>基于 P15-107 完整角色源帧，在蝴蝶结、金饰和左右金边的真实可见掩码内分别验证单源纹理及隐藏边界。原生 60°、67.5°、75° 关键帧按文件字节完整保留，非关键帧使用来源几何约束；P15-115 的金边归属规则保留 75° 的原生右侧金边。</p>
<label for="method">真实渲染方式</label><select id="method">'''+options+'''</select>
<label for="yaw">目标视角：<b id="angle">60°</b></label><input id="yaw" type="range" min="0" max="8" step="1" value="0">
<div class="grid">
<figure><img id="frame" src="../p15-101-head-render/head_alpha_blend-yaw60.png" alt="实际1024原画渲染帧"><figcaption>实际角色渲染帧</figcaption></figure>
<figure><img id="loop" src="P15-101-original-loop.gif" alt="真实九帧双向GIF"><figcaption>双向九角度动画</figcaption></figure>
</div>
<h2>真实 P0 原画与金边修正差异</h2>
<figure><img src="trim-reference-difference.jpg" alt="原生金边和局部修正及像素差异"><figcaption>上：原生背景；中：金边局部修正；下：RGB 绝对差异×5（仅辅助显示变化位置）</figcaption></figure>
<h2>全部候选逐帧对照</h2>
<figure><img src="source-matte-occlusion-contact.jpg" alt="九角度的来源掩码和遮挡策略对照"><figcaption>角色原画、局部纹理归属及边缘修正的九帧对照</figcaption></figure>
<small>工程检查包括来源哈希、像素改变边界、关键帧字节一致性、帧间局部差异与浏览器操作。完整 360° 美术验收仍为独立门禁。</small>
<script>
const files='''+json.dumps(paths,separators=(',',':'))+''',angles='''+json.dumps(angles)+''';
const method=document.querySelector('#method'),yaw=document.querySelector('#yaw'),frame=document.querySelector('#frame'),loop=document.querySelector('#loop'),angle=document.querySelector('#angle');
function update(){let m=method.value,a=String(angles[Number(yaw.value)]);angle.textContent=a+'°';frame.src=files[m][a];loop.src=m+'-loop.gif';}
method.addEventListener('change',update);yaw.addEventListener('input',update);
</script></body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
review={'schema':'KOMA_P15_116_VISIBILITY_REVIEW_V1','character':'p0_character_001',
 'angles':angles,'methodFrames':paths,'animations':gifs,
 'evidenceSHA256':sha256((R/'evidence/p15-116-render-qa.json').read_bytes()).hexdigest(),
 'entry':str((D/'index.html').relative_to(R)),
 'sourceNativeKeyframesPreserved':True,'artistFullYawAccepted':False}
(R/'evidence/p15-116-review-qa.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
print('REVIEW',review['entry'],'methods',len(paths),'angles',len(angles))

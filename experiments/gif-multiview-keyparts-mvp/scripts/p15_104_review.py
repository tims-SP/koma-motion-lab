#!/usr/bin/env python3
"""P0 60°–75° real native garment ink tied landmark ArtMesh review."""
from pathlib import Path
from PIL import Image
from hashlib import sha256
import json,os
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports';D=P/'p15-104-detail-render'
detail=json.loads((R/'evidence/p15-104-render-qa.json').read_text())
previous=json.loads((R/'evidence/p15-103-render-qa.json').read_text())
head=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
angles=detail['angles'];sources={
 'P15-101-baseline':head['methods']['head_alpha_blend'],
 'P15-103-part-grid':previous['methods']['all_parts_blend']}
sources.update(detail['methods'])
review={}
for name,records in sources.items():
 images=[]
 review[name]={}
 for a in angles:
  k=f'{a:g}'
  src=R/records[k]['relativePath']
  im=Image.open(src).convert('RGBA');white=Image.new('RGBA',im.size,'white');white.alpha_composite(im)
  images.append(white.convert('RGB').resize((490,490),Image.Resampling.LANCZOS))
  review[name][k]=os.path.relpath(src,D)
 seq=images+images[-2:0:-1]
 gif=D/(name+'-loop.gif')
 seq[0].save(gif,save_all=True,append_images=seq[1:],duration=170,loop=0,optimize=False)
 detail.setdefault('animations',{})[name]={'path':str(gif.relative_to(R)),'sha256':sha256(gif.read_bytes()).hexdigest()}
css="""body{font:15px/1.53 system-ui;background:#182839;color:#edf3fa;max-width:1460px;margin:12px auto;padding:0 16px}h1{font-size:23px}h2{font-size:18px}p,small{color:#bfcedc}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{background:#2a4055;border-radius:8px;padding:11px;margin:0}figure img{width:100%;display:block;object-fit:contain;background:white}figcaption{font-size:12px}label{display:block;margin:11px 0}select,input{width:100%;padding:8px;box-sizing:border-box;margin:5px 0 12px}@media(max-width:700px){.grid{grid-template-columns:1fr}}"""
options=''.join(f'<option value="{name}">{name.replace("_"," ")}</option>' for name in review)
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 · Garment Ink Correspondence VDD Review</title><style>'''+css+'''</style></head><body>
<h1>P0 · 60°–75° 衣领、蝴蝶结褶皱、金饰、肩部线稿对应</h1>
<p>通过源原画 SIFT 互选与 RANSAC 提取候选墨线对应点，再施加掩膜归属、运动位移和三角网格不翻转约束。与 P15-103 九点部件网格及 P15-101 视觉基准对照，展示实际的两端原画及所有中间角度。</p>
<label for="method">视角间插值策略</label><select id="method">'''+options+'''</select>
<label for="yaw">渲染目标：<b id="label">60°</b></label><input id="yaw" type="range" min="0" max="8" value="0" step="1">
<div class="grid">
<figure><img id="current" src="../p15-101-head-render/head_alpha_blend-yaw60.png" alt="实际渲染帧"><figcaption>1024×1024 RGBA 源与中间帧</figcaption></figure>
<figure><img id="motion" src="P15-101-baseline-loop.gif" alt="连续转头实际GIF"><figcaption>正向及返程循环</figcaption></figure>
</div>
<h2>真实对应点与共用网格</h2>
<div class="grid">
<figure><img src="../p15-104-detail-landmarks/bow-sift-matches.jpg" alt="蝴蝶结褶皱的真实特征对应"><figcaption>蝴蝶结匹配点与几何约束</figcaption></figure>
<figure><img src="../p15-104-detail-landmarks/shoulder_left-sift-matches.jpg" alt="肩部金边的真实特征对应"><figcaption>肩部饰线匹配点与几何约束</figcaption></figure>
<figure><img src="../p15-104-detail-mesh/bow-yaw60.png" alt="60度蝴蝶结网格"><figcaption>60° 共享面索引与真实内部锚点</figcaption></figure>
<figure><img src="../p15-104-detail-mesh/bow-yaw75.png" alt="75度蝴蝶结网格"><figcaption>75° 对应 UV 与纹理</figcaption></figure>
</div>
<h2>全角度质量对照</h2>
<figure><img src="detail-garment-contact.jpg" alt="P15-101 P15-103 P15-104连续画面对照"><figcaption>前两轮基准与当前候选渲染</figcaption></figure>
<small>几何不翻面、端点原画像素保真以及图像加载是工程门禁。内部墨线是否唯一、连续和自然属于独立的视觉门禁。</small>
<script>
const frames='''+json.dumps(review,separators=(',',':'))+''',angles='''+json.dumps(angles)+''';
const method=document.querySelector('#method'),yaw=document.querySelector('#yaw'),
current=document.querySelector('#current'),motion=document.querySelector('#motion'),label=document.querySelector('#label');
function update(){const m=method.value,a=String(angles[Number(yaw.value)]);label.textContent=a+'°';current.src=frames[m][a];motion.src=m+'-loop.gif'}
method.addEventListener('change',update);yaw.addEventListener('input',update)
</script></body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
report={'schema':'KOMA_P15_104_DETAIL_REVIEW_V1','angles':angles,'frameFiles':review,
 'animations':detail['animations'],'entry':'private-assets/exports/p15-104-detail-render/index.html',
 'visualAccepted':False}
(R/'evidence/p15-104-review-qa.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print('REVIEW',report['entry'],'methods',len(review),'angles',len(angles),flush=True)

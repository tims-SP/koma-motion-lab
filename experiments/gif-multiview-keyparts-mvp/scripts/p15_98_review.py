#!/usr/bin/env python3
"""Interactive 52.5-75 P0 semantic-anchor VDD research review."""
from pathlib import Path
from PIL import Image
import hashlib,json
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-98-vdd-review'
q=json.loads((R/'evidence/p15-98-anchor-vdd-qa.json').read_text())
methods=list(q['methodFrames']);angles=q['anglesDegrees']
for method in methods:
 frames=[]
 for ang in angles:
  path=R/q['methodFrames'][method][f'{ang:g}']['relativePath']
  assert path.is_file(),path
  im=Image.open(path).convert('RGBA')
  bg=Image.new('RGBA',im.size,'white');bg.alpha_composite(im)
  frames.append(bg.convert('RGB').resize((480,480),Image.Resampling.LANCZOS))
 animation=frames+frames[-2:0:-1]
 anim=D/f'{method}-loop.gif'
 frames[0].save(anim,save_all=True,append_images=animation[1:],duration=170,loop=0,optimize=False)
 q.setdefault('animated',{})[method]={'sha256':hashlib.sha256(anim.read_bytes()).hexdigest(),
         'relativePath':str(anim.relative_to(R))}
css="""body{background:#162638;color:#f3f6fa;font:15px/1.5 system-ui;max-width:1500px;margin:12px auto;padding:0 16px}h1{font-size:23px}h2{font-size:18px}p{color:#bacbdc}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{margin:0;padding:10px;border-radius:8px;background:#2a4057}img{display:block;width:100%;object-fit:contain;background:#fff}figcaption{font-size:12px}label{display:block;margin:12px 0}input,select{width:100%;padding:8px}table{width:100%;border-collapse:collapse}td,th{border-bottom:1px solid #384d63;text-align:left;padding:7px}small{color:#b7c8da}@media(max-width:690px){.grid{grid-template-columns:1fr}}"""
items=''.join(f'<option value="{m}">{m.replace("_"," ")}</option>' for m in methods)
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 · 52.5-75° Semantic VDD comparison</title><style>'''+css+'''</style></head><body>
<h1>P0 · 连续转头 52.5°–75° 对照验收</h1>
<p>原画来自 Codex 独立多视角资产，局部前发来自 SAM3 语义蒙版和 P15-97 已验证的 6px 发梢位移。DIS 光流与基于视觉代理锚点的 VDD 直接对照。当前为研究候选，面部连续性、美术质量和真实几何角度均未通过正式验收。</p>
<label for="method">渲染方式</label>
<select id="method">'''+items+'''</select>
<label for="yaw">目标角度：<b id="angle-value">52.5°</b></label>
<input id="yaw" type="range" min="0" max="8" step="1" value="0">
<div class="grid">
<figure><img id="current" src="dis_blend-yaw52p5.png" alt="当前插值角度候选"><figcaption>指定方法与角度的真实输出</figcaption></figure>
<figure><img id="loop" src="dis_blend-loop.gif" alt="当前方法的循环转头预览"><figcaption>正向及返程循环的实际 GIF</figcaption></figure></div>
<h2>全部角度比较</h2><figure><img src="three-method-contact.jpg" alt="全部方法与角度的视觉对比"><figcaption>相同身份原画与不同插值算法的脸部区域对比</figcaption></figure>
<h2>原画语义锚点</h2><figure><img src="../p15-98-anchor-review/source-landmark-overview.jpg" alt="各独立角度的手动锚点代理"><figcaption>眼睛、鼻子、刘海根部、发梢及面部轮廓的视觉代理点</figcaption></figure>
<small>约束：源关键帧像素哈希保真。候选输出具有可检验的几何流场，但视觉连续性尚需逐帧人工检查。</small>
<script>
const methods='''+json.dumps(methods)+''',angles='''+json.dumps(angles)+''';
const method=document.querySelector('#method'),yaw=document.querySelector('#yaw'),label=document.querySelector('#angle-value'),current=document.querySelector('#current'),loop=document.querySelector('#loop');
function update(){const m=method.value,a=angles[Number(yaw.value)];label.textContent=a+'°';current.src=m+'-yaw'+String(a).replace('.','p')+'.png';loop.src=m+'-loop.gif';}
method.addEventListener('change',update);yaw.addEventListener('input',update);
</script></body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
q['review']='private-assets/exports/p15-98-vdd-review/index.html'
(R/'evidence/p15-98-anchor-vdd-qa.json').write_text(json.dumps(q,indent=2,ensure_ascii=False)+'\n')
print('HTML',D/'index.html','methods',len(methods),'yaw',len(angles))

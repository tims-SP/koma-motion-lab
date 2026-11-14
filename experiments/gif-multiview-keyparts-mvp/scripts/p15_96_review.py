#!/usr/bin/env python3
"""P0 yaw60 root-pinned front-bang visual review in real browser."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports'
D=P/'p15-96-yaw060-root-artmesh'
q=json.loads((R/'evidence/p15-96-motion-qa.json').read_text())
assert q['frameCount']==13
for dx in range(13):assert (D/f'frame-{dx:02}.png').is_file()
css="""body{font:15px/1.5 system-ui;background:#162738;color:#eef3fa;margin:14px auto;padding:0 16px;max-width:1460px}h1{font-size:23px}h2{font-size:18px}p{color:#becdda}.layout{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.compare{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{margin:0;padding:10px;border-radius:8px;background:#273d54}img{background:white;object-fit:contain;width:100%;height:auto}figcaption{font-size:12px}label{display:block;margin:8px 0}input{width:100%}.caption{font-size:12px;color:#becdda}@media(max-width:680px){.layout,.compare{grid-template-columns:1fr}}"""
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P0 60° 前发局部 ArtMesh 动画验收</title><style>'''+css+'''</style></head><body>
<h1>P0 · 60° 前发根部固定与发梢运动</h1>
<p>原画像素是身份基准；新增 13 帧仅修改有语义归属的前发区域。额头根部由局部约束固定，遮挡暴露区域使用有来源的隐藏脸部纹理。正式 ArtMesh 及跨角度连续旋转仍需独立验收。</p>
<label for="pose">位移：<strong id="offset">0</strong> px</label>
<input id="pose" type="range" min="0" max="12" value="0" step="1">
<div class="layout"><figure><img src="../p15-92-angle-keyart/yaw060-registered.png" alt="角色原始关键原画"><figcaption>原始 60° 原画</figcaption></figure>
<figure><img id="candidate" src="frame-00.png" alt="局部前发动态候选"><figcaption>根部固定，发梢平滑变形</figcaption></figure></div>
<h2>固定区与发梢的对照</h2>
<div class="compare"><figure><img src="motion-contact.jpg" alt="四个姿态的局部视觉对照"><figcaption>0、4、8、12px 实际运动画面</figcaption></figure>
<figure><img src="../p15-96-root-pinned/root-pinned-contact.jpg" alt="四种根部约束方案对照"><figcaption>根部锚定位置的效果比较</figcaption></figure></div>
<h2>动画预览</h2><figure><img src="root-pinned-13-poses.gif" alt="13帧连续动作"><figcaption>基于 0–12px 的连续 GIF 预览</figcaption></figure>
<script>
const slider=document.querySelector('#pose'),label=document.querySelector('#offset'),image=document.querySelector('#candidate');
slider.addEventListener('input',()=>{const id=String(slider.value).padStart(2,'0');label.textContent=slider.value;image.src='frame-'+id+'.png';});
</script></body></html>'''
(D/'index.html').write_text(html,encoding='utf-8')
print('HTML',D/'index.html')

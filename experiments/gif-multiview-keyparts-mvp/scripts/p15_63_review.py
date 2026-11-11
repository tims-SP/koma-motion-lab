#!/usr/bin/env python3
"""Build static local HTML viewer; the source and diagnostic images stay unmodified."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-63-masked-lama'
q=json.loads((R/'evidence/p15-63-masked-lama-qa.json').read_text())
tiles=[
('source-face.png','原 P15-56 右向候选'),
('underpaint-face.png','LaMa 神经补绘后的无遮挡皮肤'),
('shift-face.png','近眼右移 18px：仍有边缘和发丝残片'),
('input-512.png','发送给模型的 512px 输入'),
('mask-512.png','仅近眼位置的黑白 Mask'),
('model-512.png','模型直接生成的 512px 图'),
('eye-near-cutout.png','粗略眼部 ROI：仍含非眼睛像素'),
('underpaint-full.png','严格限制 Mask 内改动的整图'),
('eye-shift18.png','眼部位移完整画面')]
css='''body{max-width:1480px;margin:16px auto;padding:0 16px;background:#162637;color:#f1f4fb;font:15px/1.55 system-ui}h1{font-size:25px}.warn{color:#ffce9b}.good{color:#b1e1cd}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:14px}figure{margin:0;background:#293e53;padding:12px;border-radius:8px}img{width:100%;max-height:650px;object-fit:contain;background:repeating-conic-gradient(#e0e0e0 0 25%,white 0 50%) 50%/22px 22px}figcaption{margin-top:5px;font-weight:600}p{color:#d2dce8}'''
s='<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-63 · Masked neural underpaint</title><style>'+css+'</style></head><body><h1>P15-63 · 近眼神经补绘与语义层门禁</h1>'
s+='<p class="good">LaMa 神经补绘成功。Mask 内改动 '+str(q['insideMaskChangedPixels'])+' 像素，Mask 外改动 0，右移 18px 无透明洞。与 P15-62 的面颊复制不同，补绘使用神经网络预测被遮挡内容。</p>'
s+='<p class="warn">正式视觉门禁仍不通过：右移后的近眼 ROI 含头发和皮肤碎片，边缘出现不自然的亮色轮廓。遮罩内新底图可进入候选库，但近眼 ArtMesh 尚未得到语义纯净图层，不能进入正式 VDD。</p><div class="grid">'
for p,desc in tiles:
 assert (D/p).exists(),p
 s+=f'<figure><img src="{p}" alt="{desc}"><figcaption>{desc}</figcaption></figure>'
s+='</div><p>来源 SHA256 与严格像素断言参见 qa/p15-63-masked-lama-qa.json。</p></body></html>'
(D/'index.html').write_text(s)
print('HTML',len(tiles))

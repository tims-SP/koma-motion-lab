from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-89-masked-local-art'
q=json.loads((R/'evidence/p15-89-final-qa.json').read_text())
css='''body{background:#172739;color:#eff5fb;max-width:1450px;margin:20px auto;padding:0 16px;font:15px/1.55 system-ui}h1{font-size:24px}h2{font-size:18px}p{color:#d7e2eb}.warn{color:#ffd19a}.ok{color:#b9e7c9}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}figure{margin:0;background:#2b4053;border-radius:8px;padding:12px}img{width:100%;max-height:610px;object-fit:contain;background:repeating-conic-gradient(#ddd 0 25%,#fff 0 50%) 50%/24px 24px}figcaption{margin-top:8px}'''
html='<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-89 Mask 修复验证</title><style>'+css+'</style></head><body><h1>P15-89 · 空间约束 Mask 实际推理</h1>'
html+='<p>原始完整 1024×1024 画布、独立控制线稿、局部 Mask 均已真实准备，Mask 与原始图以独立参数提交给模型服务。</p>'
html+='<p class="warn"><b>正式视觉门禁：未通过。</b> Qwen ControlNet 状态 '+q['qwenStatus']+'；SD Mask 状态 '+q['sdStatus']+'。无论推理是否返回，均不自动替换正式 ArtMesh；只有经过 0/9/18px 真实动态视觉审查才能批准。</p><div class="grid">'
imgs=[('full-source-1024.png','完整同视角原底图'),('local-mask-1024.png','独立局部灰度修复 Mask'),('control-lineart-1024.png','结构控制线稿'),('mask-region-overlay.png','残线周围 Mask 放大')]
imgs += [(f'baseline-{n:02d}-face.png',f'原 P15-86 {n}px 运动参考') for n in (0,9,18)]
for kind in q.get('modelCandidates',{}):
 imgs.extend([(f'{kind}-model-aligned-canvas.png',kind+' 模型输出对齐画布'),(f'{kind}-strict-mask-preview.png',kind+' 仅 Mask 内替换的安全检查候选')])
for file,label in imgs:
 assert (D/file).exists(),file
 html+=f'<figure><img src="{file}" alt="{label}"><figcaption>{label}</figcaption></figure>'
html+='</div></body></html>'
(D/'index.html').write_text(html,encoding='utf-8')
print('IMAGES',len(imgs))

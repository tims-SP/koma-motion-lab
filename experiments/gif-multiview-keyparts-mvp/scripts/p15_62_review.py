from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-62-near-eye-underpaint'
q=json.loads((R/'evidence/p15-62-near-eye-underpaint-qa.json').read_text())
tiles=[('source-face.png','原始右向候选面部'),('underpaint-face.png','局部皮肤底图：清除了近眼'),('shifted-face.png','近眼右移 18px 后合成'),('eye.near.cutout.png','独立近眼切片（实验）'),('skin.underpaint.png','局部皮肤底图（实验）')]
css='''body{margin:18px auto;padding:0 16px;max-width:1400px;background:#172533;color:#eff4fa;font:15px/1.5 system-ui}h1{font-size:24px}.warn{color:#ffc89c}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}figure{margin:0;padding:12px;background:#283d50;border-radius:8px}img{width:100%;object-fit:contain;background:repeating-conic-gradient(#d9dce2 0 25%,white 0 50%) 50%/20px 20px}figcaption{font-weight:650;margin-top:6px}p{color:#d3dce8}'''
s='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-62 近眼 underpaint 实验</title><style>'+css+'</style><h1>P15-62 · 近眼底图与 18px 位移</h1>'
s+='<p class="warn"><b>工程通过、视觉失败：</b>局部 ROI 内无透明洞，但采用邻近脸颊纹理复制，不是真正的独立原画；放大可见补片色调和边界不自然，不能作为正式 ArtMesh。</p><p>生成式补绘曾尝试通过 Hugging Face Qwen-Image-Edit 2511 Anime-V2；当前已连接账户 ZeroGPU 免费配额耗尽，未取得可用模型输出。下面只展示本地纹理复制的诊断结果。</p><div class="grid">'
for f,label in tiles:s+=f'<figure><img src="{f}" alt="{label}"><figcaption>{label}</figcaption></figure>'
s+='</div><p>ROI: '+str(q['eyeMaskPolygon'])+'；donor: '+str(q['donorRect'])+'；位移: 18px。透明洞像素 '+str(q['transparentHolePixelsNearEyeROI'])+'；遮罩外改动 '+str(q['outsideMaskChangedPixels'])+'。</p></html>'
(D/'index.html').write_text(s,encoding='utf8')

from pathlib import Path
D=Path(__file__).resolve().parents[1]/'private-assets/exports/p15-54-edge-landmark-review'
items=[
('before-clip-detail.png','P15-53 修复前发夹局部'),
('after-clip-detail.png','P15-54 局部边缘清理后'),
('candidate-refined.png','修订后的透明候选'),
('landmark-comparison.png','青色为人工测量位置，洋红为工程预期锚点'),
('preview-light.png','浅色背景检查'),
('preview-blue.png','蓝色背景检查'),
('preview-pink.png','粉色背景检查')]
s='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-54 · 发夹边缘与面部锚点审查</title><style>body{background:#172331;color:#edf3fa;font:15px/1.55 system-ui;max-width:1400px;margin:18px auto;padding:0 18px}h1{font-size:23px}p{color:#ccd8e6}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}figure{margin:0;padding:12px;background:#283b4f;border-radius:8px}img{width:100%;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#d9dde6 0 25%,#fff 0 50%) 50%/24px 24px}figcaption{font-weight:650;margin-top:6px}</style><h1>P15-54 · 发夹边缘与面部锚点审查</h1><p><b>结论：</b>眼、鼻、嘴、下颌的人工估点与既有代理锚点接近；发夹中心仍有约37px偏差。该锚点来自两视角外推，不足以证明绝对65°。发夹边缘仍需人工修图，不准入正式 ArtMesh。</p><div class="grid">'''
for n,t in items:
 assert (D/n).exists()
 s+=f'<figure><img src="{n}" alt="{t}"><figcaption>{t}</figcaption></figure>'
s+='</div>'
(D/'index.html').write_text(s,encoding='utf8')

from pathlib import Path
D=Path(__file__).resolve().parents[1]/'private-assets/exports/p15-53-gold-clip-repair'
tiles=[
 ('before-clip-zoom.png','修复前：发夹侧向压缩'),
 ('after-clip-zoom.png','修复后：交叉结构清晰，边缘残影仍需处理'),
 ('source-clip-clip-zoom.png','复用的旧 P0 65° 发夹独立图层'),
 ('hair.clip.cross_gold.png','独立透明发夹（1024×1024 RGBA）'),
 ('underlay-repaired.png','原发夹清理后的底图'),
 ('candidate-gold-cross-restored.png','发夹独立合成候选'),
 ('preview-light.png','浅色背景检查'),
 ('preview-blue.png','蓝色背景检查'),
 ('preview-pink.png','粉色背景检查')]
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-53 · 发夹局部修复审查</title><style>body{background:#172331;color:#f2f5fa;font:15px/1.5 system-ui;max-width:1440px;padding:0 16px;margin:18px auto}h1{font-size:24px}p{color:#ced9e6}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}figure{margin:0;background:#283b4f;padding:12px;border-radius:6px}img{width:100%;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#d9dde6 0 25%,#fff 0 50%) 50%/24px 24px}figcaption{margin:6px 0;font-weight:600}</style><h1>P15-53 · 金色交叉发夹局部修复</h1><p>发夹来源为项目旧 P0 65° 透明部件，未重新生成人物。恢复了交叉结构，但仍有边缘残影，绝对 65° 也未标定。此包属于工程候选，不得覆盖正式 ArtMesh。</p><div class="grid">'''
for n,label in tiles:
 assert (D/n).exists(),n
 html+=f'<figure><img src="{n}" alt="{label}"><figcaption>{label}</figcaption></figure>'
html+='</div>'
(D/'index.html').write_text(html,encoding='utf8')
print('review assets',len(tiles))

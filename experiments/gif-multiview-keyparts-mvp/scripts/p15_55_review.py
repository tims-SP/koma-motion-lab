from pathlib import Path
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-55-registration'
tiles=[('crop-former.png','P15-54：原始发夹位置'),('crop--22.png','P15-55：左移 22px'),('crop--28.png','P15-55：左移 28px（选用）'),('clip--28.png','分离的发夹透明层'),('underlay--28.png','旧发夹区域修复底图'),('candidate--28.png','透明候选合成'),('preview--28-light.png','浅色背景'),('preview--28-blue.png','蓝色背景'),('preview--28-pink.png','粉色背景')]
style='''body{background:#172331;color:#edf3fa;font:15px/1.5 system-ui;max-width:1450px;margin:18px auto;padding:0 16px}h1{font-size:24px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}figure{margin:0;background:#283b4f;padding:12px}img{width:100%;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#d6dae2 0 25%,#fff 0 50%) 50%/24px 24px}figcaption{margin-top:8px;font-weight:600}p{color:#ccd8e7}'''
html='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>P15-55 发夹坐标与遮挡验收</title><meta name="viewport" content="width=device-width, initial-scale=1"><style>'+style+'</style><h1>P15-55 · 发夹重注册与透明遮挡检查</h1><p>按实际发丝轮廓挂载，不强制对齐两视角外推的单点。交叉发夹移至发丝内侧，但放大仍可见残留描边与克隆纹理差异；暂不批准正式 65° 原画。</p><div class="grid">'
for name,label in tiles:
 assert (D/name).is_file(),name
 html+=f'<figure><img src="{name}" alt="{label}"><figcaption>{label}</figcaption></figure>'
(D/'index.html').write_text(html+'</div>',encoding='utf8')
print('review',len(tiles))

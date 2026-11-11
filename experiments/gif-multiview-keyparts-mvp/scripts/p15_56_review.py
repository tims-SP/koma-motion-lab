from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-56-edge-matting'
tiles=[('crop-erode-1.png','透明蒙版收缩 1px'),('crop-erode-2.png','透明蒙版收缩 2px（选用）'),('crop-erode-3.png','透明蒙版收缩 3px'),('clip-erode-2.png','独立发夹透明图层'),('candidate-erode-2.png','修订后的透明合成'),('preview-2-light.png','浅色背景'),('preview-2-blue.png','蓝色背景'),('preview-2-pink.png','粉色背景')]
style='''body{background:#172331;color:#edf3fa;font:15px/1.5 system-ui;max-width:1450px;margin:18px auto;padding:0 16px}h1{font-size:24px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}figure{margin:0;background:#283b4f;padding:12px}img{width:100%;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#d6dae2 0 25%,#fff 0 50%) 50%/24px 24px}figcaption{margin-top:8px;font-weight:600}p{color:#ccd8e7}'''
h='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-56 发夹透明边缘精修</title><style>'+style+'</style><h1>P15-56 · 发夹透明边缘精修</h1><p>同一独立发夹图层分别收缩 alpha 1px、2px、3px。选择 2px：抑制粉色外缘，同时保留金属交叉臂端部。角色底图及正式 ArtMesh 均未修改。绝对 65° 及角色身份仍未完成最终校准。</p><div class="grid">'
for n,t in tiles:
 assert (D/n).exists()
 h+=f'<figure><img src="{n}" alt="{t}"><figcaption>{t}</figcaption></figure>'
(D/'index.html').write_text(h+'</div>',encoding='utf8')

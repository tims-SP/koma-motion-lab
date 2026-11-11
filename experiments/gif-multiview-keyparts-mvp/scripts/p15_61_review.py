from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-61-semantic-feasibility'
q=json.loads((R/'evidence/p15-61-semantic-feasibility-qa.json').read_text())
tiles=[
 ('source45-face.png','P0 45° 面部源图'),
 ('target65-face.png','当前右向候选（名义 65°）'),
 ('eye-shift-with-hole-face.png','近眼右移 18px：露出底图空洞'),
 ('eye.near.visible.png','近眼 ROI：含皮肤背景'),
 ('eye.far.visible.png','远眼 ROI：含眼周背景'),
 ('nose.visible.png','鼻区域可见裁切'),
 ('mouth.visible.png','嘴区域可见裁切'),
 ('hair.ahoge.visible.png','呆毛区域可见裁切'),
 ('hair.clip.cross_gold.independent.png','此前独立发夹 RGBA 层'),
 ('remaining.visible.composite.png','剩余完整合成底图（并非下层原画）'),
 ('reconstructed.png','ROI 回拼：像素一致，但不等于 ArtMesh')]
css='''body{margin:18px auto;padding:0 16px;max-width:1480px;background:#172533;color:#eff4fa;font:15px/1.5 system-ui}h1{font-size:24px}h2{font-size:18px}.warn{color:#ffc89c}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:14px}figure{margin:0;padding:12px;background:#283d50;border-radius:8px}img{width:100%;object-fit:contain;max-height:500px;background:repeating-conic-gradient(#d9dce2 0 25%,white 0 50%) 50%/24px 24px}figcaption{font-weight:650;margin-top:6px}p{color:#d3dce8}code{overflow-wrap:anywhere}'''
s='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-61 新原画语义分层验收</title><style>'+css+'</style><h1>P15-61 · 新原画语义分层可行性验证</h1>'
s+='<p class="warn"><b>视觉门禁失败：</b>可见像素虽然能够按区域切出、完全回拼，但不包含隐藏皮肤、眼白或头发底色。单独移动近眼 18px，原区域产生 '+str(q['movingEye']['transparentHolePixelsInNearEyeROI'])+' 个明显透明缺口像素；无法作为真实 ArtMesh。</p><div class="grid">'
for file,desc in tiles:
 assert (D/file).exists(),file
 s+=f'<figure><img src="{file}" alt="{desc}"><figcaption>{desc}</figcaption></figure>'
s+='</div><h2>技术结论</h2><p>当前角色右向候选仅有整张合成 PNG。五官和呆毛的多边形可见 ROI 包含邻近头发、皮肤及眼周像素，没有纯净的语义边界。金色交叉发夹是目前真正独立、带独立底图的 RGBA 部件。下一阶段须生成/绘制被遮挡的皮肤和头发底图、清洁五官遮罩，再验证局部形变和遮挡。</p>'
(D/'index.html').write_text(s,encoding='utf8')
print('review tiles',len(tiles))

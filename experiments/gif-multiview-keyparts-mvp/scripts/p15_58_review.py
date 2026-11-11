from pathlib import Path
import json,html
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-58-provenance-pose'
q=json.loads((R/'evidence/p15-58-provenance-pose-qa.json').read_text())
tiles=[
('canonical45.png','P0 45° · 可信工程源'),
('relative-plus20-candidate.png','相对 +20° · 当前候选'),
('historical90.png','历史 90° · 仅用于视觉参考'),
('canonical45-face.png','45° 面部局部'),
('relative-plus20-candidate-face.png','候选面部局部'),
('relative-plus20-candidate-clip.png','候选金色发夹细节')]
style='''body{margin:18px auto;padding:0 18px;max-width:1500px;background:#182533;color:#edf3fa;font:15px/1.55 system-ui}h1{font-size:24px}h2{font-size:18px}p{color:#d2dce8}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}figure{margin:0;padding:12px;background:#2a3b50;border-radius:6px}img{width:100%;object-fit:contain;background:repeating-conic-gradient(#ddd 0 25%,#fff 0 50%) 50%/24px 24px}figcaption{margin-top:7px;font-weight:650}table{border-collapse:collapse;width:100%}td,th{padding:9px;text-align:left;border-bottom:1px solid #506479}.warn{color:#ffd199}code{overflow-wrap:anywhere}'''
s='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-58 · P0来源与相机姿态验收</title><style>'+style+'</style>'
s+='<h1>P15-58 · P0 来源与相机姿态审查</h1><p class="warn">本轮通过原始 45° 图在存档与五份工程拷贝中的字节一致性核验，但未获取批准的 Hero 原始图文件。当前 +20° 模型候选的绝对 yaw 未经独立标定，因此不准入正式 VDD。</p><div class="grid">'
for name,label in tiles:
 assert (D/name).is_file(),name
 s+=f'<figure><img src="{name}" alt="{label}"><figcaption>{label}</figcaption></figure>'
s+='</div><h2>可见身份特征</h2><table><tr><th>特征</th><th>当前观察</th><th>判断</th></tr>'
for f in q['features']:
 s+='<tr><td>'+html.escape(f['feature'])+'</td><td>'+html.escape(f['candidate'])+'</td><td>'+html.escape(f['assessment'])+'</td></tr>'
s+='</table><h2>溯源级别</h2><p>45° 工程源与多视角恢复包、P15-37 / P15-38 / P15-42 / P15-43 真实文件哈希一致：<code>'+q['canonical45']['sha256']+'</code>。历史 Hero 批准文件只有 SHA 登记，找不到可比对的原始字节；因此原始 Hero → 45° 关系未证明。</p>'
s+='<h2>角度判断</h2><p>Qwen 的“相机左转 +20°”是模型条件，不是标定后的空间旋转。源图的 45° 同样是名义方向标签，不能相加得到有测量意义的绝对 65°。</p>'
(D/'index.html').write_text(s,encoding='utf8')
print('review tiles',len(tiles))

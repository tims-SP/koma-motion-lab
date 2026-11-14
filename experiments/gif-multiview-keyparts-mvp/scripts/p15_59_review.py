from pathlib import Path
import json,html
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-59-camera-identifiability'
q=json.loads((R/'evidence/p15-59-camera-identifiability-qa.json').read_text())
css='''body{background:#172331;color:#edf3fa;font:15px/1.55 system-ui;max-width:1450px;margin:18px auto;padding:0 18px}h1{font-size:24px}h2{font-size:19px}p{color:#cfdaea}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}figure{background:#283c50;margin:0;padding:12px}img{width:100%;object-fit:contain;background:repeating-conic-gradient(#ddd 0 25%,#fff 0 50%) 50%/24px 24px}figcaption{margin-top:6px;font-weight:650}table{border-collapse:collapse;width:100%;max-width:900px}td,th{padding:9px;border-bottom:1px solid #52687b;text-align:left}.warn{color:#ffcf9b}'''
h='<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-59 相机姿态可辨识性</title><style>'+css+'</style></head><body><h1>P15-59 · 绝对相机角度可辨识性验证</h1>'
h+='<p class="warn"><b>结果：现有数据不能独立证明绝对 65°。</b> P15-12 的 10 个三维坐标是从名义 0°、45°、90° 二维绘图反算的投影代理；远眼、发夹是二维外推。不存在独立世界坐标与相机标定。</p>'
h+='<div class="grid">'
for name,title in [('canonical45.png','P0 45° 身份基准'),('candidate-relative20.png','LoRA 相对 +20° 候选'),('gauge-equivalence.png','坐标旋转与角度重标记：图像投影完全相同')]:
 h+=f'<figure><img src="{name}" alt="{title}"><figcaption>{title}</figcaption></figure>'
h+='</div><h2>可复现的数学验证</h2><p>代理使用 x=c+Xcos(θ)+Zsin(θ)。同时把未知物体 (X,Z) 旋转 δ，并把相机角度 θ 增加 δ，投影坐标保持完全一致。因此即使 P15-12 在注册帧重投影误差接近零，也无法据此辨识真实物理 yaw。</p><table><tr><th>角度重标记 δ</th><th>最大屏幕坐标差异</th></tr>'
for x in q['gaugeSymmetryExperiment']:
 h+=f'<tr><td>{x["gaugeRotationDeg"]}°</td><td>{x["maxProjectionDifferencePx"]} px</td></tr>'
h+='</table><h2>最小缺口</h2><p>'+html.escape(q['minimumMissingEvidence'])+'</p>'
h+='<p>现有面部估点与投影代理很接近，但人工点位是参照原代理进行的，属于循环检验；不能当作独立测量。正式关键帧与 ArtMesh 均保持未批准状态。</p></body></html>'
(D/'index.html').write_text(h,encoding='utf8')
print('wrote HTML')

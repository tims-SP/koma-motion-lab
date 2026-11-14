import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-57-multiview-audit'
q=json.loads((R/'evidence/p15-57-multiview-audit.json').read_text())
style='''body{background:#172331;color:#edf3fa;font:15px/1.5 system-ui;max-width:1500px;margin:18px auto;padding:0 16px}h1{font-size:24px}h2{font-size:19px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}figure{margin:0;background:#283b4f;padding:12px}img{width:100%;height:auto;object-fit:contain;background:#000}figcaption{margin-top:8px;font-weight:600}p{color:#ccd8e7}.bad{color:#ffb6a8}.good{color:#9fddb5}table{border-collapse:collapse;width:100%;font-size:13px}td,th{padding:7px;border-bottom:1px solid #536579;text-align:left}'''
h='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-57 多视角身份连续性审计</title><style>'+style+'</style><h1>P15-57 · 多视角身份连续性审计</h1><p class="bad"><b>审计结论：当前 45°–65° 注册弧线不能作为已通过的角色身份连续性参考集。</b>13 个角度都尚无艺术验收批准；插值帧的 Alpha IoU 只能证明轮廓相似，不能证明眼睛、鼻梁、脸型和头发身份正确。57.5°–65° 的整图参考可见脸部/眼睛合成瑕疵。</p><h2>参考视角对照</h2><div class="grid">'
for f in q['frames']:
 if 'preview' in f:
  h+=f'<figure><img src="{f["preview"]}" alt="yaw {f["yaw"]}"><figcaption>既有 P15-38 参考 · yaw {f["yaw"]}° · {f["kind"]}</figcaption></figure>'
h+='<figure><img src="p15-56-current-candidate.png" alt="P15-56 candidate"><figcaption>P15-56 当前 AI 生成候选（相对旋转 +20°，绝对 yaw 未校准）</figcaption></figure></div><h2>工程指标</h2><table><tr><th>角度</th><th>来源类型</th><th>Alpha IoU</th><th>艺术验收</th><th>443px 发夹 bbox</th></tr>'
for f in q['frames']:
 h+=f'<tr><td>{f["yaw"]}°</td><td>{f["kind"]}</td><td>{f["alphaIoU"]}</td><td>{f["artisticallyAccepted"]}</td><td>{f["clipBBox443"]}</td></tr>'
h+='</table><h2>结论与下一步</h2><p>保留 45° canonical P0 原画作为唯一身份基准。不可用高角度旧合成图来证明新候选的五官正确，也不能把 LoRA 的相对 +20° 直接写成物理绝对 yaw 65°。下一步应从 canonical 45° 做独立角度条件生成，修正高角度五官与遮挡，并用可测量的相机/投影基准校准。</p>'
(D/'index.html').write_text(h,encoding='utf8')

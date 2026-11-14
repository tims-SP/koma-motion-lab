#!/usr/bin/env python3
"""Build a compact HTML visual audit for alpha extraction and pose proxy; never admit art."""
from pathlib import Path
import json,hashlib,zipfile
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-52-transparency-geometry'
tiles=[
 ('source45.png','P0 批准的 45° 原画','身份与发夹基准'),
 ('registered65.png','工程注册 65°','相机锚点的来源，不是合格原画'),
 ('camera-plus20-transparent.png','新候选透明 RGBA','来自 P15-51 相机 LoRA，已清理外部黑色及呆毛环内黑底'),
 ('candidate-anchor-overlay.png','相机几何对照','彩色十字来自 P15-12 预期坐标；非检测出的真实五官坐标'),
 ('preview-light.png','浅色背景','查看头发与深蓝制服轮廓黑边'),
 ('preview-blue.png','蓝色背景','查看透明边缘及发丝细节'),
 ('preview-pink.png','粉色背景','检查面部边界及残留黑底'),
 ('silhouette-alpha.png','提取的 Alpha 通道','白色不透明，黑色透明，灰色为抗锯齿边缘')
]
style='''body{background:#172331;color:#edf3fa;margin:16px auto;max-width:1500px;padding:0 20px;font:15px/1.55 system-ui}h1{font-size:23px}p{color:#cbd7e6}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:15px}figure{margin:0;padding:12px;background:#273a4f;border-radius:8px}img{width:100%;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#d9dce3 0 25%,#f9faff 0 50%) 50%/24px 24px}figcaption{font-weight:700;margin-top:5px}small{color:#c1cddb}header{padding-bottom:12px}strong{color:#ffda99}'''
html='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-52 · 透明原画与65°几何审查</title><style>'+style+'</style>'
html+='<header><h1>P15-52 · 透明原画与65°几何审查</h1><p><strong>视觉准入未通过：</strong>发夹侧向压缩，未完整保留交叉结构；精确65°未经独立标定。当前为工程候选，正式 ArtMesh 未修改。</p></header><main>'
for name,title,detail in tiles:
 assert (D/name).is_file(),name
 html+=f'<figure><img alt="{title}" src="{name}"><figcaption>{title}</figcaption><small>{detail}</small></figure>'
html+='</main>'
(D/'index.html').write_text(html,encoding='utf8')
print('html images',len(tiles))

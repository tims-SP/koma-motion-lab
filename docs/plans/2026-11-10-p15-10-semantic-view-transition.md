# P15-10 · 55°–65° ArtMesh 语义对应与遮挡验收

日期：2026-11-10
角色：`p0_character_001`
测试仓库：`tims-SP/koma-motion-lab`
入口：`experiments/gif-multiview-keyparts-mvp/`
技术主线：多视角独立原画 + P5 物理锚点 + Live2D 式 ArtMesh + VDD + TypeScript/HTML

## 目标与方案

将 P15-09 已验证的 55° 解剖锚点几何参考拆分为 13 个独立 1024×1024 RGBA 语义部件，再和已有 65° 原画的 13 个注册部件建立跨视角一致的身份、深度和可见性关系。以 2.5° 间距输出 55°、57.5°、60°、62.5°、65° 关键画面，并通过 HTML 对比 P15-07 与 P15-09。

源数据按原画类别区分：45° 是 P0 原始图像；55° 是对原始 45° 做 P5 物理锚点变形的**派生几何原画参考**；65° 是已登记的独立生成绘画源。新建 55° ArtMesh 是从派生几何参考逐像素划分的语义可编辑图层，不等同于独立绘制的 13 部位原画，也不代替不可见区的隐藏补绘。

## 来源与身份校验

| 角度 | 来源角色 | SHA-256 |
|---|---|---|
| 45° | P0 原画正向 3/4 图 | `78a08d5f010a8f449efda915a710a2de8958c3b1a32375df491d806fca251e40` |
| 55° | P15-09 P5 锚点绘制变形参考 | `2ef4bca92ebe4bd197adf62ad1ac91d55519330007bd97222d2366d6169e1d2e` |
| 65° | P15 独立侧转原画 | `c8e92f9c9c733a0a62f02258998273d7221a4b1eb394b85f77f7ef2111a1f506` |

来源部件必须持有原画图像 SHA；55° 的 13 部件在完全相同的透明 RGBA 画布中复合后与注册的 55° 图像**存储 RGBA 逐字节相等**，由源文件与回归测试保证。不可见区的源图层继续作为后续独立绘画任务，不将语义归属图层误登记为独立绘画。

## 几何、显隐与遮挡

`scripts/p15_10_semantic_key55.py` 用 P5 控制点的逆采样场计算原始 45° 像素的 55° 位置；在原始 45° 的深度顺序里为变形像素登记部件所有权，导出 13 张全画布可编辑 RGBA。

`scripts/p15_10_semantic_arc.py` 使用 P15-07 的正反光流校正原画局部位置，以 13 个语义部件分别采样、变形和合成。每个部件在每一帧由一个原画来源负责笔触，降低混合两套线稿产生的双重描边。远眼和金色交叉发夹分别以独立可见性曲线进入侧脸遮挡状态；近眼、鼻、脸、后发、侧发和服装保持独立深度顺序。

示意图层包含 `body.reference`、`hair.back`、`face.skin`、`ear.far`、`ear.near`、`hair.side`、`eye.far`、`eye.near`、`nose`、`mouth`、`hair.front`、`hair.ahoge`、`hair.clip.cross_gold`。

## 真实 VPS 验收

P15-10 完成 55° 分层 13 张、5 个中间视角全图及其各 13 张语义图层；提供所有文件的来源哈希和遮挡状态。

| 相邻角度 | P15-10 语义合成 Alpha IoU | P15-09 锚点全图 Alpha IoU |
|---|---:|---:|
| 55→57.5 | 0.93669 | 0.89519 |
| 57.5→60 | 0.78654 | 0.90870 |
| 60→62.5 | 0.93416 | 0.90896 |
| 62.5→65 | 0.93313 | 0.90784 |

这组值验证轮廓连续性和来源切换影响，不能代替角度真值或人物视觉质量。源归属切换目前集中在 57.5°→60°；该过渡仍需要独立 57.5°、60° 原画和对应的笔触、隐藏部位与遮挡校准。

已真实执行 Chromium，生成 8 张截图，验证 32 次图像加载，JavaScript 错误 0、请求失败 0。新增 7 项定向单元测试覆盖 RGBA 重组、P0 身份、关键帧精确保持、13 部件深度与来源、双眼/发夹显隐、Chromium 哈希以及画面连续性记录，全部通过。完整离线 HTML 资源归档 SHA 和内容条目由 `evidence/p15-10-delivery.json` 提供。

## 文件与复现入口

```bash
cd experiments/gif-multiview-keyparts-mvp
bash scripts/run-p15-10-review.sh
```

- 主审查入口：`review/p15-10-semantic.html`
- 55° 语义来源登记：`evidence/p15-10-semantic-source-qa.json`
- 55°–65° 语义过渡 QA：`evidence/p15-10-semantic-arc-qa.json`
- 浏览器图片与校验：`private-assets/p15-10-semantic-pose/browser/qa.json`
- 私有 ZIP 包：`private-assets/exports/p15-10-artmesh-correspondence-review.zip`
- 内容哈希：`evidence/p15-10-delivery.json`
- 全量资产留在 VPS 私有目录；GitHub 保留代码、元数据和验收文本。

## 后续关键任务

1. 根据原始角色身份基准生成与 45°/65° 解剖角度一致的独立 57.5°、60° 原画，保留远侧眼逐渐被鼻梁/刘海遮挡的形态，以及金色发夹的物理侧别。
2. 针对 55°、57.5°、60° 绘制 13 个原生 RGBA 部件及远眼、头发、耳和面部的隐藏补绘，登记独立来源、姿态、原画和遮挡边界。
3. 引入笔触/部件跨视角身份对应；采用独立留出原画验证轮廓 IoU≥0.90、面积偏差≤8%，并执行脸/发夹/领口视觉审核。
4. 通过 45°–65° 人工视觉验收后，回接 0°–90° 的 37 帧 HTML，继续完整 360° 多视角原画与遮挡一致性验收。

参考：Mo 等，[LayerInbetween](https://github.com/MarkMoHR/LayerInbetween)（SIGGRAPH 2026，DOI `10.1145/3811364`）；Even 等，[Inbetweening with Occlusions for Non-Linear Rough 2D Animation](https://mostyle.github.io/blog/rr9559/)（2025）。当前复用 P5/P8/P15 实验，实现结构化原画层与遮挡可视化验收。

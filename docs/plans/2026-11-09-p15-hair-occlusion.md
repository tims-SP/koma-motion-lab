# P15-05 · 视角相关头发笔触与动态遮挡

角色：p0_character_001
实验：experiments/gif-multiview-keyparts-mvp/
状态：P15-05 工程验证通过，原画视觉质量继续验收

## 任务目标

基于批准的原始 P0 45°/90° RGBA 原画及 67.5°/72.5° 同角色生成式关键视角，建立头发前、侧、后及呆毛的持续语义身份、源文件校验、P5 物理锚点与显式深度/遮挡对应。

四个发型部件的唯一语义身份：
- hair.back：后发
- hair.side：侧发
- hair.front：刘海及额侧前发
- hair.ahoge：单根呆毛

头发发束与五官/面部独立绘制，仅利用真正的原始 RGBA 图层验证遮挡几何。

## 已复用的实现和学术依据

- P5 物理锚点与全局坐标系；45°/90° 是原始来源，生成式中间角的物理锚点属于线性投影参考。
- P9 图层色域；P10 内部笔触连通区域与双向唯一候选排歧。
- LayerInbetween, SIGGRAPH 2026：https://github.com/MarkMoHR/LayerInbetween
- JoSTC, SIGGRAPH 2024：https://github.com/MarkMoHR/JoSTC

对生成式角度不追认缺失的物理原画像素，不将锚点预测、图层掩码或笔触匹配候选视为已经艺术签收的动画。

## 本阶段实测

| 指标 | 结果 |
|---|---:|
| 四个头发语义部件与三种面部遮挡参照物，每视角七个图层 | 28 张 PNG |
| 四视角与三段逐笔触对应 | 12 组 |
| 笔触候选（一对一歧义门禁） | 23 条 |
| 四视角与四组前后深度关系 | 16 组 |
| HTML 四个部件截屏 | 4 张 |
| Chromium 中实际 SHA 检验 | 16 次 |
| P15-05 单元测试 | 5 项，通过 |

语义遮挡关系：hair.front 覆盖 eye.near；hair.side 覆盖 ear.near；face.skin 位于 hair.back 之上；hair.ahoge 位于 hair.front 之上。逐角度通过原始层的 alpha>64 重叠区域与声明的 depthOrder 校验。

| 深度交叠 | 原始 45° | 候选 67.5° | 候选 72.5° | 原始 90° |
|---|---:|---:|---:|---:|
| 刘海与近侧眼 | 625 | 0 | 0 | 0 |
| 侧发与近侧耳 | 5,037 | 0 | 0 | 0 |
| 面部与后发 | 122,536 | 0 | 0 | 15,821 |
| 呆毛与刘海 | 3,005 | 0 | 2,784 | 0 |

单位为源图 alpha 阈值交叠像素，属于图层空间交叠的工程诊断，不能替代最终合成画质审查。

原始与生成式角度之间的发束笔触密度、头发层实际边界存在风格差异。特别是 67.5° 的四组图层交叠均为零，需要通过真实合成图对分层遮挡的正确性进一步审查。呆毛在 P10 规则下没有高置信内部墨线候选，维持其 P5 原始根部锚点身份和角度映射。

## 复现

在当前实验根目录，确保私有 P0 原始素材可用，并设置对应 Python/OpenCV/Pillow 与 Playwright Chromium 环境：

    KOMA_P14_PYTHON=/path/to/vision-venv/bin/python \
    KOMA_PLAYWRIGHT_MODULE=/path/to/node_modules/playwright \
    bash scripts/run-p15-hair.sh

交付：
- 数据：experiments/gif-multiview-keyparts-mvp/evidence/p15-hair-correspondence-qa.json
- 工程验收：experiments/gif-multiview-keyparts-mvp/evidence/p15-05-acceptance.json
- 浏览器查看：experiments/gif-multiview-keyparts-mvp/review/p15-hair-strands.html
- 私有对照：private-assets/p15-hair-occlusion/hair-strands-contact.jpg

## 后续画质门禁

- [x] 头发四部件独立身份及 28 张来源 PNG 的 SHA-256 核验
- [x] 12 组视角相关候选笔触对应与物理根部锚点引用
- [x] 16 组语义深度与 RGBA 交叠检查
- [x] 原始与生成式角度的 Chromium HTML 实际截图与回归
- [ ] P15-06：完成独立 65°、77.5° 解剖原画留出参考，与三段关键帧 VDD 对照
- [ ] 修正五官与发束的绘制笔触/遮挡连接，完成 0°–90° 视觉签收
- [ ] 完成 90°–180° 独立后侧/背面部件扩展

正式动画渲染基线保持 P8 语义 ArtMesh，P14/P15 中间角素材按来源证据单独审查。

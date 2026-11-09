# P15 · 语义笔触对应与视角遮挡连续性

角色：p0_character_001
范围：0°–90° 的面部和头发中间角画质优化
实验位置：experiments/gif-multiview-keyparts-mvp/
正式工程对照：P8_SEMANTIC_OCCLUSION_ARTMESH

## 关键技术判断

已有 P0 原始 0°/45°/90° 关键帧和 67.5°/72.5° 生成中间帧，各层保留唯一语义 ID 和源哈希。当前失真集中在临近生成关键帧的 65°、77.5°：鼻梁、眼周、发束与遮挡交界处光流不稳定，部分部件出现显著边缘偏移。插值纹理选择与位移限制只能作为诊断工具。

参考研究：[LayerInbetween，SIGGRAPH 2026](https://github.com/MarkMoHR/LayerInbetween)，采用遮挡感知的笔触对应与自动分层；[JoSTC，SIGGRAPH 2024](https://github.com/MarkMoHR/JoSTC)，研究逐笔触的跨关键帧对应。二者提供可借鉴的技术路线，但原始项目依赖模型权重及 GPU，当前采用轻量、可核查的局部语义对应原型，不直接集成大型推理服务。

## 已执行的诊断

- P14 原始平滑语义光流（P14）：37 帧，来源 QA 通过。
- 单侧源纹理保真（coherent）：8 个来源及检查角度实拍复核。
- 限制每角度位移为 4 px（bounded）：7 个来源及检查角度实拍复核。
- 65°、67.5°、72.5°、77.5° 四个固定视角，逐个校验 PNG SHA、RGBA 尺寸、透明缺口。
- 原始 90° 与候选 67.5°、72.5° 的 hair、eye、nose、mouth 内部边缘密度进行源一致性审计。
- 独立的流场位移边界单元测试 3 项通过。

实测 77.5° 透明缺口：P8 1988、P14 5666、位移限制候选 5341 像素；65° 分别为 1576、4988、4987。透明缺口是辅助结构代理，不是最终画质分数。当前新候选仍需原画笔触对应的修正和实际画面签收。

公开可复现的指标：experiments/gif-multiview-keyparts-mvp/evidence/p15-view-transition-qa.json。
本机实际图片：private-assets/p15-flow-cap4/p15-stroke-occlusion-contact.jpg。

## 验证方法

依赖原先 P14 注册的私有图像资产及 Python/OpenCV/Pillow。进入实验目录，使用同一隔离 Python 环境执行：

    KOMA_P14_PYTHON=/path/to/vision-venv/bin/python bash scripts/run-p15-transition.sh

该脚本运行位移限制单测、两组 VDD 输出，并重新计算四个关键对照角度的 QA 和图片。保存证据后再推进更细的解剖、笔触和遮挡改动。

## 原画对应与遮挡实施步骤

- [x] P15-01：注册 65°/77.5° 源对照与逐层透明缺口诊断
- [x] P15-02：实现有界形变实验参数，使用来源哈希及单元测试验证
- [x] P15-03：建立原始 90° 与新中间角的语义内部纹理/笔触密度报告
- [ ] P15-04：对 face.skin、nose、mouth、eye.near 建立局部可追溯锚点和逐笔触跨视角匹配
- [ ] P15-05：对 hair.front、hair.side、hair.back、hair.ahoge 建立分束对应与可见性/遮挡边界校验
- [ ] P15-06：生成独立的 65°、77.5° 解剖原画留出参考，验证身份、轮廓和笔触的真实一致性
- [ ] P15-07：补齐动图审查，在逐帧无可见重影、连续性及源身份验收后升级 0°–90° 艺术门禁

原始 P0 Hero 身份母图 SHA-256 核验仍单独作为 T00；模型候选的重新绘制不能代替原始身份基准的核验。

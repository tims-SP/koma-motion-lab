# P14 · 原创角色五视角 ArtMesh 画面验收

角色：p0_character_001
实验路径：experiments/gif-multiview-keyparts-mvp/
工作分支：feature/gif-multiview-p0-ingestion-20261105
验收环境：目标主机 Python 视觉环境与本地 Chromium

## 技术实现与证据

- 已批准的原始关键视角：0°、45°、90°，固定语义部件身份与来源 SHA-256。
- 67.5°、72.5° 生成式原画候选：以同角色视角参考为输入，经过独立 RGBA 蒙版和基于原始 ArtMesh 语义的部件映射，每角度 13 个独立透明 PNG。
- 原始 0°/45°/90° + 中间两视角生成候选，使用五个关键视角的 VDD 实现 37 帧 0°–90° 运动。
- HTML 审查：逐部件源图 SHA-256 检验、原画叠合、P8 基线与 P14 画面并排查看。
- 自动验收：源文件 SHA、26 张 RGBA 部件、37 张运动帧、时间连续性、纹理边缘诊断、12 张真实 Chromium 截图。
- 可追溯文字证据：experiments/gif-multiview-keyparts-mvp/evidence/p14-painted-view-qa.json。
- 图像、GIF、PSD、浏览器截图与原图 QA 保留在 private-assets/。

部件层注册依赖生成候选的后处理语义映射；原画艺术验收需要验证它们是否真正沿用同一组五官、头发线条和对应解剖位置。

## 本地复现

依赖 Python 3、numpy、Pillow、opencv-python、Node.js、Playwright Chromium，以及已登记 SHA-256 的原始 P0 私有素材。

在实验目录内执行：

    KOMA_P14_PYTHON=/path/to/vision-venv/bin/python \
    KOMA_PLAYWRIGHT_MODULE=/path/to/node_modules/playwright \
    bash scripts/run-p14-review.sh

此脚本复核现有 P14 原画候选；新原画候选的生成与分层导入分别由 p14_background_matte.py、p14_identity_ahoge.py、p14_register_painted_67.py、p14_semantic_reproject.py 管理。

## 视觉验收门禁

正式渲染基线为 P8 语义 ArtMesh 遮挡。P14 生成式中间关键视角作为独立候选登记，由源图与结果双重约束决定是否升级。

| 验收 | 结果 |
|---|---|
| 26 张 RGBA 部件、原始 P0 资源一致性 | 工程通过 |
| 37 帧 0°–90° 动画与 Chromium 源图校验 | 工程通过 |
| VDD 时间连续性、纹理边缘诊断 | 工程通过 |
| 67.5°、72.5° 生成视角五官身份与发束笔触 | 视觉审查中 |
| 65°、77.5° 相邻帧部件过渡及遮挡 | 视觉审查中 |
| P0 Hero 原图身份 SHA-256 一致性 | 原始主图直读待核实 |

透明遮挡缺口像素值属于辅助结构诊断；艺术验收须独立检查轮廓、眼睛、耳鼻口、刘海、呆毛、发夹及阴影在连续运动中的一致性。

## 下一阶段任务

- [x] P14-01：独立候选原画、26 张语义 RGBA 层与来源哈希登记
- [x] P14-02：37 帧 VDD、HTML 交互和 Chromium 截图验收
- [x] P14-03：工程证据重放、便携 QA JSON 与仓库持续化
- [ ] P15-01：修正 65°/77.5° 眉眼、下颌、发束等跨关键帧对应关系
- [ ] P15-02：对 67.5°/72.5° 生成候选进行身份、解剖结构和笔触独立视觉审查
- [ ] P15-03：验证真实独立留出角，完成 0°–90° 最终画质签收
- [ ] P15-04：验收通过后扩展 90°–180° 的后侧与背面多视角原画

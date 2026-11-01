# P0 · 原始像素保真分层基线

验证环境：当前隔离容器。原始素材：`1000012009.png`（1254 × 1254，RGBA），See-through 产物：`seethrough_output.psd`（768 × 768，18 个语义图层）。

## 本地实测

- 原图 SHA-256：`76a25ef6b1197462e99d9b517b8016c7502c6c2ff9ad8556f01b779b7aa99bfd`。
- 与修正眼睛叠放顺序后的 See-through 静态输出对比：缩放到 768 px 后的可见主体 PSNR = **24.60 dB**；Alpha≥80 轮廓 IoU = **0.98348**。
- 使用 See-through 图层 Alpha 和遮挡贡献识别源图的图层归属，再将 **1254 px 原画中的真实 RGBA 像素**分配给 18 个互斥可见图层。
- 对可见分区按原坐标合成：**源图非零 Alpha RGBA 像素完全一致、最大差值 0**。这仅验证可见原像素的保留和分区重建，**不能证明语义分割、层间遮挡或网格运动正确**。
- 弱分配区：原图有像素但 See-through 图层贡献低于 0.055，计 **1,280 像素**，约占 Alpha>3 原画像素的 **0.187%**。需重点抽检边缘与器官邻接处。
- 侧刘海覆盖的交叉金色发夹单独修正可见归属：**1,740 像素**划入 `headwear` 层。

## 后续验收条件

1. **语义质量**：当前可见分区发现 `mouth` 过度覆盖下巴皮肤、`eyebrow-r` 可见分配极少等问题，应检查局部掩膜而非只依赖像素零误差。
2. **隐藏图层**：See-through 补画内容作为 768 px 推断图层保存并独立审查。隐藏内容的真实细节不可从原图找回。
3. **移动测试**：刘海、眼睛、耳朵等图层移动后，必须检查缺口、残留发丝、重复影像以及局部不连续。
4. **编辑格式**：源像素互斥可见层与补画候选分开保存，明确哪些图层属于经过模型推断的隐藏区域；最终导入 PSD/ArtMesh 前需通过重合成与位移测试。

本地结果路径：`/mnt/data/p0_hd_relayer/`（`audit.json`、`layers_source_exact/`、`generated_hidden_candidates/`、`source_reassembled_exact.png`、`ownership_map.png` 等）。以上路径是隔离容器交付位置，Git 仓库只存放文本记录与工具规范。

验收状态：`VISIBLE_PIXEL_FIDELITY_PASS / SEMANTIC_MASK_REVIEW / HIDDEN_LAYER_REVIEW`。

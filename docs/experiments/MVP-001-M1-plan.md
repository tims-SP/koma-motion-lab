# MVP-001 / M1 — 多视角分层动漫人物 360° 旋转：执行计划

制定：2026-10-31。状态：**PLANNED；未开始 M1 代码实现；未生成角色原画；未完成 360° 验收**。

关联总计划：[`MVP-001-multiview-anime-plan.md`](./MVP-001-multiview-anime-plan.md)。

## 0. 前置核验（已完成）

- 已核对 M0 `experiments/mvp001/src/main.js`、`scripts/smoke.mjs` 和 `.github/workflows/mvp001-smoke.yml`。
- M0 于 [Actions #41188109729](https://github.com/tims-SP/koma-motion-lab/actions/runs/41188109729) 已通过，说明 Chromium + WebGL2 + 25 个**程序化矩形/平面** + 24 帧截图 + MP4 可用。
- M0 **没有**分层原画、跨视角对应、纹理变形或 VDD；M0 画面只能算渲染器连通性测试。保留它为回归夹具，不可拿来充当 M1 的质量证据。
- `tims-SP/koma-motion` 为本体；所有阶段先在 `tims-SP/koma-motion-lab` 实验。旧 UV 皮肤、Rive/Spine 转换、Godot 流程均**不是新 MVP 的依赖**。

## 1. 本任务唯一要回答的问题

在同一套**原创日式动漫人物全身分层资产**上，能否经过 **3D Anchor + 视角相关二维形状/纹理 + Live2D 式 ArtMesh + 遮挡规则 + VDD**，生成可重复采样的 360° 水平转身视频；其关键角度和任意中间角度是否仍然具有高水平的原画保真？

**本阶段不做：**完整 IK/全身动作片（M2）；法线、面部 SDF、粒子合成（M3）；通用建模器/无限输入人物/全自动化。人物骨骼父节点和锚点必须**预留**，否则后续 M2 无法复用。

### 准确定义 360°

M1 验证的是 **水平 Yaw 0°~360° 的全身连续旋转**，固定正交相机、自然站姿、无大幅俯仰。UI 可提供 Pitch ±15° 作为技术诊断，但**不能声称已证明全空间任意方向**。每帧角色必须来自单一的部件资产包，不得整身切图、整身平面绕轴或以整身 alpha 淡入淡出伪造旋转。需要部件层级的连续形变、深度与可见性。

## 2. 角色基准与资产生产方法

### 2.1 角色复杂度和设计约束

原创、无第三方版权争议、正交站姿、不佩戴巨大遮面附件；采用中等复杂度的二次元美少女/少年角色（建议肩部长度的深色头发、短外套及单独衣摆、裙装/裤装、一个**非对称发卡或衣服图案**专门校验镜像错误）。服装、发色、瞳色、四肢长短、肩宽、胸腰比例事先锁定。

1. 写 `character-brief.json`，包含背景、颜色、角色比例、唯一不对称标记、参考图源和使用许可。
2. 制作**一张正式正面角色图**并检查造型满意后才扩展角度；禁止只靠一句独立提示词生成其他方向。
3. 将正面作为**显式参考图**，在同一角色约束下制作 90°、180°、270°。所有视角必须为同一姿势、同一相机高度、同一人物尺度（建议单张源图至少 2048×3072），并统一中性光照。
4. 单独整理正面 / 右侧 / 背面 / 左侧并进行四视图对照（面部一致、服装纹理与发卡位置、鞋型、腿长与肩宽）；多视角生成模型仅做候选，达不到一致性就重绘/修图，不准在引擎中通过模糊处理掩盖错误。
5. 斜侧 45°、135°、225°、315° 的原画先作为**质量参照**；若相邻关键视角插值明显失真，将对应斜侧图升级为正式形变关键视角。基础目标为 4→按需 8 方向，但绝不假设 8 张必定能保证任意角度质量。

**素材发布规则：** 原画、PNG、PSD/分层工程、视频只放 GitHub DRAFT Release 或经授权私有位置；Git 历史只存文本源代码、清单、散列、报告和工具。必须核实每份资产的来源与可使用权限。

### 2.2 每个视角都必须拆出真实 ArtMesh

初版需要一套稳定语义 ID（估计 25~40 个实际绘画部件，必要时更多）：
`head.face`, `eyes.left/right`, `brow.left/right`, `mouth`, `hair.front.*`, `hair.side.left/right`, `hair.back`, `ear.left/right`, `neck`, `torso`, `pelvis`, `arm.upper.left/right`, `arm.lower.left/right`, `hand.left/right`, `leg.upper.left/right`, `leg.lower.left/right`, `foot.left/right`，衣摆、发卡等另拆。

每个部件保留透明 RGBA、轮廓关键点、可见性/遮挡状态、局部 pivot、空间 anchor、网格与 UV；跨角度复用相同语义 ID。若部件在某角度消失，标为 `occluded/not-present`，**不能**误删、错配到另一只眼睛、用镜像复制来编造。

从正面/侧面基础参考还原出来的关键视角重新合成回单张图，作为遮罩切割质量测试；局部无法一致的图层必须返工。可选用 See-through 辅助分层/遮挡补全，但其输出必须单独验证；不把它当作完整 rigging 解决方案。

## 3. 数据契约（必须先定再写插值）

角色版本化结构：
```text
character.json
  coordinateConvention: right-handed, +Y up, yaw around +Y, units, camera convention
  identity: palette, asymmetryMarker, provenance, license, sha256
  views[]: {yawDeg, portraitAsset, referenceDimensions, cameraOrthoScale}
  parts[]: {
    id, parentBoneId, pivot, anchor3D,
    perView[]: {
      yawDeg, texturePath, textureSha256,
      outlineLandmarks[], meshVertices[], triangles[], uv[],
      visibility: visible|occluded|absent,
      painterOrder, depthHint, viewCorrectionXY, correspondenceGroup
    },
    transitionRules[]
  }
```
明确：每个视角的左右眼均以**角色自己的 left/right** 命名，不能随观看方向交换。允许部件出现/消失和网格局部拓扑变化，但跨拓扑区间必须显式定义分割、替换或遮挡规则，不能把不同顶点数量的网格强行相加。

本阶段创建 JSON Schema 与可运行 validator；至少包含：唯一 ID、纹理存在且散列一致、正交相机尺度一致、轮廓和三角形索引合法、没有 NaN/Inf、没有未定义跨视角匹配、角度 0/360 等价。

## 4. 实现的核心求值顺序

```text
yawDeg + camera + future bone pose
 -> normalize yaw / wrap 0..360
 -> select adjacent compatible key views per PART (not per whole character)
 -> evaluate 3D anchor projected position
 -> compute VDD view-corrective 2D offsets
 -> warp corresponding triangular ArtMesh / contour
 -> apply per-view visibility, depth and occlusion rules
 -> sample registered RGBA texture / optional controlled part transition
 -> composite painted lines/colors (no lighting in M1)
 -> deterministic renderer.render(frame)
```

- **基础可行性先行**：通过 2D landmark/triangle correspondence + 有界的 mesh warp 实现，避免在缺乏真实人物和可比较结果前投入全部 ARAP。
- **VDD 基线**：对同一语义部件用关键视角的二维原画位置与投影位置之差作为 view-dependent correction，在水平角度圆周上无接缝插值；对比“只投影”和“VDD 修正”的关键帧。
- **纹理**：不得将两个不对应的整个人物 JPEG/PNG 直接 alpha 混合。先在部件内完成对应网格变形；当纹理无法可靠对应时优先补画角度/拆分部件，必要时局部受控切换而不是整脸重影。
- **层级**：借鉴 Live2D 的 ArtMesh / Warp Deformer / Glue 语义，但自己实现最小局部网格与接缝约束。Three.js BufferGeometry 可存索引、UV、顶点；不能假定普通 morph target 自动解决多视角、遮挡及纹理对应。
- **遮挡**：以部件 anchor/depth 为初值，增加视角区间覆盖规则及必要的图层拆分。重点验证脸↔刘海、左右眼、手臂↔躯干、头发↔颈部与衣服。
- **ARAP 分支**：只有基线在相邻关键角度中发生明显三角形折叠、收缩、眼睛/发丝形变时，才对受影响部件加入预计算 ARAP 修正，与基线同帧对照后决定保留。

## 5. 可执行任务顺序、验收与提交

| ID | 明确操作 | 输出/验证 | 失败处理 |
|---|---|---|---|
| M1-00 | 冻结 M0 基线，登记 commit、Action、渲染器与参考论文；创建独立 M1 入口；保留原 M0 冒烟测试 | M0 仍成功；M1 状态初始为 NOT_STARTED | M0 出错先修基础设施，不能混入人物质量判断 |
| M1-01 | 定义原创角色 brief；产出/审核高精度正面，再基于该图生成右侧、背面、左侧 | 单张统一角色设定参考板、四张整身关键原画、来源与 SHA、镜像标记 | 身份、比例、服装不一致即退回重画 |
| M1-02 | 分层/补全、稳定部件 ID、拼回四视图；制作可见性矩阵 | 每角度多部件透明图、四张重建对照图、部件清单 | 穿帮和缺失填充必须修正 |
| M1-03 | JSON Schema、anchors、pivots、landmarks、triangle indices 与 UV；建立跨视角 correspondence | schema validator PASS、对应关系可视化及深度 debug | 错配眼睛/头发、非法拓扑则禁止进入渲染 |
| M1-04 | 把 M0 平面夹具替换为真正透明贴图部件；在 0/90/180/270 用同一角色包独立重建 | 四个关键方向与原画比对图，五官/服装/背面正确 | 原画重建不通过不开始插值 |
| M1-05 | 实现 yaw view selector、0/360 环绕、anchor 与部件级形状插值 | 24 个每隔 15° 的静帧、部件形变与角度日志 | 中间角度折叠/失真则定位具体 Part ID |
| M1-06 | 引入 VDD 修正、图层遮挡规则、连续 transition；针对失真补 45° 等局部关键形状 | same-angle no-VDD vs VDD 对照、遮挡切换诊断、修改前后对照 | 无法对应则改进遮挡/局部补图，不整身交叉淡入淡出 |
| M1-07 | 按需对坏变形部件加入 ARAP 或结构化局部 mesh warp；修正刘海、脸、衣摆轮廓 | 提供线性变形 vs 修正变形的同角度对照与成本记录 | 无清晰视觉收益的复杂算法不纳入正式核心 |
| M1-08 | 固定相机和角色尺寸，渲染 192 帧、1920×1080、24fps、8s；额外求 frame 192 = yaw 360° 检测 loop seam | MP4 + 24 方位图 + 边界角度特写 + 深度/mesh debug + QA JSON | 任一缺帧、黑屏、裁切、角度错误直接 FAIL |
| M1-09 | 独立视觉抽样：正侧背各方向、45°、鼻眼发束遮挡、对称误翻、帧间闪烁、动作设计兼容性；记录修复数量及工时 | 质量 gate PASS/FAIL 与后续 M2 资产接口；Git commit + DRAFT Release | 若广泛中间角度都需要逐帧手工重画，明确 NO-GO |

**每个 ID 完成后，必须提交代码/文本报告，并写明对应 commit、CI run、可复核的视频/图像位置。不能因为 CI 为绿色就把人物质量标为通过。**

## 6. 关键验收定义

### Engineering gate

1. 真实带 Alpha 的纹理 ArtMesh 而不是程序化矩形，至少 25 个独立语义部件，带跨视角可见性/对应证据。
2. 四个原画关键方向可复原；角度 0、90、180、270 与指定参考图一致；禁止镜像错误，尤其是不对称发卡/衣服图案。
3. `yaw=360°` 与 `yaw=0°` 各项模型状态等价；额外检查两幅渲染结果的差异；**视频本身输出 0°..358.125° 共 192 帧**，保证连续循环。
4. 24 个每 15° 的独立位置抽样；每帧完整角色不能离开画面；无 NaN、错位纹理、错误索引、空白、WebGL 异常。
5. 能任意随机跳帧求值，即 `render(yaw=127°)` 不需要依次播放 0°..126°。

### Visual gate（必须独立检查）

6. 眼睛、鼻子、嘴、脸部轮廓清晰，无双眼叠影、面部忽胖忽瘦、发束突然生灭；视角左右侧造型可信。
7. 刘海/额头、下颌/脖子、手臂/躯干、衣摆/腿部无遮挡穿帮，深度顺序变化不突然跳层。
8. 头身比例、配色、饰品及服装细节在 360° 保持同一角色；线条无显著模糊、锯齿和涂抹。
9. 重点比较人工选定的高质量参考视角，而不是只统计 PSNR/SSIM；自动指标仅捕获技术性错误。
10. 保存**实际人工局部修图量、额外关键视角数量和单次角色制作成本**；若为每个角度重画近似全帧才能过关，判 NO-GO。

## 7. 仓库和运行设计

原 M0 `experiments/mvp001/src/main.js` 保留为 fixture；M1 新增以下文本代码（名称可在首次开发提交时一并固定）：

```text
experiments/mvp001/
  src/m1/
    types.ts
    view-space.ts
    anchors.ts
    part-mesh.ts
    correspondence.ts
    vdd.ts
    visibility.ts
    turntable.ts
  schemas/character-multiview.schema.json
  scripts/render-m1.mjs
  tests/m1-{schema,view-wrap,correspondence,occlusion}.test.ts
docs/experiments/
  MVP-001-M1-plan.md
  MVP-001-M1-status.md
.github/workflows/mvp001-m1-turntable.yml
```

- GitHub Actions Ubuntu + Chromium/Playwright (WebGL/SwiftShader) + FFmpeg，固定依赖，逐帧截图并使用 FFprobe 验证实际编码帧数和时长。
- 输出到 DRAFT Release：`m1-turntable-1080p.mp4`、`m1-angles-contact-sheet.png`、`m1-reference-comparison.png`、`m1-depth-debug.mp4`、`m1-quality.json` 与授权允许的角色资产 ZIP。
- Git 历史只保留代码、JSON/MD、素材元数据与 SHA，不上传二进制；使用脚本按允许的存储位置拉取校验过的原画，不在公有仓库泄露原画和密钥。

## 8. 决策点（强制顺序）

1. **先做 M1-01 原画方向一致性审核**，否则后面的 rigging 不具意义。
2. **M1-04 四个原画关键视角准确还原**是插值研发入口；若关键视角尚不能复原，不允许跳到旋转视频。
3. **M1-05 VDD 之前先有简单插值基线**，才能证明 VDD 带来的实际提升。
4. **M1-08 输出真实 1080p 视频**之后才能判断 M1 成功；720p、640x360 或仅三四张截图不能替代。
5. 如果 M1 画质失败但 M0 可渲染，故障归因应归入资产生产/形状匹配/遮挡等，不能归因成「Three.js 不支持」。
6. 如果 M1 被判 NO-GO，只保留成功的基础模块、记录失败原因；暂停 M2/M3 而不是叠加更多功能。

## 9. 参考材料

- Rivers/Igarashi/Durand, `2.5D Cartoon Models`: https://alecrivers.com/2.5dcartoonmodels/
- Kitamura/Kanamori/Tsuruno, `2.5D Modeling from Illustrations of Different Views`: https://www.jstage.jst.go.jp/article/adada/18/4/18_74/_article/-char/en
- Fukusato/Maejima, `View-Dependent Deformation for 2.5-D Cartoon Models`: https://pubmed.ncbi.nlm.nih.gov/35544514/
- Live2D official deformer: https://docs.live2d.com/en/cubism-editor-manual/deformer/
- Live2D official Glue: https://docs.live2d.com/en/cubism-editor-manual/glue/
- Three.js BufferGeometry: https://threejs.org/docs/pages/BufferGeometry
- Third-party 2010 replica for algorithm study (license must be checked before code copying): https://github.com/without-paper/2.5d_cartoon_model

## 10. 当前状态与下一执行入口

- 此文件为 M1 **计划提交**，不可将它标记为 M1 完成。
- **紧接着执行 M1-00 与 M1-01**：冻结 M0 验收证据、明确原创角色 Art Direction 和多视角图像生成参考；优先产出可供目视审查的正面、侧面、背面和斜侧候选角色图，确认真实原画能够稳定统一之后才着手部件绑定。

# P0 · 角色 001 原画、分层与视角验收规范 V1.0

日期：2026-11-01  
角色：`p0_character_001`  
执行仓库：`tims-SP/koma-motion-lab`  
运行时集成：`experiments/head009`（沿用 `docs/MVP-009-plan.md` 和 `docs/MVP-009-face-authoring-contract.md`）

## 1. 验收目的与阶段边界

把已经确认的日系短发少女从身份原画转为可追溯、多视角一致、器官可独立移动、可还原并能接入 3D Anchor / ArtMesh / VDD 的标准资产。

采用三条独立证据路径：

1. **结构化程序门禁**：文件、哈希、尺寸、RGBA、图层语义、PSD 导入/回读、像素重组、关键点与遮挡拓扑。
2. **锁定参考视觉门禁**：关键视角与独立留出视角，各器官裁切叠图，人工逐器官检查；记录检查员、结论、理由。
3. **动态扰动门禁**：器官平移/变形/揭露隐藏区域/连续 0°–90° 旋转与 80°–90° 密集取样。

G0–G4 属于 P0 的正式资产准入；G5 是分层可动画化准入；G6 是 HEAD009 渲染集成。HEAD009 仍独立维护自己的 T03B/T04 进度；P0 资产通过不意味着头部 360° 或全身动画通过。

每一项报告状态：`PASS` / `FAIL` / `BLOCKED` / `REVIEW_REQUIRED`。必要证据缺失属于 BLOCKED；人工拒绝可否决数值通过；任何强制项未通过就不能进入依赖阶段。

## 2. 统一约束

- 锁定 Hero SHA-256、角色 `character_id` 与身份 JSON，必须可复现。保持粉紫短发、弧形单根呆毛、角色自身左侧交叉金色发夹、紫粉眼睛、深蓝金边外套/白衬衫/酒红领结。
- 显式区分 `anatomical_left/right` 与 `screen_left/right`，记录 `yaw_positive_convention`、固定镜头、透视/正交投影和校准参数。禁止用视觉猜测去等同跨视角局部像素坐标。
- `reference_role` 只可为 `hero`、`key_art`、`heldout`、`generated_debug`。仅独立绘制且来源可追溯的 `key_art` 可进入运行时；`heldout` 不能参与调参/插值。
- 显式记载 `native_detail_px` 与 `canvas_px`。高分辨率验收按实际源图细节判断，插值放大不计为原生高清。
- 原画固定颜色空间 sRGB。输出 PNG RGBA 与 PSD RGB/8-bit/channel；图层名语义唯一。对可选 Cubism 导入遵循官方 PSD 约束，实际目标仍为 Three.js。
- 源文件、视角、分层源/掩码/遮挡补全、版本、检查代码、运行环境、人工审阅记录都要有 SHA 和父级溯源。
- 大型 PNG/PSD/HTML/视频留在附件或受控 Release/Artifact，Git 只保存文字、配置、验证代码及索引。审查不能以生成图板中画出的“已通过”标识为依据。

## 3. 门禁 G0–G6

### G0 · 身份与输入基线

**输入** `hero_master.png`、`identity_spec.json`、`source_manifest.json`。

程序：有效 PNG 解码，原始 SHA/尺寸/颜色模式/ICC/Alpha 记录；输出有效像素 bbox、四边安全边距、A 通道范围、预乘/直通 Alpha 口径；主图来源一致、JSON Schema 合法。生成白/灰/黑底合成预览。

视觉：脸型、眼型、刘海方向、发夹实际侧别、呆毛、服装和画风匹配已确认 Hero。所有角色身份强约束均通过。

初始阈值：建议角色外轮廓距非设计性截断边界 ≥8% 对应画布边长，作为可调整安全预算；原生主图细节须足以检查眼睛、耳朵与发束边界。底部确需画外延伸时明确记录裁切类型而非默认判过。

**输出** `qa/g0-source.json`、`qa/hero-on-black-white-gray.png`、`qa/identity-review.json`。

### G1 · 多视角原画

**输入** 四张同角色独立关键视角：0/45/90/180；每视角 source SHA、画布、标定和独立生成/绘制记录。

程序：四文件 RGBA、校准后的头高/眼高/肩高对齐，方向元数据，自身左右身份映射，发夹对应侧别，独立图像 SHA，非预览裁切/镜像。中心点和归一化头部框记录。每视角实际可见部件清单。

视觉：0° 双眼/眉耳、45° 真实立体脸、90° 单可见眼与鼻梁/鼻尖/口唇/耳根/下巴轮廓、180° 后脑体积与后发/衣领；检验发型、金色发夹、连帽衣领的结构连贯。重点取各器官独立裁切看局部身份；对侧脸的真实结构实行强制否决。

补充：只生成 0/45/90/180 是资产 P0 范围，不据此宣称 360° 运行时已经可用。

**输出** `qa/g1-turnaround.json`、`qa/turnaround-board.png`、`qa/organ-identity-overlay.png`。

### G2 · 器官独立图层及遮挡补绘

**输入** 逐视角 `layers/*.png`、`layer_manifest.json`、`hidden_fill_manifest.json`。

最小语义：rearHair、sideHair.L/R、fringe/frontHair、ahoge、hairpin；face/scalp、neck、eye.L/R（眼白/虹膜/瞳孔/高光/眼线）、brow.L/R、nose、mouth、ear.L/R、cloth/collar。某部件在指定角度不可见时显式 `visibility=occluded`，而不是删除语义身份。

程序：尺寸与画布统一，解码与 alpha/非空 bbox，可单层开关，名称和 stable semantic ID 唯一；穿越前后深度的发束按局部遮挡关系拆分；可移动层的 hidden fill 对应并可单独开关。

视觉：所有独立器官形状完整，没有邻接眼皮/头发/肤色碎片污染，边缘干净。刘海移开后额头连续、侧发移开后耳朵完整、虹膜移动后眼白完整、后发移动后颈部与后脑完整。

动态验证：对每个主要器官执行 `hide`、`translate`、`scale_or_warp`。初始压力动作建议位移为头部包围框宽度 5%，前发上抬为头部高度 10%；在差异图上标记露底、漂浮边缘和相邻结构误带。位移量是压力测试夹具，不是正式动作范围。

**输出** `qa/g2-layer-check.json`、`qa/parts-contact-sheet.png`、`qa/occlusion-reveal.mp4` 或逐帧 PNG。

### G3 · PNG 重组与 PSD 往返验证

**输入** `hero_master.png`、分层 PNG、原生 PSD、OpenRaster 可选。

执行三次独立合成：
A. 锁定参考原画；
B. 按明确线性/非线性颜色与 Porter-Duff source-over 规则生成 PNG 图层合成；
C. 从磁盘重新打开 PSD，使用 PSD 图层解析器和实际编辑器分别导出合成。图片必须先在同一颜色空间、透明度口径、对齐坐标下规范化再比较。

程序记录每通道绝对差（含 alpha）、透明区域统计、opaque-interior/anti-alias-edge 分区、MAE/max、阈值超限像素、局部最坏图块。透明像素的 RGB 值不计入颜色差；只比较有可见贡献的像素。生成原画/PNG/PSD 三联图、放大 4× 差异图。

**建议首版门槛**：
- 若源图由无损分层精确分配和同一合成算法重组，PNG→参考应能取得可见像素零差；这是工程回归目标，不作为语义分层合格的证据。
- PSD 文件确实包含预期的可编辑栅格图层，图层位置/名称/透明度通过回读。
- 对 Photoshop/CSP 或目标实际消费应用的 PSD 合成，在统一色彩约定后：不透明区域 99.9% 像素每通道差 ≤2/255，最大差异像素需要逐点归因；Alpha 结构一致。此为初始预算，必须通过颜色转换基准样本校准。
- 全图 SSIM 可用于趋势和辅助筛查，不能掩盖眼睛/鼻/耳/发夹局部错误；若用 LPIPS，必须记录模型版本、输入范围、裁切方式，并且只作为辅助信号。

**输出** `qa/g3-recompose.json`、`qa/psd-roundtrip.json`、`qa/reconstruction-diff.png`。

### G4 · 器官身份与空间关系

**输入** 每视角独立标注 `landmarks_{yaw}.json`、`organ_identity_map.json`、`occlusion_graph.json`、分层图及源校准。

程序：语义 ID 稳定，左/右按解剖定义，缺失点按 `occluded` 标记；关键点由原图独立标注并且手工复核，验证必要部件归属及点对其 alpha/ROI；遮挡关系为带区域/角度的有向图，真实循环必须拆层；检查局部 mesh/遮挡边界、图层深度约束。0/45/90 原画重建关键点误差初始 ≤头高 2%；不使用跨角度原始 2D 像素距离作为身份一致性唯一指标。

视觉：眼睛身份、鼻尖轮廓、耳根/耳廓位置、发际线；局部发束移位/遮挡逐点复核。

**输出** `qa/g4-semantics.json`、`qa/landmark-overlay.png`、`qa/depth-order-samples.json`。

### G5 · 可动画化压力测试

检查眼球平移、眼睑开闭、嘴巴张开/闭合、前发摆动、侧发/耳朵显露和肩领轻微扰动的实际帧。源图缺少口腔/舌牙内容时，`mouth_open` 明确 `BLOCKED_SOURCE_ART`，不得以拉伸闭嘴线代替。

将 5% 头宽平移、10% 头高抬刘海、可配置 ±角度器官局部 Warp 和连续帧逐项测试。检查源 artmesh/alpha/补绘是否出现破洞、双线、边缘残影、错层、孤立岛；记录部件、角度、帧号和截图。

**输出** `qa/g5-movement.json`、`qa/motion-contact-sheet.png`、动画视频或帧序列。

### G6 · HEAD009 连续旋转集成

复用现有 `experiments/head009` Three.js / HTML / Playwright / Chromium 证据机制。

- 第一轮 0/15/30/45/60/75/90，重点 78–90 每 1–2° 检验耳朵入镜与远侧眼消失。
- 锁定 0/45/90 生产原画做插值 key，保留 20/55/82 新独立留出原画做盲验；不使用调参时见过的旧 30/60/75 作为独立评测。
- Beauty / Part-ID / Depth / Alpha 来源必须是同一几何/掩码覆盖机制；在非边缘不透明区域初始预算覆盖失配率 ≤0.5%，边缘容忍 1 像素。必须使用故障注入证明错误深度/遮挡可导致 FAIL。
- 关键绘制角的 silhouette IoU 初始 ≥0.93、语义关键点误差 ≤头高 2%，且独立视觉通过。留出角度必须报告分器官偏差与完整画面视觉结论。相关预算与 `docs/MVP-009-plan.md` 保持一致。
- 必须输出局部放大连续帧条、WebGL 实际截图/视频、HTML 中各诊断通道和程序 JSON；HTML 打开真实可复现的 `file://` 渲染，不使用静态截图替代运行时。
- 通过此门禁仅表示头部 0°–90° 的工程/视觉接受；水平 360° 需后续 135/180/225/270/315 + 连续闭环独立门禁。

**输出** 复用 `head009-review.html`、`html-review-qa.json`、`organ-qa.json`，新增 `qa/g6-head90-visual.json`、`qa/heldout-20-55-82/`、`qa/ear-entry-78-90/`。

## 4. 视觉审阅与责任分离

审阅人不应只看整张图。对以下组件逐项给出 `PASS/FAIL/REVIEW_REQUIRED`：眼睛 L/R、鼻、嘴、耳 L/R、前/侧/后发、发夹、脸/下巴、颈部与衣领。每项需要：
- 具体角度/帧号、独立原画局部、实际合成局部、重叠对照、失败位置。
- 判定理由与修改动作（例如要补绘的遮挡区域、错误的 semantic ID、需要新增绘制 key 的角度）。
- 核心身份部件、真实侧脸、动态遮挡的人工否决权优先于总体相似度。

对每轮加入故障注入：镜像交换左右眼/发夹、移除耳后补绘、错置鼻尖 landmark、调乱前后发层级、PSD 改色、单独改 alpha，要求门禁按预期失败，记录检测灵敏度。

## 5. 审核记录格式

每轮保留：
```json
{
  "character_id": "p0_character_001",
  "run_id": "P0-001-YYYYMMDD-NNN",
  "stage": "G0",
  "status": "REVIEW_REQUIRED",
  "source_sha256": "...",
  "tool_versions": {},
  "camera_calibration": {},
  "checks": [
    {
      "id": "G0-IDENTITY-01",
      "status": "REVIEW_REQUIRED",
      "metric": null,
      "threshold": null,
      "evidence": [],
      "finding": "",
      "repair_task": ""
    }
  ],
  "reviewer": null,
  "artifacts": []
}
```

每次门禁输出不可变 `run_id` 和原始证据的 SHA、验收代码 SHA、输入哈希。技术结果和人工结果分别存储；综合结果由门禁逻辑算出，不能人工覆盖原始测量。

## 6. 执行批次及交付定义

**批次 A：基线与四视角（G0–G1）**。锁定 Hero / 身份；生成独立 0/45/90/180 的 RGBA；校准；角色视觉审批。

**批次 B：正面器官作者资产（G2–G3）**。修订 19 层原型语义边界，补绘隐藏区域，重新形成可独立运动的图层；生成 PSD，必须实测编辑器回读与合成。

**批次 C：跨视角器官（G2–G4）**。45/90/180 每个真实可见器官独立分层；每视角 landmark/identity/occlusion，进行局部错层与镜像负控。

**批次 D：变形与 HEAD009（G5–G6）**。完成器官运动压力样本；接入 0–90，检验 78–90 耳入镜及 20/55/82 独立参考。

建议第一轮实现验收工具的最小闭环：**一个已锁定 Hero + 一组真正的左右眼图层 + 一个额头/耳朵隐藏补绘 + PSD 回读 + 平移/遮挡帧测试**。证明语义图层成立后再批量化全头四视角，避免重复生成低价值文件。

## 7. 当前基线与阻塞

- 目前正面可见像素拆分原型：19 PNG/PSD 图层、PNG 合成像素误差 0；源图原生 1122×1402。`docs/P0-character-001-front-layer-prototype.json` 记录 PSD 回读最大通道差 239、差值大于 2 的像素 47,770，需在 G3 校准后处理。
- 多视角设定图板裁切属于参考级。当前缺少四张有独立高清来源的生产 PNG 与真实语义分层；G1、G2、G3 的正式美术验收仍等待输入。
- HEAD009 T03B 工程侧已有 0–90 实测，当前耳朵显露与独立留出视角视觉验收仍在推进，P0 的图像流程不修改其状态。
- G0–G6 的门禁数值为 V1 初始预算，需通过已知正确样本和注入错误样本校准。校准只可在独立留出验证之前完成并冻结。

## 8. 依据

- [Live2D 官方 Illustration Processing](https://docs.live2d.com/en/cubism-editor-tutorials/psd/)：结构分层及隐藏绘制区域。
- [Live2D 官方 PSD Creation Notes](https://docs.live2d.com/en/cubism-editor-manual/precautions-for-psd-data/)：PSD 颜色与导入约束。
- [Live2D 官方 PSD Import](https://docs.live2d.com/en/cubism-editor-manual/psd-import/)：层级与 ArtMesh 兼容性。
- [psd-tools](https://github.com/psd-tools/psd-tools)：独立解析和合成，注意与 Photoshop 的合成差异。
- [LPIPS, CVPR 2018](https://openaccess.thecvf.com/content_cvpr_2018/html/Zhang_The_Unreasonable_Effectiveness_CVPR_2018_paper.html)：感知差异辅助评估，不能替代结构、遮挡和人工器官验收。

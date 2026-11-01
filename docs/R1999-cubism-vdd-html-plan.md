# R1999 · Cubism 多视角原画与 VDD HTML 验证方案

日期：2026-11-01
状态：PLAN_APPROVED_SCOPE / INPUT_INVENTORY_VERIFIED / RUNTIME_VALIDATION_PENDING
实验仓库：`tims-SP/koma-motion-lab`
本体仓库：`tims-SP/koma-motion`
任务状态：[`docs/R1999-cubism-vdd-html-tasks.json`](R1999-cubism-vdd-html-tasks.json)

## 1. 目标、试验对象与成功定义

技术主线：**Cubism 原生高质量立绘 + 多视角分层原画 + 3D Anchor + View-Dependent Deformation (VDD) + Three.js/WebGL2 + HTML 实时验收**。

选择《重返未来：1999》角色 `302301_shisihangshi`（十四行诗 / Sonetto）原生 Cubism 模型进行真实验证。核心不是做一个能旋转的演示图，而是：

1. **Native fidelity**：先在原生 Cubism Web 运行时重现纹理、原动画、蒙版、透明、颜色与 Drawable 顺序。
2. **Part interoperability**：在运行时可重复读取参数与动态 Drawable 结构，逐部件映射到增强渲染器；每一步对照原生基线。
3. **Novel views**：使用独立绘制并可追溯的侧面与背面素材，建立一致器官 ID、坐标、深度与 VDD 连续过渡；先完成 **0–90°**，再完成头部水平 **360°**。
4. **HTML acceptance**：相同模型状态/时间/角度下同时呈现原生、扩展、独立参考及差异；产出真实浏览器截图、逐帧结果、结构化 QA、可复现报告。

**角度语义**：`cameraYawDeg` 是物体相对相机的水平方位角，0°=角色正面，90°=角色右侧视图，180°=背面，270°=角色左侧视图，360°=正面环回。角色的解剖学左/右单独标注。Cubism 的 `PARAM_ANGLE_X/Y/Z` 属于原生二维面部控制，不用作真实空间角度；实际参数范围由 Core 加载后枚举确定。

**精度边界**：源仓库含已导出的 `.moc3`、贴图及动作，并未因此取得 `.cmo3` 编辑工程、原 PSD 或完整侧面/背面设计。现有原生 Drawable 数据可进行运行时重放与采样；运行时顶点采样不直接等于原始建模关键帧/可编辑网格。背面与真侧脸的独立原画以 R03 资产门禁审计，任何缺失角度列出最小需补画部件及数量。

## 2. 已核对输入与固定版本

资产源：<https://github.com/myssal/Reverse-1999-CN-Asset/tree/master/live2d/roles/302301_shisihangshi>
最近核对的上游 `master` HEAD：`45e75248ba3b25053fd32e63ab13c2f9f54dd9df`（后续下载使用 commit 固定引用并写入 SHA-256）。

```text
302301_shisihangshi/
├── 302301_shisihangshi.moc3             # 1,006,080 bytes
├── 302301_shisihangshi.model3.json       # 包含路径和动作/表情引用
├── 302301_shisihangshi.cdi3.json         # 180 参数记录 / 46 Part 记录
├── textures/
│   ├── 302301_shisihangshi_00.png
│   └── 302301_shisihangshi_01.png
├── motions/                             # 22 个 motion3.json 文件
└── expressions/                         # 6 个唯一 exp3.json 文件
```

`model3.json` 共有 12 条表情引用，其中 6 个名称重复；保留原始引用/顺序，内部索引用唯一文件路径规整。眨眼及口型群组指向 `PARAM_EYE_L_OPEN`、`PARAM_EYE_R_OPEN`、`PARAM_MOUTH_OPEN_Y`。`Physics` 为 null，按缺省行为处理，不虚构物理模拟结果。`b_idle.motion3.json` 元数据：11.87 秒、30 fps、217 条曲线。

R00 只下载该目录必需资产，不克隆整个大仓库。禁止将游戏原画、含角色画面的 HTML/视频/截图或 Cubism Core 专有二进制提交公开 Git 或发布公开 Artifact/Release。Git 存放代码、构建脚本、相对文件列表、版本/哈希、匿名或自绘测试夹具、可公开的数值 QA。

## 3. 采用成熟组件的工程架构

| 层 | 选型 | 职责与验收 |
|---|---|---|
| Native oracle | 官方 [CubismWebSamples](https://github.com/Live2D/CubismWebSamples) + [CubismWebFramework](https://github.com/Live2D/CubismWebFramework) + 官方下载的 Cubism Core | 以此为像素及参数行为基线；锁定 SDK commit/版本/许可；Core 不是 GitHub 开源依赖 |
| Model adapter | TypeScript，运行时只读提取 | 获取 parameter ID/range/current、Drawable index/part、顶点、索引、UV、纹理 index、opacity、blend、multiply/screen colors（存在时）、mask、draw/render order |
| 2.75D renderer | Three.js/WebGL2，复用现有 `experiments/head009` 诊断组件 | 将源 ArtMesh 与新视角特有 ArtMesh 置入统一部件语义、3D Anchor、VDD 与可见性/局部遮挡层 |
| View authoring | 带独立 source SHA 的 PNG RGBA / 语义 landmark / 分部件遮罩 | 视角 0/45/90（第一阶段）；保留独立 20/55/82° 真值；360 阶段再扩展侧背关键视图 |
| Browser acceptance | Vite + Playwright + Chromium + Canvas/WebGL2 | 同一 HTML 面板实时互动、固定时间逐帧、浏览器截图/QA JSON、受控文件包 |
| Video export | 实际 browser frame PNG 序列 + ffmpeg | HTML 渲染帧与 MP4 同源，帧号和源哈希可复查 |

Native oracle 保持正确的动画/透明/裁剪和绘制顺序；适配层从稳定的 SDK Model API 或明确版本的 Core Wrapper 读取数据。在增加 3D 锚点之前先证明中性姿势与至少两段动作的像素级对齐。若当前 SDK 允许复用原生 clipping 机制，优先保留原始 mask 逻辑；迁移到 Three.js 时实现独立匹配的 clipping，避免用全局 Z 顺序替代复杂 Cubism 遮罩。

官方文档：
- <https://docs.live2d.com/en/cubism-sdk-manual/cubism-core/>
- <https://docs.live2d.com/en/cubism-sdk-manual/parameters/>
- <https://docs.live2d.com/en/cubism-sdk-manual/ow-sdk-mask-premake-web/>
- <https://docs.live2d.com/en/cubism-sdk-manual/cubism-sdk-for-web/>

## 4. 多视角原画与 VDD 数据标准

建立 `experiments/r1999-cubism-vdd/`，其中：

```text
experiments/r1999-cubism-vdd/
├── src/
│   ├── native/                 # Cubism SDK 引导、参数和逐帧状态采样
│   ├── bridge/                 # Drawables/PartID -> 标准语义部件
│   ├── views/                  # 源视角登记、关键帧选择、视角切换
│   ├── vdd/                    # 语义 landmark 对齐、局部形变
│   ├── occlusion/              # view-relative depth + clip/alpha/masks
│   ├── renderer/               # Three.js 视图和四通道
│   └── review/                 # 双/三视图对比、控制器与导出
├── fixtures/                   # 可公开的自绘测试贴图/参考
├── schemas/                    # 输入、部件、视角、验收 JSON Schema
├── scripts/                    # audit-assets/render-frames/qa-html
└── package.json
```

个人资产缓存位置通过 `R1999_ASSET_ROOT` 配置，Git 仅跟踪路径映射与哈希记录。实际 SDK Core 通过 `CUBISM_SDK_ROOT` 配置；不从不受信任的 CDN 下载专有运行库。

关键结构：
- `sourceRef`：`upstreamCommit`、`path`、`sha256`、`width/height`、`alpha`、`origin`、`role='key|heldout|runtime-sample'`。**只有真正独立素材可作为视角真值**，Cubism 参数渲染截图属于 `runtime-sample`。
- `part`：稳定解剖学 `semanticId`、`cubismPartId`、Drawable indices、纹理与蒙版引用、可见性和渲染合成规则；相机层局部 `anchorXYZ`，Canvas / source / UV / model 坐标变换矩阵及逆矩阵。
- `viewKey`：角度、原生/新增 RGBA 层、局部 ArtMesh 顶点/UV/三角形、器官 landmarks、`frontOf`/`behind`、动态裁剪 masks、`visible|occluded|enter|exit|split|merge`。
- `vdd`：对应器官身份的顶点/landmark 插值，支持按部位权重和局部 corrections。只有具有可靠对应关系的同一个器官才形变；轮廓拓扑变化采用新增 source key、可见性切换、局部 occlusion、分片替换。
- 原生运动参数 `nativePose(t)` 与相机视角 `cameraYawDeg` 分离：生成增强视角时先计算相机相对局部骨骼朝向，再叠加眼球、眨眼、口部等独立参数。所有中间状态可序列化并重放。

**VDD 首轮优先器官**：近/远眼、眼白/虹膜、鼻梁鼻尖、嘴唇与口腔、下颌、两耳、前刘海、侧发与后发。视角之间不混合整张完整人物 PNG；对于身份未对齐的轮廓禁止直接顶点 lerp、整图 alpha crossfade 冒充真实旋转。

## 5. HTML 工作台（首要交付界面）

至少 1366×900 桌面浏览器设计，适配 390×844 手机浏览器；像素比锁定的离屏截图模式与响应式预览模式分离。页面由一个本地静态服务运行，可在完全断网状态完成验收。先交付可复制的 **HTML + JS/CSS + 本地依赖资源包**；只有验证运行时许可和 file:// 模块加载安全性后才考虑单 HTML 离线嵌入格式。

### 页面面板

1. **原生 Cubism**：冻结原生随机 idle，固定可重放时间 `t`，与扩展视图使用相同模型和参数状态；仅显示原生合法的参数姿态。
2. **2.75D 扩展**：用户控制 `cameraYawDeg`，原生部件形变叠加新增视角纹理/局部 VDD 和正确遮挡。
3. **独立视角参考**：选择对应角度的 `key` / `heldout` 真值；缺少同角度源素材时明确显示 `REFERENCE_UNAVAILABLE`，不拿最近角度假装真值。
4. **像素差异与部件诊断**：Beauty、Part ID、Depth、Alpha、Mask、UV Wireframe、Landmarks、Visibility Graph，左右/叠图切换。
5. **控制区**：角度滑杆与 0/15/30/45/60/75/90 快捷键；360 阶段扩展至 0/45/90/135/180/225/270/315/360；motion、expression、eye open、mouth open、time、play/pause、帧号。
6. **导出区**：导出 PNG、指定范围逐帧截图、JSON 报告及 MP4；保存 `assetSha`、`sdkVersion`、`engineCommit`、`yaw`、`time`、`parameters`、`referenceRole`、QA 结果；含原画时采用私有存储。

**硬约束**：禁止用视觉参考图代替实际 Canvas 的渲染截图；QA 与截图来自相同帧和状态；自动化状态必须实际经过 WebGL renderer 更新后计算；随机项全部固定种子。Chrome/Chromium 真实运行检查 network=0、JS exceptions=0、资源 load fail=0、UI 实际控件切换以及测试注入错误的报警。

## 6. 执行任务与阶段门禁

| ID | 子任务 | 交付与验收 |
|---|---|---|
| C00 | 固定资产源与运行时依赖 | `asset-manifest.json`、每文件 SHA、引用检查、Cubism Core/Framework 版本和许可证记录 |
| C01 | 原生 Cubism HTML 基线 | `native.html`：完整角色、idle/点头/摇头、至少两种表情和眨眼口型；PNG+时间线，人工通过 |
| C02 | 原生网格/遮罩采样 | 全 Drawable/Part/参数清单、动态 vertices/UV、mask/order、实际两种动画时间点数据；检查稳定性 |
| C03 | 原生→Three.js 逐帧保真 | 同分辨率相同姿态的 Native/Adapter 双屏、RGB/alpha/轮廓/Mask 误差、自动注错；视觉通过后建立基线 |
| C04 | 多视角素材审计与试验准备 | 0/45/90 源层及独立 20/55/82 检验源的来源/身份、SHA、层/器官标注和需补部位；缺少则输出精准增补清单和可演示边界 |
| C05 | VDD 与空间锚点 | 部件语义映射、3D Anchor 标定、局部形变、可见性和分区域深度图；debug overlay + 同源 Beauty/ID/Depth/Alpha |
| C06 | 0–90° 连续运动 | 原画关键角、独立留出角的轮廓/五官/蒙版/发丝审核，0–90° 视频，机器+人工双验收 |
| C07 | 头部水平 360° | 新增 135/180/225/270/315 的必要部件视图，完成左右/后脑视角与 0/360 连续性，提供 360° 视频 |
| C08 | 表情 × 视角 × 时间组合 | blink、mouth、表情、头发运动与转头组合抽样，遮挡/身份不变；录制完整镜头案例 |
| C09 | HTML 成品与跨环境复现 | 离线资源包、Chromium QA、桌面/移动端 HTML、30fps 固定帧导出、QA JSON 与人工验收 |
| C10 | 引擎迁入 | 仅将通用 VDD/数据契约/QA/Renderer 迁入 `tims-SP/koma-motion`；Git SHA 与再现命令 |

**优先级路径：C00 → C01 → C02 → C03；C04 可与 C01–C03 并行；C03+C04 → C05 → C06 → C07 → C08 → C09 → C10。** 一阶段门禁通过就推进下一项；C04 素材若不足，在 C03 后先做局部可证实 VDD 原型与资产补画工作，不用伪造 90/180° 验收结果。

## 7. 验收矩阵与停止条件

指标为首次验收的候选阈值，必须在固定 640×640/1280×1280 离屏画布、匹配色彩空间/抗锯齿/缩放、真实基础模型和人工样本上校准，报告原始数值；数值过线不能推翻可见视觉瑕疵。

| 维度 | 标准 |
|---|---|
| 原生加载 | `.moc3` 与两张主纹理、22 个动作、6 个唯一表情可解析、依原定义播放；实际引用完整率 100% |
| 逐部件结构 | Drawable 的模型索引、网格顶点/索引/UV、纹理关联、Opacity、Mask、Sort、Blend 均按 SDK 当前实际数据校验 |
| Native/Adapter 保真 | 固定典型状态下关键视图 Alpha coverage mismatch 初期预算 <= 0.5% 非边缘前景像素；边界容差 1 px；像素颜色误差另行记录，违规遮挡人工一票否决 |
| 新视角关键图 | 0/45/90 对应独立绘画源，校准后关键视角 silhouette IoU 初期目标 >= 0.95，关键器官 landmark 误差 <= 2% 头部高度，需独立人工复核 |
| 中间视角 | 使用 20/55/82° **新独立留出**素材，不参与插值和调参；记录 IoU、五官形状、遮挡与像素误差并经人工确认 |
| 动作一致性 | 固定 t 下连续扫描 0–90°/0–360°；检查眼鼻口耳头发身份、帧跳变、前后层穿插、深度裂缝；0/360 同姿一致 |
| 诊断独立性 | 真实 Beauty/ID/Depth/Alpha/Mask 的共享覆盖一致，故意破坏 mask/depth/UV 的负例必被诊断识别 |
| HTML 功能 | Chromium 浏览器真实操作角度、表情、动作、帧暂停/步进、每种诊断、PNG/JSON/帧导出、全离线运行，所有测试记录包含 SHA |
| 视觉签收 | 正面、45°、真侧脸、背面及过渡帧由实际截图/视频检查；如基础结构失真，状态为 `VISUAL_REWORK` |

每个任务只允许：`PENDING`、`RUNNING`、`ENGINEERING_PASS`、`VISUAL_PASS`、`BLOCKED`、`VISUAL_REWORK`，且必须附可访问日志/报告/截图来源。总任务达到 C10 且 C01/C03/C06/C07/C08/C09 的真实可视验收状态为 `VISUAL_PASS` 才能标识 `MVP_COMPLETE`。

## 8. 首轮执行顺序

1. 核对官方 Core 获得方式、下载授权、版本；读取上游固定 commit 中十四行诗的全资源，实际完成 `.moc3` 加载。
2. 使用 SDK 官方 Sample 制作 **原生 Cubism HTML**：idle + 点头 + 摇头 + 表情与面部控制，可冻结随机与按帧采样；立刻输出真实 PNG 和参数清单。
3. 枚举 Drawable、mask、order、UV/顶点等；同一帧在 Three.js 适配 renderer 重放并生成差异报告。
4. 同步审查角色现有能否获得正、3/4、真侧、背面独立可用原画；按角色器官列出来源、缺失像素/层与补画成本。测试用模型实际姿势渲染仅作近似原型，不充作新视角真值。
5. 为首轮 0/45/90 + 20/55/82 建立 provenance、landmarks 和可见性，完成 VDD。HTML 每一步持续可查看而非最后统一生成空白预览。
6. 从 0–90° 视觉门禁进到 360°；按实际补画成本决定是否需要鼻/耳/头发接缝的局部几何辅助，Cubism 立绘与多视角 VDD 保持主架构。

## 9. 与现有实验的关系

现有 `experiments/head009/` 已实现 Three.js/WebGL、单 HTML 交互界面、Beauty/Part ID/Depth/Alpha 及 Playwright 浏览器截图的技术框架。其审计报告含 0/45/90 SVG 原画关键视角、独立开发参考的多个角度、故障注入与视觉复核结论。新实验复用其可验证技术；**R1999 的保真与新视角门禁使用真实 Cubism 模型与独立的 R1999 参考资料重新评测**。

开发在本次仓库继续，经过正式验收的通用引擎代码迁往本体仓库。每个步骤提交源码、记录精确运行输入/输出哈希和 GitHub Actions 检查结果。

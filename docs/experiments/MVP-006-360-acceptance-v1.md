# 2.75D Anime Studio · 360° 核心验收规范 V1
**制定日期：2026-10-31｜状态：方案已制定，尚未按本规范执行/通过验收**

目标：回答“当前人物是否真正具备连续、结构合理的水平 360° 旋转”，而不是“是否能生成 MP4”。该规范是 **MVP-006 / 下一轮核心实现的验收依据**。旧 MVP-002—005 的 \`PASS_ENGINEERING\` 只代表旧渲染/动作/纹理工作流通过，不能自动升级为本规范的 360° PASS。

## 0. 选择：一次渲染 + 三重验收，而非二选一

**必选 A：TS 结构化规则检查**。精确证明数据、空间、跨视角一致性及遮挡控制没有错；逐帧自动执行。
**必选 B：实际输出图像的视觉模型/人工检查**。观察轮廓、五官、头发、部件出入和遮挡穿帮。输入是同一次渲染产生的真实图，绝不能用单独生成的“概念图”替代。
**必选 C：完整 192 帧视频/异常帧邻域检查**。检查时间上的跳层、闪烁和莫名动作；只看 24 张静帧不够。

三者按 **AND 硬门禁** 决策，不设计“综合评分高于 80 即通过”：一个严重的背面眼睛错误不能被 99% 的正确数据抵消。视觉模型不能替代数据结构和真人审查，结构化检查也不能证明动漫画质。

此阶段验收的是**同一简化角色的几何/视觉 360° 连续性**，不要求日本动画商业美术精度；与后续的“动漫原画保真验收”和“带动作的全身 360°”分别记状态。

## 1. 一次真实渲染的输入/输出

固定同一 **12 部件**样机、同一角色定义、同一 Three.js/TypeScript \`evaluate\`。锁定浏览器、WebGL、分辨率、随机种子、相机位置/投影、姿势、灯光（先固定灯光避免将阴影跳变误判成视角问题）。禁止另写一个假数据来源供 QA 使用。

- **A 核心影片**：8s / 192 帧 / 24fps / 960×540（当前核心阶段即可；高画质终验再上 1920×1080）。\`yaw\` 全范围覆盖 0°→360°；影片可等速或有明确定义 easing，但每帧 trace 必须记录实际角度。另独立渲染 \`yaw=360°\`，不把 192 帧视频最后一帧 358.125° 误当 360°。
- **B 角度采样**：从同一求值器独立渲染 \`0,15,30,...,345,360\` 共 **25 个角度状态**，与视频时序无关；按方向拼接 24 样本 + 360/0 接缝对照。特别突出 45/135/225/315。
- **C 边界邻域**：对 0、90、180、270 的两侧额外采样 \`±1°\`，共最多 8 张；如果角度 360 对应 0，则按环绕取值。
- **D 每帧元数据**：192 帧全部输出结构化 JSONL/JSON；选定 24 帧额外输出 \`beauty\`、\`partId\`、\`depth\`、\`alpha/mask\`、\`mesh/landmarks\` 可视化图层。无需给全部 192 帧导出调试 PNG。
- **E 关键姿势/角色数据**：角色 Part ID 表、前后左右四个**独立的视角几何设计**、骨架/anchor、可见性/遮挡约束表、关键轮廓/语义 landmark 与参考图；必须对 90°/270° 各自独立定义，禁止 \`mirror(90)\` 冒充已实现 270°（可以明确作为 FAIL/暂存 fallback，但不得 PASS）。
- **F 真实成片**：\`turn360-8s.mp4\`、\`turn360-angles.png\`、\`turn360-transitions.png\`、\`turn360-qa.json\`；不放第三方未授权二进制入公共 Git。

独立角度检查和 8 秒影片使用同一 \`evaluateCharacter({yaw,pose,camera,debug})\`，不能为了得到 PASS 写第二套渲染器或特例分支。

## 2. 最小结构化数据契约（必须由引擎实际输出）

逐帧 \`FrameTrace\`：
- \`frameIndex, timeSeconds, yawDeg, cameraHash, poseHash, characterAssetHash\`;
- \`parts[]\`，每个包含 \`partId, parentBoneId, worldAnchorXYZ, projectedAnchorXY, vddOffsetXY, viewKeyA, viewKeyB, viewWeight, verticesXY, uvXY, triangles, visibility, topologyMode, depthRange, occlusionRulesApplied, materialTextureKey/sha\`;
- \`actualVisiblePartIds\`，来自渲染后的 **part-ID pass**，而非“运行时认为应显示”的意图字段；
- \`boundsPixels\`、\`geometryWarnings[]\`、\`imageDiagnostics[]\`。

\`RenderEvidence\` 同帧同状态输出 beauty / partId / depth / alphaMask / meshOverlay；每张证据带 \`frameOrAngle, characterAssetHash, cameraHash, poseHash, rendererCommit\`。当资产量大时可以将顶点完整坐标只保存为异常帧 dump + 25 角度采样，其余帧保留摘要和诊断指标，但结构检查必须真正遍历对应顶点数据，不能只检查部分数目。

提供一个受控不对称标记（例如衣襟左侧胸针）并报告它在四方向是否可见及位于身体哪一侧。不能因镜像后看起来像同一角色就 PASS。

## 3. 门禁 A：程序自动判定，整段范围

| ID | 输入 | PASS 要求 | FAIL 条件 |
|---|---|---|---|
| S01 角度覆盖 | 所有 192 帧 + 25 独立角度 | 单调覆盖一个完整周，方向正确；帧角度/采样角度均与实际求值一致 | 漏角、反向、只旋转平面、重复卡片替换 |
| S02 0/360 周期 | 同 pose/camera/light 的 0° 与 360° | 各 Part anchor、mesh、UV、visibility、depth、纹理混合参数数值等价；实际 RGBA 像素差同渲染设备上在校准容差内 | 0/360 出现明显接缝或不同角色状态 |
| S03 3D Anchor / VDD 责任 | source anchor/projection/VDD + vertex traces | 对应关系 \`p=project(R·A)+D(theta)\` 可独立从 trace 复算；检测部件按设计在深度和横向变化；禁止整身 2D 平面旋转冒充 3D anchors | 偏移只做一次全身平移/缩放、真实 Anchor 缺失、trace 无法复算 |
| S04 局部 ArtMesh / UV | 所有部件各角度 mesh | triangles/UV/landmark 有效、有限数、三角形没有未申报的退化/翻折、自交、纹理索引越界 | 负面积突然翻转、错误 UV、NaN/Inf、五官成为整身一张贴图 |
| S05 姿态与连续性 | 帧间部件 anchor/mesh/visibility | 相邻角度的连续轨迹、局部轮廓变化符合预期；拓扑/显隐切换必须有显式规则并经过遮挡 | 部件跳位、突然消失、未登记的 split/merge |
| S06 动态遮挡 | per-part depth、实际 partId pass、遮挡约束 | 刘海/脸、后发/脖颈、左右眼、手臂/躯干关键视角遵循“期望谁遮住谁”的显式规则；计算可见区域 | 只靠 Mesh 的深度数值，但最终合成露出本应隐藏的图层 |
| S07 角色身份与不对称 | 0/90/180/270 的 marker/左右部件语义 | 角色的左手/右手、头部/后发、胸针等标记真实方向正确，不误用镜像 | 90° 和 270° 仅自动镜像、左右语义交换、背面出现正面五官 |
| S08 渲染完整性 | WebGL + PNG + MP4/ffprobe | 192 帧、固定分辨率、无空帧、无裁切、无异常 WebGL、同 yaw 随机 seek 确定性 | 缺帧、空白、模型出屏、同状态图像不一致 |

**容差策略**：S02 的世界坐标重算可从 \`1e-5\` 单位量级开始；像素差应先用同设备同状态双渲染确定可复现噪声。其余视觉跃迁、轮廓变化和局部遮挡不能拍脑袋统一设置“10px 一票否决”：相机、角色缩放、部件大小、原画风格不同，阈值必须用 **角色 bbox/部件 bbox 归一化**，与人工标注的已知好/坏样本校准。异常分数先用于排序与捕捉异常，再由约束及实际图像定性。

**重要**：程序不可能从单个 frame 推知“人物正面看起来好不好”。也不能用 \`partCount===12\`、\`keyViewCount===4\`、MP4 大小和 \`IKError≈0\` 代替以上 S01—S08。

## 4. 门禁 B：视觉模型读取真实截图（低成本）

第一轮固定读取最多 **两张图板**：
1. 24 方向全身表：角度+角色 bbox 对齐；同时显示指定参考关键方向（不必夸张放大）。
2. 关键部件特写表：正/斜/侧/背的脸、刘海、身体与最容易穿帮的遮挡过渡。

**给视觉模型明确任务**：只用这些实际截图检查“同一个角色？正侧背空间关系合理？眼睛数量/位置正确？额头刘海是否穿过脸？衣服标记有无左右翻转？是否出现双影、坍塌或奇怪宽度？”；输出 JSON issue \`{id, severity, angleDeg, partIds, observation, evidenceFrame, suggestedFix, confidence}\`。不得仅回答“很好”“看起来顺滑”或自行宣称完整 360 已通过。

若 24 帧粗筛出现问题，**只**附相关的 2—4 张原分辨率局部放大图。若程序指标发现跃变，追加**最差 3—5 个时序窗口的帧条带**。无需让模型为每次提交读取 192 张完整帧。

视觉模型的结论是审核建议，不是模型替用户按下最终画质 PASS。置信度不足则 \`NEEDS_REVIEW\`。如果无需 API，就在当前 ChatGPT 对话里由模型阅读 CI 上传的联系表；**GitHub Actions 无法在不配 API/模型服务的情况下自动启动 GPT 视觉理解**。不能假装这种步骤已经在 CI 自动执行。

## 5. 门禁 C：完整视频 + 时间连续性

- 所有 191 对相邻视频帧计算基础的归一化角色轮廓面积、中心移动、各 Part 轮廓形状/位置变化、可见区域变化、图像亮度差；与角速度/期望遮挡切换相关联，按异常程度排序。
- 在变化最快的位置检查 **连续帧条带**，避免静帧“全对”但播放中闪烁/跳图。合法的前后遮挡切换有定义且有稳定过渡；数值突变不是自动失败，必须检查对应部件设计。
- 关注 0/360 循环接缝，另比较相同状态的 0/360 独立图（视频最后一帧并非 360°）。
- 由视觉模型/人工观看**同一条原始 8 秒 MP4**（若工具不能直接读视频，则使用首尾、关键阶段的逐帧条带以及视频观看的人工判定）；不能用只看了 3 张 QA JPG 冒充“完整 360° 视频验收”。

可选研究：
- [LPIPS](https://github.com/richzhang/PerceptualSimilarity) 可用作**与相同预期关键图之间的感知差异辅助指标**，但需要参考图，且它不验证 Anchor/VDD/遮挡；
- 光流 warp error 可用于检测非预期闪烁，但视角旋转产生的合法形变也会造成光流误差；不能拿一个“光流分数”定 PASS；
- MVP 核心阶段**不强制 PyTorch/LPIPS/光流深度网络**，避免引入新语言、大模型下载、额外算力/费用。TypeScript/图层 ID pass 和简单图像差即可先满足可执行性。

## 6. 验收等级与停机规则

- \`NOT_RUN\`：尚无新 8 秒视频及全部结构化证据，不能算通过。
- \`FAIL_STRUCTURE\`：任一 S01—S08 的 P0 缺陷（例如镜像伪视角、缺失深度、错误拓扑、明显背面正面五官、无法渲染/接缝失败）即暂停视觉“评分”，修根因。
- \`PASS_STRUCTURE_PENDING_VISUAL\`：所有必须结构化项有证据通过；只表示模型层符合规格。
- \`FAIL_VISUAL\`：结构正常但出现持续明显的造型/遮挡/闪烁问题；精确指向角度与 Part ID。
- \`NEEDS_HUMAN_REVIEW\`：模型判断不确定，或大范围的艺术夸张需要美术选择。
- \`PASS_360_CORE\`：S01—S08 全部通过、角度图板、异常帧条带与完整视频均已查看，没有未解决 P0/P1；此 PASS 仅限**固定姿势、指定原型角色、水平 360°**。
- \`PASS_ANIME_VISUAL\`：**另一个阶段**，正式高保真原画输入后对细节风格/光照/动作的专门验收。不可由 \`PASS_360_CORE\` 自动升级。

P0：结构错、资产误翻/遗漏、视频缺失、未校验的假 360°；P1：明显视觉穿帮、跳帧或角色变形；P2：局部像素/线条不理想但不影响连续结构。

**成本规则**：一次正常修改→一次 CI 输出→结构自动诊断→至多两张模型图板→按需追加少量失败帧。只针对 P0/P1 作定点修复；不复现 Spine/Live2D 教程；不无限美术微调。保留 \`qa.json\` 的前次差异，下一轮只重新审查已变区域及相关时序段，最终正式放行再完整浏览一遍视频。

## 7. 现有仓库缺少什么，实施位置

目前 [\`src/integrated.ts\`](../../experiments/mvp002/src/integrated.ts) 输出的 \`FrameStats\` 只有 \`yaw / partCount / ikError / handDepth / shadowOffset\` 等宏观值；\`render-integrated.ts\` 只判断帧数、透明 PNG、基本深度/IK 和极少数截图。**完全不足以通过 S01—S08**。本规范**不是**宣称它已经通过了新的规范。

下一轮只改当前工程，按以下优先顺序：
1. \`src/core/qa-trace.ts\`（TypeScript）暴露统一 \`evaluateCharacter(yaw, pose, camera)\` 的内部状态，记录每 Part 位置、VDD、mesh、UV、可见性、深度、keyview；输出时不改变渲染结果。
2. \`src/core/qa-passes.ts\`：为同一组 Mesh 提供 Beauty、ID mask、depth、alpha-mask 和 mesh overlay；actualVisible 必须依据真实合成结果而不是意图。
3. \`scripts/validate-turn360.ts\`：同一运行时控制角度并产生 8s/192 frames、25 key angles、接缝对照、两张图板和 \`qa.json\`，完整执行 S01—S08。
4. Visual review 读取真实板、按需异常角度截图，并将结构化 issue 合并到 \`qa.json\`；最终用户或 Agent 审查依据标记 \`PASS_360_CORE\` 或 FAIL。

唯一的修复目标：在当前小角色上拿到**真实可复核的固定姿势 360° 核心通过证据**。通过之前，不把程序化画质提高、动作/特效整合或大型商业角色导入作为前置。

## 8. 参考与设计理由

- SIGGRAPH 2010 [2.5D Cartoon Models](https://dspace.mit.edu/entities/publication/5f707aa6-c1ee-4d0b-aa5e-06916c13a971)：多视角二维形状可产生拟真新方向，但前提是形状与空间关系合理。
- IEEE 2022 [VDD for 2.5D Cartoon Models](https://pubmed.ncbi.nlm.nih.gov/35544514/)：艺术夸张可在关键视角中通过视角依赖二维修正表达，不能要求全部部件必须符合真实三维几何。
- Three.js 官方 [Transparency](https://threejs.org/manual/pages/transparency.html)：透明相交层不能仅靠自动深度/排序推出“正确遮挡”，所以必须实际渲染 ID/mask pass。
- [LPIPS / CVPR 2018](https://github.com/richzhang/PerceptualSimilarity)：感知指标只测视觉相似性，无法替代内部结构正确性与动画连续性。

**规范实施前的最终立场：360° 尚未解决，MVP-005 以前的成功是渲染通路成功，不是此规范的核心 PASS。**

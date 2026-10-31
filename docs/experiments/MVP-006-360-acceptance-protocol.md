# 2.75D Anime Studio — 360° 核心验收协议 V1（2026-10-31）

**状态：ACCEPTANCE_SPEC_FROZEN / EXECUTION_NOT_STARTED。** 本文覆盖 MVP-003～005 中“视频可播放 = 360° 已解决”的旧口径。只有新的 8 秒 360° 专项片通过本文的独立几何、屏幕遮挡和时序审查，才允许写 \`360_CORE_PASS\`。本文件是验收方案，不代表已经执行或已通过。

## 0. 目标边界与验收对象

验证的只有 **同一轻量 2.5D 人物、固定身体姿势、固定正交摄像机下的水平 Yaw 一整圈**。3D Anchor、部件局部视角、逐顶点 VDD/形状修正、跨视角 RGBA/UV、出现消失以及可见区域的真实前后遮挡必须共同成立。后续全身动作和高质量画风单独验收，不能借这次通过来替代。

**反作弊**：不允许整身 Sprite 旋转/整身跨淡入淡出/复用同一前侧图片冒充四方向/仅改变状态 JSON 不改变实际渲染。可允许**有设计依据**的对称部件镜像，但不能以 90° 源图派生整个 270° 完整视角而声称独立多视角。需要源部件覆盖证据和至少一个真实非对称衣饰标志在全圈保持正确方位。

素材不要求日漫高画质；完整业务质量另用 \`ART_QUALITY\` 状态表示。但**不能使用错误的假视角素材使表示系统“通过”**：关键视角必须至少在部件形状、可见性、遮挡上分别定义，而不是只有贴图颜色不同。MVP 目标 8～12 个可独立描绘的语义部件。角色可为简化原创图。

## 1. 方案：结构化几何证据（主）+ 屏幕空间独立验证（关键）+ 视觉模型/人工审查（辅）

**只渲染一遍**，使用同一帧求值器和固定随机种子，在必要关键角度从 GPU 附加导出 ID/可见性/深度/网格/UV 诊断通道。关键点是**不能仅信任同一渲染函数自己报告的状态**；实际屏幕 ID 像素需要与 CPU 几何/预期交叠区域单独比对。官方 Three.js \`WebGLRenderTarget\` 和 \`readRenderTargetPixelsAsync\` / \`readRenderTargetPixels\` 可实现。

三个判定层：
- **A — STRUCTURAL**（自动/硬门槛）：素材覆盖、角度/环绕、部件锚点/顶点合法性、逐帧确定性、裁切、可见性、网格翻折和 0/360 接缝。数据来自角色 manifest + 引擎输出，不能代替屏幕证据。
- **B — SCREEN_AND_TEMPORAL**（自动/硬门槛）：实际 RGB、Part-ID、可见像素、深度/遮挡、相邻帧时序误差；抽帧必须从真正渲染的图像读取，而不是只看内部 z 值或配置。只评估有合法对应的可见像素，出现/消失边界需用显式遮挡掩码排除。
- **C — VISUAL**（模型审查/人工复核）：对每个基准方向与中间方向判断脸、头发、衣物、肢体是否自然，发现造型突变/双眼残影/穿帮/静态纸板感；阅读 8 秒视频或相邻帧序列判断闪烁。视觉模型**不给算法正确性认证**，只能报告证据、缺陷与不确定性。自动 PASS 并不等于日漫画质 PASS。

## 2. 唯一核心验收镜头与采样

- 固定 orthographic camera、固定角色站姿/眼口状态和固定照明；特效不随时间随机变化。角色 yaw(\`frame\`) = 360 × frame/192；视频使用帧 0…191（共 192 帧、24fps、8s），额外**独立**求值帧 192 = 360° 与帧 0 比较。不能将最后一帧 358.125° 与第 0 帧硬性像素相等。
- 24 方位：0,15,30,…,345°（分别对应视频帧 0,8,16,…184）；另 360° 接缝帧。必要时增加四个风险点：遮挡层级交叉前后 ±1 帧/±5°、严重局部纹理变形前后。
- 0/90/180/270 对照各自独立的**原始参考视角**；必须同时生成参考叠图与差异图。45/135/225/315° 作为最重要的新视角视觉判断，模型不得拿四张源图直接代替它们。
- 每 192 帧输出一张 RGB，原本的 24 方向 + 变化事件帧额外导出 Part-ID、Depth、Mesh/Anchor Overlay；必要时抽出在相同局部条件下的 RGB 对照。720/540p 可先快速调试，但最终核心门槛为 **1920×1080 H.264**；在生产流程稳定前使用单次快速低清调试不是正式 PASS。
- 用**同一个 renderer 实例 + 同一个确定性 frame evaluator**完成主片/诊断；不拆成三段新样机。诊断视角不得与正式镜头使用不同的角色/原画/修正规则。

## 3. 结构化硬门槛 (A)

| ID | 必须检查 | PASS 条件 / 原则 |
|---|---|---|
| A01 | 输入资产与角度覆盖 | 至少 4 个**相互独立记录**的 0/90/180/270 关键方向；每个核心 Part 有可对应的来源、稳定 Part ID、anchor、局部轮廓/UV、可见性与明确的分裂/消失定义。不能以镜像整身当作一个独立方向。 |
| A02 | 角色与姿势不变 | 全部帧使用相同角色 UUID/版本/hash，除了 yaw 没有悄悄更换帧图、骨架、场景或播放新的动作。 |
| A03 | 几何与纹理 | 可见非退化三角形无 NaN/Inf/非法顶点索引、无未声明的拓扑切换、UV 有效；**允许**被授权的消失/压扁边缘视角，不用纯符号面积检查错误拒绝合法侧向变形。 |
| A04 | 部件形变的独立性 | 多个可见部件的顶点/锚点/轮廓确实随方向独立变化；发现**只有整张平面一次性旋转或 4 张全身图切换**即 FAIL。 |
| A05 | 周期与接缝 | 每个部件状态 \`E(0)\` 与 \`E(360)\` 等价；固定相机/灯光且无特效差异的两张真正 RGB 截图几乎完全一致；第一次可采用差异像素率 ≤0.1% 的**暂定**门限，需同运行环境校准并保留差异图。 |
| A06 | 覆盖与裁切 | 全身角色按镜头设计保持画面范围；任何核心可见部件不得被意外裁掉。隐身部件应声明原因（occluded/backface/intentional absent），而不是悄悄丢失。 |
| A07 | 确定性 | 同一 angle/state 随机 seek 两次，CPU 状态和渲染图片一致；和此前帧的播放顺序无关。 |

## 4. 实际屏幕与时序门槛 (B)

**B01 屏幕 Part ID / Depth**：部件使用固定整数编码输出无抗锯齿 ID pass（或边缘在测试中单独处理）及深度/可见性 pass。CPU 记录各部件在该方位投影轮廓与预期遮挡区域；GPU 可见像素 ID 必须合理一致。**只有数学 z 顺序变化、屏幕未发生实际覆盖时，不构成遮挡通过。**

**B02 遮挡事件**：给出真实部件交叠的事件，例如 face ↔ fringe、head ↔ backHair、arm ↔ torso（在固定姿势的 360 镜头内确实发生的才适用）。每个事件需指定两边角度、哪一侧部件在前、实际可见像素的证据。要求至少一组已覆盖且可观测的**部件前后切换**和一个部件被遮住再恢复；不足则 \`BLOCKED_INSUFFICIENT_OCCLUSION_SCENE\`，绝不将无交叠算 PASS。全身动作场景中的手臂穿胸属于**另一个动作能力**，不能冒充 360 转身的遮挡检验。

**B03 纹理 / 轮廓注册**：在 0/90/180/270 的可见区域比对实际渲染与真实原画参考（裁切、坐标注册、色彩空间一致后）。\`pixelmatch\`/Playwright 快照仅用于**相同角度同一原画的保真或回归**，不能把两张不同角度做像素差阈值。基准由已经审核的源素材定义，不能从有 bug 的输出自动更新生成一个“正确答案”。

**B04 跨角度连续性**：跟踪部件 anchor / contour / mesh / bbox 的相邻帧运动，一般角度无无法解释的位置跳跃、错误消失、顶点翻面、奇异拉伸；同一部件的画面增减/面部朝向变化应与角度和可见性规则匹配。单纯降低像素变化幅度不能证明正确（静止纸板会虚假高分）。

**B05 视频时间稳定**：可追踪区域通过几何/UV 运动补偿后计算相邻帧纹理残差（warp discrepancy），只统计前后两帧共同可见区域，剔除新显露区域/预设切换区域。不要直接用整幅相邻帧像素差判断闪烁——旋转本来会产生真实差异。产生最严重时间区间与对应帧；只在自动阈值**经首个已人工确认的基线校准后**启用硬阈值，未校准先报 \`REVIEW_REQUIRED\`。

**B06 视频完整性**：8s / 24fps / 192 编码帧 / 1920×1080，非空白/非全黑，不能临时用 6s 里前 2s 的 48 帧冒充完整 360。

可借鉴视频时序评价中的 optical-flow/warp error，但优先用已有的**每部件三角网格与 UV 对应**代替昂贵的新光流模型；这是自带精确运动对应信息的可控渲染器。参考：Wiley 2024《Evaluation in Neural Style Transfer: A Review》之 temporal consistency、NeurIPS 2010 分层遮挡工作。

## 5. 视觉模型验收 (C)

视觉模型**只看真实输出**：不允许阅读预期分数后决定是否通过，不允许把图像生成的概念图当作渲染证据。

**默认预算**：
- 8 个高分辨率角度：0/45/90/135/180/225/270/315，每个都标明源角度/插值角度，必要时提供邻近帧。
- 程序风险排行选**最多 4 个**额外帧/相邻帧小拼图（网格折叠、异常跳跃、深度切换点、差异最大段）。
- 还需实际连续看一遍完整 8s MP4，或等价的短时连续帧切片；**只读 8 张图不能检查闪烁**。
- AI 检查：角色身份/服饰标记、脸型/眼睛与头发、体态/手脚、空间转向可信度、遮挡/轮廓、时间连续性。任何缺陷必须输出 \`frame, angle, partId, issue, severity, imageEvidence, confidence\`，不得“整体 93 分所以 PASS”。
- 模型输出只有 \`VISUAL_PASS_CANDIDATE\`, \`VISUAL_FAIL\`, \`REVIEW_REQUIRED\`；严重缺陷或结构失败不可被高模型分覆盖。最终由用户/人工观看视频作最少一次最终品质复核；日常不要求用户逐帧审核。
- 不在默认 CI 中引入付费多模态 API 或重复 192 次视觉模型调用。没有模型授权/可用上下文时保存 12 张候选图 + 缺陷 JSON，标 \`PENDING_VISUAL_REVIEW\`，不假称 AI 已审核。

## 6. 接受/拒绝的状态制度

- \`NOT_RUN\`：尚无本次新 8s 验收片。
- \`BLOCKED_EVIDENCE\`：少真实关键方向/无可观测遮挡交叠/源对应没定义/实际 ID 通道未生成；不能以 PASS 代替。
- \`FAIL_STRUCTURAL\`：空间/拓扑/遮挡、角度和接缝硬门槛失败。
- \`FAIL_VISUAL\`：结构正确但人物中间方向明显不可信、局部穿帮或时间闪烁。
- \`PASS_360_CORE_CANDIDATE\`：A + B 全部可证明且通过，C 模型无重大缺陷，人工复核待完成。
- **\`PASS_360_CORE\`：A + B + C 的真实影像审查均通过，8 秒整片已复核。**
- \`PASS_ANIME_ART\`：是独立的未来高画质验收，**绝不**由 \`PASS_360_CORE\` 自动推导。

验收硬门槛不能被多个绿灯状态简单求平均；\`BLOCKED_EVIDENCE\` 与 \`FAIL\` 都禁止宣传完成 360°。

## 7. 一次执行的产物规范

\`\`\`text
out/acceptance360/
  turn360-8sec-1080p.mp4              # actual 192 full-color frames
  keyviews-24-angles.png             # 0/15...345°
  8-angles-hires/                    # eight model/auditor images
  pass-id/                            # Part ID or color coding (sampled)
  pass-depth/                         # comparable depth/occlusion (sampled)
  pass-wire-anchors/                  # mesh, 3D anchor overlay
  source-reconstruction/              # cardinal source vs rendered RGB diffs
  seam-0-360-diff.png                 # extra exact pose comparison
  worst-temporal-sequences/           # top frame pairs or short clips
  frames-and-parts.json               # per-frame geometry/state/occlusion events
  structural-report.json              # A gates
  screen-temporal-report.json         # B gates
  visual-review.json                  # C status with defects, can be pending
  acceptance-summary.json             # authoritative final / pending decision
\`\`\`

仅代码、文本 schema、少量小型诊断索引进 Git；视频与图像进入非仓库的 Actions Artifact/Draft Release（原创测试艺术可分享）。所有失败结果也保留，可定位具体角度与部件并恢复工作。

## 8. 最短实施顺序（不建立单独算法实验）

**实施顺序是修改已有 \`experiments/mvp002\` 一套工程**：
1. \`turn360\` 独立 8s 同角色站姿镜头（不是现在 6s 混合镜头的 2s 转身），额外 360° 样本；固定相机/光照。
2. 补足真正具有非对称标记的四方 **几何** 关键造型，记录语义 Part/anchor/visible 与不同方向的画法；确保所有核心部件 keyviews 的对应与源参考。无需先制作高清动漫角色。
3. 为正常渲染器增加必要诊断输出和 CPU/GPU 独立比对，完成 A/B 的一轮联通验收。
4. 只对 8+风险图和整条视频执行一次视觉审查；修复真实缺陷，不增加重复 K0/K1/K2 基础测试。
5. 通过 \`PASS_360_CORE\` 后才进入全身动作的核心验收；高质量美术换肤和特效是其后的独立目标。

## 9. 成熟工具选型

- Three.js \`WebGLRenderTarget\` / \`readRenderTargetPixelsAsync\`：真正 RGB / ID / Depth/UV 采样。
- \`playwright\` / \`pixelmatch\`：固定角度源画/回归比较，禁止用未经确认的 golden 代替 ground truth。
- \`sharp\`：TS 环境图像裁切、拼图和处理；\`ffmpeg\` / \`ffprobe\`：真实成片/帧数。
- TS 的每部件 barycentric mesh + registered UV：计算时间连续性，有精确 correspondence 时无需新引入 GPU 光流网络。
- 多模态视觉模型：**按需**处理少量真实关键帧，不代替结构性证据或真正视频观察。

### 研究依据

- https://threejs.org/docs/pages/WebGLRenderer
- https://threejs.org/manual/pages/rendertargets.html
- https://github.com/microsoft/playwright/blob/main/docs/src/test-snapshots-js.md
- https://github.com/mapbox/pixelmatch
- https://onlinelibrary.wiley.com/doi/10.1111/cgf.15165
- https://proceedings.neurips.cc/paper_files/paper/2010/hash/f7664060cc52bc6f3d620bcedc94a4b6-Abstract.html
- https://alecrivers.com/2.5dcartoonmodels/
- https://arxiv.org/abs/2103.15472

# MVP-001 / M1 — 现有资产优先的 360° 多视角人物验证（TypeScript）

版本：2026-10-31 / 修订 2。状态：**PLANNED；未完成 TS 迁移、现有资产参考渲染或真实 360° 模型质量验收**。

主计划：[MVP-001-multiview-anime-plan.md](./MVP-001-multiview-anime-plan.md)。
[现有资产调查、具体路径、限制与 TS 技术路线](./MVP-001-assets-research.md)。

## 0. 已确认的策略变更

- **先真实资产、后建模**：不得再把“从零画原创角色”作为下一轮的起点。优先 `myssal/Reverse-1999-CN-Asset` 中角色的 Spine、Live2D、场景/剧情预制资源，并主动寻找 GitHub/官方样例/论文图形中的分层、骨骼或多视角资产。
- **代码统一 TypeScript**：浏览器、Node 工具、转换器、校验、测试均编写/维护 TS；使用 `tsx` 执行脚本、`tsc --noEmit` 严格类型检查、Three.js、Playwright、FFmpeg。旧 M0 的 JS 作为待迁移遗留，不能宣称已经迁移。
- **只迁移有价值的原始数据**：Spine 的骨骼、slot、mesh weights、animation，可帮助 M2；Live2D .moc3 及 motion/expression 可帮助 M3；二者没有被证明同一网格/坐标可一键合并。最终不是 Rive、Spine 或 Cubism 模型，转换为自定义多视角 2.5D 部件数据。
- **现有资产没有证实完整 360°**：没有真实侧面/背面时，允许在源角色的外观基准上使用 AI 或手绘**补缺的关键视角和被遮挡图层**，但不得重新独立生成另一名人物并声称是在复用资产。
- **无许可扩张**：研究个人使用。第三方游戏原画不进入公共 Git 历史、公开 Actions artifacts 或已发布的 Release；预览需要访问控制（仅非公开存储或确认未发布的 Draft Release）与许可审核。

## 1. 最终 M1 输出契约

一个经过版本化、可编辑、保留原画细节的日式动漫全身角色资产；必须在同一个角色包内有明确的 per-part ArtMesh、跨视角部件对应、anchor、visibility/occlusion、VDD correction、可供以后 M2 绑定的骨骼父节点。

- 固定正交相机；Yaw 0°~360°，**仅水平 360°**，不对 Pitch 任意方向作质量承诺；
- 8 秒 / 24 fps / 192 视频帧，1920×1080 H.264 MP4；单独求值 360° 并与 0° 对比 loop seam；
- 24 张每隔 15° 的方位采样，重要遮挡转折点再加 ±5°/±10°，四关键视角及必要八方向对照；
- 可交互 yaw、逐帧独立求值、图层/网格/深度 debug；视频、分层预览、审计报告；
- 禁止整身卡片旋转、整身 PNG 切换、整体 alpha crossfade，不能拿运行时的普通 Spine 转头动画当作完整 360° 验证；
- 后续 M2 全身动作和 M3 面部光照特效必须能够复用同一角色资产，而不是重新做独立视频。

## 2. 现有资产分级

| 等级 | 来源 | 本阶段实用目标 | 已知短板 |
|---|---|---|---|
| P0 / 主角候选 | `myssal/Reverse-1999-CN-Asset/roles/300401_hongnujian` | 原生 Spine 4.2.36、mesh、atlas、动作、部件纹理 | 不证明有真正侧面/背面绘画 |
| P0 / 面部候选 | 同仓 `live2d/roles/300401_hongnujian` | 同角色 moc3、25 个 motion、表情、双纹理 | 编译 .moc3 非编辑器分层工程；不能直接解出所有 warp controls |
| P1 / 其他候选 | `rolesstory/rolesprefab`、`roles` 中其他具有较少遮挡的角色 | 找更适合整身旋转的角色与多视角素材 | 各种相似命名不等于视角证据 |
| P1 / 绑定基准 | Spine Examples / spine-runtimes 4.2 TS | 检验骨骼/FFD/IK/constraint 解析和渲染完整性 | 卡通示例视觉质量不能代替动漫画质 |
| P1 / Cubism 基准 | Live2D 官方 Haru/Mao/Hiyori/Miara 等 | 检查参数、mesh 形变、可见性、表情、glue | 需 SDK/Core 与许可，通常不是完整 360° 资产 |
| P1 / 论文基准 | without-paper/2.5d_cartoon_model/data 多视角 SVG | 定位 Orientation Space/anchor/插值数学问题 | 简单矢量头像，非动漫全身角色 |

## 3. M1 的唯一正确执行顺序

| 任务 | 实施要求（按顺序） | 必交证据 / 阶段门禁 |
|---|---|---|
| M1-00 | 保存当前 M0 commit/Action/report，建立 M1 状态文件，完成 `main.js`→`main.ts` 与 `smoke.mjs`→`smoke.ts` 无差异迁移（类型检查、截图、编码回归） | TypeScript 核心与脚本可运行；M0 24 帧/渲染回归 PASS；不得改造成与原 fixture 不同的测试而冒充回归 |
| M1-01 | **联网现有素材普查**：对 Reverse1999 具体同一角色的 Spine/Live2D/rolesstory 做有限、版本固定、按需下载；再检查另 2~3 个候选；用官方 Live2D/Spine 及论文多视角 SVG 作对照 | TS `asset-inventory.ts` + candidates JSON，路径/散列/格式/角色左右不对称性/版权状态/视角覆盖矩阵；明确有没有真实侧背原画 |
| M1-02 | **原生参考渲染**：Spine 4.2 TS 匹配加载 .skel/.atlas/.png，复现原始 idle + 3 个动作/姿势（不沿用旧 Python bake 结果作通过证明）；Cubism 通过官方 TS SDK 独立演示眼部/表情（若不可用单独标 blocker） | 提交实际各自运行时的 1080p 关键帧/短视频、骨骼/mesh/FFD/constraints 清单和已知缺口。若原始数据都不能渲染，先修 loader/version |
| M1-03 | **选定单一最终角色和参考库**：按分层质量、全身完整、衣服/头发的复杂度、骨骼、面部表情、视角覆盖和补图成本打分 | 角色 ID + 源路径/源 commit + 参考图/骨架/需要补图的角度和区域；给出选这个角色而非其他人的理由 |
| M1-04 | **构建目标多视角资产**：保留源角色部件与外观，定义画质基准；优先复用实际已有视角，缺的 90/180/270 再由 anchored AI/手工补全，失败角度增补 45/135/225/315；将各视角切为可编辑透明部件 | 原图与 4 基本方向的同人一致性对照（头身比例、衣服花纹、非对称饰品）及每角度原画重组差异；人工审核合格才允许正式插值 |
| M1-05 | **TS 自有部件 schema / 对应关系**：建立稳定 Part ID、二三维 pivots / anchor、对应三角形/轮廓点、源纹理 UV 和 occlusion 的多视角图；向未来 3D bone hierarchy 预留空间 | TS JSON schema validator PASS，左右眼/手/脚与被遮挡的部件按角色实际解剖命名，不能用一张整身 sprite 作为唯一 Mesh |
| M1-06 | **准确重建原画关键视角**：Three.js BufferGeometry 的多部件 RGBA/UV 原画渲染；逐个部件确认纹理切图、三角网格、alpha 和遮挡 | 0/90/180/270 的原始参考 vs 程序重建 side-by-side；关键视角还原失败则禁止进入任意视角 |
| M1-07 | **空间和形变**：TS 视角选择、anchor、部件级二维 shape interpolation + VDD；一律处理 0/360；在实物中对比无 VDD/VDD；保持视角相关遮挡/图层可见性 | 24×15° 独立采样图、每部件对应日志、无眼睛双影、衣服错位、侧脸穿帮；缺关键视角先增补角度/局部修形，ARAP 只在真正有收益时追加 |
| M1-08 | **正式 360° 1080p 视频**：192 帧、24 fps、8s，另外独立求值 360°；输出正常视频、alpha/debug layer 视频和完整元数据，使用 FFprobe 校验编码帧数 | 3 类视频/对照组，非空帧、无画面裁切、接缝状态与像素差异、运行时日志；Release/非公开资产存储位置可访问 |
| M1-09 | **独立画质与效率验收**：对关键角度、最差中间角度、连续帧、所有层级和纹理人工抽检，统计额外视角和局部补画工时 | 质量 PASS/FAIL/NO-GO，附缺陷复现、修正成本；不得因 CI=green 直接认定画质 PASS |

**每完成一任务必须提交可恢复的 git commit、状态和日志；较大视频/图像严禁进 Git。只完成 M1-01 不能声明 360° 已可行。**

## 4. 全部新增维护代码统一为 TS

```text
experiments/mvp001/
  src/main.ts                  # M0 migrated; preserve smoke behavior
  scripts/smoke.ts             # M0 migrated; preserve reference outputs
  scripts/asset-inventory.ts   # inventory with commit hash, paths, SHA, feature flags
  scripts/spine-reference.ts   # 4.2 source runtime reference (adapter)
  scripts/cubism-reference.ts  # official SDK reference where license/core allows
  scripts/asset-import.ts      # source -> canonical schema
  scripts/render-m1.ts         # Playwright/Chromium deterministic frames/FFmpeg
  src/m1/
    types.ts
    spine-adapter.ts
    cubism-adapter.ts
    view-space.ts
    correspondence.ts
    part-mesh.ts
    vdd.ts
    visibility.ts
    turntable.ts
  schemas/character-multiview.schema.json
  tests/m1/*.test.ts
  tsconfig.json
  package.json
.github/workflows/mvp001-m1-turntable.yml
docs/experiments/MVP-001-M1-status.md
```

Runtime: Node.js + TypeScript + `tsx` + `tsc --noEmit` (strict), Three.js, Vite, Playwright, FFmpeg. Binary loader libraries may be native upstream tools when licensed, but **our own application and test code must be TypeScript**. The old Rive+Python scripts remain historical only; *not* hidden M1 dependencies. Blender/Godot not required.

For Spine, choose [official spine-ts 4.2](https://github.com/EsotericSoftware/spine-runtimes/tree/4.2/spine-ts) to match the actual 4.2.36 source. The 4.3 release should not silently be used to read 4.2 .skel. Keep its license/module isolated. Cubism Web TS code requires proper Cubism Core; `.moc3` is not an editable `.cmo3`.

## 5. Stop/no-go criteria

- Data/source: if selected character's source Spine/Cubism cannot be verifiably rendered, **stop and fix the reference renderer before claiming asset extraction works**.
- Asset geometry: if no trustworthy true side/back keyviews exist, list missing assets explicitly and generate/repaint **only those** while using existing character as a locked reference. This is not an automatic one-image-to-360 guarantee.
- Visual continuity: no whole-body card flip or total-body crossfade. Fix matching/wrapping/depth first, before adding effects.
- Evaluation: sample every 15°, independently inspect worst transitions, verify asymmetric details and front/back joint locations, check mesh foldovers and no doubled eyes; deterministic random frame seek.
- Economic: report amount of manually redrawn new angles + corrected parts; if essentially every intermediate frame must be repainted, report technical possibility but **economic NO-GO**.
- Rights: public text-only repository, protected storage for third-party binary art; only privately inspect derivative video.
- If any gate fails: commit failure evidence, mark blocked, do not quietly switch to a different source or success metric.

## 6. Next action (no need to generate unrelated original art)

**First implement M1-00 and M1-01**: migrate the M0 JS files and scripts to TS, run parity tests; then write TS inventory and download only one or two specific character bundles; audit original source rig/mesh/views and select source candidate. Do **not** start automatic generating four different views until existing source assets have been rendered and compared.

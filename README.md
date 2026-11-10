# 2.75D Anime Studio · Koma Motion Lab

面向高质量二次元动画的 **Cubism 原生立绘 + 多视角分层原画 + 3D Anchor + ArtMesh/VDD + Three.js** 实验与验收仓库。

## GIF 多视角一致性与关键部位资产验证

- [MVP 制作与验收计划](docs/plans/2026-11-05-gif-multiview-keyparts-mvp.md)
- [T00–T05 任务状态与资产合同](experiments/gif-multiview-keyparts-mvp/tasks.json)
- [P14 五视角原画及 ArtMesh 审查计划](docs/plans/2026-11-09-p14-painted-view-review.md)
- [P14 实际源文件、37 帧与 Chromium 验收证据](experiments/gif-multiview-keyparts-mvp/evidence/p14-painted-view-qa.json)
- [P15 语义笔触对应与视角遮挡研究](docs/plans/2026-11-09-p15-stroke-occlusion.md)
- [P15 四角度、多方法、原画笔触诊断 QA](experiments/gif-multiview-keyparts-mvp/evidence/p15-view-transition-qa.json)
- [P15-04 五官笔触与物理锚点 HTML 审查](experiments/gif-multiview-keyparts-mvp/review/p15-facial-strokes.html)
- [P15-04 来源、Chromium 与验收证据](experiments/gif-multiview-keyparts-mvp/evidence/p15-04-acceptance.json)
- [P15-05 头发部件、笔触与遮挡研究](docs/plans/2026-11-09-p15-hair-occlusion.md)
- [P15-05 头发独立原画 HTML 审查](experiments/gif-multiview-keyparts-mvp/review/p15-hair-strands.html)
- [P15-05 原画来源与深度遮挡验收](experiments/gif-multiview-keyparts-mvp/evidence/p15-05-acceptance.json)

本实验固定使用此前批准的 P0 原创角色 `p0_character_001`（批准身份参考板与 `hero/hero_master.png`），直接生成八方向整头 GIF 以及按角度和语义分组的透明部件 GIF；每帧严格对应一个关键部位，逐帧校验后进入 RGBA ArtMesh 和 HTML VDD。

## 当前验证主线 · R1999 Cubism VDD HTML

使用 [Reverse-1999-CN-Asset](https://github.com/myssal/Reverse-1999-CN-Asset) 中十四行诗（`302301_shisihangshi`）的实际 Cubism 模型，首先还原原生立绘、表情和动作，再构建动态 ArtMesh 适配、独立视角原画、VDD 和视角依赖遮挡，最终在 HTML 浏览器中对比原生画面、2.75D 扩展、独立参考和逐像素诊断。

- [完整技术架构、资产标准、HTML 验收设计](docs/R1999-cubism-vdd-html-plan.md)
- [C00–C10 可追踪任务与验收门禁](docs/R1999-cubism-vdd-html-tasks.json)
- [真实资源 SHA-256 清单](experiments/r1999-cubism-vdd/evidence/source-manifest.json)
- [桌面 Chromium HTML 控件及画面测试](experiments/r1999-cubism-vdd/evidence/native-browser-qa.json)
- [移动端浏览器测试](experiments/r1999-cubism-vdd/evidence/native-mobile-qa.json)
- [ArtMesh/Mask/动态顶点结构化验收](experiments/r1999-cubism-vdd/evidence/drawable-qa.json)
- [私有截图哈希与官方 SDK 指纹](experiments/r1999-cubism-vdd/evidence/native-screenshot-hashes.json)
- [Cubism 原生到 Three.js 的 Drawable 渲染适配器](experiments/r1999-cubism-vdd/src/cubism-three-adapter.ts)
- [C03 五种动态状态逐像素验收与故障注入报告](experiments/r1999-cubism-vdd/evidence/c03-threejs-parity-qa.json)
- [C03 官方 Sample 适配构建脚本](experiments/r1999-cubism-vdd/scripts/prepare-c03.py)
- [C03 Chromium 自动验收脚本](experiments/r1999-cubism-vdd/scripts/qa-c03.cjs)
- [C04 Cubism 原生参数与独立视角资产覆盖审计](experiments/r1999-cubism-vdd/evidence/c04-view-source-audit.json)
- [C04 原生 Part 身份与 Anchor 位置](experiments/r1999-cubism-vdd/evidence/c04-semantic-anchors.json)
- [C04 独立视角资产登记与来源规则](experiments/r1999-cubism-vdd/evidence/c04-view-source-registry.json)
- [C04 原生正面透明 PNG 分层清单（40 张）](experiments/r1999-cubism-vdd/evidence/c04-front-layer-manifest.json)
- [C04 私有正面分层资源包校验](experiments/r1999-cubism-vdd/evidence/c04-front-layer-bundle.json)
- [C05 Cubism Anchor / View Proxy HTML 代码](experiments/r1999-cubism-vdd/src/cubism-anchor-view.ts)
- [C05 VDD 关键视角插值实现](experiments/r1999-cubism-vdd/src/vdd-keyframes.ts)
- [C05 HTML 浏览器验收结果](experiments/r1999-cubism-vdd/evidence/c05-html-package-qa.json)
- [C05 侧向视角可见面积检查](experiments/r1999-cubism-vdd/evidence/c05-visual-readiness.json)
- [C05 私有 HTML 资源包校验](experiments/r1999-cubism-vdd/evidence/c05-html-bundle-manifest.json)
- [独立 45° / 90° 分层原画规范](experiments/r1999-cubism-vdd/docs/view-artwork-authoring.md)
- [原画来源与语义部件输入合同](experiments/r1999-cubism-vdd/assets/view-key-contract.json)
- [透明 PNG、来源哈希与定位点校验器](experiments/r1999-cubism-vdd/scripts/validate-view-layers.py)
- [多视角语义部件 HTML 工作台](experiments/r1999-cubism-vdd/web/view-layer-lab.html)
- [HTML 分部件插值及原生 Part 对照](experiments/r1999-cubism-vdd/web/view-layer-lab.js)
- [HTML 实机 Chromium 测试证据](experiments/r1999-cubism-vdd/evidence/c06-view-layer-browser-qa.json)
- [Cubism 原生渲染回归验证](experiments/r1999-cubism-vdd/evidence/c06-cubism-regression-qa.json)
- [45° / 90° 原画合同实测状态](experiments/r1999-cubism-vdd/evidence/c06-art-source-contract-qa.json)
- [私有 HTML 工作台资源包及哈希](experiments/r1999-cubism-vdd/evidence/c06-workspace-package.json)
- [R1999 视角素材及 VDD 单元测试 CI](.github/workflows/r1999-view-layer-qa.yml)
- [WTHN_Ross Sonetto PMX 模型源与许可审计](experiments/r1999-cubism-vdd/evidence/c06-pmx-source-audit.json)
- [Blender 8 视角离线结构渲染器](experiments/r1999-cubism-vdd/scripts/render-sonetto-structural-views.py)
- [8 视角 PNG、透明度与来源 QA](experiments/r1999-cubism-vdd/evidence/c06-structural-view-qa.json)
- [独立 HTML 结构参考浏览器生成器](experiments/r1999-cubism-vdd/scripts/build-structural-viewer.py)
- [离线 HTML Chromium 验收 15 项](experiments/r1999-cubism-vdd/evidence/c06-offline-structural-viewer-qa.json)
- [可重复生成单文件离线 HTML 的脚本](experiments/r1999-cubism-vdd/scripts/build-structural-viewer.py)
- [GitHub Actions 一键获取八视角 PNG 与独立 HTML](.github/workflows/r1999-structural-reference.yml)
- [带原生 Cubism 部件及 3D 侧脸参考的 HTML 验收 18 项](experiments/r1999-cubism-vdd/evidence/c06-structural-html-qa.json)
- [本轮私有资源包与技术验收清单](experiments/r1999-cubism-vdd/evidence/c06-structural-reference-delivery.json)
- [独立 GitHub Actions 三维参考渲染及产物](https://github.com/tims-SP/koma-motion-lab/actions/runs/41685596255)
- [R1999 原生资产技术路线与候选研究](docs/R1999-native-asset-validation-plan.md)

**当前状态：** C00–C03 已通过真实工程验收。固定资产源 33 个文件；官方 Cubism 5-r.4 成功加载 263 Drawable、180 参数、7,826 顶点和 21 个带蒙版的 Drawable。C03 使用 Three.js 0.181.0 同帧重放原生网格、贴图、蒙版与动态绘制顺序，5 组真实 Chromium WebGL 状态的前景轮廓 IoU 均超过 0.99975，RGB MAE 均低于 0.055/255；蒙版、UV、绘制顺序故障注入检查通过。从官方干净 5-r.4 仓库按本仓库脚本重新构建后，重复验收通过。模型画面人工复核已完成；用户视觉签收待执行。

**C04 当前进度：** 263/263 Cubism Drawable 来源追踪、40 张原生正面 Part RGBA PNG 已完成。取得 WTHN_Ross 在 BowlRoll 公开的十四行诗 PMX 参考模型，审阅英文/日文 ReadMe：允许个人非商业编辑和制作图片视频，要求注明 BLUEPOCH / Reverse: 1999 与 WTHN_Ross，限制模型及零件数据再分发。以 Blender 4.0.2 + MMD Tools v4.0.0 渲染 0°、45°、90°、135°、180°、225°、270°、315° 共 8 张 768×768 RGBA 正交截图，透明像素和轮廓检查通过；独立 GitHub Actions 已成功复现并提供预览 Artifact。八视角图像属于第三方 3D 结构参考，不作为独立二维原画或 2.75D 镜头完成证据。45° 与 90° 语义原画输入合同仍需 16 张独立透明 PNG 及留出角画作。

**C05 当前进度：** Cubism → Three.js 的动态 ArtMesh 与原画保真基础继续可用；多视角 HTML 工作台现可并排查看 40 张原生 Cubism Part 与 45°/90° 真实三维结构参考，逐部件登记独立原画及计算 SHA-256。HTML 打包后 18 项实际 Chromium 测试、12 项原生 Cubism 回归通过。另有 8 方向单 HTML 离线结构预览器，提供角度滑杆、动画播放、PNG 导出与视角检查，15 项浏览器检查通过。正式 VDD 视觉验收依赖新绘制的 45°、90° 关键原画及 20°/55°/82° 独立留出参考。

预计新实验源码位置：`experiments/r1999-cubism-vdd/`。HTML 先采用本地静态服务的资源包（HTML/JS/CSS/已授权的本地依赖），离线运行；个人游戏原画及包含这些原画的截图、视频和 HTML 包保存在私有实验路径，Git 保存通用程序与文本证据。

## 已建立的 Three.js 几何/诊断参考 · HEAD009

`experiments/head009/` 包括 Three.js/WebGL 渲染、0–90° 头部 ArtMesh/VDD、Beauty/Part-ID/Depth/Alpha 四通道、故障注入、可交互单 HTML 与 Playwright/Chromium QA。新 Cubism 实验可以复用其渲染诊断方法和验收程序。

- [HEAD009 几何与视觉验收方案](docs/MVP-009-plan.md)
- [HEAD009 任务及证据](docs/MVP-009-tasks.json)
- [Cubism / Agent 面部语义和层级契约](docs/MVP-009-face-authoring-contract.md)
- [HTML 隔离环境打包](.github/workflows/mvp009-container-bootstrap.yml)
- [Chromium 工具链打包](.github/workflows/mvp009-browser-bootstrap.yml)

复现现有 HEAD009 浏览器验收：

```bash
cd experiments/head009
HEAD009_BROWSER_EXECUTABLE=/path/to/chrome-headless-shell ./scripts/run-isolated-review.sh
```

生成 `out/head009/head009-review.html`、`out/head009/html-review-qa.json` 和截图。该 SVG 几何示例的 WebGL/交互验收结果见 [GitHub 同源构建校验](https://github.com/tims-SP/koma-motion-lab/actions/runs/41253856374)；R1999 的真实 Cubism 模型各项质量指标按新任务独立验收。

## 仓库职责

- `tims-SP/koma-motion-lab`：单角色验证、对照实验、原画来源登记、结构化 QA、浏览器与视频证据。
- `tims-SP/koma-motion`：接收经过正式技术与视觉验收的可复用渲染器、VDD 数据模型和测试工具。

- [P15-06 独立中间角原画与验证合同](docs/plans/2026-11-09-p15-06-independent-holdout-artwork.md)
- [P15-06 角色来源与 ArtMesh 导入 QA](experiments/gif-multiview-keyparts-mvp/evidence/p15-06-stage-qa.json)
- [P15-06 独立多视角原画与部件 HTML 审查](experiments/gif-multiview-keyparts-mvp/review/p15-06-keyview-art.html)
- [P15-06 新原画、26 张 RGBA 与隐藏补绘 QA](experiments/gif-multiview-keyparts-mvp/evidence/p15-06-generated-keyviews-qa.json)
- [P15-07 多视角原画与 ArtMesh 对应验收方案](docs/plans/2026-11-10-p15-07-view-correspondence.md)
- [P15-07 37 帧多视角交互 HTML](experiments/gif-multiview-keyparts-mvp/review/p15-07-view.html)
- [P15-07 来源保真、Chromium 与艺术审核](experiments/gif-multiview-keyparts-mvp/evidence/p15-07-renderer-qa.json)
- [P15-07 私有审查包 SHA 与内容校验](experiments/gif-multiview-keyparts-mvp/evidence/p15-07-delivery.json)
- [P15-08 55° 独立原画与 13 部件生成合同](experiments/gif-multiview-keyparts-mvp/metadata/p15-08-yaw055-generation-contract.json)
- [P15-08 原画姿态与身份侧别校准记录](docs/plans/2026-11-10-p15-08-pose-calibration.md)
- [P15-08 55° 原画五图并排 HTML 审查](experiments/gif-multiview-keyparts-mvp/review/p15-08-mid-angle.html)
- [P15-08 两组生成候选、Alpha、发夹侧别 QA](experiments/gif-multiview-keyparts-mvp/evidence/p15-08-source-candidate-qa.json)
- [P15-08 私有审查包校验](experiments/gif-multiview-keyparts-mvp/evidence/p15-08-delivery.json)
- [P15-06 中间视角轮廓、画布对齐与 P8 对照](experiments/gif-multiview-keyparts-mvp/evidence/p15-06-view-geometry-qa.json)

- [P15-09 P5 解剖锚点与视角形变方案](docs/plans/2026-11-10-p15-09-anchor-correspondence.md)
- [P15-09 45°–65° 交互 HTML 画面对照](experiments/gif-multiview-keyparts-mvp/review/p15-09-midarc.html)
- [P15-09 P5 20 锚点原画几何 QA](experiments/gif-multiview-keyparts-mvp/evidence/p15-09-anchor-pose-qa.json)
- [P15-09 连续转头和画面连续性 QA](experiments/gif-multiview-keyparts-mvp/evidence/p15-09-midarc-qa.json)
- [P15-09 离线 HTML 审查资源验收](experiments/gif-multiview-keyparts-mvp/evidence/p15-09-delivery.json)

- [P15-10 ArtMesh 语义分层与遮挡验收](docs/plans/2026-11-10-p15-10-semantic-view-transition.md)
- [P15-10 55°–65° 部件交互 HTML](experiments/gif-multiview-keyparts-mvp/review/p15-10-semantic.html)
- [P15-10 13 部件 RGBA 来源校验](experiments/gif-multiview-keyparts-mvp/evidence/p15-10-semantic-source-qa.json)
- [P15-10 语义转头连续性 QA](experiments/gif-multiview-keyparts-mvp/evidence/p15-10-semantic-arc-qa.json)
- [P15-10 离线审查资源校验](experiments/gif-multiview-keyparts-mvp/evidence/p15-10-delivery.json)

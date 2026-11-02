# 2.75D Anime Studio · Koma Motion Lab

面向高质量二次元动画的 **Cubism 原生立绘 + 多视角分层原画 + 3D Anchor + ArtMesh/VDD + Three.js** 实验与验收仓库。

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
- [R1999 原生资产技术路线与候选研究](docs/R1999-native-asset-validation-plan.md)

**当前状态：** C00–C03 已通过真实工程验收。固定资产源 33 个文件；官方 Cubism 5-r.4 成功加载 263 Drawable、180 参数、7,826 顶点和 21 个带蒙版的 Drawable。C03 使用 Three.js 0.181.0 同帧重放原生网格、贴图、蒙版与动态绘制顺序，5 组真实 Chromium WebGL 状态的前景轮廓 IoU 均超过 0.99975，RGB MAE 均低于 0.055/255；蒙版、UV、绘制顺序故障注入检查通过。从官方干净 5-r.4 仓库按本仓库脚本重新构建后，重复验收通过。模型画面人工复核已完成；用户视觉签收待执行。

**C04 当前进度：** 从真实 Cubism Core 恢复了 46 个 Part 与 11 个根层面部 Drawable 的来源关联，263/263 Drawable 可追踪。实际导出 40 张每 Part 独立透明 PNG（其中 34 张在当前姿态可见），通过 alpha、身份、源 SHA 与浏览器错误检查，保留私有档案。`PARAM_ANGLE_X/Y/Z` 均为 -30～+30 的二维模型参数，不作为三维相机角度。45°、90° 和独立留出角原画登记门禁等待可信来源和语义透明图层。

**C05 当前进度：** 3D Anchor 估算深度和 HTML 角度滑杆代理已在实际 Three.js WebGL 中运行；纯 VDD 视角键插值算法 5/5 单元测试通过，HTML 包装后 12/12 浏览器检查通过。0° 下保持与 Cubism 原生画面接近的逐帧保真；45°、90° 仍为几何重投影代理，90° 头部视觉验收待独立侧面原画。源码、QA 与私有 HTML 包哈希已登记。

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

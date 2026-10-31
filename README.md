# 2.75D Anime Studio · Koma Motion Lab

**技术路线：** Euclid 式多视角原画、3D Anchor、ArtMesh/VDD 与相机空间遮挡。现阶段以头部 0°–90° 为首轮视觉验收目标。

- [MVP-009 技术方案与验收标准](docs/MVP-009-plan.md)
- [MVP-009 任务与状态](docs/MVP-009-tasks.json)
- [Live2D 制作与 Agent 器官数据契约](docs/MVP-009-face-authoring-contract.md)

## 交互 HTML 验收

本体项目使用 `experiments/head009/` 中的 Three.js 模型源码。验收产物为单文件 `head009-review.html`，包括真实 WebGL、连续 0°–90° 偏航、参考原画、四通道调试、器官语义标记、人工器官结论和 JSON/PNG 导出。

开发与真实验收在隔离容器中进行。GitHub 的 [源码与依赖打包工作流](.github/workflows/mvp009-container-bootstrap.yml) 和 [Chromium 工具链打包工作流](.github/workflows/mvp009-browser-bootstrap.yml) 为隔离容器提供可校验的依赖包。源码、依赖及浏览器完成解包后，在 `experiments/head009` 内执行：

```bash
HEAD009_BROWSER_EXECUTABLE=/path/to/chrome-headless-shell ./scripts/run-isolated-review.sh
```

输出：`out/head009/head009-review.html`，以及 `out/head009/html-review-qa.json`、`out/head009/review-html-*.png`。可直接用浏览器打开 HTML，无需开发服务。

本轮 HTML 的 SHA-256：`c483291902d5d7d93639540acce478b2f478d67e2793015d92274eabba1af249`，本地隔离容器 WebGL 测试通过，外部请求 0 次。与 [GitHub 同源构建校验](https://github.com/tims-SP/koma-motion-lab/actions/runs/41253856374) 一致。

**当前状态：** HTML 交互验收工程完成，T03B 的艺术视觉复核继续进行。重点为 80°–90° 耳部显露与 20°/55°/82° 新独立参考。T04 方案决策和头部 360° 尚未进入。

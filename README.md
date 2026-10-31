# 2.75D Anime Studio · Koma Motion Lab

**当前目标：** 基于独立多视角原画、3D Anchor、局部 ArtMesh 和深度关系，实现头部 0°–90° 的真实侧脸与连续遮挡，通过后扩展到头部 360° 和全身动作。

- [MVP-009 技术方案与验收标准](docs/MVP-009-plan.md)
- [MVP-009 任务与状态](docs/MVP-009-tasks.json)

当前阶段：`HEAD90_IMPLEMENTATION_IN_PROGRESS`。已实现独立头部 Three.js/TS 原型、六幅原始矢量参考图、7 角度真实 WebGL 四通道覆盖与故障注入验收。

[本轮 GitHub Actions 实机运行](https://github.com/tims-SP/koma-motion-lab/actions/runs/41230438902) · [头部角度截图、独立参考和 QA 证据](https://github.com/tims-SP/koma-motion-lab/actions/runs/41230438902/artifacts/13052664086)

状态：`PASS_ENGINEERING_OPAQUE_ONLY`；原画对位与侧脸视觉验收 `FAIL_VISUAL`。下一关：把已有 SVG 分层原画与头部 ArtMesh 的语义点、几何、RGBA 覆盖对齐，再审查 30°、60°、75° 留出视角。正式仓库保持独立。

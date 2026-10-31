# 2.75D Anime Studio · Koma Motion Lab

**当前目标：** 基于独立多视角原画、3D Anchor、局部 ArtMesh 与相机空间深度，实现可连续转向的动漫角色。先验收头部 0°–90°，再扩展左右侧、背面与全身动作。

- [MVP-009 技术方案与验收标准](docs/MVP-009-plan.md)
- [MVP-009 任务与状态](docs/MVP-009-tasks.json)

阶段：`HEAD90_SOURCE_REGISTERED_PENDING_HELDOUT_REVIEW`。

TypeScript + Three.js 已将 0°、45°、90° 独立绘制 SVG 的部件轮廓与描边接入头部空间渲染；三关键角度与原画的轮廓 IoU 分别为 **0.9954 / 0.9958 / 0.9940**。30°、60°、75° 留出视角 IoU 为 **0.9279 / 0.9211 / 0.9069**。七角度 Beauty/ID/Depth/Alpha 可见像素覆盖一致，故障注入被检测到。

[真实 GitHub Actions 渲染与验收](https://github.com/tims-SP/koma-motion-lab/actions/runs/41230925330) · [角度截图、源参考、四通道数据及 IoU 报告](https://github.com/tims-SP/koma-motion-lab/actions/runs/41230925330/artifacts/13052724463)

工程状态：`PASS_ENGINEERING_KEY_RECONSTRUCTION`；视觉状态：`PENDING_HELDOUT_VISUAL_REVIEW`。下一阶段只针对 30°、60°、75° 的真实中间视角与部件遮挡完成视觉验收和形变校准。

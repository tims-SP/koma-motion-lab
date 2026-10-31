# 2.75D Anime Studio · Koma Motion Lab

**目标：** 独立多视角原画 + 3D Anchor + ArtMesh/VDD + 相机空间遮挡，实现可信动漫人物水平 360° 旋转。先验证头部 0°–90°。

- [MVP-009 技术方案与验收标准](docs/MVP-009-plan.md)
- [MVP-009 任务与状态](docs/MVP-009-tasks.json)
- [Live2D 官方规范与 Agent 面部器官制作契约](docs/MVP-009-face-authoring-contract.md)

阶段：`HEAD90_INTERMEDIATE_CORRESPONDENCE_IN_PROGRESS`。

0°、45°、90° 独立 SVG 分层原画已经接入 Three.js 头部，三关键视角源图轮廓 IoU 分别为 **0.9954 / 0.9958 / 0.9940**。30°、60°、75° 独立留出视角轮廓 IoU 为 **0.9279 / 0.9211 / 0.9069**。7 个角度四通道覆盖一致，故意注入的遮挡故障能够检出。60°、75° 的耳部深度修形已用实际 Part-ID 像素量验证。

[最新渲染、独立参考图和 QA 结果](https://github.com/tims-SP/koma-motion-lab/actions/runs/41231186707/artifacts/13053493315) · [Actions 工作流](https://github.com/tims-SP/koma-motion-lab/actions/runs/41231186707)

当前验收：`PASS_ENGINEERING_KEY_RECONSTRUCTION`，中间视角独立视觉审查 `FAIL_HELDOUT_VIEW_CORRESPONDENCE`。下一阶段仅校准 30°、60°、75° 的语义位置与局部图层遮挡，完成头部 0°–90° 验收后再扩展 360°。

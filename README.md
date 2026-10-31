# 2.75D Anime Studio · Koma Motion Lab

**技术路线：** Euclid 式多视角独立原画 + 3D Anchor + ArtMesh/VDD + 相机空间遮挡。当前只验收单个头部 0°–90°。

- [MVP-009 技术方案与验收标准](docs/MVP-009-plan.md)
- [MVP-009 任务与状态](docs/MVP-009-tasks.json)
- [Live2D 官方规范与 Agent 面部器官制作契约](docs/MVP-009-face-authoring-contract.md)

当前阶段：`HEAD90_ORGAN_VDD_ENGINEERING_SWEEP_PASS_VISUAL_REVIEW`。

**T03B-3** 已完成四组局部 VDD 形变（下巴、鼻尖轮廓、鼻部线条与嘴部），校正侧脸眼部身份及逐渐遮挡，并使 60° 侧发描线与皮肤深度一致。0°/45°/90° 独立 SVG 原画的轮廓 IoU = **0.9954 / 0.9958 / 0.9940**；30°/60°/75° 开发参考对照 = **0.9314 / 0.9211 / 0.9069**。

[本轮成功 CI](https://github.com/tims-SP/koma-motion-lab/actions/runs/41251837430) · [91 帧 MP4、逐帧截图、角度图板及全部机器验收](https://github.com/tims-SP/koma-motion-lab/actions/runs/41251837430/artifacts/13060994438)（3.03 秒，H.264）

静态器官点位和连续旋转的工程验收通过。视觉抽检仍需修正 80°–90° 耳部形变，并采用新独立制作的 20°/55°/82° 参考确认模型泛化。**T04 / 360° / 全身动作尚未进入。**

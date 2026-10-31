# 2.75D Anime Studio · Koma Motion Lab

**目标：** 以多视角分层原画、3D Anchor、ArtMesh/VDD 和相机空间遮挡实现可信的水平 360° 动漫人物旋转。当前优先完成头部 0°–90°。

- [MVP-009 技术方案与验收标准](docs/MVP-009-plan.md)
- [MVP-009 任务与状态](docs/MVP-009-tasks.json)
- [Live2D 官方规范与 Agent 面部器官制作契约](docs/MVP-009-face-authoring-contract.md)

当前阶段：`HEAD90_ORGAN_REFERENCE_PASS_HELDOUT_ALIGNMENT_IN_PROGRESS`。

**T03B-2 器官语义注册与 QA 工程通过：** 已把眼、鼻梁、鼻尖、鼻部描线、嘴、下巴、左右耳及发际线纳入六个视角的独立源图标注，检测实际 WebGL ID 像素和故障注入。0°、45°、90° 的源图器官对位门禁通过。30° / 60° / 75° 留出角度仍存在突出形变误差（30° 下巴 39.8px、鼻尖 32.4px；60° 眼睛 51.1px；75° 眼睛 30.2px），因此 **T03B-3 的视觉修形尚未通过**。

[实际 GitHub Actions QA](https://github.com/tims-SP/koma-motion-lab/actions/runs/41250758705) · [器官对照图片、源图校验、QA JSON](https://github.com/tims-SP/koma-motion-lab/actions/runs/41250758705/artifacts/13060844731)

下一步只针对面部五官与脸部的真实多视角对应，准备修正关键视角与新留出参考并完成视觉门禁。头部 360° 和全身动作按现有顺序继续依赖头部 0°–90° 正式视觉验收。

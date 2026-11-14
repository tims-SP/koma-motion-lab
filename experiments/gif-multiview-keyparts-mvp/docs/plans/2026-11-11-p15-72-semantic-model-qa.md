# P15-72 · CPU GroundingDINO/SAM 前发语义分割实测

## 目标与基线
- Git 2ee9c33；目标为 P15-56 同视角、同角色的真实 front-hair 透明 RGBA。保留 P15-69 发夹和 P15-70 底图。
- 不接受从整图按颜色分类的蒙版、不接受其他视角独立前发作为正式 ArtMesh。

## 模型发现与实际调用
- 先检查 Hugging Face 上当前运行的分割模型。SAM2 共享 ZeroGPU 先前配额耗尽，当前 VPS 没有已安装本地 SAM 模型，内存不足以轻易部署大型模型。
- 找到 CPU-basic RUNNING 的 Volkopat/SegmentAnythingxGroundingDINO，并用 Gradio 实际上传 512px P15-56 参考图。
- 第一次调用 detect_objects，提示词 pink anime bangs hair，模型报告识别 1 个对象、置信度 59%，保存真实输出 grounded-sam-output.png。
- 第二次提示词 front hair fringe bangs，识别 1 个对象、置信度 57%，保存真实输出 grounded-sam-fringe.png。

## 视觉判断
- 两张模型图都把大块脸颊、近眼与其他面部像素包含在结果中，并不是真正独立的前发语义遮罩。
- 逐像素样本核对结果：原图裁切坐标中 near_eye 与 cheek_skin 在两张输出中均非背景，而非仅仅刘海被保留。
- 模型返回不等于资产可用。没有根据这两份不合格结果伪造正式 RGBA 前发层，没有将其纳入正式 ArtMesh、VDD Keyframe。
- 审查 HTML 中 0/9/18px 图直接复用 P15-70 基线，未声明新的动态图层验收通过。

## 工程验收
- 新增 11 项单测验证原始来源哈希、两张模型真实结果 SHA、面部/眼部污染、正式禁入以及对照帧来源。
- Chromium 桌面/移动验证图片加载和 0/9/18px 滑杆。
- 视觉门禁：FAIL_MODEL_SEGMENTATION_INCLUDES_EYES_AND_CHEEK。

## P15-73 最小下一步
需要真正支持动漫人物头发部件、交互正负点或局部图层编辑的模型，或者同一视角独立绘制的前发原画。先在 0px 验收视觉重组身份与轮廓一致，再在 9/18px 验收前发遮挡；不要重做已经通过的近眼底图及发夹。

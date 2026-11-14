# P15-51 · Qwen Camera-Angle LoRA 候选

## 目的
在 P15-50 认证 ZeroGPU 仍缺少 VPS HF_TOKEN 的情况下，验证 Hugging Face MCP 账户可调用的明确相机角度控制模型。

## 输入与实际调用
- 输入：此前批准的 P0 45° 原画 p0-yaw45-original.png，SHA256 78a08d5f010a8f449efda915a710a2de8958c3b1a32375df491d806fca251e40。
- 模型：mcp-tools/Qwen-Image-Edit-Angles（Qwen Image Edit 2509 + Qwen-Edit-2509-Multiple-angles LoRA）。
- 参数：1024×1024、4 steps、guidance 1、seed 固定、randomize_seed=false。
- 负向对照：rotate_deg=-20，seed 65450。输出更接近正面，拒绝。
- 正向候选：rotate_deg=+20，seed 65451。模型返回文本确认“将镜头向左旋转20度 / Rotate the camera 20 degrees to the left”。
- 新输出：private-assets/exports/p15-51-qwen-angle-plus20deg.webp，SHA256 c3151c9a2defd7fa61bd71fa80107b1c6dd2948174ef66e5d8e14464ed917127。
- 同一调用在两个已连接的免费 HF 账户均返回图像；没有创建付费 GPU 作业。

## 视觉检查
正向 20° 候选比源 45° 明显更侧：近眼占主导，远眼窄且部分遮挡，鼻梁向侧面偏移，金色交叉发夹仍在画面右侧，粉紫短发、呆毛、深蓝制服及红色蝴蝶结保留。负向 20° 结果趋近正面，不符合目标。

## 限制
输出为 1024×1024 RGB WebP，无 Alpha 通道，背景为黑色。角度控制是相对旋转，模型没有返回经外部相机标定的绝对 yaw；不能据参数简单宣称已经精确等于 65°。因此它是有价值的 65° 候选原画，不是正式 VDD 关键帧或 ArtMesh 部件。不得覆盖已批准 P0 原画。

## 验收
- 6 项 P15-51 单测通过。
- Chromium 桌面/移动 2/2，6 张图片加载，0 页面错误。
- 本轮只登记候选，不修改 ArtMesh。
- 审查包：private-assets/exports/p15-51-camera-angle-review.zip。

## 下一阶段
从正向 20° 候选提取透明背景并检查边缘/发丝；使用 65° 现有锚点校准绝对朝向与双眼/鼻/嘴遮挡。通过视觉门禁后再拆分眼、鼻、口、头发和发夹层，正式进入 ArtMesh。

# P15-45 · Qwen-Image-2.1 Lineart + Inpainting 实际推理

## 已完成

- 确认 Space hugging-apps/qwen-image-2-1-controlnet-union-demo 在线，实际检查 /gradio_api/info 与 /config。
- 绕过 MCP 动态 schema 的复杂参数限制，使用 Space 原生 Gradio API；Space 使用 ZeroGPU A10G。
- 实际向模型传入 P15-44 Lineart 控制图、65° 注册图作为 inpaint source、局部面部 mask；control_context_scale=1.0、1024、24 steps、seed 65445。
- 推理成功返回 RGBA 1024² 图像；输出 SHA256 记录在 QA JSON。
- 独立视觉观察：右朝向未镜像、双眼均出现、金色交叉发夹仍在画面右侧、粉紫短发与呆毛保留。脸部较源图清晰。
- 锚点叠加发现远眼、鼻、嘴相对既有 65° 几何锚点存在偏移；精确 yaw 和身份一致性没有足够证据。因此不准入正式关键帧。
- 第二个 seed 65446 请求因 ZeroGPU quota exceeded 被拒绝；这不是模型失败或生成质量结论。
- 未更改原始 P0 RGBA ArtMesh 或 VDD 数据。

## P15-46 下一项

改进控制图，不再简单把注册合成图的边缘检测结果当作充分条件。基于已登记锚点绘制高对比眼形、鼻梁、鼻尖、嘴线、下颌线和发夹边缘 guide；局部 inpaint mask 缩小到面部器官和轮廓。等待 ZeroGPU 配额恢复或通过 Hugging Face MCP 将该 Space 添加到可调用工具后，使用相同模型做固定种子 A/B 对照。对照远眼中心、鼻尖、嘴中心相对锚点偏移，并检查两眼、方向和发夹；不满足准入条件不得替换正式关键帧。

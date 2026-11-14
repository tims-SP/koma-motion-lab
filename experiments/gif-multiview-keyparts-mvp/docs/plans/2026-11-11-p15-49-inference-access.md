# P15-49 · 可用的真实 ControlNet 推理入口审计

目标：直接生成同一角色、右朝向 65° 的新原画；保留 P0 身份、远眼透视、金色发夹和透明通道。

## 核实结果
- 读取 Git 基线 0aab263；P15-44 至 P15-47 已有结构输入和测试仍在。
- Hugging Face Spaces API 搜索 qwen-image-controlnet、lineart-controlnet、controlnet-inpaint、controlnet-union，共 135 个去重候选，其中 8 个运行中；不能仅据名称推断能接受实际条件输入。
- 运行中的 Qwen-Image-2.1-Fun-Controlnet-Union 依然使用 ZeroGPU，P15-48 的真实 SSE 返回 ZeroGPU quota exceeded。不再重复匿名推理。
- FLUX 类 Space 检查：multimodalart FLUX Union 的 /gradio_api/info 无 named endpoints；jiuface FLUX ControlNet Inpainting 的 /gradio_api/info 为 HTTP 404；Catherine57533 演示仅公开登录检查。
- 已连接 Hugging Face MCP 的 Spaces discover 未提供上述 Qwen ControlNet 的专用入口。之前动态调用时因为 inpaint_image 复杂参数 schema 被拒绝，本地匿名 Gradio 请求能提交但无推理额度。
- 已连接 Hugging Face Jobs 在 P15-48 返回 HTTP 402 Payment Required，不能作为无需授权的 GPU 方案。

## 技术结论
本轮没有新的 65° 输出，不修改正式关键帧。当前可重现的直接阻塞是受认证和额度约束的真实 GPU 生成服务，并不是新提示词或 HTML 测试。

最小可用接口：lineart/control_image + inpaint_image + mask_image + control strength + seed。得到实际模型输出后，使用已有 P15-47 局部 RGBA 保护和人物视觉对照验收。

## 最短恢复动作
在 Hugging Face MCP Settings 为对应账户添加 hugging-apps/qwen-image-2-1-controlnet-union-demo 的专用工具，或为 VPS 提供有额度的认证 GPU 推理方式。接通后运行固定 seed 的 P15-46 Lineart + Mask A/B；必须得到实际图片 SHA256 才算生成完成。否则不重复匿名推理、不新增无关模块。

P15-45 旧候选仍未通过精确 65° 和身份门禁，ArtMesh 保持原状。

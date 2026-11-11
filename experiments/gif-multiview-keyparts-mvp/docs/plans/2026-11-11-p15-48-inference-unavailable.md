# P15-48 · ControlNet 固定种子推理复核

目标：针对 P15-46 几何线稿和面部 Mask，产生真正新的 65° 图片，判断 P15-45 的五官偏移是否改善。

## 实际复核
- 基于 P15-47 已完成的仓库和验收记录。
- P15-44 至 P15-47 单测 30 项再次通过。
- 真正向 Hugging Face Space 提交 seed 65445 的新 Gradio SSE 任务，event 22418fb2785b4891acb2dfa534467358。
- 结果为 ZeroGPU quota exceeded，没有输出图片，不能做新图的视觉 A/B。
- 核查其他 3 个相近 Spaces：运行状态分别为 PAUSED、RUNTIME_ERROR、PAUSED。
- 连接 Hugging Face 账户的 Jobs 接口返回 HTTP 402 Payment Required；没有创建计算任务，不应未经授权购买 GPU 或升级。
- VPS 中未检测到 Hugging Face 访问 Token 环境项及本机 token 缓存。
- 完整保留 P15-45 的唯一真实生成图、P15-46 控制图及 P15-47 局部合成产物。没有更新正式 ArtMesh 或新 65° Keyframe。

## 判断
本轮是实际推理被配额阻止，不是模型生成质量失败，也不是成功生成。剩余核心事项是取得可用、允许 Lineart + Inpainting 的 GPU 推理入口。

## 接续指令
配额恢复或接通已认证账户的专用 Space 入口后，运行：
python3 scripts/p15_47_controlnet_inference.py --evidence-stage p15-49 --seed 65445
然后用真实新图和现有 HTML/RGBA 局部化程序进行验收。

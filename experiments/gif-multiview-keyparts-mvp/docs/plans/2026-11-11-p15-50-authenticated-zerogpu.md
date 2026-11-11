# P15-50 · 认证 ZeroGPU 推理入口

## 真实结果

- 从提交 1bf63b9 继续，确认已有 P15-45 唯一真实候选、P15-46 Lineart/Mask 和 P15-47 局部 RGBA 修补。
- 对两个已连接的 Hugging Face 账户执行动态 Space discover：原始 Qwen ControlNet Space 均未列入可直接使用的专用工具。
- 检查两个备选在线服务：FLUX ControlNet Union Pro 仅公开 canny/depth/openpose/gray/blur/tile 等条件，不支持项目要求的线稿加面部 inpaint 联合输入；另一个 FLUX inpaint 接口仅接受原图URL和 Mask URL，没有结构 Lineart。不能视为 P15-46 的等价替代。
- Hugging Face 官方 API 文档明确 REST 调用可使用 Authorization: Bearer HF_TOKEN，已认证账户将消耗个人 ZeroGPU 配额，而匿名 API 使用更严格的共享额度。参考 https://huggingface.co/docs/hub/spaces-api-endpoints
- 补充认证请求头（包括 upload/submit/SSE/源站文件获取），限定只发送给目标 Space 主机。
- 认证前置门禁：没有 HF_TOKEN 就退出码 3，写入不含密钥的失败证据，不上传私有原画，不触发匿名生成。
- 本轮目标 VPS 环境没有可用 HF_TOKEN，因此没有真实新生成；不能将这一轮算作视觉验收通过。
- 新增 4 项认证头、异域不外传、缺密钥不联网和持久化无密钥自动测试，历史测试一并通过 34/34。正式 ArtMesh 无修改。

## 唯一剩余用户动作

在 VPS 运行环境中设置该 Hugging Face 账户的个人访问 Token；例如由用户自行安全设置 HF_TOKEN 环境变量，不要把密钥贴入聊天、提交到 GitHub，或写入 HTML / evidence。

账号免费额度具体剩余秒数并未得到授权的额度查询结果，不能保证认证后推理立即成功。

## 接续命令

仅在有额度的认证环境中运行：

python3 scripts/p15_47_controlnet_inference.py --evidence-stage p15-51 --seed 65445

若成功获取实际 1024×1024 结果及 SHA256，则继续视觉对照：远眼透视、鼻梁、嘴、发夹、65° 方向及同一 P0 身份；合成仍必须保留 Mask 外 RGBA 和源 Alpha，最后才考虑正式 ArtMesh 准入。

# P15-89 · 真正 Mask 条件的模型接口与空间约束验收

## 最小目标
仅修复 P15-86 隐藏底图在外眼角附近的发丝/皮肤边缘，不改变原始眼睛和整张脸的几何；拒绝将 P15-88 的全画面缩放/漂移输出作为隐藏原画。

## 实际输入
- 继续使用 P15-86 hidden-face.reassigned.png（1024×1024），以同尺寸保存背景 RGB；保留 P15-56 原始身份参考和 P15-86 正式候选不变。
- 在画面 x499..553、y424..479 内建立明确的 2259 个非零 Mask 像素。未重新做 SAM3，也未归还原先误分配的 391 个睫毛像素。
- 独立输出完整原图、Mask、控制线稿、脸部放大 Mask 对照，以及 0/9/18px 正式旧基线参考。

## 推理后端判别
1. hugging-apps/Qwen-Image-2.1-ControlNet-Union-Demo 的 /generate 实际有 control_image、inpaint_image、mask_image 三个不同参数；已上传完整控制线稿、背景和实际 Mask，POST 返回 event_id a39fd57826b84ea0b3fcb33e5243009c。随后服务在模型调用处明确返回 ZeroGPU quota exceeded；该分支无模型输出。
2. pg56714/Inpaint-Anything 的 /get_fill_img_with_sd 有独立 image、mask、text_prompt 参数（区别于 P15-84 的无文本 LaMa）；将同一完整画布按服务最大尺寸映射为 768×768，Mask 等比映射，成功上传和提交 event_id 18e64851829e4e1ea031aaf436cba3a8。该事件持续超过六分钟仅返回 heartbeat，未取得 complete 事件或图像，停止轮询并将状态记录为 QUEUE_TIMEOUT_NO_MODEL_RESULT。
3. 这两个接口的独立 Mask 参数是真实模型输入；单纯在客户端把无 Mask 模型的整图输出裁回区域，不计为模型本身受 Mask 约束。

## 严格验收
- 外部不应被新模型触及：不论模型输出是否存在，最终候选仅按固定坐标、同一 Mask 将图像替换回原底图，要求 Mask 外像素变化为 0。该工程条件不能替代美术验收。
- 必须取得真实模型输出并检查目标区域颜色/连续发丝，重组独立头发/眼睛后渲染 0、9、18px。如果无有效新图或仍有边缘竖线/发色漂移，ArtMesh/VDD 均不更新。
- 当前已验证的 0px 源像素和 Alpha 准入沿用 P15-86；不得把新图的局部静态检查表述为新 9/18px 动画已经通过。

## 最终实际验收（本轮）
- Qwen Mask 接口：INFERENCE_FAILED，明确 ZeroGPU quota exceeded；Mask 已真实作为独立 API 输入提交，模型没有完成推理。
- SD Mask 接口：QUEUE_TIMEOUT_NO_MODEL_RESULT，已真实提交 Mask 与文字提示词，6 分钟以上仅 SSE heartbeat，无任何模型输出。
- 正式可用模型图 **0 张**；没有生成新的 0/9/18px 动画，沿用 P15-86 原始参考。静态工程检查与旧基线验证不能等同于 P15-89 的画质成功。
- 新增 18 项测试通过，P15-86 至 P15-89 共 71 项测试通过，Chromium 桌面与手机 2/2，HTML 7 张图每视口加载完好。
- 图像生成的阻塞来自实际服务配额和推理队列而非本地 Mask/坐标准备；本轮不增加更多无效模型尝试。

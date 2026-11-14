# P15-13 · 结构化姿态条件与面部 ArtMesh 归属验收

日期：2026-11-10
角色：`p0_character_001`
测试仓库：`tims-SP/koma-motion-lab`
执行：普通 ChatGPT → Supabase → `chatgpt-vps-bridge-worker` → 目标 VPS
原画主线：多视角独立部件 + P5 解剖锚点 + 分层遮挡 + TypeScript/WebGL VDD

## 验收目标

明确 57.5° 和 60° 转头时近眼、远眼、鼻、下颌和发夹的画面坐标，并生成可直接供条件模型或手绘修改器使用的结构信息。使用 P15-10 注册的 13 个独立语义部件保留深度身份，把原有 P15-12 的 RGB 绘画候选作为改绘基底。

最终高质量关键原画须满足：
1. 角色始终为已批准的 P0 唯一身份；
2. 镜头偏航真实处于 45°–65° 之间，双眼向右侧面转向时存在渐进可见性；
3. 金色交叉发夹处于原始画面的物理侧别，遮挡按头发/脸的独立层规则发生；
4. 眼、鼻、口、耳、刘海、后发、服装等以原生 RGBA 部件存在；
5. 面部不可见区域具备可靠的补绘，局部隐现和相邻帧能按 ArtMesh/VDD 约束连续过渡。

## 技术实现

`scripts/p15_13_structural_condition.py` 从 P15-12 的 12 类 P5 关键点和 P15-10 的 13 层原画分别生成 1024×1024 的结构数据。

| 通道 | 内容 | 作用 |
|---|---|---|
| Landmark Heatmap | 12 个空间控制点的 R/G/B 高斯热图 | 眼、鼻、下颌、发丝等局部位置条件 |
| Semantic Owner | 13 层 ArtMesh 的逐像素 owner ID | 分离可见图层与层次身份 |
| Lineart | 原注册 ArtMesh 的线条边缘 | 固定外部参考轮廓与笔触形态 |
| Preview | 原画参考、边缘和关键点的组合 | 浏览器及支持普通图像输入的改绘端观察 |

每一个输出都登记源文件 SHA、角色身份和空间位置。遮挡可见性来自 P5 拟合规则，是辅助参数，不作为真实隐藏笔触数据。

`scripts/p15_13_local_alignment.py` 使用原 P0 45° 的双色虹膜特征偏差作为检测器校准，以目标角度的 P5 坐标构建局部反向 Gaussian RBF 网格，仅对已有 AI 绘画的源像素位置进行局部重映射。它能够验证「图像特征的位置能否被约束」，保留原画来源；不能代替独立完成的新透视原画、缩窄远眼形变或藏于发束之后的补绘。

## 实际量测

从 P15-12 的 Qwen 新图中，在脸部指定位置检测两个紫色虹膜区域，比较经过原始 P0 校准的投影坐标：

| 目标视角 | 局部校准前的双眼定位总误差 | 局部几何对齐后总误差 | 误差下降 |
|---|---:|---:|---:|
| 57.5° | 84.933 px | 4.418 px | 94.798% |
| 60° | 107.001 px | 7.305 px | 93.173% |

这些数值是从同一生成画面提取的颜色特征与 P5 投影目标之间的定位误差，属于**结构条件自检**。它不是独立标注的瞳孔真值，也不能说明转头角度、头发物理结构、人物质感或画质通过。浏览器抽样后确认双眼位置改善，但是面部仍偏正面，原 P15-10 的 60° 渲染还存在显著的源画切换破损。

在本轮真正使用的图像编辑端，已连接的 Qwen-Image-Edit-2511 Gradio API 接口只提供图像数组、文本提示、LoRA、随机种子和采样控制；不具备原生 ControlNet 类型的独立条件通道参数。因此上面的结构热图是标准化的待消费条件资源，**不能把 LoRA 自由文本改绘称为结构条件扩散实际接入成功**。

## 现有研究与复用方向

- [See-through / SIGGRAPH 2026](https://github.com/shitagaki-lab/see-through)：提供二次元人物单张图像的语义分层、隐藏部位补绘、PSD 和深度信息，当前官方开源程序支持最多约 23 层。下一阶段优先对齐我们的 13 层语义 ID，检查透明层是否具有实际隐藏补绘。
- [LayerInbetween / TOG SIGGRAPH 2026](https://github.com/MarkMoHR/LayerInbetween)：以显式笔触对应、分层和遮挡控制处理关键帧插值，可供面部、刘海和眼部真正的线条拓扑变化参考。
- [ComfyUI ControlNet Aux](https://github.com/Fannovel16/comfyui_controlnet_aux)：提供 Anime Lineart / Canny / Face Mesh 等结构提示前处理器。P15-13 导出的线稿和锚点条件可进一步对接实际支持这些条件的扩散管线。

这些成熟仓库作为能力来源与对照，不意味着它们已经在当前 CPU VPS 上成功加载模型。现有 VPS 无 CUDA 设备，部署基于 GPU 的 See-through 全量分层和 ControlNet 图像生成需要独立计算资源。

## 验收与交付

源程序：
- `scripts/p15_13_structural_condition.py`
- `scripts/p15_13_local_alignment.py`
- `scripts/capture_p15_13.cjs`
- `scripts/p15_13_package.py`
- `tests/test_p15_13_structural_control.py`

浏览器对比：`review/p15-13-structure.html`。可切换 57.5° / 60°，并交互查看 AI 绘制、几何眼位校正、原有 ArtMesh、语义 owner-ID、线稿和锚点热图。

复现命令：

```bash
cd experiments/gif-multiview-keyparts-mvp
bash scripts/run-p15-13-review.sh
```

验证结果由 `evidence/p15-13-structural-qa.json`、`evidence/p15-13-local-alignment-qa.json` 和 `evidence/p15-13-delivery.json` 记录。私有原画及浏览器截图存放在 `private-assets/p15-13-structural`，离线 ZIP 由 GitHub Draft Release 保存。

## P15-14 · 生产原画接入

下一阶段直接围绕独立原画的最终视觉门禁开展：
1. 对接有真实结构控制通道的图像编辑器，输入 P15-13 的 RGB 关键点、线稿或单独的空间掩码，并保留 P0 身份参考；优先验证图像模型确实接收了条件信号。
2. 重新绘制 57.5° 和 60° 两张真实姿态原画，分别验收双眼宽度、鼻梁、颌面轮廓、发夹物理方向与阴影。
3. 使用 See-through 参考流程形成各角度 13 张实际分离的 RGBA 部件和被遮住的补绘部分；逐层回贴对比原画像素和遮挡规则。
4. 与 45°、65° 原画形成局部 VDD，使用独立留出角、相邻帧轮廓和真实 Chromium 抽样执行正式画质验收。

当前阶段完成的是**可重复的空间条件生成、局部几何约束和来源追踪**；最终 57.5°–60° 动漫关键原画还需实际绘画生产。

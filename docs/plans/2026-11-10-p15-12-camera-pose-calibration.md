# P15-12 · 角色相机方位与解剖锚点校准

日期：2026-11-10
角色：`p0_character_001`
工程仓库：`tims-SP/koma-motion-lab`
主线：多视角原画 + P5 3D Anchor 近似 + ArtMesh/VDD + 浏览器验收

## 目标和输入

建立可复现的 45°–65° 相机方位和关键解剖点几何约束，再将姿态条件图与已批准身份参考用于生成 57.5°、60° 绘画候选；工程来源、姿态质量和最终 ArtMesh 原画准入分别核定。

输入是此前登记的 P0 0°/45°/90° 标注（`p5-see-through/mv-candidate/landmark-qa.json`）以及已核对 SHA 的 P0 45°/90° 原图。角色双眼、鼻、下颌、嘴、耳、呆毛、刘海、侧发、后发、物理侧别发夹共 12 个控制锚点。

## 相机数学模型

对三个原始视角都可见的锚点，使用正交相机近似：

```text
x(yaw) = c + X*cos(yaw) + Z*sin(yaw)
```

其中 `c, X, Z` 由同一角色原始 0°/45°/90° 的 x 坐标求解，三点必须能够反投影到自身原始位置。纵向 y 在已知 45°–90° 间进行线性插值。对于 90° 已隐藏的远眼和发夹，不制造不可见侧的人工金标准：以原有 0°/45° 位置建立单独的两视角趋势预测，并将可见度作为 `cosine` 逐渐降低的**不确定性代理参数**。

该方案属于从原画标注拟合的 2.5D 摄像机近似，不是对真实角色体积的三维重建或独立人工标注真值。

### 实测锚点关系

| 水平角度 | 预测远眼–鼻水平间距 |
|---|---:|
| 45° | 32.01 px |
| 55° | 21.295 px |
| 57.5° | 18.967 px |
| 60° | 16.807 px |
| 62.5° | 14.824 px |
| 65° | 13.032 px |
| 90° | 7.940 px |

关键画面锚点必须保持近眼、鼻、远眼的屏幕顺序，并维持发夹源身份对应的物理方向。几何投影、显隐代理参数和每帧标注图由 `scripts/p15_12_camera_proxy.py` 生成，详见 `evidence/p15-12-camera-proxy-qa.json`。

## 原画生成实验

分别从 P15-12 已标定的 57.5°/60° 几何姿态图和 P0 45° 身份参考组成两图输入，通过已连接 Hugging Face 上的 `Qwen-Image-Edit-2511`、`Anime-V2` 生成两张独立 RGB 绘画候选。生成输出、模型和随机种子由 `scripts/p15_12_guided_qa.py` 记录并通过 Git 对象与原始 SHA 复核。

| 目标角度 | 输出候选相对几何导引的前景轮廓 IoU | 艺术画质 |
|---|---:|---|
| 57.5° | 0.89550 | 待校准面部和真实角度 |
| 60° | 0.80923 | 面部角度及不必要表情变化待修正 |

这些 IoU 衡量前景轮廓一致性，并不等于眼部位置、鼻骨方向或镜头角度准确。实际抽检确认两张图保留多数角色身份特征，但面部仍偏正脸，60° 版本含明显表情/面颊细节漂移，均暂不作为独立关键原画登记。

**独立绘制的关键帧准入为 0/2，原生绘制的 ArtMesh 部件准入为 0。** 当前 P15-10 正式语义渲染基线保持不变。

## LoRA 相机控制边界

核对 `fal/Qwen-Image-Edit-2511-Multiple-Angles-LoRA` 的模型说明，官方相机姿态词汇使用 `<sks> [azimuth] [elevation] [distance]`，已列出八个以 45° 为间隔的水平关键机位。精确的 57.5°/60° 属于非原生控制角度。既有 `Multiple-Angles` 适配器还存在与官方 `Fal-Multiple-Angles` 不同的模型来源，因此生成试验必须明确记录具体 adapter、提示、随机数和输入角色，而不是仅记录 “Qwen 多角度”。

参考：
- [fal 官方 Multiple-Angles LoRA](https://huggingface.co/fal/Qwen-Image-Edit-2511-Multiple-Angles-LoRA)
- [2.5D Cartoon Models 重实现](https://github.com/without-paper/2.5d_cartoon_model)，提供参数化方向、分组、形状插值和 3D Anchor 计算思路
- [See-through](https://github.com/shitagaki-lab/see-through)（SIGGRAPH 2026），用于后续 13 个语义图层和隐藏区域补绘

## 浏览器及 QA

可交互审查页 `review/p15-12-pose-calibration.html` 支持 57.5°/60° 相机视角、原始 ArtMesh 基线、姿态导引、新绘画候选及锚点覆盖切换。使用 Chromium 在桌面与移动端进行真实截图。原画资产及浏览器截图均留在 VPS 私有目录；源码、任务、来源 SHA 和验收 JSON 进入 GitHub。

完整复现：

```bash
cd experiments/gif-multiview-keyparts-mvp
bash scripts/run-p15-12-review.sh
```

产物包括 `evidence/p15-12-camera-proxy-qa.json`、`evidence/p15-12-guided-candidate-qa.json`、`evidence/p15-12-delivery.json`，以及私有离线 HTML ZIP `private-assets/exports/p15-12-camera-pose-review.zip`。

## P15-13 · 下一道门禁

采用能真正接受 **连续 2D 人脸/部件坐标或结构化姿态图** 的图像编辑/绘制入口；优先复用成熟的关键点条件、分层补绘与 2.5D 身份约束能力。取得解剖一致的 57.5°、60° 原画后，再进入 13 个独立 RGBA 部件、隐藏补绘、真实局部遮挡与 45°–65° 连续原画视觉验收。

必须采用新绘画以外的独立留出角检查轮廓、眼鼻口、发夹与笔触；不能用输入几何引导帧自我评价来宣布正式画质通过。

# P15-36 · P0 57.5° / 60° 局部原画与 13 语义部件验收

日期：2026-11-11
角色：`p0_character_001`
代码与证据：`tims-SP/koma-motion-lab`，`feature/gif-multiview-p0-ingestion-20261105`
运行路线：Hugging Face 插件远程图像生成；`chatgpt-vps-bridge-worker` 在 VPS 上执行资产处理、Python、Chromium 和 Git。

## 目标与输入

在 P15-35 的九帧 2.5D 深度和前发局部 UV 机制上，制作与 P0 源头身份有关联的 57.5°、60° 远眼、面部眼窝和刘海局部补绘。必须保留完整原生 RGBA 语义 ID、眼睛隐藏像素、原始镜头及其来源 SHA。审查对象从原画是否真正新增独立像素出发，而非单纯 Mesh 变形误差。

- P0 45° 身份来源：`private-assets/p2-views/whole/yaw045.png`，已登记 SHA-256 `78a08d5f010a8f449efda915a710a2de8958c3b1a32375df491d806fca251e40`；Hero 单独审批哈希仍由 T00 负责。
- P15-35 的源帧/13 个 ArtMesh：`private-assets/p15-35-occlusion-mount/yaw57p5/`、`yaw60/`。
- P5 原画关键点：P15-12 的鼻、远眼、近眼、嘴与发夹投影。
- 新绘画由已连接 Hugging Face 账户运行 `akhaliq/Qwen-Image-Edit-2511-LoRAs-Fast`，`Anime-V2`，带 P15-35 姿态及 P0 身份参考图。生成服务未在目标 VPS 上运行。

## 实际的新画面来源

| 角度 | 原画生成随机数 | 局部远眼配准平移（1024 坐标） | 全图差异像素 |
|---|---:|---:|---:|
| 57.5° | 575612 | (+19.053, −18.760) px | 24,801 |
| 60° | 603613 | (+5.860, −9.360) px | 26,211 |

`scripts/p15_36_qwen_local_repair.py` 对新画图像中的远眼有色虹膜进行实际像素定位，将局部绘画置于 P5 已登记位置，再在 1024 RGB 上将新像素划分为远眼、面部和刘海区域。新区域以面部周围的椭圆软边约束，仅作用于小范围局部。分离后按原始 ArtMesh native 443×443 RGBA 输出，并用 P15-35 的语义深度顺序重组。

每个角度固定输出 `body.reference`、`hair.back`、`face.skin`、`ear.far`、`ear.near`、`hair.side`、`eye.far`、`eye.near`、`nose`、`mouth`、`hair.front`、`hair.ahoge`、`hair.clip.cross_gold` 等 13 张透明 PNG。两组共 26 个角色文件。远眼、面部皮肤、刘海三个角色包含新的模型 RGB 绘画；其他十个角色保持 P15-35 输入源文件字节一致。所有图层仍来源于角色空间注册而非自立 PSD 原始图层。

完整远眼原始 RGBA 和被 P15-35 2.5D 遮挡的原画像素单独保存在 `eye.far.original-underpaint.png` 与 `eye.far.hidden-original.png`，便于后续真正的隐藏区补绘与物理遮挡裁定。

另外，`scripts/p15_36_cel_keyparts.py` 使用独立绘制的眼睑、鼻梁、面部和刘海向量笔触形成局部人工基准，按四个角色输出透明图层。该基准用于对比 P0 原像素与新增像素形态。最终交互主审查仍以模型生成的局部绘画和原始 P15-35 对照为中心。

## 结果与验收边界

| 检查项 | 实测 |
|---|---:|
| 新局部原画角度 | 2 |
| 每个角度 RGBA 语义部件 | 13 |
| 有新模型绘画像素的语义角色 | 3 类/角度 |
| 完整角色集合 | 26 PNG |
| 新向量笔触对照角色 | 4 类/角度 |
| 定向 Python 测试 | 11/11 通过 |
| Chromium 交互状态检查 | 12 |
| 资源图像加载 | 48 次，错误 0 |
| Chromium 桌面/移动截图 | 8 |
| 离线审查 ZIP 条目 | 73，逐项 SHA-256 与 CRC 验证通过 |
| ZIP 大小 | 9,081,546 字节 |

当前原画已经有独立于 P15-35 变形源的新 RGB 绘画，但不能将单张模型绘画自动分离成三张角色 PNG，认定为三张完全独立、具有背后真实补绘的 PSD ArtMesh。完整 Qwen 画面的相机方位和表情仍与冻结的 P0 目标存在差异，因此只采用局部修画用于研究；整幅新关键原画的正式准入数仍为 0。真实人工评审确认的 3D 鼻梁遮挡、同一发束的发夹物理固定、眼部隐藏区新增绘画仍需完成。

### 浏览器审查

`private-assets/exports/p15-36-original-keypart-review/index.html`：

- **整图对照**：P15-35 基线、P15-36 局部模型补绘、完整模型来源与差分。
- **语义分层**：远眼、面部皮肤、刘海、金色发夹四张独立 RGBA 图层。
- **隐藏补绘**：新远眼与面部局部 RGB、原始完整远眼和源层隐藏像素。

浏览器分别在 57.5°、60°、桌面/手机与上述三种模式各进行真实检查。用户可通过 ZIP 中的独立 HTML 打开并逐部件检查。

## 研究依据和后续对接

- [See-through (SIGGRAPH 2026)](https://github.com/shitagaki-lab/see-through)：主程序能将一幅动漫图像拆成最多 23 个含隐藏区域补绘的语义图层，并生成 PSD。适合未来对独立模型原画进行真正的 PSD 隐藏补绘，本阶段仅复用已有分层，不冒充运行了完整分层 GPU 模型。
- [LayerInbetween (ACM TOG 2026)](https://github.com/MarkMoHR/LayerInbetween)：处理分层动画中受遮挡笔触的一一对应，可作为 45°–65° 连续动画的跨角度画线与视觉门禁参考。
- [P15-35 面部深度与发夹](2026-11-11-p15-35-face-depth-hair-uv.md)：当前局部绘画需要匹配的原始 Z/UV 状态。

## 复现与交付

```bash
cd experiments/gif-multiview-keyparts-mvp
bash scripts/run-p15-36-review.sh
```

源码：`scripts/p15_36_cel_keyparts.py`、`scripts/p15_36_qwen_local_repair.py`、`scripts/p15_36_review.py`、`scripts/p15_36_browser.cjs`、`scripts/test_p15_36_paint_source.py`、`scripts/p15_36_package.py`。

证据：`evidence/p15-36-cel-keypart-qa.json`、`evidence/p15-36-qwen-local-repair-qa.json`、`evidence/p15-36-visual-review-qa.json`、`evidence/p15-36-browser-qa.json`、`evidence/p15-36-delivery.json`。

ZIP：`private-assets/exports/p15-36-original-keypart-review.zip`
SHA-256：`b63bf91ff005982b89b8658405e63c32a9528b16e28bf3a0a5e7b3205ee94256`

## P15-37 · 关键画质门禁

使用已保存的 57.5° 和 60° 原画候选，首先对整张脸部 3/4 转向、真实眼睑、发夹固定和头发连贯性进行统一的艺术验收，再完善真实视角下被遮挡的眼睛/脸/刘海笔触。需要取得完整原画并核对 P0 Hero 身份后，再正式生成和签收独立 PSD 部件。仅将通过视觉与来源双重验收的关键帧接入 45°–65° VDD，再扩展到更大角度。

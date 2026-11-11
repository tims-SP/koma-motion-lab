# P15-35 · 面部局部深度与前发附着坐标

日期：2026-11-11
角色：`p0_character_001`
项目：2.75D Anime Studio
测试：`tims-SP/koma-motion-lab`，分支 `feature/gif-multiview-p0-ingestion-20261105`
执行：ChatGPT → Supabase → chatgpt-vps-bridge-worker → VPS Python / Chromium

## 目标与来源

在已经可复验的 P15-34 5 关键帧、4 中间帧语义 Mesh 上，创建镜头角度相关的远眼局部遮挡与发夹绑定试验。使用原有 13 个 ArtMesh 语义 ID、原画像素、P15-34 的真实墨线特征来源与 443×443 RGBA 原生分层。全部输入按源 QA 与 SHA-256 引用，正式生产 VDD 版本保持独立。

参考成熟实践：

- [Live2D Cubism 的 ArtMesh Draw Order](https://docs.live2d.com/en/cubism-editor-manual/draworder/)：绘制顺序能随参数调整，适用于眼/面/发部件层级。
- [Live2D Cubism Clipping Mask](https://docs.live2d.com/en/cubism-editor-manual/clipping-mask/)：基于 ArtMesh ID 的局部可见性，避免整层透明度取代遮挡。
- [LayerInbetween（TOG 2026）](https://doi.org/10.1145/3811364)：遮挡区域的独立笔触对应和补绘是关键质量前提。

## 数据测量与修正方案

直接从 P15-34 的原始 ArtMesh 计算远眼与鼻、前发、面部皮肤的 RGBA 空间交集，以及发夹与前发、侧发的接触占比。

五个源角度 55°、57.5°、60°、62.5°、65° 中：鼻部真实 Alpha 对远眼遮挡只有约 0.1%–0.2%；发夹和前发的覆盖比例从 72.6% 下降到 50.9%。侧发覆盖约为 0%，因而当前角色的发夹应优先与 `hair.front` 建立局部坐标候选关系，不应强行绑定到 `hair.side`。

### 1. 源原画面部深度图

使用已登记的 `face.skin` 原画 RGBA 作为近面部遮挡材质。根据 P15-34 远眼原画轮廓 x 范围，使用归一化角度 `t = (yaw-55)/10` 和平滑连续函数，计算面部与远眼的局部 Z 次序切换边界。脸部现有像素负责遮挡的颜色，遮挡只作用于远眼局部源像素；眼睛完整 RGB 与透明 underpaint 单独保存。

用独立分区保存：

```text
eye.alpha = eye.hiddenByBangs + eye.hiddenByNose
          + eye.hiddenByFaceSurface + eye.visible
```

整个区间按固定明确的源角色绘制顺序重组 13 层，生成 `eye.far.original.png`、`eye.far.hidden-underpaint.png`、`face-depth-proxy.png`、`composite.png` 等结构化 RGBA 诊断输出。此处角度相关遮挡边界属于确定性 **2.5D 面部深度假设**，没有可独立证明的三维头骨体积和原画师确认的鼻梁轮廓，因此不登记为真实 3D 鼻梁几何。

### 2. 金色交叉发夹前发附着

在每帧 `hair.front` 的可见 Alpha bounding box 上建立二维局部 UV，源发夹的质心与该矩形构成相对坐标。对四个中间角度插值原有关键帧的局部 UV 候选，并使用限制在 ±4px 的局部平移搜索，在保留发夹原画像素的前提下，优化发夹与前发的覆盖接触率及 UV 残差。

**全部 9 帧都使用同一规则**，避免只在中间帧移动产生锯齿式关键帧跳动。原始五个源关键帧及其图层文件始终保存在 P15-34，P15-35 的九帧是独立候选画面。

## 实测

| 角度 | 远眼候选可见率 | 发夹与前发接触：源画面 → 局部绑定 |
|---|---:|---:|
| 55° | 83.34% | 72.57% → 91.16% |
| 56.25° | 76.19% | 69.73% → 89.68% |
| 57.5° | 64.10% | 67.04% → 86.20% |
| 58.75° | 46.77% | 64.54% → 84.45% |
| 60° | 29.61% | 61.66% → 81.77% |
| 61.25° | 14.74% | 59.25% → 77.81% |
| 62.5° | 7.28% | 56.54% → 74.45% |
| 63.75° | 5.56% | 54.08% → 71.88% |
| 65° | 5.56% | 50.87% → 68.51% |

以上百分比是原始像素 Alpha 和确定性深度遮挡规则产生的可见性及覆盖率指标，不等于可靠的美术判定。各帧发夹局部平移为 `(-4, +1)` 或 `(-4, +2)`，相邻帧差异为 0–1 个原生像素的平移参数，未发生只移动中间帧造成的明显几何步进。源画远眼 RGB 与相机下隐藏像素均保存了 SHA 可复核的 RGBA。

## 工程和视觉验收

| 项目 | 实测 |
|---|---:|
| 实验视角 | 9 |
| 独立 ArtMesh roles | 13 |
| 源 RGBA 角色保持字节一致 | 11（远眼和发夹分别生成候选） |
| 可见/隐藏像素互斥重组 | 验收通过 |
| 自动化测试 | 9/9 |
| Chromium 桌面/手机逐帧检查 | 18 |
| 图片加载 | 198，错误 0 |
| 浏览器证据截图 | 6 |
| ZIP 资源与清单 SHA-256 | 110 项 |

真实画面抽检了 55°、60°、65°：55° 的人物外观大体延续源画，发夹在前发上定位稳定；60°–65° 远眼逐步被面部材质覆盖，但**遮挡后的远眼眼窝、眼睑延伸、眼周发丝与侧脸轮廓的绘制仍有明显不自然的接缝**。这是源图未提供专门视角补绘的实质缺口，不能靠像素遮挡条件或 IoU 分数消除。

**工程验收范围：局部深度分区、遮挡 underpaint 保留、发夹依附前发的 UV 约束、9 帧来源和渲染复现。**

**艺术签收条件：** 在统一角色身份下重新绘制远眼逐步遮蔽所需的眼窝、鼻梁、面颊及前发遮挡笔触；对金色交叉发夹的实际固定发束作独立原画认证；取得真实 3D Anchor 几何与物理侧别验证之后，才能将上述 2.5D 代理升格为正式模型数据。

## 复现及文件

```bash
cd experiments/gif-multiview-keyparts-mvp
bash scripts/run-p15-35-review.sh
```

- `scripts/p15_35_depth_mount.py`：9 帧深度与局部 UV 候选。
- `scripts/p15_35_review.py`：交互 HTML，可逐帧比较深度前后、隐藏远眼、原有前发和发夹。
- `scripts/p15_35_browser.cjs`：浏览器检查与截图。
- `scripts/test_p15_35_depth_mount.py`：像素来源、互斥遮挡、局部附着连续性及 browser QA。
- `scripts/p15_35_package.py`：包含逐文件哈希的离线 HTML ZIP。
- `evidence/p15-35-occlusion-mount-qa.json`、`evidence/p15-35-browser-qa.json`、`evidence/p15-35-delivery.json`：工程证据。
- `private-assets/exports/p15-35-face-depth-hair-review.zip`：私有审查资产。

## 下一阶段 P15-36

以 **55°–65° 真实原画补绘** 为中心，采用已有同一 P0 身份关键帧生成可验证的远眼、眼窝、鼻梁、侧发、发夹独立透明部件，并检查背后的完整 underpaint。优先验证关键局部修画能否通过真实视觉与逐部件闭环，再扩大覆盖角度和迁移到 TypeScript/WebGL 生产渲染。

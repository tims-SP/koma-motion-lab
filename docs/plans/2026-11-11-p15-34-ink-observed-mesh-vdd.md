# P15-34 · P0 原画墨线特征与局部 ArtMesh 形变

日期：2026-11-11
角色：`p0_character_001`
仓库：`tims-SP/koma-motion-lab`，实验分支 `feature/gif-multiview-p0-ingestion-20261105`
运行：ChatGPT → Supabase Bridge → VPS Python + Chromium

## 阶段目标与输入

在 P15-33 的 P0 相机锚点约束 Mesh 上，新增有**真实原画像素来源**的可命名辅助特征：远眼上眼睑墨线两端、金色交叉发夹两根斜杆的四个颜料端点、侧发的局部根部边界和末端边界。三个关键角色保持相同 ArtMesh role ID：`eye.far`、`hair.clip.cross_gold`、`hair.side`。

输入素材沿用 P0 原画 45° 来源 SHA-256 `78a08d5f010a8f449efda915a710a2de8958c3b1a32375df491d806fca251e40`，从 P15-31 注册的五个 443×443 RGBA 分层源帧读取角色像素，P15-12 摄像机投影提供主锚点。P15-33 候选和此前 P15-21 正式生产渲染输出均保留作对照。

图层是原有原画的派生关键帧，并非独立绘制的 55°、57.5°、60°、62.5°、65° 原画。

## 实际完成的程序

- `scripts/p15_34_ink_landmarks.py`：检测眼部深色线稿、发夹金属着色和侧发 Alpha 轮廓边界，从实际带颜色的源像素挑选辅助特征点，关联 443 坐标、语义名称、来源 SHA、来源角色、可视化标注。
- `scripts/p15_34_ink_mesh_vdd.py`：与 P15-33 的 7×7 / 每角色 72 三角形网格兼容，复用双向 Farneback 光流和 RBF 顶点校正，按特征 identity 插值，得到四个独立中间 Mesh 画面；原有五个关键帧及其余十个角色的字节完全保持一致。
- `scripts/p15_34_review.py`：输出可交互九角度 HTML；比较 P15-34、P15-33、RGBA 差异和 11 个带名字的源像素采样点，提供三类部件的透明图层。
- `scripts/p15_34_browser.cjs`：真实 Chromium 桌面/移动双视口逐帧验收及 SHA-256 截图。
- `scripts/test_p15_34_ink_mesh.py`：回归来源哈希、采样点着色邻域、跨角度 feature ID、Mesh 无翻转、键帧保真、十个非 Mesh 部件字节保真和浏览器证据。
- `scripts/p15_34_package.py`：将私有图像、HTML、截图与来源 QA 打成带校验清单的独立 ZIP。

### 特征控制点

| 角色 | 控制点数 | 具体来源 |
|---|---:|---|
| `eye.far` | 3 | P15-12 虹膜相机坐标 + 原画上眼睑暗色墨线两端候选 |
| `hair.clip.cross_gold` | 5 | P15-12 发夹相机坐标 + 两条斜向颜料纹理的四个端点候选 |
| `hair.side` | 3 | P15-12 侧发相机坐标 + 侧发轮廓上的根、梢候选 |

共 **11 个有名控制点**，在五个已登记关键角度分别记录源图像 SHA。所有二级点确实落在对应角色源像素支持附近；这证明「来自原画」，不能推导出「已由原画师确认这就是正确的解剖笔触根梢」。

## 运行结果

| 项目 | 实测 |
|---|---:|
| 55°–65° 全部画面 | 9 帧 |
| 原始关键帧 | 5 帧，字节一致 |
| 生成的局部 Mesh 中间帧 | 4 帧 |
| 改动角色 | 3 / 13 |
| 每个角色网格 | 7×7 顶点、72 三角形 |
| 最大特征跟踪残差 | 0.54734 原生像素 |
| 最小相对三角形面积 | 0.560092 |
| 三角形翻转 | 0 |
| 中间帧相对于 P15-33 的全图差异像素 | 123,849 / 118,607 / 122,586 / 139,757 |
| 中间帧相对于 P15-33 的 Alpha IoU | 0.996101 / 0.997414 / 0.994979 / 0.991065 |
| 单元测试 | 8/8 PASS |
| Chromium 桌面+移动角度检查 | 18 |
| 实际图像加载 | 126，错误 0 |
| 可见截图 | 6 |
| ZIP 资源条目 | 75，SHA-256 逐项复验 |

这组数字证明关键帧来源保真与图像局部网格几何稳定，不是相机真实方位误差或独立画师的艺术质量分数。视觉抽样确认分层、头发、发夹在渲染画面中可辨认。四个中间帧与 P15-33 显示了不同的局部笔触和形变，但它们共享原始源图，不能用像素差异证明任何一种最终画质更好。

## 验收边界与后续

**工程门禁：通过。** 原有生产输出完整保留；P15-34 独立实验镜头可追溯、可重跑。

**关键艺术与物理门禁：尚需完成。** 当前自动提取的墨线采样点尚未正式通过人工/独立原画认证；仍需要从角度真实的 55°–65° 原生部件确认眼角、发夹交叉金属条端点、以及某根侧发的物理根/梢。远眼挡在鼻梁之后的真实三维遮挡、发夹固定于指定发束的空间关系和 360° 原画一致性，必须在独立原画与可见/隐藏笔触得到确认后验收。

下一阶段 **P15-35** 以发束局部坐标系、发夹几何固定点及鼻面深度关系建立可实际渲染的遮挡约束；随后进行 WebGL/TypeScript ArtMesh 参数化和真实视觉抽检。

## 重放与证据

```bash
cd experiments/gif-multiview-keyparts-mvp
bash scripts/run-p15-34-review.sh
```

- 来源特征：`evidence/p15-34-ink-landmarks-qa.json`
- 网格形变：`evidence/p15-34-feature-mesh-qa.json`
- 浏览器：`evidence/p15-34-browser-qa.json`
- 私有 HTML 目录：`private-assets/exports/p15-34-source-ink-mesh-review/`
- SHA 审查包：`private-assets/exports/p15-34-ink-mesh-review.zip`
- 交付哈希：`evidence/p15-34-delivery.json`

研究参考：[LayerInbetween](https://github.com/MarkMoHR/LayerInbetween) (SIGGRAPH 2026，doi:10.1145/3811364) 对遮挡笔触对应的分层处理；[scikit-image PiecewiseAffineTransform](https://scikit-image.org/docs/stable/api/skimage.transform.html) 的三角网格形变原理。当前使用已有 OpenCV 网格方案，不另建复杂模型运行环境。

# Sonetto · C06 双视角语义图层与留出角验收

验证范围：十四行诗 `302301_shisihangshi`，Cubism 原生立绘 + PMX 正交结构参考 + HTML Canvas2D 双视角 VDD 工程。

## 已实现

- 原生 Cubism 对照：40 张按 Part 分开的透明 PNG，263 个 Drawable 映射；由官方 Cubism Core 提供保真基准。
- 三维参考来源：WTHN_Ross 的 Sonetto PMX v1.1，在 Blender 4.0.2 中定角渲染；使用许可已按英文/日文 ReadMe 审查。原模型、纹理仅存个人私有环境。
- 分层代理：在 45° 与 90° 真实镜头下，结合 PMX 材质、网格位置和可见深度，对 `face.skin`、`eye.near`、`nose`、`mouth`、`ear.near`、`hair.front`、`hair.side`、`hair.back` 生成 16 张 640×640 RGBA PNG。服装在头部资产提取时透明，保留后发完整轮廓；嘴部以原 PMX 嘴部几何投影选取真实画面颜色。
- 源类别标记为 `third_party_3d_proxy`；每图登记角度、语义 ID、SHA-256、像素数、透明包围盒与源版权。独立绘制原画覆盖率仍为 0/16。
- HTML 语义工作台可一次加载 16 张真实像素代理，预览逐部件双视角局部变形及深度顺序；保留 Cubism 原画 Part 对照及 45°、90° 三维结构参考。

## 验收数据

| 门禁 | 结果 |
|---|---|
| 透明语义代理 45°/90° | 16/16 RGBA 非空，来源和哈希通过 |
| 独立原画合同正反例 | 9/9 测试通过，PMX 代理不会计入原画合格数 |
| HTML 真正 PNG 像素及角色来源测试 | Chromium 24/24 |
| 官方 Cubism 原生与 Three.js 回归 | Chromium 12/12 |
| VDD 留出视角 | 55°、67°、82° 三张额外独立 3D 镜头参考 |
| 实验室正式视觉门禁 | `NEEDS_VDD_REFINEMENT` |

留出角指标（无需人工猜测“好不好”）：

| 角度 | 预测轮廓 IoU ↑ | RGB MAE /255 ↓ | 预测轮廓面积 / 参考 |
|---|---:|---:|---:|
| 55° | 0.866875 | 28.763 | 1.037927 |
| 67° | 0.819558 | 37.8148 | 1.127993 |
| 82° | 0.853299 | 27.173 | 0.903310 |

当前几何留出门禁采用全部角度 IoU ≥0.90、RGB MAE ≤20/255、预测面积比 0.92～1.08；这只是用同一角色三维结构参考验证原型质量，不能替代最终二维原画的人工视觉签收。中间角显隐切换与五官对应仍需完成。

## 插值方法对照

主运行时是分语义部件的两组三角形矩形变形 + 源图透明度混合。对同一 45°/90° 关键图片另使用 OpenCV 的 Farneback 与 DIS 双向光流估计后，在 55°/67°/82° 比较。完整数字见 [C06 光流实验报告](../evidence/c06-pmx-optical-flow-benchmark.json)。这些方法未代替正式的面部几何锚点和视角相关遮挡。

论文和成熟实现参考：

- [Fukusato & Maejima, View-Dependent Deformation for 2.5-D Cartoon Models (2022)](https://doi.org/10.1109/MCG.2022.3174202)：研究用不同视角指定的二维形状插值，适合进一步建设器官与轮廓约束。
- [OpenCV Farneback Dense Optical Flow](https://docs.opencv.org/4.x/dc/d6b/group__video__track.html)：像素位移候选。
- [OpenCV DIS Optical Flow](https://docs.opencv.org/4.x/de/d4f/classcv_1_1DISOpticalFlow.html)：另一种成熟稠密光流候选。

## 下一个验收切口

1. 从源网格／Cubism ArtMesh 建立 45°、90° 相同语义器官的**对应顶点与边缘锚点**，尤其是眼角、鼻尖、颌线、耳廓、发束切口。
2. 在每张二维部件图层上使用三角网格进行约束形变；按逐视角拓扑可见性动态改变器官深度／显隐，并使用局部形变而非单纯透明重影。
3. 每轮生成 55°、67°、82° 留出预测，和上述源无关镜头参考比较。工程量化通过后，再由独立画师／AI 高质量正面与侧面原画进行动漫质量验收。
4. Cubism 继续负责 0° 原生画面质量基准，最终 VDD 关键原画仍按 `assets/view-key-contract.json` 签收；不将结构代理视为生产原画。

## 复现入口

- `scripts/render-sonetto-semantic-proxies.py`：两方向 PMX 材质／网格抽层，仅依赖允许访问的私有 PMX。
- `scripts/qa-semantic-view-proxies.py`：透明度、颜色像素与源哈希审核。
- `scripts/prepare-view-layer-lab.py --semantic-proxy ...`：将本地私有图层放入 HTML 工作台。
- `scripts/capture-pmx-vdd-predictions.cjs`：真实 Chromium 输出 45°～90° 图像。
- `scripts/render-sonetto-holdout-views.py`：留出角正交镜头参考。
- `scripts/qa-pmx-vdd-holdouts.py`：轮廓及 RGB 误差。
- `scripts/evaluate-pmx-optical-flow.py`：OpenCV 对照实验。

正式数据与工程代码保存在 `koma-motion-lab`，原始 PMX、纹理和 RGB/PNG 像素仅在授权私有资源包中保存；可复用运行时组件在通过生产视觉门禁后再进入 `koma-motion`。

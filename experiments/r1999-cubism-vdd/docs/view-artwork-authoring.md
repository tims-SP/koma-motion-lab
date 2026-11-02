# Sonetto · C04 独立视角语义原画制作规范

状态：VIEW_AUTHORING_READY / ARTWORK_PENDING
验证角色：`302301_shisihangshi` · 原生 Cubism，源提交 `45e75248ba3b25053fd32e63ab13c2f9f54dd9df`
实验：`experiments/r1999-cubism-vdd`
相关合同：[`assets/view-key-contract.json`](../assets/view-key-contract.json)

## 视觉目标

从已验证的原生 Cubism 角色外观、服装、面部和发型身份出发，建立能与原画无缝结合的 **45° 三分之四侧视**和 **90° 真侧脸**。原生人物脸型、橘红色头发、黑白棋盘格发饰、灰白服装和金棕色眼睛作为身份基准。输出保持成熟日本动画的线条、色彩块与阴影厚度。

原生 Cubism 动态 ArtMesh 是保真基线。模型现有 `PARAM_ANGLE_X/Y/Z` 为二维形变控制，不是标定过的物理相机角度，因此在登记的视角元信息中保留 `sourceView: uncalibrated`，并对新视角使用统一相机方向。相机水平角度定义：0° 目标正面，90° 角色右侧脸朝画面左侧，180° 背面。若作者按相反方向绘制，需要更新视角标定和镜像元信息，而不是暗中翻转。

## 核心源资产

VPS 私有路径：

- Native Cubism 模型：`/root/koma-motion-r1999/private-assets/302301_shisihangshi/`
- 40 张原生 Part 透明 PNG：`/root/koma-motion-r1999/output/private-front-layers/`
- 正面 Part 哈希：[`evidence/c04-front-layer-manifest.json`](../evidence/c04-front-layer-manifest.json)
- 原生视觉 HTML：`/root/koma-motion-r1999/output/c05-web/`
- 新增多视角 HTML：`/view-layer-lab.html`，通过私有静态服务访问

固定画布尺寸为 640×640 RGBA PNG，同一头部物理尺度和中心锚点。只允许一张 PNG 对应一个 `semanticId`。一个语义部件内部可以有自己的纹理、轮廓和阴影，但眼、鼻、口、耳等分别是独立图片。所有图必须具有透明边界、稳定像素尺寸与 SHA-256；正式视角键须具备来源、许可核查、相机标定和 3 个以上非共线特征点。

## 首批视角层（每角度 8 张）

| semanticId | 45° 重点 | 90° 重点 | 原生 Part 参考 |
|---|---|---|---|
| `face.skin` | 颧骨、下颌、左右脸不同宽度 | 鼻根—唇—下巴侧轮廓与颈部连接 | `__UNPARENTED_DRAWABLES__` |
| `eye.near` | 近眼尺度、睫线、眉弓比例 | 只有靠近镜头的眼；侧视巩膜与眼睑轮廓 | `PARTS_01_EYE_001` |
| `nose` | 鼻根至鼻尖透视 | 鼻梁鼻尖、鼻翼和鼻底前突轮廓 | `PARTS_01_NOSE_001` |
| `mouth` | 唇线偏离脸部中心 | 唇峰、开闭口和下唇侧面切线 | `PARTS_01_MOUTH_001` |
| `ear.near` | 近耳可见边缘、头发遮挡 | 耳廓、耳垂、耳根及发饰位置 | `PARTS_01_EAR_001` |
| `hair.front` | 额发体积和棋盘格发饰投影 | 刘海穿越额头边界的侧轮廓 | `PARTS_01_HAIR_FRONT_001` |
| `hair.side` | 脸颊附近发束和头骨宽度 | 发束从耳前绕向耳后，透出侧脸 | `PARTS_01_HAIR_SIDE_001` |
| `hair.back` | 后脑圆度及垂发分束 | 后脑完整体积、发尾内外层轮廓 | `PARTS_01_HAIR_BACK_001` + `Hair_B_*` |

发色、发饰与服装细节以原生 PNG 参考进行交叉检查。两个角度中的器官使用相同的 `semanticId`；存在遮挡或拓扑切换时，登记 `visibility`/`split`/`merge`，由分部件融合器处理。

## 单部件图片生成模板

每一项作为独立生成任务执行：

> 绘制《重返未来：1999》十四行诗同一身份、同一阴影与线稿风格的 `{semanticId}` 部件，视角为 `{cameraYawDeg}` 度，保持与附带 Cubism 原生头部图片相同的构图和头部尺度。仅生成本部件及其必要的线稿和局部阴影，640×640 PNG RGBA、透明留白、角色结构明确、每个笔触服务于该部件。使用本次视角设定参考与原生 Part PNG，记录稳定定位点及遮挡层级。

当 `semanticId` 为 `face.skin` 时，保留脸部皮肤与下颌轮廓，眼、鼻、口独立处理；为 `eye.near` 时，只生成近眼；90° 时鼻梁、鼻尖和嘴唇必须真的具有突出的侧轮廓。

每个生成结果进入私有候选区，首先核对视觉身份，再执行 `validate-view-layers.py` 的文件和来源校验，通过后才能进入 VDD 真视角输入。AI 产物的源提示、输入参考和输出文件 SHA 统一登记。

## 双门禁

1. **工程门禁**：每角度 8 个 semantic PNG，共 16 个；满足 PNG RGBA、独立 SHA、透明背景、非共线特征点、相机元数据、授权、来源 ID、手绘/生成记录。命令：`python3 scripts/validate-view-layers.py --manifest <private_manifest> --root <private_asset_root> --strict`。
2. **视觉门禁**：实际 HTML 截图中 45°、90° 的五官比例、轮廓、发型、耳鼻遮挡、人设身份一致。提供 20°/55°/82° 的独立留出图，验证中间角度而不把训练输入当真值。逐帧采样检查遮挡、闪烁、轮廓断裂。

独立原画的角色形象生成和 90° 侧面视觉签收必须得到真实素材结果支持。当前 `C04` 视角来源检查报告记录需制作的 16 张图片，并保留工程测试用合成夹具与真实生产原画之间的严格边界。

## 结构参考

- <https://booth.pm/en/items/5601866>：WTHN_Ross 免费 Sonetto Blender 参考模型。网页可浏览，模型下载需要账号登录并检查 ReadMe 的具体许可；可用于结构核对，不直接作为独立绘画关键帧。
- Cubism 官方 SDK 与固定的资产源模型作为真实面部/风格参考。

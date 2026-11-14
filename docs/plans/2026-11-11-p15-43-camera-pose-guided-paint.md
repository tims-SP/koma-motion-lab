# P15-43 · 65° 相机锚点引导原画审查

## 既有结构来源

采用 P15-12 的 0°/45°/90° 已登记相机投影与角色 `p0_character_001`，使用其 65° 关键几何锚点：近眼 `(604.739, 460.617)`、远眼 `(729.373, 469.040)`、鼻 `(716.341, 535.644)`、下巴 `(637.199, 660.889)`、发夹 `(789.948, 320.100)`。该集合是现有几何假设，不代表已获画师认证的生理解剖。

`private-assets/exports/p15-43-camera-pose-review/yaw65-anchor-overlay.png` 已从真实 65° 注册原图与上述六个锚点渲染；原图、45° P0、60° 注册图与独立侧脸参考均提供可视化对照。

## 实际模型推理

通过连接的 Hugging Face Space `akhaliq/Qwen-Image-Edit-2511-LoRAs-Fast` 执行带姿态图和身份图的双图编辑。参考分别是当前 65° 登记合成与批准角色 45° 原始视角。受限于输入容量，将两张图各转成 768×768 JPEG，哈希保存在 VPS 原图目录中；使用 `Multiple-Angles`、seed `65431`、4 步推理。

真实输出原画 `private-assets/p15-43-structured-pose/yaw065-pose-controlled-account-3.png` SHA-256：`f8e3db93fc8fc9214b18d9d34b57f11e13342ce5a0dca27378f0da76ec51fd4a`。

独立视觉核查：输出的脸朝画面左侧，眼睛只有一只，金色交叉发夹移动到画面左侧，且出现额外后束发；与要求的右朝向 65° 严格相反。新绘画不具备当前关键帧的准入条件，不替换原始 13 张 ArtMesh RGBA 文件。

## 工程与画面验收

- `scripts/p15_43_structured_pose_review.py`：使用真实登记相机数据、来源哈希和生成原画形成可复核的视觉审查包。
- `scripts/test_p15_43_camera_review.py`：**8/8** 来源、Canvas、锚点、HTML、画质准入测试通过。
- `scripts/p15_43_browser.cjs`：真实 Chromium 桌面与移动端共 **4 组**、**12 次图片加载**、**4 张截图**，运行错误 **0**。
- 证据：`evidence/p15-43-camera-pose-qa.json`、`evidence/p15-43-browser-qa.json`。
- HTML `private-assets/exports/p15-43-camera-pose-review/index.html`；ZIP 11 个文件、6,116,935 字节，SHA-256 `dc9b0153630d1b16e996743eaf0c4263eacad404f90db5f26eb1be2e70a33b3f`，已上传项目 Draft Release。

## 下一项决定性工作

P15-44 需要验证具有真正显式姿态条件输入的推理路径：先以眼、鼻、面部轮廓与发夹锚点构建可消费的 pose/lineart/mask 控制，而非仅把图作为软性参考。要求具体后端确认可读取控制图和强度，真实生成后必须逐眼/鼻/发夹局部视觉审查。目标是保留正确右朝向、两眼、65° 透视及 P0 发型；通过整体原画后才执行独立隐藏笔触与透明 ArtMesh 分层。

P0 Hero 原始批准文件哈希尚待原图恢复。保持 P15-38 主资产与 P15-41 侧面素材原字节可追溯。

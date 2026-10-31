# MVP-005 · 分视角细节原画 + 近景验收（2026-10-31）

## 状态

**ENGINEERING_SUCCESS (初次 CI: #41194734772) / FINAL VISUAL QUALITY: FAIL**

本次沿用 MVP-004 的**相同人物、骨骼/锚点、VDD、网格与 IK、阴影、动态遮挡以及 6s/144-frame 时间轴**。没有去复现 Spine/Live2D、没有另建技术样机，也没有引入第三方游戏原画。

**事实边界：** 本次绘画均是新编写的 TypeScript Canvas2D/SVG-like 矢量笔触算法，而非独立画师或 AI 生成的高质量正侧背原画。在工程上确实是四方向分别缓存的 512×512 透明 RGBA 纹理，且能够沿稳定 UV/语义顶点驱动同一 ArtMesh；但是 *这一点不能等同于高质量日式动漫资产已经完成*。

## 真正做了什么

1. 新增 [\`src/anime-ink.ts\`](../../experiments/mvp002/src/anime-ink.ts)。为同一角色的面部、瞳孔/睫毛、刘海、后发、上衣、裙褶、围巾、徽章、手袖、腿部添加多笔触颜色/轮廓/高光，依不同角度绘制相应的局部形态。
2. \`rgba-view-art.ts\` 将纹理从 256×256 提升至 512×512，仍为每部件/角度独立 alpha CanvasTexture，并在原本面部与眼睛粗略画法上采用新的局部绘制规则。
3. \`integrated.ts\` 相同角色单镜头在最后 1 秒多增加了真正的相机近景（约 0.33 倍原正交视野，镜头中心移动至眼睛/面部）。原有 0—360 与手臂从后穿到前的动作不变。
4. 渲染脚本 [\`render-integrated.ts\`](../../experiments/mvp002/scripts/render-integrated.ts) 导出 16 个真实关键图层 PNG，以及**新增**的四方向源原画 checkerboard 对照板 \`key-art-contact.png\`；再执行原来的整个 6 秒镜头。
5. 严格 TS 检查、实际 Chromium WebGL 帧/FFprobe 视频验收、IK 误差/手臂正负深度、眨眼和光影控制一并保留。
6. 抽检发现眼睛比例偏小，已增大 \`eyes\` 网格、同时用**预乘 Alpha 纹理混合**纠正相邻画面透明边界色的插值（这是最后一次定点修正）。

## 可核实证据

首轮 512² 绘制版（**尚不含最后的眼睛比例/预乘 alpha 修正**）：
- [成功的 Actions #41194734772](https://github.com/tims-SP/koma-motion-lab/actions/runs/41194734772)
- [原画 16 张 + 成片 + 抽帧 Artifact #13040420694](https://github.com/tims-SP/koma-motion-lab/actions/runs/41194734772/artifacts/13040420694)
- [对应 Draft Release](https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-051b6bc615652548b44e)
- [6 秒 H264 / 144 帧](https://github.com/tims-SP/koma-motion-lab/releases/download/untagged-051b6bc615652548b44e/integrated-6sec.mp4)
- [真实源原画 4×4 对照板](https://github.com/tims-SP/koma-motion-lab/releases/download/untagged-051b6bc615652548b44e/key-art-contact.png)

**请在最后的 CI 完成后再记录最终链接与视觉结果，不应拿第一轮链接声称最终修正通过。**

## 从实际渲染帧观察到的质量问题

实际抽取 frame 12、87、114、132，逐帧查看。
- 可见改进：刘海细条/后发高光、上衣门襟与胸针、围巾和裙褶均明显可辨，脸部特写成为了可观察的评价窗口。
- 仍未解决：眼睛近景偏细（已进行尺寸修复，待最后结果确认），侧脸轮廓不具有高质量日漫的典型设计，头发尖锐僵硬，衣袖和手臂连接像机械木偶，面部阴影缺少手绘细腻性。
- 360° 的侧/背方向目前存在同一个 90° 侧轮廓派生出 270° 的简化规则，不是具有不同造型/配饰侧面的真正四张原画。
- 只确认了透明贴图、关键形变和合成可协同；不能据此声称单张图片推完整 360、商业作品画质、复杂 Alpha 交叉遮挡、全身 IK+脚步接地都已解决。

## 当前决策：停止进一步修饰程序化素材

**继续增加 Canvas2D 笔触的边际收益已经较低。**

下一项不应再进行新一轮 K0/K1/K2、“先验证三秒教程”，而应直接在现有统一角色格式中替换成**真正外部绘制的高品质、多角度、分层、可对应 RGBA 原画**：

1. 用同一个固定人物设定制作/获取正面、右侧、背面、左侧角色原画及真实可单独编辑的脸/眼/刘海/后发/上衣/裙装（8—12 个必要语义部件即可）。若图像不自带透明层，需要定向遮罩+局部补图，不能把整张 turnaround 当作分层 Rig。
2. 用现有 \`Part ID / viewKey / UV landmark / anchor / IK\` 直接输入，保留一条 6 秒动画，不做资产导入框架大工程。
3. 具体查看四个关键视角与 45° 中间角度，检查脸和五官是否变形/重影；补充局部 art shape 或 occlusion mask，不要求所有部件同样复杂度。
4. 若外部原画无法和固定 UV 拓扑对应，则需要对受影响部件做拓扑 split/merge 和 view-specific mask，而不是将整张人物 PNG 交叉淡入淡出。

目标仍是同一角色全身 360、全身动作、精细面部与光影三者共同满足画质要求；本轮只代表技术图层和 lookdev 进一步进展。

## Stage score

- 同一角色 / 单镜头：是。
- 3D Anchor、VDD、ArtMesh、手臂双骨 IK、前后遮挡、画师式阴影、Particle：本轮保留。
- 4 方向 RGBA 独立缓存 + 512² 更精细手绘规则：已接入。
- 镜头真正从远景转近景：已接入。
- 真实独立多视角高画质人物原画：**未实现**。
- 电影级高保真面部/身体动作：**未通过**。

## 最终修订版验收（已完成）

- [成功的最终 Actions #41194923884](https://github.com/tims-SP/koma-motion-lab/actions/runs/41194923884)
- [最终 Draft Release](https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-29dfef1130728dc814a9)
- [最终 6 秒视频](https://github.com/tims-SP/koma-motion-lab/releases/download/untagged-29dfef1130728dc814a9/integrated-6sec.mp4)；357,537 bytes；960×540 / 144 decoded frames。
- [最终 16 图分视角 RGBA 原画对照板](https://github.com/tims-SP/koma-motion-lab/releases/download/untagged-29dfef1130728dc814a9/key-art-contact.png)
- [包含真实透明 PNG、视频、4 张实际 QA 图、数值报告的 Artifact #13040540770](https://github.com/tims-SP/koma-motion-lab/actions/runs/41194923884/artifacts/13040540770)
- 最新 \`src/integrated.ts\`：eyes mesh 区域增加到 0.37×0.155（模型半宽/半高）；view-crossfade shader 采用 alpha premultiplication/recovery，减少透明像素插值边缘错误。
- 严格 TypeScript、原有 IK/深度/阴影校验、16 张 PNG 的真实 Alpha 和角度差异校验、FFprobe 全部通过。
- 关键自动指标：IK max error ≈ 2.22e−16；手臂相对躯干前后深度 −0.343→+0.680；面部阴影偏移跨度 ≈ 0.353；眼睛形变及额外近景镜头正常执行。
- 实际查看 frame 12 / 114 / 132：frame 132 两只眼较此前明显增大，睫毛/眼线更可辨；但依然缺少有质量的头部与服装真实多视角原画。仍为 **PASS_ENGINEERING / FAIL_VISUAL_ANIME_QUALITY**。
- **下阶段禁止继续仅为程序化笔触做无限小修**。核心基础已能消费真正 RGBA 分层资产，应该转向独立真实高保真前/侧/背/左侧原画及 semantic part registration；只在当前镜头验证。

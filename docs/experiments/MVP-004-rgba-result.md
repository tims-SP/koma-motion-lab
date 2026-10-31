# MVP-004 · 多视角分层 RGBA 原画/UV 接入结果（2026-10-31）

## 本轮结论：PASS_ENGINEERING_TEXTURE_PIPELINE / VISUAL_QUALITY_FAIL

沿用已经成功的 MVP-003 **同一条 6s / 144 帧 / 960×540** 的人物镜头；没有开设新的技术证明 MVP、导入游戏角色、复现 Spine/Live2D。

在实际运行时：
1. 为每个语义 Part 按 0°、90°、180°、270° 生成并保持独立透明 CanvasTexture（总 12×4），材质域采用可重复的固定 UV。
2. \`face\`、\`fringe\`、\`torso\`、\`skirt\` **16 个透明 RGBA PNG** 是真实单独导出的图像（Actions Artifact 中），不像过去只是一张共享渐变纹理；检查 PNG 大小、Alpha 透明边缘、中心不透明、角度内容与 SHA 不全相同。
3. 使用每 Part 四个 key-contour 的稳定语义顶点 ID；**UV 从 key0 定义，独立于变形后的屏幕坐标**，防止纹理随角度滑动。头部视角与身体/手臂局部观察方向可以各不相同。
4. WebGL 自定义 shader 在同一部件 UV 域中采样相邻两张透明原画，并根据视角权重转换；透明片元按阈值 discard，保留深度测试。原有骨骼 IK、VDD/anchor、动态遮挡、表情、手臂跨越躯干与移动光照均保留。
5. 眨眼改为 eye ArtMesh 顶点几何压缩，不再只通过整层 alpha 消失；删除此前额外生成的重复眼睛多边形。
6. 每帧重复生成的网格和临时材质得到销毁，纹理 atlas 作为共享缓存保持。

### 真实成功证据

- [GitHub Actions #41193491555 — success](https://github.com/tims-SP/koma-motion-lab/actions/runs/41193491555)
- [Owner-only Draft Release with 6s MP4, actual contact sheet, per-frame stats and QA JSON](https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-a480696722d1ce6ffce6)
- [integrated-6sec.mp4](https://github.com/tims-SP/koma-motion-lab/releases/download/untagged-a480696722d1ce6ffce6/integrated-6sec.mp4) (202,167 B)
- [integrated-contact.png](https://github.com/tims-SP/koma-motion-lab/releases/download/untagged-a480696722d1ce6ffce6/integrated-contact.png)
- [Actions Artifact #13039093464](https://github.com/tims-SP/koma-motion-lab/actions/runs/41193491555/artifacts/13039093464)（本轮 16 张 RGBA key PNG、三个 480×270 QA 截帧、视频、JSON）
- 144 帧帧率/视频尺寸/IK 误差、手臂 z 深度翻转、阴影变化、角度采样和眼部形变均通过此前合约。
- 原有 MVP-003 视频（未接入真实分角贴图）只有 152,569 B，新视频编码为 202,167 B。**文件大小变化不能当画质分数**。

### 实际人工查看 frame 12 / 87 / 114

- 渲染时真正能看到不同颜色/描边的头发、脸部、胸衣、裙褶、围巾；显式打断了从单一 shared gradient texture 伪装成分角原画的旧实现。
- **仍不合格**：眼睛出现白色横条状造型，头发/脸轮廓在侧向显得尖硬，衣袖与手的几何连接生硬，后方/侧向图层未达到动漫原画表现。
- 三帧人工抽检不能证明全部 144 帧视觉完美；完整视频需继续由用户验收。
- 该阶段生成的是**小型原创 Canvas 绘制的矢量化图层**，不是 AI/画师制作的正式高精度多角度原画；虽然确实走真实 RGBA 纹理 + 稳定 UV 管线，仍不能称作高质量日本动漫人物生产技术成功。
- 270° 从 90° 轮廓派生并微调，虽然其 RGBA 绘图单独生成，但不是对不对称人物独立美术绘制的左侧原画。
- Mesh 是固定语义轮廓顶点 + 扇形三角剖分，尚未处理复杂 topology split/merge、多层剪裁网格、ARAP 或在内容跨角度差异很大时的视觉重影问题。当前两贴图颜色插值只对已对齐语义的简单贴图成立。

## 用户目标与接下来的唯一主线

用户最终要高质量日本动漫外观，重心是艺术资产质量与视角注册。**不要再通过额外基础算法验证争取“成功率”。**

下一任务应为 **MVP-005 · 多角度高质量分层原画替换**：

1. 为现有同一人物制作/引入真实画质比当前高得多的 0°/90°/180°/270° 人物 reference art（不再扩展骨骼 SDK）。
2. 只把最容易穿帮的四类：face、eyes、fringe/backHair、torso/skirt 抽取为**真正不同角度、同语义 ID、带 Alpha 的独立 PNG/SVG 图层**；保留详细线条/色彩，与当前 Canvas key 资产并排显示。优先修改脸和眼睛条纹问题。
3. 使用同一固定 UV/semantic landmark schema 校准并导入真实源画，错误匹配时补补图/局部遮挡过渡；不能以全身 alpha 交叉淡入淡出替代 mesh 变形。
4. 不重复构建 6 个模块：仅替换素材引入器和必要的网格局部修形，**只重渲染同一条 6 秒视频**并检查 0/45/90/135/180/225/270/315° 与交叉手臂帧。
5. 记录最差视角的真实图像质量、额外修正的部件数及人工工作量；如渲染数据正确但造型失败，应判 \`VISUAL_FAIL\` 并指向具体部件和角度。

## 代码

- [原画 TS 自动绘制和 RGBA 源图导出](../../experiments/mvp002/src/rgba-view-art.ts)
- [主统一引擎：registered UV + multi-image shader + VDD/IK](../../experiments/mvp002/src/integrated.ts)
- [端到端渲染和 16 个 PNG 验证](../../experiments/mvp002/scripts/render-integrated.ts)
- [CI](../../.github/workflows/mvp003-six-modules.yml)

**该项目研究阶段无需商业分发；如果未来以复杂游戏素材替换，必须核实使用和再分发条款，并避免第三方图像进入公有制品。**

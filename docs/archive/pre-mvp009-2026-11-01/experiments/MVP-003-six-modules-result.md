# MVP-003 · 按六模块单镜头流程完成的实际验证（2026-10-31）

## 结论

**PASS_ENGINEERING_ONLY / VISUAL_QUALITY_NOT_ACCEPTED**。

与此前的 K0/K1/K2 和三条分开拍摄的视频不同，MVP-003 用**一个原创极简角色**、**同一 TypeScript evaluator**、**一条 6 秒完整视频**联通以下机制：
3D bone/anchor → view-space yaw → keyed VDD position/contour → part ArtMesh/UV → 3D two-link arm IK → real depth occlusion transition → art-authored shadow/light and blink → Chromium WebGL2 → MP4。

- [本次 GitHub Actions 成功运行 #41192559514](https://github.com/tims-SP/koma-motion-lab/actions/runs/41192559514)
- [视频与报告（GitHub Draft Release，仓库有权限的用户可访问）](https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-1950b50997738b4e881f)
- [动作完整视频 integrated-6sec.mp4](https://github.com/tims-SP/koma-motion-lab/releases/download/untagged-1950b50997738b4e881f/integrated-6sec.mp4)
- [实际 15 帧拼图 integrated-contact.png](https://github.com/tims-SP/koma-motion-lab/releases/download/untagged-1950b50997738b4e881f/integrated-contact.png)
- [Actions Artifact #13038944807](https://github.com/tims-SP/koma-motion-lab/actions/runs/41192559514/artifacts/13038944807)（20 天保留）
- [源码](../../experiments/mvp002/src/integrated.ts) / [逐帧视频脚本](../../experiments/mvp002/scripts/render-integrated.ts) / [Actions workflow](../../.github/workflows/mvp003-six-modules.yml)。

## 验证素材与明确的技术边界

- 1 个原创简笔动漫风格代理角色，不导入《重返未来：1999》，因为跨视角外观对应需要先建立。
- 正面 0°、右侧 90°、背面 180° 三个**显式人工定义的部件形状**，270° 用镜像右侧临时模拟，**不能证明真实动漫左侧的非对称造型**。
- 12 个语义部件：backHair, torso, skirt, face, fringe, eyes, scarf, emblem, leftArm, rightArm, leftLeg, rightLeg。还会创建若干独立 Mesh 用于关节段/阴影/粒子。
- key-contour 每 Part 顶点对应 + 视角变化顶点内插 + Canvas RGBA 纹理 UV；**不是生产级多张 PNG/SVG 图层的纹理重采样和连续对应**。
- 3D anchor 和世界姿势坐标、头部局部观察方向、右臂 full XYZ 双骨 IK。左手/腿是简化动画，**没有完整 3D 全身 Skeleton/脚部锁定**。
- 动态遮挡是实际 3D 深度缓冲和跟随 IK 姿势的局部覆盖；**暂未实现 Live2D 式通用透明裁剪 mask、复杂交叉 alpha**。
- 法线贴图和阴影几何还不是研究级 full 2.5D Normal-map Shading；当前为**有方向变化的画师阴影遮罩**和前后景简单特效，避免用 PBR 破坏画风。
- 没有实现 ARAP；这是质量修复算法，不是完整闭环的前提。

## 单镜头段落

| 时间（秒） | 发生什么 | 必看现象 |
|---|---|---|
| 0.0—2.0 | 同一角色原地 Yaw 0°→360° | 正、侧、背视角及 0/360 接缝 |
| 2.0—3.4 | 抬手、3D IK 伸向躯干左侧 | 关节位置变化，手先在身体后面 |
| 3.1—4.2 | 手部深度从负 z 向正 z 穿越躯干 | 手在交叉处的遮挡顺序切换，而不是全身 Sprite 变更 |
| 2.0—6.0 | 头部局部观察方向与躯干分离，面部轻动 | 头转动时眼睛/刘海显示、局部网格调整 |
| 3.5—6.0 | 光源方向变化、面部阴影与局部投影改变、粒子、眨眼 | 可见光影及网格压缩，不用 alpha 消失冒充眨眼 |

## 实际 CI 结果（同一次 GitHub Action）

- \`npm run typecheck\`：通过。
- 真 Chromium/WebGL 逐帧求值/截图：**144 帧 × 24fps / 6 秒**，每帧角色 12 个语义部件状态。
- \`ffprobe\` 校验：**960×540 H.264 / 144 解码帧**。
- MP4 实际大小：**152,569 B**。
- 3D arm IK 最大终端误差：\`2.220446049250313e-16\` 模型坐标单位（仅该动作轨迹，并非复杂姿势泛化）。
- frame 82 手相对躯干深度：\`-0.34283885688844407\`，在后侧。
- frame 110 手相对躯干深度：\`+0.68\`，在前侧。
- 原画阴影控制位移跨度：\`0.35342649419749844\` 模型单位。
- 面部眨眼参数激活；\`eyes\` ArtMesh 实施局部 y 顶点压缩（非简单将 alpha 归零）。
- Release 含 15 个实际视频采样的拼图、完整逐帧状态 JSON、三张 QA JPEG。
- 通过 CI 不等于“复杂遮挡视觉绝对正确”或“动漫画质已达到目标”。

## 真实视觉抽检

从 GitHub Actions 的 **frame 12 / 87 / 114** 真实截图提取了三个 480×270 JPEG 并检查：
- 正侧过渡人物站姿可见，脸部/后发/裙装都有非零厚度的视角外形变化；非整身贴图切换。
- 抬手后的上臂和前臂可见；透明背景和躯干材质没有大面积丢失。
- 简化轮廓显得僵硬，脸部/眼睛是简笔技术素材，缺少真正高保真的线条与衣服纹理；还不能评价为合格的日本动漫质量。
- 仅三张人工抽检截图**不足以证明完整 360 连续视觉品质和所有前后遮挡帧都无瑕疵**。完整视频需由仓库所有者观看/验收。

## 核心工程判断与正确下一步

1. **六个能力在同一枚角色求值器上的基础组合已有实际证据**。不再重复单独复现 Spine、Cubism、2010 论文等成熟基础功能，也不用复杂游戏原画重新开一个技术样机。
2. 当前弱项来自**画质数据表示**而不是 MP4/浏览器。下轮应直接把本工程的简单 CanvasTexture + fan-mesh 替换为 8—12 块小尺寸但真正高质量的 RGBA/SVG 分层原画，保留统一 schema、3D anchor、bone/IK 和 render 函数；先在实际同一条视频中提升轮廓和遮挡。
3. 之后才需要高质量多视角对应关系、局部 occlusion masks、art-directed normals、关键 pose correction。优先改缺陷处，避免为了导入商业角色打造大规模转换器。
4. 为节省 CI 费用，旧 MVP-002 自动三片工作流已改为 \`workflow_dispatch\` 手动运行，新的 MVP-003 每次仅运行**同一个一镜到底视频**。

**最终 MVP 质量结论：尚未通过。** 目前确认的是最小集成技术链路在指定简化输入下可运行；下一道关键门槛是引入真实连续的多视角原画皮肤后还能保真。

# MVP-007 · 360° 核心三项修复、完整验收与视觉复核（2026-10-31）

## 最新权威结果

**S01—S08：8 PASS / 0 FAIL / 0 BLOCKED**，技术级验收已通过。

- [最终 GitHub Actions #41200083182](https://github.com/tims-SP/koma-motion-lab/actions/runs/41200083182) — CI success。
- [完整实际证据：8s MP4、25 角度图板、关键邻帧、深度/Part-ID/Mask、逐帧 JSON 和 QA 报告](https://github.com/tims-SP/koma-motion-lab/actions/runs/41200083182/artifacts/13042725038)（20 天保留）。
- 同一套 TypeScript + Three.js 简化原创角色，同一 evaluator，一段固定姿态水平 360°（**192 帧 / 24 fps / 960×540**），未更换复杂游戏素材或重复 Spine/Cubism 功能性试验。
- 自动 \`coreStatus=PASS_STRUCTURE_PENDING_VISUAL\` 仍保持（不能在 CI 里冒充人工/模型审查完成）。本报告记录了在 ChatGPT 会话中进行的**实际截图模型复核**，但**未有用户对整段 MP4 的人工放行**。
- 此阶段不是高保真二维原画生产级模型，也不能证明任意姿势/俯仰角 360° 可用。**不可将“固定简化角色技术闭环”扩大解释为“高质量动漫 360° 已解决”。**

## 三个核心缺口的真实修复

### S07：独立 270° 部件视角

[\`src/left-keyviews.ts\`](../../experiments/mvp002/src/left-keyviews.ts) 定义 12 个部件各自独立的左侧 270° 语义轮廓与 VDD 偏移；不再在 \`patch()\` 内直接 \`mirror(rightSide)\`。另以固定语义顶点对应表使左侧轮廓与另外三个方向**相同 winding/landmark 序**，防止关键形状间 morph 面积翻转。脚本检查源数据内容不同，并检测非对称胸章在右、左侧的投影位置。仍属极简参考造型，不等同专业独立侧背原画。

### S03：真实骨骼局部／3D Anchor／VDD

[\`src/integrated.ts\`](../../experiments/mvp002/src/integrated.ts) 与 [\`src/qa/turn360-runtime.ts\`](../../experiments/mvp002/src/qa/turn360-runtime.ts) 记录真实当前求值的 \`boneLocalAnchorXYZ, boneWorldMatrix, worldAnchorXYZ, cameraViewMatrix, cameraProjectionMatrix, vddOffsetXY\`。在 Node 端独立矩阵运算核验每个可见部件：
- \`maxAnchorAudit=3.10e-17\` 模型单位
- \`maxProjectionAudit=0\` 像素
- \`maxDeformationAudit=5.68e-14\` 像素

修正了腿部绑定位置的两个真实数值不匹配；右前臂由 IK 链真实生成变换矩阵。不代表全身完整约束骨骼已达生产级。

### S06：实际重叠、深度与遮挡

[\`src/qa/occlusion-audit.ts\`](../../experiments/mvp002/src/qa/occlusion-audit.ts) 在当前相机下分别渲染每个目标 Part 的独立 alpha mask，再读取最终合成的真实 Part-ID 像素，对比眼/脸、刘海/脸、脸/后发、手臂/躯干的交叉区域。0°、15°、180°、345° 规定的 13 组约束全部拥有非零重叠样本且未检测到错误后层像素。右臂 IK 弯曲参考向量改为随躯干旋转，修复背面错误前压躯干。

此 S06 只证明**已定义的 13 个局部约束样本**，尚不涵盖复杂长发／透明服饰／任意关节姿态和互相穿插。

## 视觉验收发现并真正修复的两个额外核心问题

### 问题 A：225°／315° 人物整身塌缩

在第一版 S01—S08 全绿之后，实际查看 25 个角度图板仍发现 225°、315° 角色塌成细线。根因是独立 270° 轮廓顶点 winding 与其他视角相反，常规“顶点有限 + 相邻帧中心位移”不能发现。已：
- 修正跨视角语义顶点对应顺序。
- 把轮廓**有向面积翻面／相对面积异常缩小**加入 S04。最终最小面积比例 \`0.72526\`，\`flippedOrCollapsed=[]\`。
- 重新检查 25 方向图，225° 与 315° 全身轮廓恢复正常。

### 问题 B：90°／270° 面部与后发跳层、后侧鬼脸

实际检查连续 6 帧条带发现 90→91.875° 与 268→270° 左右整块面部可见性突然变化。根因：面部/后发透明网格在侧视时 Z 深度相等，依赖普通透明排序导致瞬间翻层。已：
- 把 face/fringe/eyes 作为明确的 front-art compositing 图层控制，并让 QA ID pass 保留与真正 beauty pass 相同的 depth 策略。
- 对 90→110° 与 250→270° 使用显式平滑可见性窗口，在后侧 135°/225° 完全隐藏正面五官，清除后脑出现的半透明灰色鬼脸。
- 将真实解码 MP4 的连续帧灰度差峰值 / 中位数纳入 S05（静相机、静姿势、静灯光限定场景，阈值 2.5）。
- 最终 \`medianTemporalDiff=0.86017\`，\`peakTemporalDiff=1.45744\`，\`temporalSpikeRatio=1.69437\`，无高峰超限；90°/270° 周围 6 连帧条带已经实际查看，未再见整块跳层。

## 最终八项机器门禁

| 门禁 | 最终结果 |
|---|---|
| S01 真实旋转角度覆盖 | PASS |
| S02 独立 0°/360° 图像周期一致性 | PASS |
| S03 Anchor/Bone/Camera/VDD 独立重算 | PASS |
| S04 ArtMesh/UV/有向面积/塌缩 | PASS |
| S05 顶点连续 + 全视频帧差异常扫描 | PASS |
| S06 实际 alpha-mask 与合成的 13 组遮挡约束 | PASS（此测试集合） |
| S07 左右独立关键几何 + 胸章方向 | PASS（此原型） |
| S08 192 帧完整性/实际 bbox 无裁切 | PASS |

机器数据：\`192 frames\`，\`25 angle samples\`，\`8 ±1° boundary samples\`，\`2062 part traces\`，\`maxVertexJump=0.021603\`，\`minimumAreaRatio=0.725262\`，\`seamEqual=true\`，\`screenBoundsOkay=true\`。

## 抽帧视觉审核范围与尚未放行的事项

已在模型端读取**最终 Actions Artifact 的真实 \`angle-board.png\`（25 个角度）、\`detail-board.png\`（45/135/225/315 + ID/depth）**；并用最终 MP4 实际解码生成 90°、270° 的 6 连帧局部图带查看。它们清楚显示此前塌缩、突变及后脑鬼脸被修复。

当前仅可判定：**简化静态站姿 360° 核心在既定输入和检测集下具备工程运行闭环，模型抽帧未发现残余 P0/P1**。不能宣称：
- 由真实高质量四视角原画完成的画质验收；
- 人物全部关节动作+任意视角的动态遮挡和肢体空间保真；
- 相机 pitch/roll、近景手绘细节的稳定 360°；
- 完整人体 IK/脚步锁定、头发网格互穿消除；
- 用户已在播放器观看并正式接受完整 MP4。

为避免把结构化绿灯等同视觉放行，机器 JSON 状态保持 \`PASS_STRUCTURE_PENDING_VISUAL\`；本报告是**模型抽帧复核已完成、人工视频验收待用户确认**，不是用户确认的 \`PASS_360_CORE\`。

## 下一阶段建议（不重开基础技术实验）

固定并冻结这个成功的静态 360 工程，进入**同一个角色上的“旋转同时抬手、前后穿越躯干、头部独立转向”联合动态试验**。只新增动画复合参数与姿态依赖 VDD/occlusion constraints、全身足部锁定必要的骨架约束；保持完全相同的 ID/depth/beauty/trace 和视觉验收标准。不要首先导入复杂游戏资产、不要继续程序化细节绘画。

# MVP-006 · 360° 核心正式验收运行与修复记录

Date: 2026-10-31
**总判定：FAIL_STRUCTURE，绝不声称 360° 已通过。**

唯一验收规范：[MVP-006-360-acceptance-v1.md](./MVP-006-360-acceptance-v1.md)。

## 工程提交

- \`experiments/mvp002/src/qa/turn360-contract.ts\`：S01—S08 分级、PartTrace、FrameTrace、问题结构。
- \`experiments/mvp002/src/qa/turn360-runtime.ts\`：读取运行时真正渲染的 ArtMesh 顶点、UV、VDD、角度、部件 ID 和深度。
- \`experiments/mvp002/src/integrated.ts\`：沿用原 TypeScript/Three.js 角色，新增固定姿势、固定相机/灯光的 360° 求值与真正 WebGL render-target ID/depth/mask。
- \`experiments/mvp002/scripts/render-turn360.ts\`：8 s / 192 帧 / 24 fps 视频，0—360° 独立循环等价比较、25 角度板、8 个边界±1°图像、结构化硬门禁；业务 FAIL 仍上传证据。
- \`.github/workflows/mvp006-360-acceptance.yml\`：单次 CI 完整工程+质量证据，保存 20 天。
- 旧 MVP003 自动三视频任务改为 manual-only，避免重复收费。

## 第一次完整运行（证据存在）

[GitHub Actions #41197300471 — CI SUCCESS / CORE FAIL_STRUCTURE](https://github.com/tims-SP/koma-motion-lab/actions/runs/41197300471)
[Video / real ID/depth diagnostic images / 25-angle board / trace ZIP](https://github.com/tims-SP/koma-motion-lab/actions/runs/41197300471/artifacts/13041470598)

机器摘要（来自该次 Actions 输出）：
- 视频编码 192 帧成功；8 秒/24 fps/960×540。
- 单次 360 角度覆盖 + 0/360 独立 PNG 完全相同。
- 2262 份真实 Drawn-Part Trace；192/192 帧 ID pass 中记录到 >=4 个可见部件。
- \`maxAnchorJump=0.01867807637990199\` 模型单位；本轮加上 per-vertex jump 检查。
- S01=PASS, S02=PASS, S03=BLOCKED, S04=PASS, S05=PASS, S06=BLOCKED, S07=FAIL, S08=FAIL。
- **S07 FAIL**：12 部件的 270° 形状继承 90° 镜像，缺少独立视角设计。
- **S03 BLOCKED**：回传数据仍是投影后位置，缺少可独立复算的原始绑定 anchor + bone/world/view transform 证据。
- **S06 BLOCKED**：存在实际 ID mask / WebGL 深度读取，但是没有前后/发丝/眼部的具体局部遮挡约束表与关联测试。
- **S08 旧版 FAIL 为验收器误判**：Node 拿到的是浏览器 readback 更新前的 placeholder bounds。模型是否裁切不能由这个旧值判断；已修复跨进程数据读取，新增逐帧真实 mask bbox 判定。

## 修正运行

[Actions #41197555224](https://github.com/tims-SP/koma-motion-lab/actions/runs/41197555224)

变更：导出 ID readback 的真实 pixel bbox 到 Node 侧，删除旧的占位包围盒假阳性；检查真实 ArtMesh 相邻帧逐顶点跳变，而不仅是 anchor。

在新的 CI 全面完成前，**不能推断 S08、新视频或视觉质量通过**。无论 S08 是否通过，S03/S06/S07 已知仍存在，整体 360 核心仍 FAIL_STRUCTURE。

## 下一项核心研发（不是再次写测试）

1. **S07**：去掉镜像 270°，对 12 个部件定义真实独立的左侧关键形状与左右语义；侧面、背面都应处理好非对称胸章、眼睛、发束，必须先有数据资产。
2. **S03**：bone-local anchor / world transform / projection / VDD 单独输出，验证 \`p=project(R·A)+D(view)\`，不要将 worldAnchor 伪装为 project result。
3. **S06**：针对刘海-脸、后发-颈、袖-手/身体实现明确 occlusion constraints + clip/ID mask 的可复核实际图像，与 depthBuffer 一起使用。
4. 用当前 8 秒视频与 25-angle contact board 对上述修改作一轮复验；审查 S01—S08 后再视觉审查，未通过不放行。

禁令：不再投入程序化画风打磨、新人物生成/复杂游戏资产导入/独立 Spine/Cubism 基础复现实验作为这三个核心缺口的前置。


## 最终修复后验收（本轮权威结果）

**[GitHub Actions #41197555224：流水线 SUCCESS，角色核心 FAIL_STRUCTURE](https://github.com/tims-SP/koma-motion-lab/actions/runs/41197555224)**

**[MVP-006 验收证据：MP4、25 角度图板、真实 ID/深度/Alpha 遮罩、逐帧 Trace、机器 QA 报告](https://github.com/tims-SP/koma-motion-lab/actions/runs/41197555224/artifacts/13041610450)**

最新真实数据：
- 8 秒 H.264 视频，192 帧、960×540，视频大小 369,866 字节。
- 25 个独立角度（0°~360°），8 张关键方向±1°照片；0° 和 360° 在相同姿势/光照/相机下 PNG 完全一致。
- 2,262 份实际可见的分部件网格 Trace，192/192 帧有真实 Part-ID pass。
- 同帧最大部件中心位移 \`0.018678\` 模型单位；相邻帧最大顶点位移 \`0.034569\` 模型单位；真实 ID-mask 包围盒检测 **screenBoundsOkay=true**，证实旧 S08 是 Node/浏览器之间的同步误报。
- 最终硬门禁：**5 PASS / 2 BLOCKED / 1 FAIL**。

| 检查 | 实际结果 | 下一步 |
|---|---|---|
| S01 角度覆盖 | PASS | 保留 |
| S02 0/360 接缝 | PASS | 保留 |
| S03 3D Anchor / VDD | BLOCKED | 显式输出 source local anchor、world bone matrices、projected 2D 与独立复算的 corrective |
| S04 Mesh / UV / topology | PASS（当前简单 Fan-Mesh 范围） | 不代表复杂 topology 无误 |
| S05 轨迹/顶点连续 | PASS（数值范围） | 不代表角色外形天然好看 |
| S06 真实遮挡 | BLOCKED | 建立头发/脸/眼睛/手臂约束表和局部 mask 证据 |
| S07 不对称与独立视角 | FAIL | 将所有 Part 的 270° 侧面从自动镜像改为独立左侧关键视角 |
| S08 帧数/画面包围盒 | PASS | 旧误报已修复 |

**最终结果仍然是 \`FAIL_STRUCTURE\`，不是 \`PASS_360_CORE\`。** 这一次不要继续补画程序化角色或重新复现 Spine/Live2D。应直接针对 S07→S03→S06 修正**核心数据与渲染机制**，继续用同一套验收器复验。结构正式通过后，才交由视觉模型阅读两张真实图板、重点连续帧和完整 MP4，再判 \`PASS_360_CORE\`。

由于 S03/S06/S07 尚未过门禁，未启动正式视觉模型放行审查；这不会省略后续必须进行的实际画面检查。

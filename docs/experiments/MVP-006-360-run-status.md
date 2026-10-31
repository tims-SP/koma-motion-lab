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

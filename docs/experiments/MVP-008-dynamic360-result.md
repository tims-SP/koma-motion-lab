# MVP-008 · 动态 360° 同一角色联合动作 — 工程实测记录

**日期：2026-10-31｜技术栈 TypeScript + Three.js/WebGL2**

## 与 MVP-007 的差异

这不是先旋转后播放手臂动画，也不是换模型：一个 12 语义部件角色在同一个 8 秒镜头内以 24 FPS 走完 Yaw 0→360°，同时间连续运行头部局部 yaw、VDD/UV ArtMesh、右臂两段 3D IK、目标手从躯干背面到正面、简化膝关节活动和固定相机灯光。

逻辑位于 [同一 evaluator](../../experiments/mvp002/src/integrated.ts) 的 \`renderDynamic360\`，没有新建第二套角色渲染器。

## 首次真实工程视频和数据

- [GitHub Actions #41202693389](https://github.com/tims-SP/koma-motion-lab/actions/runs/41202693389)：success。
- [完整 8s MP4、16 角度图板、逐帧几何和遮挡 ID/depth pass](https://github.com/tims-SP/koma-motion-lab/actions/runs/41202693389/artifacts/13042958958)。
- [Draft Release 预览（后续阴影修复前的历史版本）](https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-b35bea0537141043a6d4)。

首次真实结果 D01—D09：全部 PASS，状态是 **PASS_STRUCTURE_PENDING_VISUAL**，不是最终视觉 PASS。

| 检查 | 结果/具体证据 |
|---|---|
| D01 全周旋转同时动作 | 192 帧、360°、960×540 |
| D02 同姿势 0/360 接缝 | PNG 完全一致 |
| D03 头部局部 yaw | 变化范围 51.998° |
| D04 右臂三维 IK | max endpoint error 2.22e-16；手部世界空间行程 2.003 |
| D05 躯干局部前后穿越 | 手部 Local-Z = −0.60→+0.68 |
| D06 双脚纵向 | Y 误差 0，但不能证明脚步锁定和零滑移 |
| D07 动态锚点矩阵 | max bone 3.10e-17；max camera project 0px |
| D08 mesh/视频完整 | 192/192 帧边界有效，无非有限几何/UV |
| D09 时间像素异常 | 峰值/中位帧差 2.083，阈值 3.2 |

## 独立姿态遮挡实测

为了避免为 6 组姿态重新编码整个 192 帧，增加 [focused pixel audit](../../experiments/mvp002/scripts/audit-dynamic-occlusion.ts)：

- [CI #41203063274](https://github.com/tims-SP/koma-motion-lab/actions/runs/41203063274)：success。
- [真实动态遮挡和 PNG 复核 Artifact](https://github.com/tims-SP/koma-motion-lab/actions/runs/41203063274/artifacts/13043485305)。
- 10 个有效重叠约束（眼/脸、刘海/脸、脸/后发、双臂/躯干），**0 错误、0 无法判定**。
- 世界正面与背面的同一动画时刻，手在角色**局部** +0.68 深度；实际遮挡图分别显示合理的前后层级。
- 90°/180° 的正面五官按局部观察方向退出可见区，没有幽灵五官可见像素。
- **限定结论**：只覆盖选定姿态、角度、部件约束，尚未验证任意全身动作和所有透明细节。

## 实际视觉模型读取真实图片的发现

从同一 GitHub Actions 视频提取了 16 角度板及 frame 42/90/144 的 JPEG，逐张检查（不是依赖 AI 概念图）：

- 正、侧、背、另一侧确实属于同一个人物，一条 8 秒镜头；动作与旋转同时发生。
- 约 79° 的头部存在灰色楔形鬼影；排查发现面部 Alpha 已渐隐，脸部/发丝投影阴影的绘制强度却没有同步减少。因此遮挡 ID pass 会绿，但实际 Beauty pass 仍有多余像素。
- 270° 附近手臂缩短、脸部轮廓硬折、脚部动作仍然僵硬，后续必须单独解决部件局部平面/形变，不应当靠美术精度掩盖。
- 已在 \`src/integrated.ts\` 中**将面部阴影强度乘以真实 face visibility**，并为专项 MP4 增加 **D11_VIEW_DEPENDENT_FACE_SHADOW** 硬门禁。

## 当前严格状态与后续任务

**MVP-008 最新阴影修正后视频**：以 [新 Actions #41203392024](https://github.com/tims-SP/koma-motion-lab/actions/runs/41203392024) 结果为准。上面 41202693389 链接是修正前**历史版本**，不能被用作最终修复通过证据。

保留动态-360 视频结构通过的初步结论，但**高质量动漫人物、任意视角×动作、脚步无滑移、复杂头发/手部多层遮挡仍未通过**。下一阶段优先给躯干与前臂添加适配视角的独立形状／遮罩与实际交叉采样，不先扩大美术资产规模。

所有本轮视频存 GitHub Actions Artifact / Draft Release，git 仓库只存代码与文档。


## 动态裁剪的后续真实视觉问题（不能隐瞒）

- [局部 UV 裁剪版实际 192 帧 #41203880305](https://github.com/tims-SP/koma-motion-lab/actions/runs/41203880305) 机器十项全 PASS，但视频连续帧扫描峰值/中位数上升至 **2.9556**（原影子同步版为 1.8044）。
- [真实抽帧、动态遮挡复验 #41204162688](https://github.com/tims-SP/koma-motion-lab/actions/runs/41204162688) 输出 frame 42 及 frame 130—134：79° 侧脸的灰色半透明背景明显降低；**帧 130 左方出现脱离头部的细线，131—132 才逐步出现面部轮廓**，这是实际 P1，不因 D09 阈值勉强通过而视为合格。
- 根因：靠近 250—270° 的面部裁剪先揭露错误的远端 UV 边缘，导致最先显示的皮肤/刘海碎片离开后发轮廓。
- 已在 \`src/integrated.ts\` 统一改为**从与后发相邻的 UV 边缘开始揭露**，修复提交 \`0787416\`，最新完整验收 [#41204371527](https://github.com/tims-SP/koma-motion-lab/actions/runs/41204371527)。新结果未完成之前，动态 360 的视觉状态保持 **FAIL_VISUAL / NOT_ACCEPTED**。

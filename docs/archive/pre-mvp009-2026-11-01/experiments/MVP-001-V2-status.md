# MVP-001 V2 · 唯一状态记录（2026-10-31）

**LATEST MASTER PLAN**: [MVP-001-V2-master-plan.md](./MVP-001-V2-master-plan.md)

## 总体判定

- V2 新方案：**PLANNED**。
- M0 (旧 JS/Three.js 程序化夹具)：**PASS_ENGINEERING_INFRA_ONLY**，证据 [Actions 41188109729](https://github.com/tims-SP/koma-motion-lab/actions/runs/41188109729)，不能视作实际动漫 360 画质通过。
- V2 TypeScript 迁移：**NOT_STARTED**。
- 资产原始运行时参考视频：**NOT_STARTED**。
- K1 多视角高画质头肩 0°→90°：**NOT_STARTED**。
- K2 同角色骨骼 + VDD + 表情/阴影协同：**NOT_STARTED**。
- A 水平全身 360°：**NOT_STARTED**。
- B 全身动作+IK：**NOT_STARTED**。
- C 高保真人物/光影：**NOT_STARTED**。
- 整体 M1/M2/M3 联合视觉验收：**NOT_STARTED**。

## Task board

| Task | 状态 | 工程证据 | 视觉证据 |
|---|---|---|---|
| T00 TS 迁移 M0 parity | NOT_STARTED | — | — |
| T01 现有素材普查与覆盖矩阵 | NOT_STARTED | — | — |
| T02 官方源参考渲染与算法样例 | NOT_STARTED | — | — |
| T03 最终角色选择/跨资源语义映射 | NOT_STARTED | — | — |
| T04 IR schema + 源数据导入 | NOT_STARTED | — | — |
| T05 K1 头肩 0°→90° | NOT_STARTED | — | — |
| T06 K2 骨骼/表情/VDD 协同 | NOT_STARTED | — | — |
| T07 全身视角补齐与多视角插值 | NOT_STARTED | — | — |
| T08 A：360 视频 | NOT_STARTED | — | — |
| T09 B：全身动作 | NOT_STARTED | — | — |
| T10 C：高保真特效 | NOT_STARTED | — | — |
| T11 三视频联合验收与成本决策 | NOT_STARTED | — | — |

## 工作制度

每完成 Task 必须写入：完成日期、输入文件/来源和 SHA、Git commit、GitHub Action Run、真实截图/视频 URI、工程 PASS/FAIL、视觉 PASS/FAIL、未解决问题及下一动作。不允许只凭流水线绿灯或 MP4 文件存在判定画质达标。不得把第三方原画或派生视频直接提交公共 Git。

## 立即执行入口

T00：`experiments/mvp001/src/main.js`、`scripts/smoke.mjs` → TypeScript；`tsc --noEmit`、截图/视频回归；保留旧测试验收依据。随后 T01 针对 `300401_hongnujian`、两名备用角色做有限范围下载和 TS 素材清单。

**本文件创建本身属于规划工作，不代表已经完成任一 T 项。**

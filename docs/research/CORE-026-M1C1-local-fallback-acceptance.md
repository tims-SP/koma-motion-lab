# CORE026 M1C1：本地兜底实现与接收提案验收

日期2026-10-31（Asia/Shanghai）。状态PASS_SOURCE_FACTS_AND_RECEIVER_PROPOSALS，本地与干净CI均通过。M1整体NOT_ACCEPTED、M2未开始，自然3D转头未验收。

## 实际归属与安全边界

mcode标准会话未产出实现；最后改用lightweight、permission off、独立目录且只输入通用公开schema，仍被自动审批以未知阿里云存储载荷拒绝。该提示不是网络请求抓包结果。没有继续重试或读取认证文件。为继续已授权任务，本轮由Codex本地编写提取器并执行验收；不冒称mcode实现、执行或提交。所有来源和渲染器保持原哈希，媒体不进git。

## 实际产物与边界

- extract_core026_constraints.py从原始INX、冻结合同、已验证默认配准和62张原始PNG重新推导数据，不读取监督报告作为生产输入；SHA/唯一UUID/图层范围/绑定数量均有检查。
- config/core026-constraints.json恰好62条，源事实与设计提案分开；19个独立曲面提案、43条接收映射、7条投影阴影caster，11Multiply、9默认阴影裁剪均保留。
- 源28/29/38/39的实际native_blend_mode为ClipToLower；它不自动证明新眼部遮罩已实现。
- 晚叠画58/59/60/61与实体头发交叠实际重算28/15/2156/1954像素，不能把它们无条件烘在头发下面的Face。
- 所有physical_depth、local_before_behind、local_mask仍UNKNOWN。设计status均为DESIGN_PROPOSAL_NOT_RENDER_VALIDATED，pose_scope=DEFAULT_ONLY。本轮没有实现接收面合成或转头渲染。
- 配置SHA256为2aefaa9ae0829dfe4bfb0e3d1708e037f4ec98fcc52c44e0b88d86b64ddeb482；构建不依赖当前git提交或时间。

## 实际命令与验收

在experiments/reference-factory执行以下命令，全部实际exit0：

```bash
python extract_core026_constraints.py --build
python extract_core026_constraints.py --verify
python verify_core026_m1c1_supervisor.py
python run_core026_m1c1_regressions.py
python audit_core026.py --audit
python audit_core026.py --verify-source
python verify_core026_supervisor.py
python verify_core026_registration.py
python verify_core026_constraints.py
python extract_core026_constraints.py --verify
```

监督检查从旧独立源观察器重建实际事实，逐字段比对62条记录和明确工单映射；通过范围是源事实/设计契约，不能代替渲染验收。JSON表示比较保留整数/浮点/布尔区别，避免ID类型混淆。10个保护文件、186张PNG及默认坐标继续通过。

回归程序从真实候选创建ignored out/中的孤立副本，不改原始配置或来源。以下9项都被生产验证器和监督验证器以exit11拒绝：

| 篡改 | 验证目标 |
|---|---|
| 互换两个有效native UUID，保留唯一性 | 身份对应，不能只查UUID存在 |
| 将Face投影阴影接收面改成caster | receiver与caster分开 |
| 删除眉60的late_paint | 保留晚叠画 |
| 将瞳孔ClipToLower改为Normal | 真实原生模式 |
| 伪造原始纹理SHA | 来源可追踪 |
| 将整数receiver改成同值浮点 | 严格ID类型 |
| 伪造晚叠画交叠数 | 实际alpha重算 |
| 宣称compositor已实现 | 不越级接受 |
| 伪造INX输入SHA | 输入出处 |

所有verify均不改候选；原始配置前后SHA不变；第二次build与提交候选逐字节相同。详细退出码与stdout尾部在out/core026/m1c1-regressions.json；受控摘要在evidence/core026-M1/constraints-local-acceptance.json。

## CI与下一门禁

已将新生产/监督/篡改检查接入koma-26-supervisor-qa.yml。CI先verify已提交配置，不能先build覆盖它；新增artifact仍仅JSON。

代码76d7f70951aab4ce358ef73b9095fcc01889d8cc的[监督CI41144806591/job124367323613](https://github.com/tims-SP/koma-motion-lab/actions/runs/41144806591)全部success：已提交配置SHA保持2aefaa9ae0829dfe4bfb0e3d1708e037f4ec98fcc52c44e0b88d86b64ddeb482；62条源事实、9组双验拒、重复构建和不改文件均真实通过。原生9图和9裁切SHA也全部核对，仍是既有原生2D参考，不是新的3D渲染结果。

同代码[旧工厂/视频回归41144806561/job124367323502](https://github.com/tims-SP/koma-motion-lab/actions/runs/41144806561)也全部success。JSON artifact13019339164为28996字节；[诊断媒体Draft](https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-8b4fe7fd1b5e4146569e)已创建成功。机器可读证据在evidence/core026-M1/constraints-ci-acceptance.json。最终文档检查点不改变这份已通过代码。

下一任务按CORE-026-M1C2-landmark-and-reference-order.md逐姿态确认19槽位的可用范围与可见性，并完成M1总验收；未知耳根、鼻根、颈连接等不补造。源阴影/层序表还不是运行时三维前后关系，M1放行后才实施M2并先过0°原画保真。

# 当前恢复入口

更新：2026-10-31（Asia/Shanghai）。仓库tims-SP/koma-motion-lab，分支feature/koma-25d-core-021。mcode负责实现，Codex下达明确工单并独立验收；每完成一段提交保存。生产仓库koma-motion未改。

## CORE026当前状态

仍在M1，整体NOT_ACCEPTED；M2–M5未开始，自然3D转头未通过。不要把源审计、截图捕获或候选跟踪通过当作深度/动态遮挡已经修好。[完整证据与阻塞](research/CORE-026-M1-clean-reference-and-remaining-gates.md)。

- 源审计a6226cc：62层中58个通过独立alpha/预乘像素对应；7/8/9/10是同图重复项，像素审计如实保持UNRESOLVED。
- 默认坐标03ad67a：用原始UV、纹理尺寸和原生祖先变换区分这4项，62个selected_uuid全部唯一。只使用一个全局平移；唯一纹理最大残差3.905124源像素。没有改原始UV，也没有验收GPU动态或三维深度。
- 清洁原生801d904：[原生CI41119224557](https://github.com/tims-SP/koma-motion-lab/actions/runs/41119224557)全部success。9姿态raw yaw=-1..+1、pitch0，固定720×880 framebuffer及652×652头部裁切；已关闭X11指针。参数未标定为物理角度。
- [原生媒体Draft](https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-2589bc212d17274d3503)真实归档；9原图和9裁切SHA全部独立核对。头部/耳尖顶部至少12像素余量。
- 62条源祖先/模式/绑定已检查：11Multiply、9默认阴影裁剪；眼皮58/59与实体头发重叠28/15像素，眉60/61重叠2156/1954像素。这是默认美术叠画事实，不能直接当三维深度。
- 19标点槽位：13源支持候选（含4眼白边界代理）、6未知。嘴角raw边界在合成中被Lip遮住，已拒绝。NCC只作诊断，所有点fit_eligible=false。
- 监督恢复代码5f9aef8：[干净环境CI41126811519](https://github.com/tims-SP/koma-motion-lab/actions/runs/41126811519)全部success。真实重建旧17图保护报告，复验源数据、坐标与叠画，恢复固定原生job的实际PNG并核对18张SHA，再复现候选数4/5/6/11/13/9/7/6/4。
- 同代码的旧回归[CI41126811438](https://github.com/tims-SP/koma-motion-lab/actions/runs/41126811438)也已真实success；两套CI的通过范围保持区分。
- [监督诊断媒体Draft](https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-270a8f25943b4d8f5dd0)已归档；Actions artifact只JSON，媒体不进git或artifact。[机器可读验收](../experiments/reference-factory/evidence/core026-M1/supervisor-recovery-ci-acceptance.json)。

## 下一工单与实际阻塞

[CORE-026-M1C1精确工单](plans/CORE-026-M1C1-constraints-order.md)：实现extract_core026_constraints.py与config/core026-constraints.json；明确62条记录的源事实/设计提案字段、接收/投影阴影/高光映射、晚叠画和UNKNOWN；按--build、--verify、独立对照及篡改验拒后提交。19标点人工复核仍是并列门禁，M1放行后才实施M2。

Work已恢复且本地仓库已同步。源像素/10保护文件/186PNG、62默认坐标、11Multiply/9clip及18张原生参考哈希均重新实测通过。监工查看了实际9姿态标点接触图与默认652×652图；19槽位的13图像候选仍有语义限制，所有点仍不自动具备拟合资格。[本轮实际记录](../experiments/reference-factory/evidence/core026-M1/supervisor-resume-and-reference-review.json)。

mcode首次启动exit3提示登录失效；已通过官方CN登录流程恢复，CLI实际返回Signed in with MiniMax、exit0。用户在agent.minimax.cn精确范围问题后回复继续，本轮按该范围启动任务；平台自动审批再次拒绝，理由是CLI还可能将项目上下文发送至agent.minimaxi.com，超出此前单域名范围。公开包代码确认CN模型接口为agent.minimax.cn，CN步骤报告接口使用agent.minimaxi.com。没有获得可验收实现文件，未在新拒绝后重试完整工作区任务。

当前剩余阻塞仅为两个官方服务域名的发送范围：本项目相关代码、任务文档及必要文本执行输出；排除凭据、登录文件和其他目录。当前不需要再次登录。此前服务500/超时、旧目的地审批与环境不可用均保留为历史，不与本轮阻塞混写。[早期事件记录](../experiments/reference-factory/evidence/core026-M1/mcode-transport-incident.json)。

## 确定性恢复顺序

先使用.github/workflows/koma-26-supervisor-qa.yml；该工作流只调用GitHub与已锁定公开源，不请求MiniMax。真实成功参考为run41126811519。

本地恢复时，先安装requirements.txt、npm ci、Playwright Chromium，随后依次运行prepare.py、native_layers.py、prepare_core025.py、capture_core025.mjs --anchors、verify_core025_supervisor.py，生成旧保护报告。再依次运行audit_core026.py --audit、audit_core026.py --verify-source、verify_core026_supervisor.py、verify_core026_registration.py、verify_core026_constraints.py。

从已授权GitHub日志接口取得job124281335070的原始日志后，以restore_core026_reference.py --job-log PATH恢复实际截图；或使用上述原生Draft及其manifest。随后运行prepare_core026_landmark_seeds.py和verify_core026_reference.py。不得用重新生成或占位图片冒充原生参考。

## 已完成的前序阶段

- CORE024：494d50b与CI41043343409，原生62层导出像素一致；侧脸C的W245仅临时抠图预览。
- CORE025 M1：默认组装及9层阴影裁剪原型通过。[验收](research/CORE-025-M1-supervisor-acceptance.md)。
- CORE025 M2：62层非平面几何数值链路、真实17图和独立0°检查通过，四种MAE均<0.05/255。[验收](research/CORE-025-M2-supervisor-acceptance.md)。这未通过艺术级转头。
- CORE025 M3：97帧、24fps、4.041667秒视频已生成并解码检查；艺术级转头FAIL，仍像浅表面摆动。[验收及失败原因](research/CORE-025-M3-supervisor-acceptance.md)。
- CORE025 M4：代码c876100、CI41084893009通过49回归及完整数值重建/归档。[验收](research/CORE-025-M4-CI-acceptance.md)。不要从A1重新开工。
- 全量资产尚未完成；侧面拆层、背面、连续UV、生产骨骼蒙皮、IK及360°仍未验收。

# 当前恢复入口

更新：2026-10-31（Asia/Shanghai）。仓库tims-SP/koma-motion-lab，分支feature/koma-25d-core-021。首选mcode执行、Codex监督；最新续跑被自动审批阻塞，按计划明确署名Codex本地兜底。M1C1原作者为Codex本地兜底；M1C2A补丁由Codex设计、mcode实际应用并运行，分别署名。每完成一段提交保存。生产仓库koma-motion未改。

## CORE026当前状态

M1总门禁已通过PASS_REFERENCE_LIMITED：代码05e8814的监督CI41157121611与旧回归CI41157121472均success，实际下载14份纯JSON产物并核对ZIP SHA。[完整CI验收](../experiments/reference-factory/evidence/core026-M1/m1-complete-ci-acceptance.json)。M2A默认绘画顺序/接收面提案本地已通过，待新CI；M2B运行时未开始，物理深度仍NOT_RECOVERED，自然3D转头仍NOT_ACCEPTED。只有原生raw yaw=-0.25、0、+0.25三个离散值具备鼻绘画/双眼图像标记及下颌轮廓对照；参数不是物理角度，插值、外推与更大角度未放行。

- 源对应：62层均经原始UV/纹理/默认祖先变换选出唯一身份；58项可单靠像素，7/8/9/10四个重复图项经默认坐标区分。只使用单一全局平移；最大残差3.905124源像素，原始UV未改。
- 原生参考：固定camera scale0.4、position[82,1773]、720×880全图和652×652头部ROI；raw yaw九姿态[-1..1]、pitch0。18张实际PNG的来源/恢复均已保存。新总门禁核对九张head SHA。
- M1C1配置schema v2：62条源事实及未验证接收提案、11Multiply/9默认阴影裁剪、四项late paint与opaque hair重叠28/15/2156/1954。指纹锁定身份、原始mesh和验证程序，避免整份浮点诊断JSON字节差异。原始PNG/INX/UV与10个保护文件未改。
- 19槽位×9姿态=171格均完成实际原生图审阅。9格VERIFIED_IMAGE_FIDUCIAL且可有限比较；31格BOUNDARY_PROXY_ONLY；22格NCC_CANDIDATE；109格UNKNOWN。轮廓不作为固定材料点，六项源未知不填坐标。
- Codex实际查看九姿态全头、中央和两侧的原图/候选局部，并保存逐姿态状态叠加图。PNG只在ignored out/及owner-only Draft；git与Actions artifact保持文本。
- 新增verify_core026_m1.py运行当前来源/保护/默认配准/M1C1/标点只读检查，再汇总有限参考。六个结构合法但不足以支持比较的用例全部BLOCKED；真实CLI缺默认鼻点返回12。标点17项检查（14种损坏拒绝）也通过。[本地验收](../experiments/reference-factory/evidence/core026-M1/m1-complete-local-acceptance.json)。

## 执行分工与当前阻塞

用户本轮要求官方链接登录，已完成；CLI实际返回Signed in with MiniMax、exit0。登录成功后，公开文字/无本地工具的mcode代码生成请求超时exit6，无产出；第二次缩小函数工单仍被自动审批以未验证Alibaba OSS传输内容/授权未明为由拒绝，无可接纳实现。此后停止调用，不换渠道重试，不把审批提示当作真实上传抓包，也不再次登录。

按已授权M2工单的本地兜底条款，本轮M2A所有代码、数据和检查均为Codex，不计作mcode产物。M1同样保留真实归属。[本轮M2A验收与执行记录](research/CORE-026-M2A-source-schedule-acceptance.md)。

M2A受控提案保持62项源身份/19独立面/43附着和完整1..62顺序，分为25个显式待验证pass。原生ClipToLower4项和派生阴影裁剪9项分列；11Multiply含60/61。Face13的13..43与58..61被头发44..57隔开，保留晚画与跨组Multiply背景依赖。108对跨组alpha支持相交、四项晚画交叠28/15/2156/1954由两种独立实现重算；不当作物理遮挡。11类损坏两验证器均exit11，重复build字节一致。新CI待本次提交，M2B未开始。[机器验收](../experiments/reference-factory/evidence/core026-M1/m2a-local-acceptance.json)。

## 下一工单

M1有限参考门禁已获两套干净CI确认；M2A本地完成，待本次干净CI确认后按[M2精确工单](plans/CORE-026-M2-local-compositor-order.md)继续M2B真实0姿态渲染。先审计跨接收面的原画顺序和Multiply，尤其58/59眼皮与60/61眉的晚画覆盖；不能把全部Face绘画提前烘成一张图而丢失与头发的交叠。先过原画0姿态保真，再进入已放行的三个raw参考点。M2实现、M3深度方案、M4动态遮挡和M5最终视频尚未通过。

前序监督CI41155423219与旧回归41155423100已经success，但只覆盖当时的零审阅初始表，不当作本次171格总验收。[前序CI](../experiments/reference-factory/evidence/core026-M1/landmark-review-ci-acceptance.json)。运行/登录/域名事件保留在[运行诊断](research/CORE-026-mcode-runtime-diagnostic.md)；这些历史不是重登或任意存储上传的理由。

## 确定性恢复顺序

先使用.github/workflows/koma-26-supervisor-qa.yml；该工作流只调用GitHub与已锁定公开源，不请求MiniMax。最新完整M1成功参考为run41157121611；早期源恢复参考为run41126811519。

本地恢复时，先安装requirements.txt、npm ci、Playwright Chromium，随后依次运行prepare.py、native_layers.py、prepare_core025.py、capture_core025.mjs --anchors、verify_core025_supervisor.py，生成旧保护报告。再依次运行audit_core026.py --audit、audit_core026.py --verify-source、verify_core026_supervisor.py、verify_core026_registration.py、verify_core026_constraints.py。

从已授权GitHub日志接口取得job124281335070的原始日志后，以restore_core026_reference.py --job-log PATH恢复实际截图；或使用上述原生Draft及其manifest。随后运行prepare_core026_landmark_seeds.py和verify_core026_reference.py。不得用重新生成或占位图片冒充原生参考。

M1C1在源检查后依次运行python extract_core026_constraints.py --verify、python verify_core026_m1c1_supervisor.py、python run_core026_m1c1_regressions.py。仅有意重新生成候选时使用--build；CI首先verify已提交配置，不能先build覆盖错误配置。完整命令/结果见上述验收报告及evidence/core026-M1/constraints-local-acceptance.json。

## 已完成的前序阶段

- CORE024：494d50b与CI41043343409，原生62层导出像素一致；侧脸C的W245仅临时抠图预览。
- CORE025 M1：默认组装及9层阴影裁剪原型通过。[验收](research/CORE-025-M1-supervisor-acceptance.md)。
- CORE025 M2：62层非平面几何数值链路、真实17图和独立0°检查通过，四种MAE均<0.05/255。[验收](research/CORE-025-M2-supervisor-acceptance.md)。这未通过艺术级转头。
- CORE025 M3：97帧、24fps、4.041667秒视频已生成并解码检查；艺术级转头FAIL，仍像浅表面摆动。[验收及失败原因](research/CORE-025-M3-supervisor-acceptance.md)。
- CORE025 M4：代码c876100、CI41084893009通过49回归及完整数值重建/归档。[验收](research/CORE-025-M4-CI-acceptance.md)。不要从A1重新开工。
- 全量资产尚未完成；侧面拆层、背面、连续UV、生产骨骼蒙皮、IK及360°仍未验收。

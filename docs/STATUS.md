# 当前恢复入口

更新：2026-10-31（Asia/Shanghai）。仓库tims-SP/koma-motion-lab，分支feature/koma-25d-core-021。首选mcode执行、Codex监督；用户最新已明确允许项目操作包括上传，M2B0阶段官方CLI已有实际执行，后续部分请求仍被平台自动审批拒绝；不加载旧禁止上传guard。M1C1原作者为Codex本地兜底；M1C2A补丁由Codex设计、mcode实际应用并运行，分别署名。每完成一段提交保存。生产仓库koma-motion未改。

## CORE026当前状态

M1总门禁已通过PASS_REFERENCE_LIMITED：代码05e8814的监督CI41157121611与旧回归CI41157121472均success，实际下载14份纯JSON产物并核对ZIP SHA。[完整CI验收](../experiments/reference-factory/evidence/core026-M1/m1-complete-ci-acceptance.json)。M2A默认绘画顺序/接收面提案已通过：代码ff2fe1a的监督CI41169579730与旧回归41169579751均success，实际下载16份纯JSON产物并核对ZIP SHA；M2B0已有真实运行时与截图，默认原画已通过PASS_DEFAULT_ART_ONLY：代码edb696f的监督CI41174418164及旧回归41174418131均success，已下载20份纯JSON产物并核对ZIP SHA；完整M2B眼组策略/空间合成未过，物理深度仍NOT_RECOVERED，自然3D转头仍NOT_ACCEPTED。只有原生raw yaw=-0.25、0、+0.25三个离散值具备鼻绘画/双眼图像标记及下颌轮廓对照；参数不是物理角度，插值、外推与更大角度未放行。

- 源对应：62层均经原始UV/纹理/默认祖先变换选出唯一身份；58项可单靠像素，7/8/9/10四个重复图项经默认坐标区分。只使用单一全局平移；最大残差3.905124源像素，原始UV未改。
- 原生参考：固定camera scale0.4、position[82,1773]、720×880全图和652×652头部ROI；raw yaw九姿态[-1..1]、pitch0。18张实际PNG的来源/恢复均已保存。新总门禁核对九张head SHA。
- M1C1配置schema v2：62条源事实及未验证接收提案、11Multiply/9默认阴影裁剪、四项late paint与opaque hair重叠28/15/2156/1954。指纹锁定身份、原始mesh和验证程序，避免整份浮点诊断JSON字节差异。原始PNG/INX/UV与10个保护文件未改。
- 19槽位×9姿态=171格均完成实际原生图审阅。9格VERIFIED_IMAGE_FIDUCIAL且可有限比较；31格BOUNDARY_PROXY_ONLY；22格NCC_CANDIDATE；109格UNKNOWN。轮廓不作为固定材料点，六项源未知不填坐标。
- Codex实际查看九姿态全头、中央和两侧的原图/候选局部，并保存逐姿态状态叠加图。PNG只在ignored out/及owner-only Draft；git与Actions artifact保持文本。
- 新增verify_core026_m1.py运行当前来源/保护/默认配准/M1C1/标点只读检查，再汇总有限参考。六个结构合法但不足以支持比较的用例全部BLOCKED；真实CLI缺默认鼻点返回12。标点17项检查（14种损坏拒绝）也通过。[本地验收](../experiments/reference-factory/evidence/core026-M1/m1-complete-local-acceptance.json)。

## M2B0最新结果与执行分工

用户明确允许mcode项目操作包括上传。首轮官方SDK实际完成14次工具调用后8分钟超时，无运行时文件；固定工单随后由mcode真实bash应用Codex设计的三个运行时文件，JS语法exit0，截图因缺Chromium失败。mcode安装系统依赖遇Work容器uid/setgroups限制；浏览器-only调用又被平台自动审批以OSS目的地/实际载荷未明拒绝。没有因这项拒绝重新登录、换SDK渠道或继续重试。Codex单独下载公开Chromium后完成了成功截图与独立验收；不把这部分执行改归mcode。

已捕获10张候选图与12张独立监督图，核对62张原始PNG、19个共享接收几何、25逻辑pass/62实际GPU源绘制。运行时只读原始RGBA，实时源域Normal/Multiply，没有用旧烘焙层或整头图片作为候选颜色。[本地验收](../experiments/reference-factory/evidence/core026-M1/m2b0-local-acceptance.json)。

第一版硬眼白裁剪真实失败：每张1219像素差>16，最大差182，失败代码/证据707cc6c7保留。修复后的原画兼容覆盖域默认图对旧浏览器最大差3，对CPU最大2，alpha最大差1；所有四张差>16为0。原RGB/alpha阈值未改。错误硬眼罩在现有反例分支仍须失败；伪造单个前景像素、同步更新SHA/repeat后仍被最大差门禁拒绝。

Codex已实际看默认鼻/眼/眉发/耳叶/颈部；默认还原可接受，单独瞳孔偏移时高光29未联动，不能算自然眼动。9681像素真实改变、复位恢复原SHA；改变在原画眼域内，533像素位于原始眼白单独支持外。旧“仅眼白域”假设继续BLOCKED，没有隐藏该失败。运行时depthTest=false、沿用未拟合CORE025高度剖面；源域CPU背景计算也不等于转头时screen-space背景，完整M2B与M3继续阻塞。[限制与反例](research/CORE-026-M2B0-default-art-and-eye-mask.md)。

本轮只到默认原画还原通过；监督CI41174418164及旧回归41174418131均success。实际下载20份纯JSON并核对ZIP SHA，CI截图SHA与已人工查看的本地图逐张一致。[CI验收与媒体Draft](../experiments/reference-factory/evidence/core026-M1/m2b0-ci-acceptance.json)。媒体仅ignored out/及owner-only Draft，SDK原始流不发布。登录态保留，OSS审批问题与登录成功分开记录。

## M2B1A离散眼动（本地与干净CI通过）

新增明确artist override策略与setEyeGaze：28/29、38/39瞳孔和高光同移，验收范围为默认头部姿态的水平-8/0/+8源像素。第一版虽然数值通过，但Codex看到固定眼域削掉移动虹膜下缘后拒绝；改为原始alpha域水平扩展固定8像素的有界包络，保留旧静止画面与单层诊断行为。原生EyeComposite mesh/UV注册及ClipToLower等价性仍BLOCKED。

实际采集36张图，32正例独立对原始62张RGBA合成oracle全部通过；最大差1，眼域包络外变化0，默认/复位SHA不变。4张高光固定/静止域裁切负例均被原RGB阈值拒绝。已查看六个偏移眼部放大图及整头图，仅验收离散控制，连续眼动画和自然转头未验收。[本地证据](../experiments/reference-factory/evidence/core026-M1/m2b1a-local-acceptance.json)、[视觉判定](../experiments/reference-factory/evidence/core026-M1/m2b1a-visual-review.json)、[实现与限制](research/CORE-026-M2B1A-discrete-eye-control.md)。本轮由Codex本地执行，未重复此前被拒的mcode SDK调用。代码b622107的监督CI41181723133与旧回归41181723122均success；实际下载22份纯JSON并核对ZIP SHA，36张眼动和12张默认截图SHA与本地一致。参见[CI验收](../experiments/reference-factory/evidence/core026-M1/m2b1a-ci-acceptance.json)。完整M2B仍未通过。

## 下一工单

M2B1A干净CI实际产物已核对，接下来按[M2B1空间合成与眼组工单](plans/CORE-026-M2B1-spatial-and-eye-policy-order.md)第5–7步及[空间合成明确工单](plans/CORE-026-M2B1B-spatial-runtime-order.md)完成接收面RGBA/UV、投影背景相关Multiply及真实depth-test/透明孔验证。原生眼组注册对照仍分列BLOCKED，不能因选定原画覆盖就删掉。完成M2B后才进M3深度方案、M4动态遮挡、M5连续视频。[目标与距离](plans/CORE-026-goals-and-distance.md)。当前尚有这四道主要门禁，不给虚构百分比或固定工期。

M2A代码ff2fe1a的监督CI41169579730及旧回归41169579751已success，覆盖顺序/alpha提案，不当作M2B运行时通过。M1仅raw -0.25/0/+0.25有限参考；全部360资产、绑骨/IK与背面模型均未验收。

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

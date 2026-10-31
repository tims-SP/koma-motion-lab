# 当前恢复入口

更新：2026-10-31（Asia/Shanghai）。仓库tims-SP/koma-motion-lab，分支feature/koma-25d-core-021。首选mcode执行、Codex监督；本轮限定命令执行已恢复。M1C1原作者为Codex本地兜底；M1C2A补丁由Codex设计、mcode实际应用并运行，分别署名。每完成一段提交保存。生产仓库koma-motion未改。

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

M1C2A已完成初始19×9审阅表和只读结构校验。mcode首次开放式实现超时exit6、无文件；随后按Codex补丁工单实际应用代码并执行prepare/verify，CLI/工具/两条命令均exit0。Codex独立17项检查通过，包括14种损坏均exit11、允许隔离的合法编辑、已有表禁止覆盖；原配置不变。171格均未审、可拟合数0。CI待本次提交复现；[验收范围与归属](research/CORE-026-M1C2A-review-preparation.md)。下一步仍是逐图人工判断与M1总门禁，未开始M2。

最新mcode[恢复证据](research/CORE-026-mcode-runtime-diagnostic.md)：用户明确允许本项目网络后，mcode实际执行两条项目验证，CLI/工具/两条命令均exit0，62条源事实无问题；无重新登录。当前恢复范围为该限定验证，下一工单继续由mcode实现、Codex验收。Node请求层自测通过，未知对象存储仍拒绝；不把SDK潜在地址或早前审批提示当作实际上传证据。M1C1原始作者仍为Codex兜底，不能事后改归mcode。

M1C1已由Codex本地实现并通过干净CI：[验收报告](research/CORE-026-M1C1-local-fallback-acceptance.md)。代码76d7f70的[监督CI41144806591](https://github.com/tims-SP/koma-motion-lab/actions/runs/41144806591)及[旧回归41144806561](https://github.com/tims-SP/koma-motion-lab/actions/runs/41144806561)均实际success。62条源事实/接收提案、9组双验证器exit11验拒、重复build一致、verify不改配置、10保护文件/186PNG、默认坐标与18张原生参考SHA均通过。M1C1通过范围仅为源事实和未验证设计契约。

下一步按[M1C2精确工单](plans/CORE-026-M1C2-landmark-and-reference-order.md)完成19槽位逐姿态可用范围/可见性复核和M1总验收。现有NCC候选仍非拟合真值；receiver均为未验证设计提案，三维深度和运动遮挡UNKNOWN。M1放行后才实施M2，不直接盲调Z。[M1C1执行归属](plans/CORE-026-M1C1-constraints-order.md)。

Work已恢复且本地仓库已同步。源像素/10保护文件/186PNG、62默认坐标、11Multiply/9clip及18张原生参考哈希均重新实测通过。监工查看了实际9姿态标点接触图与默认652×652图；19槽位的13图像候选仍有语义限制，所有点仍不自动具备拟合资格。[本轮实际记录](../experiments/reference-factory/evidence/core026-M1/supervisor-resume-and-reference-review.json)。

mcode首次启动exit3提示登录失效；已通过官方CN登录流程恢复，CLI实际返回Signed in with MiniMax、exit0。用户在agent.minimax.cn精确范围问题后回复继续，本轮按该范围启动任务；平台自动审批再次拒绝，理由是CLI还可能将项目上下文发送至agent.minimaxi.com，超出此前单域名范围。公开包代码确认CN模型接口为agent.minimax.cn，CN步骤报告接口使用agent.minimaxi.com。没有获得可验收实现文件，未在新拒绝后重试完整工作区任务。

用户随后明确放行.com，agent.minimax.cn与agent.minimaxi.com的前述范围已确认；当前不需要再次登录。重试先遇filecdn.minimax.chat审批，公开包已证实它是无认证/无正文的公共模型目录GET。另遇阿里云存储审批，公开包只定位到自定义data-URL头像的内容安全上传分支，不能据此确认实际请求载荷。复用已有会话、不进行头像操作后，mcode实际完成12个本地工具调用，但8分钟超时exit6，未生成提取器或配置。精简、低思考强度重试再次被自动审批以阿里云上传/存储未获授权且命令禁止上传为由拒绝；现已停止重试。[本轮实测记录](../experiments/reference-factory/evidence/core026-M1/mcode-post-domain-approval.json)。

上述SDK阻塞现只影响mcode协作，本地M1C1已推进。已发现的两个阿里云host存在于公开SDK头像上传白名单，但没有网络日志证明本任务真实访问或上传载荷；审批提示不能当请求抓包结果。最后一次lightweight/permission off、仅通用公开schema的尝试也被审批拒绝，随后停止mcode调用，采用本地替代。当前不因这些提示再次要求登录或逐个域名授权。

此前服务500/超时、旧目的地审批与环境不可用均保留为历史，不与本轮阻塞混写。[早期事件记录](../experiments/reference-factory/evidence/core026-M1/mcode-transport-incident.json)。

## 确定性恢复顺序

先使用.github/workflows/koma-26-supervisor-qa.yml；该工作流只调用GitHub与已锁定公开源，不请求MiniMax。真实成功参考为run41126811519。

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

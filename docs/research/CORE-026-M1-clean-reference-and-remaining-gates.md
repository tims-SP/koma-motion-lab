# CORE-026：清洁高清参考、源遮挡事实与剩余门禁

日期2026-10-31（Asia/Shanghai）。当前仍是M1；M2–M5未执行，自然3D转头仍NOT_ACCEPTED。

## 已实测并保存的结果

- 62部件默认源坐标对应已通过，58唯一纹理加4个重复后发的空间区分，不更改原始UV。
- 清洁高清原生捕获代码801d904，Actions run41119224557、job124281335070全部success。
- 原生9姿态raw yaw=-1到+1、raw pitch0，固定相机scale0.4/position[82,1773]，固定652×652头部裁切。参数未标定为物理角度，dt0不代表物理平衡。
- [清洁原生Draft Release](https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-2589bc212d17274d3503)归档真实成功。
- 无损审阅ZIP1876570字节，SHA256为8b0e9511c2781108a4335e287ab419c7563cf3e54e933d98d79be1eb6c263f73。
- 监工对9张原始PNG和9张独立裁切全部核对SHA；对照旧图，差异>16仅在固定16×16指针区域[471,329,487,345]，没有改画或改姿态。新图目视无指针；完整头部/耳尖顶部留有至少12像素余量。
- 62条实际原生祖先、blend、zsort、HeadYaw绑定名称已由监工本地只读检查。11Multiply、9默认阴影裁剪存在。
- 源眼皮58/59与实体头发分别重叠28/15像素；眉60/61重叠2156/1954像素。因此四层的晚叠画不能随意并入头发下面的Face。此为默认原画事实，不是3D前后关系。
- 原始11Multiply均有非零的有色RGB；默认背景烘焙纹理不能成为新遮挡下的正确性证明。M2需要保留实际下层颜色上下文，或验证可等效表达的合成方式。

## 标点如实保留不确定性

建立19槽位：13个有源alpha支持的图像候选（其中4个眼白边界仅是眼角代理），6项未知。鼻根、两耳根、颈连接不可直接辨认；两嘴角的raw Mouth Inner边界在实际合成中被Lip遮住，已拒绝这些raw边界，不能把alpha存在当可见性证据。

候选NCC使用相邻原生姿态、每通道去均值、半径5模板、搜索半径32、双向score>=0.82、forward-backward<=1.25像素；一旦失败就停止该方向。实际本地各姿态候选数为4/5/6/11/13/9/7/6/4。失败项不填造坐标；沿轮廓的匹配还可能存在滑动歧义。所有点仍不自动具备拟合资格，图像跟踪不是可见性真值。

## 可恢复代码与CI

Work环境在收尾时变为unavailable。已成功运行的本地命令被固化为以下监督检查程序；新增文件的干净环境运行交由新工作流验证，不把保存源码算作执行成功：

1. prepare.py、native_layers.py、prepare_core025.py恢复原始来源和旧默认组装。
2. audit_core026.py --audit、--verify-source、verify_core026_supervisor.py、verify_core026_registration.py恢复源像素/坐标证据。
3. verify_core026_constraints.py恢复源祖先和默认叠画观察。
4. 通过已授权GitHub连接下载job124281335070的原始日志；restore_core026_reference.py --job-log PATH恢复真实PNG。也可下载上述Draft中的媒体，保留对应manifest。
5. prepare_core026_landmark_seeds.py、verify_core026_reference.py复现19槽位与候选诊断。

.github/workflows/koma-26-supervisor-qa.yml执行这条CPU链路，使用GitHub自身actions:read读取固定成功job，不依赖当前Work电脑、不请求MiniMax。只有JSON进入Actions artifact；媒体进入owner-only Draft Release。该工作流即使success，也只通过源数据/恢复/诊断执行，不通过M1整体或艺术门禁。

## 实际阻塞与下一工单

mcode原任务出现服务端500和超时，未产出可验收的extract_core026_constraints.py或core026-constraints.json，不计为完成。平台自动审批又拒绝过一次mcode代码请求，理由是可能向agent.minimax.cn披露仓库/工作区上下文，认为具体目的地未获明确许可。

随后只做了低风险核验：仓库GitHub可见性确为public；已安装公开包@minimax-ai/code0.7.2中，agent.minimax.cn是CN生产地址；README说明lightweight不读取工作区/环境/工具上下文。关闭工具权限后，纯通用小函数请求成功，复杂纯代码请求仍超时。未在拒绝后恢复完整工作区模式、未另走代理上传或读取凭据。

需要的确认范围仅为：允许mcode将本项目相关代码、任务文档和必要文本执行结果发往其服务agent.minimax.cn；排除凭据、登录文件和其他目录。Work也需要恢复可用。

恢复后先运行现有验收；完成CORE-026-M1C1-constraints-order.md的实现与对照，人工复核可用标点范围/源位置/遮挡，M1放行后才开始M2。不要从CORE025重新开工，不要把源事实观察冒充接收面合成已实现。

## 恢复CI首轮失败及修复

run41125161542在source verify-source处exit11，缺out/core025/render/manifest.json和supervisor-qa.json。源组装及58个像素对应已实际通过，但流程没有先生成这两份保护报告。已补锁定Node/Chromium依赖、真实17图capture_core025 --anchors和独立QA作为前置，不删保护项、不造占位文件。修复后的运行必须真实成功，不能沿用首轮绿色准备步骤作为整体PASS。

## 监督恢复最终实测

代码5f9aef894813d8692242a04798b5817e1892d8ea的[run41126811519](https://github.com/tims-SP/koma-motion-lab/actions/runs/41126811519)、job124307345047所有步骤真实success。源层重建、旧17图真实保护报告、186PNG/10保护文件、58唯一像素对应、4重复项默认空间区分、62源叠画记录、11Multiply与9clip均通过。

恢复接口还实际暴露两项日志格式问题：run41125557918被GitHub CLI的终端转义拦截；改为仅将原始响应写文件后，run41126370320发现日志中段第二个BOM，导致时间戳混入Base64。已仅去除每行开头BOM后再剥时间戳，保留严格Base64解码、ZIP白名单、来源/补丁/图片SHA检查。三个失败运行不改记为成功。

最终恢复9张真实720×880原图和9张652×652裁切，所有SHA与原生manifest一致；审阅ZIP哈希仍为8b0e9511c2781108a4335e287ab419c7563cf3e54e933d98d79be1eb6c263f73。顶部余量实际为12/13/13/13/12/13/13/13/12像素；候选数实际复现4/5/6/11/13/9/7/6/4。所有候选仍不具备自动拟合资格。

[监督诊断Draft](https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-270a8f25943b4d8f5dd0)创建成功；JSON artifact13010862995仅26799字节。媒体不进git和artifact。机器可读记录位于experiments/reference-factory/evidence/core026-M1/supervisor-recovery-ci-acceptance.json。

本次通过范围仅为源事实、真实参考恢复和诊断可复现；M1整体、接收面合成、运动遮挡和自然3D转头仍未放行。mcode约束实现及19标点人工复核仍按工单继续，服务具体目的地发送范围确认和Work恢复是当前剩余阻塞。

同一代码5f9aef8的旧工厂回归[run41126811438](https://github.com/tims-SP/koma-motion-lab/actions/runs/41126811438)、job124307344949也已真实success。最终文档提交不改变已通过的代码。

## Work恢复后的实际执行与新的域名范围阻塞

用户在单域名agent.minimax.cn的限定范围问题后回复继续。本地从801d904干净快进至11866b7；Work已可执行。官方公开安装mcode0.7.2仍在原位置，但未加入PATH，因此使用绝对路径。第一次exec实际exit3要求登录；随后官方CN登录进程实际返回Signed in with MiniMax、exit0。

源像素/保护文件、62默认坐标、源叠画观察及19槽位诊断均已在恢复后的Work重新执行通过。实际候选数仍4/5/6/11/13/9/7/6/4，9原图与9裁切SHA一致。监工查看真实9姿态标点接触图与默认652×652标点图，记录可见图像特征、4眼白边界代理、轮廓滑动和隐藏根部的限制；未把这些点升级为拟合真值。

重新启动完整mcode任务后，等待执行的工具调用被平台自动审批拒绝，明确理由为：可能向agent.minimaxi.com发送项目代码、任务文档和工作区上下文，而此前保留的批准只覆盖agent.minimax.cn。任务日志为0字节，没有实现产物；随后检查未发现仍存活的匹配任务进程。没有更换代理、修改SDK、读凭据或在新拒绝后重试完整任务。

只读核对公开安装包发现：模型CN生产接口为https://agent.minimax.cn/mavis/api/v1/llm/v1；步骤报告的CN生产origin为https://agent.minimaxi.com，路径/mavis/api/v1/eval/steps/report。该事实说明两个服务域名确实同时存在，不证明本次已发送任何项目内容，也不替代用户对额外目的地的许可。包代码SHA及实际检查结果保存在supervisor-resume-and-reference-review.json。

当前需要确认的范围：允许mcode将本项目相关代码、任务文档和必要文本执行输出发送至agent.minimax.cn及agent.minimaxi.com，排除凭据、登录文件和其他目录。Work与登录已经恢复，当前不要求再次登录。得到此范围后重新执行已落盘M1C1精确工单，先检查是否有产物再启动，按build/verify/独立比对/三项篡改验拒提交；M1整体与M2状态保持未通过/未开始。

## 用户明确放行.com之后的真实结果

两个MiniMax接口域名的限定范围现已由用户明确放行，上一段属于历史阻塞。b496ae7的旧回归run41137822195/job124344522596已success。后续审批先拦截filecdn.minimax.chat；只读检查官方公开安装包发现GGt为公共模型目录GET，KYr在CN仅设置accept:application/json，HGt限制HTTPS、固定hostname、无凭据/查询参数、SHA256目录路径。代码SHA与调用摘要已存mcode-public-catalog-risk-check.json。此检查不授权向CDN上传项目数据。

审批随后指出matrix-internal-cn.oss-cn-shanghai.aliyuncs.com。公开包中H1r白名单列CN及US两个阿里云host；gBt用途为agent-avatar、purpose3、私有CONTENT_SAFETY上传，唯一调用方X1r仅对data:格式头像调用它，HTTPS头像只返回image_url。代码事实已存mcode-avatar-storage-risk-check.json；它不是本次实际请求载荷的抓包结果。

复用既有任务会话、明确不创建Agent/不编辑头像/不上传图片或文件后，mcode实际读取工单、合同、原生字段等，完成12个本地工具调用；8分钟上限到达，实际exit6，未产出extract_core026_constraints.py或core026-constraints.json。没有把耗时或12个工具调用当完成。后续将工单缩成先写提取器再build/verify，使用官方支持的effort low；该重试在工具调用前再次被自动审批拒绝，理由是阿里云上传/存储超出已批准MiniMax域名，且命令明确禁止上传。未在此次新拒绝后重试。

监工验收程序作为DRAFT保存到verify_core026_m1c1_supervisor.py，独立定义19曲面+43接收映射覆盖全部62层；当前缺真实候选，实际exit11并指出配置不存在，未误判PASS。候选正例、错误UUID/receiver/late_paint三项验拒均NOT_RUN_NO_CANDIDATE，不能宣称验收程序整体通过。未来先接受mcode真实产物、复核输入SHA与源事实后再运行这几项，并接入CI。

当前需要的是一次明确的SDK依赖范围确认：mcode使用MiniMax官方接口及其指定CDN/阿里云存储完成本项目任务，限定项目代码、工单、必要文本执行记录和SDK默认公开素材，排除凭据、登录文件和无关目录。已发现的存储host见上述两个白名单项；具体请求载荷尚未确认，不能悄悄开放或绕过审批。当前不需要重新登录；M1整体未放行、M2未开始，深度和动态遮挡尚未实现。

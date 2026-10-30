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

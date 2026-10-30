# CORE026 M1C2：逐姿态标点可用范围与M1总验收

前置：M1C1代码76d7f70已通过监督CI41144806591及旧回归41144806561。M1整体尚未放行；本工单先处理参考与标点，不改深度、渲染器或来源。mcode协作仍受审批阻塞时可由Codex明确署名本地执行，不再重复登录或把审批提示当网络抓包。

## 允许文件

新增experiments/reference-factory/prepare_core026_landmark_review.py、config/core026-landmark-review.json、verify_core026_m1.py；必要的独立验证程序和本工单文本证据。媒体仅ignored out/core026及owner-only Draft。不得更改原始PSD/INX/PNG、原始UV、旧CORE025程序/锁或覆盖9张真实参考。

## 明确执行步骤

1. 运行现有源、默认坐标、M1C1验证及参考哈希检查；已有成功来源可复用，不重新生成资产。读取清洁reference-manifest.json、19槽位config/core026-landmark-seeds.json和现有NCC诊断。记录本轮配置/manifest/9张head PNG的实际SHA。
2. 准备程序为19槽位×9个既定raw yaw创建审阅记录，初始全部eligible_for_fitting=false。只复制来源与候选，不因NCC阈值通过就自动接受。默认姿态源点有alpha支持也不等于遮挡后可见。
3. Codex实际查看9张652×652头图，并对鼻绘画、双眼、下颌/脸缘、耳尖与叶柄查看原图局部。先审核raw0与±0.25，再逐张扩展到其余姿态；不猜测缺失匹配。保存不改画的标点审阅图和对应native PNG SHA，媒体仍仅out/Draft。
4. 每槽位记录id、psd_order、semantic_class、source_xy、source_alpha、定义及物理语义限制。每姿态记录raw_yaw、native_head_sha256、state、xy或null、confidence、review_method、具体图像依据及eligible_for_fitting。state仅允许VERIFIED_IMAGE_FIDUCIAL、BOUNDARY_PROXY_ONLY、NCC_CANDIDATE、OCCLUDED、UNKNOWN；未实际复核者不得写VERIFIED。
5. 四个眼白边界只作BOUNDARY_PROXY_ONLY；下颌/脸缘的轮廓滑动单列，不当固定材料点。鼻绘画/眼内图像特征只能声明image fiducial，不升级为解剖鼻尖/瞳孔中心。六项现有未知不补坐标；缺可见点、模板歧义或被遮挡均保留UNKNOWN/OCCLUDED及原因。仅经过真实逐姿态复核的非代理图像特征可eligible_for_fitting=true。
6. 使用固定相机/ROI与已验收默认配准；禁止每姿态平移/缩放或用生成候选替代参考。原生raw yaw不换标为真实物理角度。报告配准残差与可比较范围，不可比指标标BLOCKED。
7. prepare_core026_landmark_review.py实现--prepare（只生成待审初始表，不覆盖已有审阅）和--verify（只读校验19身份、9姿态、171槽位、引用SHA、状态/置信度/坐标范围以及可拟合条件）。证明未审候选/未知/代理不能被自动放行；篡改真实图SHA、把代理设为可拟合、给未知填伪造坐标时均非0退出。
8. 新增verify_core026_m1.py汇总已实测来源/参数/62映射、原生9姿态、M1C1约束、标点审阅与明确阻塞。若两侧斜向参考没有可信的鼻绘画、双眼与下颌/脸缘类别观测可支持头型比较，返回BLOCKED_REFERENCE_FOR_DEPTH_FIT，不进M2盲调Z。满足有限参考门禁时只写PASS_REFERENCE_LIMITED，列可用raw范围和未知项，不写自然3D转头PASS。
9. 运行现有生产验证、独立监督、标点审阅验证及M1汇总入口，保留真实命令/退出码。提交代码/受控JSON与报告；CI复现后记录检查点。仅在M1真实放行后下达M2局部合成工单，M2必须先过0°原画保真。

本工单不要求伪造171个可见点；它要求每槽位有明确状态与来源。未知数量不是错误，伪造可用性才是失败。

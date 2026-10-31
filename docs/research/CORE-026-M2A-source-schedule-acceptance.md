# CORE026 M2A：默认绘画顺序与接收面提案

2026-10-31（Asia/Shanghai）。范围PASS_SOURCE_SCHEDULE_AND_PROPOSAL；代码ff2fe1a的监督CI41169579730与旧回归41169579751均success。实际下载16份纯JSON产物，ZIP SHA1003658943529b2d5d412610fea5e3c756cfc0f3aa3a7c1806694ea0adfa41e9与job日志一致，契约SHA与本地一致。[CI机器验收](../../experiments/reference-factory/evidence/core026-M1/m2a-ci-acceptance.json)。实际作者、执行者和独立检查为Codex本地兜底，不计作mcode产物。

## 登录与执行归属

按用户要求启动官方CN链接登录，用户授权后CLI实际返回Signed in with MiniMax、exit0。之后没有再次登录。

为收窄此前被拦截的访问，第一次工单使用仅公开文字、lightweight、显式tools=[]和禁用persona/插件配置，由mcode生成纯Python算法，不附图片/资产或工作区上下文。该请求未返回审批拒绝，但3分钟超时exit6，没有可接纳的代码文件。第二次缩小为一个分组函数，仍被自动审批以未验证Alibaba OSS传输内容/授权未明为由拒绝，没有可接纳代码；随后停止调用，不换渠道重试。官方登录成功不等于这项自动审批已经放行。

拒绝提示不作为实际网络载荷抓包证据。Node请求层检查不是OS防火墙或完整网络监控。原始SDK流仅保留ignored out/，本报告不发布token、登录码、SDK会话标识或认证文件。按M2工单中已经允许的本地兜底方式继续，所有新实现明确署名Codex。

## 已实测内容

受控config/core026-compositor-contract.json保留62项原始身份、UUID、PNG SHA、原始Normal/Multiply、receiver/caster及原生ClipToLower标志。19项独立面、43项附着提案全部有唯一去向，眼部27/37的嵌套接收关系保留。

原生ClipToLower仅28/29/38/39，共4项；派生的clean阴影裁剪是另一份9项清单。11项源Multiply包含60/61眉毛，不能把派生9clip混称为原生clip。

Face13的源成员为13..43和58..61，中间44..57属于其他头发面。契约把这两个非连续区段明确分开；再按接收面和Normal/Multiply切分，当前提案共25个顺序pass。表中requires_multiple_painter_passes按实际提案pass数计算，5（后发）、11（颈部）、13（面部）三组为true；不能因5/11的成员连续就忽略其不同混合步骤。

23号提案pass为Face的58/59晚画，24号为60/61场景背景Multiply，25号为Leaf62。25项只是显式待验证步骤，不声明是运行时不可优化的最少pass，也没有实现空间深度测试。

生产观测以原始PNG alpha在固定1630画布上对齐，接收组alpha取成员最大值，仅用于支持区域诊断。独立验证器使用Pillow逐组max重算，并用独立身份/receiver表和原始来源事实核对，未导入生产者的分组函数。共108对跨组alpha支持相交；这不是最终可见性或物理遮挡。

58/59/60/61与原始7束不透明头发支持的交叠重新得到28/15/2156/1954像素。11个Multiply层各自记录早于自身、属于其他接收面的支持交叠候选；这些候选可能被中间层遮住，状态仍UNRESOLVED_RUNTIME_VALIDATION，不能当作实际背景贡献或直接物理深度。

## 验证与恢复

```bash
python verify_core026_m1.py
python prepare_core026_compositor.py --verify
python verify_core026_compositor_contract.py
python run_core026_compositor_regressions.py
```

本地两验证器均通过；11种隔离损坏全部由两者exit11拒绝：缺层、交换合法UUID、漏Multiply眉、晚画提前、伪造深度、混淆clip来源、篡改alpha交叠、烘掉Face间隙、允许整头烘焙、浮点receiver身份、新增越权声明。验证不改候选；重复build与受控配置逐字节一致，原配置在损坏测试后未改。[本地机器验收](../../experiments/reference-factory/evidence/core026-M1/m2a-local-acceptance.json)。

CI在完整M1有限参考门禁之后先verify已提交M2A配置，再跑独立检查和损坏试验；不能先build覆盖受控数据。Actions artifact只增加两个JSON报告，不放媒体或SDK日志。

下一步按[M2B精确步骤](../plans/CORE-026-M2-local-compositor-order.md)实现真实0姿态合成并与旧基线逐像素比较。当前runtime_receiver_compositor=NOT_IMPLEMENTED，physical_depth=UNKNOWN，自然转头未通过；M2B尚未开始。

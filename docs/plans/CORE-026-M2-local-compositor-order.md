# CORE026 M2：局部接收面与0姿态保真工单

前置已满足：M1代码05e8814的有限参考总门禁、监督CI41157121611及旧回归CI41157121472均成功，实际产物已下载核对；M2A源顺序/接收面提案与11组损坏验拒已获代码ff2fe1a监督CI41169579730及旧回归41169579751成功确认；M2B0默认原画已有真实截图并通过有限门禁及监督CI41174418164/旧回归41174418131，完整M2B未过；见M2B1工单。M1只提供raw yaw=-0.25、0、+0.25的图像对照，不是物理角度或真实深度。mcode首选执行；自动审批继续阻塞时，按已授权计划由Codex明确署名本地兜底，不能把结果改称mcode产物。

## M2A：先确认合成顺序能否保留原画

1. 运行`python verify_core026_m1.py`，要求exit0且status=PASS_REFERENCE_LIMITED。核对输入SHA与受控171格审阅表；其他状态停止。本工单不再生成参考资产。
2. 新增`experiments/reference-factory/prepare_core026_compositor.py`和`config/core026-compositor-contract.json`。逐条读取62项constraints v2，保留psd_order、native_uuid、原始纹理SHA、原始blend、receiver、caster、原生ClipToLower与派生9项阴影裁剪。两类裁剪分列，禁止混称原生9clip。
3. 生成完整62项默认painter schedule，顺序1..62不变。独立面19项、接收提案43项均必须有唯一去向；嵌套眼画布27/37不能漏掉28/29、38/39。未知根点与物理深度保持UNKNOWN，不因父节点名字补值。
4. 计算每个接收组在原画顺序中的跨度、被其他组插入的间隙、跨组alpha重叠及Multiply背景依赖。重点逐项报告58/59眼皮与60/61眉在44..57实体头发之后的晚画事实；保留实测重叠28/15/2156/1954像素。11Multiply包含60/61，不能只对Face底色先做Multiply后再用Normal盖到头发上。
5. 对不能合并为单张局部纹理的非连续组，输出显式pass提案。Face基础绘画、局部眼画布、晚画绘画可以分pass共享同一Face UV/形变；不得用整头静态烘焙替代局部眼运动。跨接收面Multiply与半透明依赖单列UNRESOLVED，先给最小正确合成策略，不能靠把整眉推到相机前方解决。
6. 新增独立`verify_core026_compositor_contract.py`，不复用生产者的组表作为真值，直接从冻结来源/62项原始身份检查覆盖、顺序、纹理、blend与裁剪来源。隔离篡改缺层、交换源身份、漏Multiply、提前合并晚画、把UNKNOWN深度写为实测值时均非0退出。生产者verify不能先build覆盖受控配置。
7. 提交M2A代码/受控JSON/验收报告，状态只能写PASS_SOURCE_SCHEDULE_AND_PROPOSAL；运行时合成及深度仍NOT_IMPLEMENTED。完成提交再实施M2B。

## M2B：真实渲染验证0姿态

1. 新增`core026.html`、`core026.js`、`capture_core026.mjs`，使用现有固定three/Vite/Playwright依赖与原始UV/来源。候选颜色输入仅使用raw_source_texture；out/core025/assembly中的已烘焙层只作旧基线，不得作为候选素材绕过运行时Normal/Multiply。不得修改受保护的CORE025代码、配置、旧报告或原始PNG/INX。
2. 先仅实现source/clean的0姿态。按M2A schedule保留原始Normal/Multiply、局部alpha和late pass；每个receiver内绘画保持独立局部UV接口，不能永久烘死所有眼部图层。将冲突处理写入契约，数值未通过前不引入转头和新的Z拟合。
3. 用真实浏览器分别捕获source/clean×白底/黑底及alpha/ID诊断。记录实际输入SHA、相机、画布、每次draw/pass的62源身份去向、输出PNG SHA和命令退出码。保护旧0姿态baseline，不能拿候选自身作真值。
4. 独立`verify_core026_compositor_supervisor.py`逐像素比较旧已验收0姿态：全图RGB MAE≤0.10、前景并集MAE≤0.50、最大通道差≤4、差>16比例=0；source/clean及两种底色均需通过，同时报alpha及前景指标。鼻、双眼、刘海/眉、耳根、脸颈局部必须实际查看。失败保存差分和原因，禁止放宽阈值。
5. 若跨组Multiply/透明无法保真，保留更多显式局部pass并重测。禁止用整层renderOrder跳变、全头替代贴图、丢失源层、全局Z偏移或改源PNG掩盖失败。仍失败则报告BLOCKED_COMPOSITOR_FIDELITY，不进入M3。
6. 0姿态通过后，只在固定camera/ROI和已校准坐标映射下比较原生raw -0.25/0/+0.25；参数不标为物理角度。M1中的绝对关键点误差、Face IoU、根部裂缝目前BLOCKED_NO_CANDIDATE/UNKNOWN_ROOTS；必须先建立可比映射及有效ROI才计算，不能在看到失败值后换口径。其他角度保持未验收。
7. Git与Actions artifact仅文本；真实PNG/视频仍放ignored out/和owner-only Draft。M2B真实渲染、独立检查与干净CI通过后提交，才下达M3两组深度实验。每个失败检查点也提交，方便恢复。

本工单只推进绘画层/接收面合成与0姿态保真。深度恢复、自然转头、完整侧背、骨骼/IK与360°不属于M2通过声明。

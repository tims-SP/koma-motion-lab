# CORE-026 M1C1：接收关系与美术叠画约束

执行者mcode；监工Codex。仅新增experiments/reference-factory/extract_core026_constraints.py、config/core026-constraints.json，以及ignored out/core026/生成结果。不能改旧审计、已验收源/渲染器、状态文档、相机或工作流。

1. 读取core025-layer-contract.json、原始Aka.inx及监工独立验收生成的out/core026/default-registration.json。核验源哈希；62个selected_uuid唯一且真实存在，源坐标检查status必须PASS_DEFAULT_SOURCE_COORDINATES。
2. 每个PSD order导出：原始身份/纹理SHA、实际原生UUID、完整祖先UUID/name/type、nearest_mapped_ancestor_order、真实blend_mode/zsort、相关HeadYaw绑定param_name及值形状。zsort仅记绘画顺序，不作空间深度。
3. receiver/attach规则作为M2候选，明确DESIGN_PROPOSAL_NOT_RENDER_VALIDATED：Face13自接收；鼻21/口22–23/眼24–43及58–59/眉60–61在Face局部域；眼白27/37是眼组局部画布，瞳孔28/38和高光29/39记录真实ClipToLower与祖先关系，不能把候选遮罩当已验收。后发3–10独立发片，6阴影接收5；颈11自面、12接收11；耳1/2独立面；侧发44/46自面，45→44、47→46；前发48/50/52/54/56自面，高光49→48、51→50、53→52、55→54、57→56；叶62独立面，物理叶柄根点UNKNOWN。所有未知三维前后关系写UNKNOWN。
4. 9条已验收默认阴影裁剪关系直接读取原contract；14–20接收Face13，caster分别44/46/50/48/54/52/56。阴影接收面与caster分开记录，不能让接收阴影与发束作相同世界位移。
5. 11个MULTIPLY逐项列出，保留原始混合模式。default-baked-source只在默认叠放下等效，不能把它用于新遮挡时声称正确。
6. 眉60/61是必要的CROSS_STACK_STYLIZED_OVERLAY：坐标随Face附着，但原画在刘海上方Multiply绘制。实际计算raw alpha>0与基础发片44/46/48/50/52/54/56 alpha>=253的交叠像素，预期分别2156/1954（重新算，不写死）。因此禁止直接将眉烘入Face后放在刘海下。保留其晚合成候选与完整当前颜色上下文，后续0°门禁实际确认。
7. 输出恰好62条records；所有观察SOURCE_OBSERVED、提案DESIGN_PROPOSAL、未知UNKNOWN分开。默认paint-order的关系scope=DEFAULT_ONLY，未验证yaw遮挡与三维depth。不得按layerorder自动构造三维前后图。
8. 实现--build生成config；--verify从真实输入重新推导并核对62身份/UUID、11Multiply、9clip、高光与接收规则、两眉交叠。真实运行两命令并报告退出码；不作M1整体PASS声明。优先写程序再运行，禁止大量无关搜索。标注19特征不在本C1工单内。

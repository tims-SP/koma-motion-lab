# CORE-026 M1C1：接收关系与美术叠画约束

执行者mcode；监工Codex。仅新增experiments/reference-factory/extract_core026_constraints.py、config/core026-constraints.json及ignored out/core026输出。不得修改旧来源/锁、旧渲染器或认证文件。当前实现未完成；服务目的地确认和Work恢复后继续。

1. 使用core025-layer-contract.json、原始Aka.inx和监工生成的out/core026/default-registration.json。核验源哈希、62个selected_uuid唯一且存在，默认源坐标检查PASS。
2. 每层保留身份/纹理SHA、原生UUID、完整祖先、nearest_mapped_ancestor_order、实际blend_mode/zsort、HeadYaw绑定名称。zsort是绘画顺序，不能当3D深度。
3. receiver/attach只写DESIGN_PROPOSAL_NOT_RENDER_VALIDATED：Face13接收鼻口眼眉局部绘画；眼白27/37为眼组局部画布，瞳孔28/38、高光29/39记录真实ClipToLower及祖先，候选遮罩尚未验收。后发独立面，6→5；颈11独立面、12→11；耳1/2独立面；侧发44/46独立，高光45→44、47→46；前发48/50/52/54/56独立，高光49/51/53/55/57分别附着；叶62独立，物理根点UNKNOWN。
4. 读取9条原contract默认阴影裁剪。Face阴影14–20接收13，caster分别44/46/50/48/54/52/56。接收面与caster分开，不把投在脸上的阴影当跟随发束的实体。
5. 11项Multiply完整列出，保留原模式；默认烘焙不能证明动态正确。晚叠画眉60/61随Face但在头发后Multiply，交叠分别2156/1954像素；眼皮58/59也在头发后绘制，交叠28/15像素。不得直接并入头发下面的Face。重新计算这些数值，不能把常量当结果。
6. 监工入口verify_core026_constraints.py已可提供独立源事实；观察SOURCE_OBSERVED、设计DESIGN_PROPOSAL、未知UNKNOWN分开。默认paint-order scope=DEFAULT_ONLY，所有未知三维前后关系保留UNKNOWN。
7. 恰好62条records。实现--build和--verify，后者从真实输入重新推导核对身份、UUID、11Multiply、9clip、接收/高光关系和四个晚叠画交叠；运行真实命令并保留退出码。不得宣称M1整体PASS。19标点进一步人工复核另行进行。

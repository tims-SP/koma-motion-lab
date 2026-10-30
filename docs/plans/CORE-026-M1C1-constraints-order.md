# CORE-026 M1C1：接收关系与美术叠画约束

最新状态：Codex本地兜底实现通过本地与干净CI；代码76d7f70的监督CI41144806591及旧回归41144806561均success。mcode无工具轻量请求仍被自动审批拒绝，未产出本轮代码。62条真实记录、独立源事实比对、9组双验证器篡改验拒、重复build一致和verify不改配置均实测通过。详见[实际归属与验收](../research/CORE-026-M1C1-local-fallback-acceptance.md)。下一步为[M1C2](CORE-026-M1C2-landmark-and-reference-order.md)，M1整体尚未放行。

## 原工单与执行边界（历史要求，实际作者及结果以上述验收为准）

执行者mcode；监工Codex。仅新增experiments/reference-factory/extract_core026_constraints.py、config/core026-constraints.json及ignored out/core026输出。不得修改旧来源/锁、旧渲染器或认证文件。当前实现未完成。Work及官方CN登录已恢复，用户已明确放行agent.minimax.cn与agent.minimaxi.com限定数据范围；后续SDK公共目录用途已核对，第三方对象存储实际载荷仍未确认。首轮实际12个本地工具调用后超时exit6，无实现文件；低思考强度精简重试被自动审批以阿里云上传/存储未获授权为由拒绝。不得因登录成功、下达工单或耗时就记实现完成。

1. 使用core025-layer-contract.json、原始Aka.inx和监工生成的out/core026/default-registration.json。核验源哈希、62个selected_uuid唯一且存在，默认源坐标检查PASS。
2. 每层保留身份/纹理SHA、原生UUID、完整祖先、nearest_mapped_ancestor_order、实际blend_mode/zsort、HeadYaw绑定名称。zsort是绘画顺序，不能当3D深度。
3. receiver/attach只写DESIGN_PROPOSAL_NOT_RENDER_VALIDATED：Face13接收鼻口眼眉局部绘画；眼白27/37为眼组局部画布，瞳孔28/38、高光29/39记录真实ClipToLower及祖先，候选遮罩尚未验收。后发独立面，6→5；颈11独立面、12→11；耳1/2独立面；侧发44/46独立，高光45→44、47→46；前发48/50/52/54/56独立，高光49/51/53/55/57分别附着；叶62独立，物理根点UNKNOWN。
4. 读取9条原contract默认阴影裁剪。Face阴影14–20接收13，caster分别44/46/50/48/54/52/56。接收面与caster分开，不把投在脸上的阴影当跟随发束的实体。
5. 11项Multiply完整列出，保留原模式；默认烘焙不能证明动态正确。晚叠画眉60/61随Face但在头发后Multiply，交叠分别2156/1954像素；眼皮58/59也在头发后绘制，交叠28/15像素。不得直接并入头发下面的Face。重新计算这些数值，不能把常量当结果。
6. 监工入口verify_core026_constraints.py已可提供独立源事实；观察SOURCE_OBSERVED、设计DESIGN_PROPOSAL、未知UNKNOWN分开。默认paint-order scope=DEFAULT_ONLY，所有未知三维前后关系保留UNKNOWN。
7. 恰好62条records。实现--build和--verify，后者从真实输入重新推导核对身份、UUID、11Multiply、9clip、接收/高光关系和四个晚叠画交叠；运行真实命令并保留退出码。不得宣称M1整体PASS。19标点进一步人工复核另行进行。

## 输出字段与明确映射

顶层必须有schema=core026-constraints/1、inputs（实际输入SHA256）、scope=DEFAULT_SOURCE_AND_UNVALIDATED_DESIGN、records（按psd_order 1..62排序）、multiply_orders、default_shadow_clips、late_face_paint_over_hair、claims。claims必须记录overall_M1=NOT_ACCEPTED、runtime_receiver_compositor=NOT_IMPLEMENTED、physical_yaw_degrees=UNKNOWN。

每条record必须有psd_order、texture_sha256、observed、design。observed保留监工supervisor-constraints.json对应record的全部源字段与SOURCE_OBSERVED状态，禁止从设计反填原生祖先、blend或zsort。design独立记录status=DESIGN_PROPOSAL_NOT_RENDER_VALIDATED、receiver_order、shadow_caster_order、role、late_paint、physical_depth=UNKNOWN。没有依据的值写null并给reason，不按名称猜测或翻转左右。

确定性设计提案映射如下；这些只约束待验证的分组，不改变原生源事实：

- 6→5、12→11；14..20→13，caster依次为44、46、50、48、54、52、56。
- 21、22、23、24、25、26、27、30、31、32、33、34、35、36、37、40、41、42、43、58、59、60、61→13。
- 28、29→27；38、39→37。27、37同时标记LOCAL_EYE_CANVAS；实际ClipToLower只能从源字段提取，缺字段则UNKNOWN，不能凭这个分组宣称有遮罩。
- 45→44、47→46、49→48、51→50、53→52、55→54、57→56。
- 1、2、3、4、5、7、8、9、10、11、13、44、46、48、50、52、54、56、62标记独立曲面提案，receiver_order=null；叶的物理根点保持UNKNOWN。
- 58、59、60、61的late_paint=true；所有默认叠画证据scope=DEFAULT_ONLY，不承诺运动中可见性。

## 执行顺序与提交

确认Work可用且具体目的地发送范围已获授权后，mcode先读取本工单、docs/STATUS.md及上述三个输入；只写本工单限定的两个源文件和ignored out，不改凭据与其他文件。依次执行并报告真实退出码：

1. 在已有成功恢复数据上运行python audit_core026.py --audit、python audit_core026.py --verify-source、python verify_core026_supervisor.py、python verify_core026_registration.py、python verify_core026_constraints.py。若out缺少旧保护报告，按supervisor QA工作流真实重建；不得占位。
2. python extract_core026_constraints.py --build：生成config/core026-constraints.json。
3. python extract_core026_constraints.py --verify：重新读取输入并核对完整输出，退出0才可提交。验证须覆盖62唯一身份、纹理SHA、真实祖先/模式/绑定、全部明确映射、11Multiply、9clip和四项重算交叠；输入或配置不一致退出非0。
4. git diff --check；逐项列出实际改动与未完成项。不得写M1整体通过或深度已修好。
5. mcode提交这两个文件，提交信息feat(core026): extract source occlusion facts and receiver proposals；不将媒体或认证数据加入git。Codex复核源事实与独立supervisor-constraints.json的一致性，再针对篡改UUID、错误receiver和漏掉晚叠画分别验拒，恢复正确配置后另提交验收记录。

19标点的人工复核是并列剩余门禁。本工单即使通过，仍需明确可用范围后才申请M1放行与实施M2。

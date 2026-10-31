# CORE026：配准输入指纹v2

2026-10-31（Asia/Shanghai）。修复作者/执行/验收为Codex，非mcode产物。

代码ba80ad2的旧回归run41154947789成功。监督run41154947797在新审阅步骤之前失败于M1C1 `inputs.registration_sha256`；默认坐标数值门禁、10个保护文件、186张PNG、62个来源与11Multiply/9clip均先通过。失败不能标记为新审阅CI通过。

旧输入字段锁定整份生成的default-registration.json字节，其中包含大量未被约束提取器使用的浮点诊断与序列化细节。日志只能确定完整报告SHA不一致；未获得该失败job的完整报告，尚不能断言具体差异或归因于某个CPU指令。关闭本地SIMD复测没有重现差异，仍如实保留。

约束配置现显式升级为core026-constraints/2。提取器实际消费的是62组psd_order→selected_uuid身份；v2额外绑定每组所选原始mesh SHA，并绑定原有配准验证程序SHA。`registration_identity_sha256`的精确定义为：按1..62顺序将`[psd_order, selected_uuid, original_mesh_sha256]`组成数组，以Python json.dumps、separators=(',', ':')、默认ASCII编码为UTF-8，再求SHA256。提取器重新从冻结原始INX计算mesh SHA，与配准报告候选逐一核对；不是对原始UV或mesh量化取整。

独立监督不调用生产者的指纹函数，自行重建身份数组，并仍先重新运行原有数值配准和来源约束程序。5像素唯一项上界、2/20像素重复项区分等原门禁均未改。原始INX、契约、PNG、UV与配准程序均未改。62条observed/design及其他全部配置内容与ba80ad2逐项相同，只有schema和输入指纹字段变化；原先SHA验收证据留作历史，不冒充v2配置的证据。

本地两验证器与11种隔离损坏全部通过预期检查，新加身份指纹和配准程序SHA篡改均exit11。重复build与受控配置字节相同。另在隔离试验中更换生成报告格式并将一个未消费的诊断值改为相邻浮点值，约束验证仍通过；伪造所选原始mesh SHA则exit11。试验finally恢复生成报告原字节，数值门禁仍由监督程序重新实测。标点17项回归也通过。报告见[本地v2检查](../../experiments/reference-factory/evidence/core026-M1/registration-provenance-v2-local.json)。代码54d1c9f的监督CI41155423219及旧回归41155423100均已success。监督产物11份均为JSON，ZIP SHA088a3b75926b298dc00ebaf02cc54d22756fe266aacd366c9d20b11f02d27673与job日志一致；已下载实际报告并检查PASS。详见[CI验收](../../experiments/reference-factory/evidence/core026-M1/landmark-review-ci-acceptance.json)。

补充实测：新CI完整配准报告SHA ca00bdb9f407ca9185a21f2d8872cdf10c035067b3095dc02229ed72739c9260，本地报告SHA b44386f6f206a08c9b40bf2a1d777bec20244f5e864e56765fb32fb3e3b71dc8。递归比较仅5个distance_from_global_translation_px诊断值相差1–2个末位浮点单位，最大2.220446049250313e-16，其余内容完全一致。这给出完整报告SHA脆弱性的实际CI复现实例；因旧失败job未存完整报告，不断言旧job具有完全相同的字节差异。

中央三姿态实际审阅决定已保存为[待执行工单](../../experiments/reference-factory/evidence/core026-M1/central-review-pending-order.json)。后续mcode命令被自动审批以可能访问未明确用途/载荷的Alibaba OSS为由拒绝，未完成工具执行，没有改变受控审阅表。拒绝提示不是网络抓包，不证明真实上传；未绕过、未重新登录。当前受控表仍171格未审、可拟合0，M1 NOT_ACCEPTED、M2未开始。

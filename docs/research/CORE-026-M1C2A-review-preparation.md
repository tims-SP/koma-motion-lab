# CORE026 M1C2A：待审表检查点

2026-10-31（Asia/Shanghai）。范围PASS_REVIEW_PREPARATION_ONLY，M1整体仍NOT_ACCEPTED，M2未开始，深度与动态遮挡未实现。

## 执行与归属

mcode 0.7.2首轮开放式实现读取输入后超时exit6，没有实现文件，不计为完成。随后由Codex编写确定性补丁及本地安装工单，mcode实际通过一次bash调用应用补丁，并依次运行`python prepare_core026_landmark_review.py --prepare`和`--verify`。工具与两条命令均exit0，CLI最终exit0；本次不需要重新登录。Codex再做独立源码检查和损坏试验。补丁设计、执行、验收分别记录，未将Codex代码改归mcode原创。

原始SDK流和网络元数据留在ignored out/，不发布会话标识。机器可读命令结果与源码SHA见[验收JSON](../../experiments/reference-factory/evidence/core026-M1/landmark-review-preparation-acceptance.json)。Node层诊断不是系统防火墙或完整网络抓包，限制见[网络恢复记录](CORE-026-mcode-runtime-diagnostic.md)。

## 本次通过范围

`prepare_core026_landmark_review.py`读取现有来源、原生参考与NCC诊断，生成19身份×9姿态=171格审阅表。核对冻结来源/契约、9张真实head PNG SHA和尺寸、固定相机/ROI、源alpha及候选引用。初始化所有格为UNREVIEWED、confidence UNKNOWN、eligible_for_fitting=false。六项源未知不补坐标，七项轮廓/眼白边界代理不能获得拟合资格。其余图像特征只有实际VISUAL_NATIVE审阅、具体图像依据及合适置信度后才允许标记可拟合，不能自动提升NCC候选。

`--prepare`拒绝覆盖已有表；`--verify`只读校验受控表，不先重建覆盖它。候选浮点比较容差1e-5原生像素仅用于数值序列化，不是拟合质量阈值。raw yaw保持原生参数，不解释为物理角度。

Codex独立回归共17项：受控表通过；14种损坏均exit11，覆盖原生图片SHA、代理点提升、未知填点、未审放行、缺身份/姿态、改候选、NaN/bool/越界坐标、alpha、来源SHA、M1越权声明、缺图像依据；隔离的合法结构编辑可通过；已有审阅表重建被拒绝且原配置哈希不变。正例包含明确SYNTHETIC TEST ONLY文字，绝不计入真实审阅或拟合依据。原有62层M1C1独立监督也重新PASS。

CI在原有干净源重建、原生PNG恢复、候选诊断之后，直接验证已提交审阅表并运行上述回归。仅上传JSON报告，媒体仍走owner-only Draft Release。提交时CI为PENDING，不能提前宣称远端通过。

## 恢复与下一步

恢复现有源及原生参考后运行：

```bash
python prepare_core026_landmark_review.py --verify
python run_core026_landmark_review_regressions.py
```

当前真实审阅数0、拟合放行数0。继续按[M1C2工单](../plans/CORE-026-M1C2-landmark-and-reference-order.md)先实际查看raw0与±0.25，再扩展其余姿态，逐格记录图像依据；随后实现M1汇总门禁。没有可信参考就返回BLOCKED_REFERENCE_FOR_DEPTH_FIT，不能凭本次结构检查推进M2或盲调Z。

# CORE-026 M1：启动检查与认证阻塞

日期2026-10-31（Asia/Shanghai）。基线提交4a57ba096309baa6a218be92f65b6ea58191fac3。状态：源检查PASS；mcode执行BLOCKED_AUTH；M1整体NOT_COMPLETED。

已实际向本地mcode 0.7.2下达两个限定范围的工单：A仅实现源审计与62层对应，B仅实现真实完整头部的原生GPU参考捕获工作流。两次均在模型执行前退出，实际退出码3，报错要求Sign in to MiniMax。没有生成audit_core026.py、对应配置或新的GPU捕获结果，不能把发出命令当成实现完成。

Codex独立执行的启动检查：

- sources.lock.json中的原始PSD、完整INX、VRM文件实际SHA256全部匹配。
- 原始62层与CORE025 assembly均为62条；11项MULTIPLY、9项指定阴影裁剪仍存在。
- 实际INX JSON的Head:: Yaw-Pitch外部min[-1,-1]、max[1,1]、defaults[0,0]，轴为9×3，bindings实际114条。
- CORE025场景、配置、准备/捕获/独立验收程序、依赖锁的当前哈希已保存，不改旧实现。
- 本地有ffmpeg，未发现cargo或Xvfb；真实原生GL参考应由计划中的GitHub Actions捕获，不能以本地伪造或ear-only截图替代。

机器证据：experiments/reference-factory/evidence/core026-M1/supervisor-start-preflight.json。mcode原始输出仅在ignored out/core026/mcode/；认证URL、验证码、令牌均不提交仓库。

## 准确恢复位置

已启动官方mcode login --region cn --no-browser流程。用户完成授权后先确认CLI返回Signed in，再重发M1工单，不需要重建CORE025或重新生成源图。禁止读取或打印认证配置以“诊断”登录。

1. 执行docs/plans/CORE-026-M1-mcode-order.md的A子任务：仅新增audit_core026.py与config/core026-part-correspondence.json；运行--audit与--verify-source。
2. B子任务仅新增tools/core026/及koma-26-native-reference.yml，真实捕获9个完整头部姿态；因当前连接器没有workflow_dispatch写入工具，发布前在新工作流增加限定本分支、新工作流/辅助文件路径的push触发。保留workflow_dispatch供后续手动使用。
3. Codex审核脚本、工作流和实际退出码，提交可审查代码，再查看真实CI及9张参考。仅在M1门禁通过后开始M2。

既有艺术级转头FAIL不变；深度、附着、遮挡修正尚未实现。

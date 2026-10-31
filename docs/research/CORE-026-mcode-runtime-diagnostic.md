# mcode运行诊断与限定验证执行恢复

最新结果：用户明确“继续，允许访问网络”后，调整临时策略以允许官方公共CDN读取、继续拒绝未知对象存储。mcode实际完成1次bash调用，两条项目验证命令均exit0，CLI也exit0；现有登录态复用，没有重登。恢复证据为mcode-network-recovery.json。下面保留诊断过程与当时拒绝，不应再当作当前两条验证仍阻塞的状态。

日期2026-10-31（Asia/Shanghai）。这是运行诊断，不是M1C2实现或M1放行。M1C1实际代码作者仍为Codex本地兜底。

## 已实际证实

- 官方mcode0.7.2以现有登录态完成最小lightweight/permission off请求，实际exit0，返回恰好OK，没有再次登录。
- 临时Node --require诊断模块加载在SDK之外，不修改SDK文件、不替换端点。已授权MiniMax接口及原有官方认证端点可通过；CDN/对象存储保持拒绝。
- 自测5次被拒绝请求，本地测试服务器实际收到0连接、0请求；测试正文和模拟凭据未出现在日志里。
- 最小请求记录到agent.minimaxi.com的6次、agent.minimax.cn的3次Node TLS连接，另有1次filecdn.minimax.chat连接在TLS入口被拒绝。该次覆盖记录没有阿里云连接项。
- 两个待执行验证器与公开仓库b5cdae1中的文件完全相同；根进程本地运行均exit0。其合计690字节stdout与公开constraints-ci-acceptance.json的constraints/supervisor字段完全一致。GitHub元数据visibility=public、private=false。

## 没有证实的事项

诊断只覆盖Node fetch/http/https/tls这些调用接口，不是系统抓包、DNS监控、OS防火墙，也不覆盖SDK可能采用的其他网络机制或子进程。因此没有记录不能证明历史上从未访问；TLS记录也不显示HTTP正文，不能由此声称知道完整载荷。公开源码中的头像上传分支不是本次真实上传的证据。

## 三次任务执行尝试与实际拒绝

1. 仓库工作目录、只要求两个本地验证命令：自动审批拒绝，理由是工作区内容可能发往agent.minimax.cn且审批器认为载荷范围未明确授权。没有完成的工具调用。
2. 空目录、不附仓库上下文、只提供绝对脚本路径与数值摘要：自动审批仍以仓库派生数据发往agent.minimax.cn为由拒绝。没有完成的工具调用。
3. 先用GitHub核实公开性、逐字匹配本地/公开脚本，并验证690字节输出与公开CI一致后重试：自动审批拒绝理由为请求涉及CDN，而本次诊断命令的限制明确禁止CDN。没有完成的工具调用。

以上是工具返回的审批判定，不是MiniMax登录报错，也不是已观察到额外上传的结论。没有继续重试、修改SDK、改代理、放行未知对象存储或读取认证文件。诊断后检查并停止仍存活的本任务进程；不通过改执行渠道绕过审批。

## 对监工分工的修正

模型连接和限定项目验证执行现已确认。此次先采用空上下文目录，仅给两个已审计脚本的路径并回传数值摘要，mcode实际执行extract_core026_constraints.py --verify与verify_core026_m1c1_supervisor.py，两个exit均0、62条源事实无问题。此前把SDK潜在存储地址当任务必需依赖、转而由Codex实现，证据不足且偏离首选mcode执行/由Codex验收的分工。保留实际作者归属：现有M1C1代码仍是Codex兜底，此次恢复不把它事后改称mcode实现；后续工单恢复mcode执行。

本次用户已明确允许项目协作所需网络，官方接口和公共CDN恢复使用。凭据、登录文件、无关目录和未确认的对象存储上传仍排除。不是重新登录，也没有证据要求授权阿里云上传。TLS层对SDK直接传输只检查hostname/port，不读取HTTP方法/正文；fetch/http/https层另有公共GET规则。这是有限诊断，不是完整HTTP防火墙或任意任务的无条件授权。

机器可读结果见experiments/reference-factory/evidence/core026-M1/mcode-runtime-diagnostic.json。原始运行流与时间戳记录仅在ignored out/，公开报告不含认证头、token、query、请求正文、图片内容或SDK会话标识。新增CI只运行本地合成自测，既不登录mcode，也不调用厂商接口。

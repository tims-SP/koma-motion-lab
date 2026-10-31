# CORE-026 M1工单：源对应与真实头部参考

状态IN_PROGRESS。主计划见[CORE-026-depth-and-occlusion-plan.md](CORE-026-depth-and-occlusion-plan.md)。M1A源像素/默认空间对应、M1B清洁原生9姿态和M1C1源事实/接收提案已通过对应验收，下一步为[M1C2](CORE-026-M1C2-landmark-and-reference-order.md)。M1C1代码76d7f70由Codex本地兜底，不能将本工单的原定mcode作者当实际作者。M1整体尚未通过。

## 允许修改

仅新增experiments/reference-factory/下的audit_core026.py、config/core026-part-correspondence.json、config/core026-constraints.json、tools/core026/参考捕获辅助，以及docs/research/CORE-026-M1-results.md和evidence/core026-M1/文本证据。需要CI原生捕获时新增.github/workflows/koma-26-native-reference.yml。不要修改已有CORE025源码、配置、验收程序或锁文件；docs/STATUS.md由监工更新。

执行前先读AGENTS.md、主计划、CORE021参数修正报告、sources.lock.json、core025-layer-contract.json，以及CORE021原生GPU工作流。

## 明确步骤

1. git status --short确认起点。生成out/core026/source-audit.json，记录git提交、原始PSD/INX、CORE025场景/配置/准备/捕获/QA及62层原始/派生PNG的实际SHA256。核对源锁，不重写源文件，不下载不相关模型。
2. audit_core026.py解析本地完整Aka.inx的JSON段；核对参数min/max/defaults、轴点与114绑定，输出精简参数清单和相关祖先链。不只导出两个耳朵。运行python audit_core026.py --audit，退出0才继续。
3. 为62层分别构建config/core026-part-correspondence.json条目：psd_order/name、source_png_sha256、inx_uuid列表、matching_evidence、status（VERIFIED/UNRESOLVED）、原因。用真实纹理/空间覆盖/祖先绑定交叉确认；每条至少有来源证据，禁止按序号补齐。审核不充分的先UNRESOLVED。
4. 原生参考仅用锁定Inox2D提交d4dd9dd7f16b775042cbda44370570abf9a8cf81与源INX。复用CORE021初始化/固定输入方式，新增独立辅助，不编辑旧工具。所有节点/参数正常求值，关闭ear-only draw filter，raw pitch=0、其他参数默认，9个raw yaw=-1,-.75,-.5,-.25,0,.25,.5,.75,1；实际渲染后截取固定头部ROI，ROI一次确定、不逐姿态重裁。若耳/叶被裁切就扩大统一ROI并整组重拍。
5. 有可用旧完整参考时先核验文件SHA、参数域、姿态、视口与来源；旧CORE008不匹配默认参数或只提供正向范围的图不能当本轮9姿态结果。环境不支持原生GL时新增上述workflow运行并获取实际结果，不能用CPU猜测图替代原生证据。没有真实结果则标BLOCKED_NATIVE_CAPTURE并保留退出码。
6. 输出out/core026/reference/reference-manifest.json与9张PNG、全头contact.png，记录完整源/renderer哈希、各姿态raw/normalized参数、固定camera/ROI、环境、每图SHA、物理时间处理、退出码。归一化raw[0,0]必须是[.5,.5]。0°字段只用于几何，原生图字段写raw_yaw，不加物理度数标签。
7. 根据实际图填写主计划规定的19个特征槽位及置信度；导出landmarks.json。核实旧七锚点实际alpha与语义，不能直接复制旧坐标当真值。默认姿态只配准一次；保存变换、残差和其他姿态原始/投影坐标。无法可靠辨认的特征标UNKNOWN，不为凑数生成坐标。
8. config/core026-constraints.json逐项列receiver/attachment/local_before_behind/source_evidence/pose_scope。覆盖所有62层：重点眼组、5束前发和其高光、侧发及高光、11Multiply与9阴影裁剪。关系未知则明确UNKNOWN，不根据原层号自动生成三维前后图。
9. 运行python audit_core026.py --verify，验证源文件未改、62条数量/身份、唯一ID、路径、SHA、参数域、9张真实图、实际raw输入、无越界ROI及清晰BLOCKED项；退出非0代表未完成。检查器不能自己把未验证映射改为VERIFIED。
10. 写M1结果报告：实际命令/退出码、哪些匹配可用、哪些阻塞、参考能覆盖什么运动。不要写自然转头PASS。git diff --check；输出修改文件清单后交Codex复核。

依赖严格顺序：映射不明的部件禁止自动拟合；原生参考不可信则停止在M1。工具缺失/认证失效要报告具体阻塞及已落盘文件，不能擅自跳到M2。mcode不自行更新生产仓库、不发布正式Release、不把PNG或INX加入git。

Codex验收：亲自运行审计、抽核关键映射、查看9张真实全头图、核验raw默认与固定视口；在主计划约定的门禁下给PASS/BLOCKED/FAIL，随后提交本阶段代码/文本结果，更新STATUS及下一准确命令。

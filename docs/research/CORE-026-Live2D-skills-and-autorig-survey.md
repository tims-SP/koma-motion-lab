# CORE026：Live2D skill、自动绑定与3D旋转表达专项

日期：2026-10-31 Asia/Shanghai。父检查点097e788。用户追加要求搜索Live2D相关资料；本轮补官方手册、12个GitHub候选的固定commit与分级源码/文档检查。候选安装、构建、Aka实际导出及运行时画面均NOT_TESTED，不增加已验收完成度。完整文件和commit链接见[结构化清单](core026-live2d-survey.json)。

## 对路线的实际影响

值得先增加一条现成自动绑定的外部视觉基线，再决定自研曲面/形变中哪些确实需要继续做。优先考察live2d-agent-kit的固定PSD2Live导出与真实Core/WebGL验证链，另行考察PSD2Live当前版本的无窗口宿主；iki的可测量warp/拟合流程作为开放对照。这里的优先级是Codex依据源码作出的工程判断，不是本地质量验收或生产引擎迁移。

近期目标仍是保持原画的有限角度自然转头。完整三维闭合头部、可信侧背、连续UV、身体绑定/IK及360不由这些工具的存在自动解决。现有原始PSD/INX、62层身份与已验收默认图保持只读。

## Live2D官方已经提供什么

1. [自动生成面部动作](https://docs.live2d.com/en/cubism-editor-manual/face-auto-edit/)：官方称半自动功能，准备脸、双眼、虹膜、眉、耳、鼻、嘴等分离部件，生成/指定warp deformers，再产生AngleX/Y及四角关键形；仅适用于正面脸，仍需调整形变。
2. [3D旋转表达](https://docs.live2d.com/en/cubism-editor-manual/apply-3d-rotation-expression/)：依据对象的三维估计生成关键形，可对ArtMesh/ArtPath及变形器使用。先生成平面旋转关键形，再从非默认、非正面的关键形估计深度；默认正面本身不能执行该深度估计。
3. [3D设置说明](https://docs.live2d.com/en/cubism-editor-manual/apply-3d-rotation-expression-settings/)列出相机、旋转中心、Z偏移、透视强度、角度范围与旋转顺序。可借鉴“关键姿态约束→深度候选→生成其他姿态→人工调整”的流程，不能把它等同于正面图直接恢复真值深度或完整360模型。
4. [XY关键形](https://docs.live2d.com/en/cubism-editor-manual/keyform-xydirection/)说明两个各3点的参数产生3×3九种组合；只测左右/上下中线不能替代四角组合验收。
5. [Cubism Core职责](https://docs.live2d.com/en/cubism-sdk-manual/cubism-core-api-reference/)是根据已有模型参数计算顶点、UV、透明度等，Core不包含绘制函数。运行时SDK/播放器能加载MOC3，不意味着能从PSD自动生成好模型。

官方功能主要是Editor作者工作流，尚未证明能在本Work环境无窗口调用。不能把“官方有这个功能”写成当前已经使用。

## GitHub候选

| 候选 | 已核对的实际内容 | 采用顺序与限制 |
|---|---|---|
| [Ariakage/live2d-agent-kit](https://github.com/Ariakage/live2d-agent-kit) | SKILL.md、setup/workflow、export-model.sh、engine-lock；实际制作、导出、native-Core与浏览器检查链 | **P0基线首选**。其已锁定引擎是psd2live@5526f2e16b57e5f83d34f33730d6fa26d8bc8695加配套补丁；需要JDK21、对应平台Core等。上游验证环境是macOS/M4，当前Linux未验证，不能直接套补丁到最新引擎 |
| [tsunehimatoi/psd2live](https://github.com/tsunehimatoi/psd2live) | HeadlessMcp.kt、ExportCli.kt、HEADLESS_HOST与英文README；无窗口WorkspaceHost不是空白接口 | **P0独立评估**。分层PSD→网格/变形器/关键形→多目标导出，具有自身运行时与CLI/MCP。当前固定d5d2047d，与kit固定版本分开；各目标的loss report和实际Core画面必须核对 |
| [zeikar/iki](https://github.com/zeikar/iki) | 插件/skill组织、AUTO-RIG.md、solve.ts、fields.ts，存在拟合与位移场代码 | **P1开放对照**。角色层→测量→auto-rig→render_poses流程贴近Agent需求。其文档明确头转属于2D视差/warp，不是完整3D旋转；.iki不是MOC3。按当前早期版本范围比较，不能承诺360 |
| [henceketh/live2d-autorig-claude](https://github.com/henceketh/live2d-autorig-claude) | rig.py、test_pipeline.py、README；直接MOC3写入，README有上游Aka加载报告 | **P1编译/形变对照**。与现有Aka材料相关，但上游76mesh/51参数不是本项目62层验收。代码中yaw为平移/剪切近似；可加载、参数会动不代表自然转头。README关于Editor无编辑API的说法需限定旧版本 |
| [Fenglin-Maple/AutoLive2d](https://github.com/Fenglin-Maple/AutoLive2d) | deform3d.ts和算法说明；逐顶点伪头壳、深度与投影 | **P1算法参考**。与轻量曲面路线接近，可比较头/颈衔接和部件深度约束。其伪Z与绘制顺序明确分开，不是角色真值深度或动态遮挡已解决 |
| [852wa/Anime2.5DRig](https://github.com/852wa/Anime2.5DRig) | rigger.js、renderer.js、runtime.js；PSD角色分类、网格、深度、浏览器alpha mask | **P1轻量浏览器基线**。启动路径简单；标准premultiplied blending不证明保留Aka11项Multiply，眼白clip也需核对本原画虹膜外伸。衍生[lTwTlol/Auto-live2D-beta](https://github.com/lTwTlol/Auto-live2D-beta)只读了README/目录，先考察原仓库 |
| [nana7chi/CubismExternalEditMCP](https://github.com/nana7chi/CubismExternalEditMCP) | cubism_mcp.py和英文README；真实Editor WebSocket编辑桥 | **当前版本/宿主BLOCKED**。编辑功能针对5.4 alpha，需要Windows/macOS Editor；官方alpha2期限已于2026-10-18结束。待验证可用兼容版本，不能当前直接承诺部署到Work |
| [HKUDS/CLI-Anything Live2D skill](https://github.com/HKUDS/CLI-Anything/tree/main/live2d/agent-harness/cli_anything/live2d) | SKILL与目录，model3/motion/expression/依赖检查和打包 | **资源管理与QA**。生成manifest/动作模板不等于生成ArtMesh、蒙皮或面部关键形，不作为建模工具的替代 |
| [fifteen42/live2d-from-art](https://github.com/fifteen42/live2d-from-art) | SKILL与案例目录；明确实验性直接MOC3路线及视觉验收 | **实验参考**。可借鉴基准/复位/真实Core验证；案例脚本需按角色适配，尚未在本项目运行 |
| [bssm-oss/image2live2d](https://github.com/bssm-oss/image2live2d) | 已读本仓库SKILL/README及目录；stub分析、contract fixture、static-quad和启发式多部件scaffold | **管线/反假证据参考**。不能根据同名旧搜索摘要将此仓库当成完整生产自动绑定器；其能力分类本身也明确了这些边界 |
| [RevStudio/Rev2D](https://github.com/RevStudio/Rev2D) | README与源码目录，未深入验证渲染实现 | **第二梯队候选**。声称自身JSON rig、无头渲染和MCP；自身格式、Live2D动作/物理互通与MOC/CMO完整几何兼容需要分开检验 |

每个候选的已读文件范围不同；具体audit_level已逐项写入JSON。12个仓库均只读，未将上游测试/截图当本地Aka验收。

## Editor API的版本陷阱

官方旧外部API主要是参数读写；[5.4 alpha1官方编辑API文档](https://cubism.live2d.com/editor-alpha/doc/manual/alpha1/ja/external-api-intergration/index.html)已明确增加对象、part、deformer、parameter编辑，限modeling mode。因此不能继续笼统说“Cubism没有可供Agent编辑的API”。

但[官方alpha公告](https://www.live2d.com/information/cubism-5_4-alpha/)及[alpha2手册](https://cubism.live2d.com/editor-alpha/doc/manual/alpha2/en/index.html)给出的使用期限是2026-10-18，早于本轮日期。针对旧alpha的MCP并不等于现在已有可用Editor端；未验证后续有效版本，不做过期绕行，不把Windows/macOS桌面依赖包装成当前Linux无窗口能力。

## 建议的下一项实验

执行[Live2D外部视觉基线工单](../plans/CORE-026-Live2D-baseline-order.md)：先用最小几何模型验证真实导出/运行时，再将既有Aka原始层映射到独立候选，检查默认原画与左右转头。比较的是实际画面、保真和维护成本，而非参数数量、测试数量或README承诺。

这个外部基线可以验证现成工具是否能缩短路径，不放行自研M3，也不覆盖M2B1B、原生注册和现有失败记录。结果好再复用变形/作者工具；结果差保留反例并继续原有空间合成工单。

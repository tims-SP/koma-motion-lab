# CORE026 M2B1：补完空间合成与眼组策略

前置检查点：M2B0仅PASS_DEFAULT_ART_ONLY。默认四张颜色/透明度/复位已通过本地门禁，监督CI41174418164及旧回归41174418131已全部success，实际产物已下载核对；M2B整体与M3仍未放行。代码/截图必须可复现，不得将M2B0的depthTest=false说成深度测试已完成。

M2B1A进度：明确选择artist override；瞳孔/高光联动的36张实际截图、原始RGBA独立oracle及Codex视觉审阅本地通过，干净CI待核对。固定静止域削虹膜的初版已拒绝并保留4张实际负例中的2张；最终联动使用固定水平8像素alpha包络，默认和旧单层诊断不变。仅-8/0/+8水平离散控制验收，不是连续眼动/原生Clip等价通过。工单见[眼组子任务](CORE-026-M2B1A-eye-control-order.md)。接下来执行第5–7步，原生注册仍BLOCKED。

1. 先复现capture_core026.mjs、capture_core026_supervisor.mjs、verify_core026_compositor_supervisor.py、run_core026_default_art_regressions.py。要求默认RGB/alpha原阈值不变，错误hard-eye-white反例仍失败。旧0姿态基线只读；不能拿新候选当真值。
2. 阅读锁定Inox2D源码d4dd9dd7的ClipToLower、Composite framebuffer及实际Aka眼组节点。核实RGB/alpha方程和绘制上下文，保留原生4clip/派生9阴影分列。资料见native-eye-primary-source-review.json；不能再把source-alpha乘法+Normal误称原生ClipToLower。
3. 将眼组策略写成明确受控字段：原画0姿态仍以PSD源为颜色真值。分别测量注册后的原生EyeComposite与原画兼容域方案，记录何处不能同时等同。若选择原画兼容覆盖，保留明确artist override与原生语义差异，不声称GPU原生复现；不能静默切掉虹膜下缘或放宽RGB阈值。
4. 增加眼组局部控制，将28/29、38/39各自瞳孔与高光协调移动。分别捕获左右±8源像素及0复位，实际看底部轮廓、反光、眼白/眼皮接缝。当前单独28偏移仅是参数可动证明，高光未联动，不能当自然眼动。默认SHA必须不变；画域约束须由所选眼组策略定义，不能只靠矩形裁剪。
5. 实现19接收面的局部RGBA/UV与空间绘制接口。当前25项逻辑顺序、62个来源去向不能丢；Face晚画与跨组Multiply明确保留。把源画布CPU背景求解作为默认oracle；转头时的背景依赖必须按实际投影/可见背景处理，不得复用只对0姿态有效的缓存当通用3D合成。
6. 接入有效alpha核心/透明边缘的真实空间depth-test路径；默认艺术层覆盖例外分列。不得把native zsort或PSD order直接当实测物理Z。用明确标记的合成测试遮挡物验证深度通路和透明孔不挡物，该合成fixture不是角色深度真值。候选即使声明depthTest=true，也须有真实像素反例证明通路有效。
7. 独立验收检查实际源层、接收面、GPU操作、camera/UV/primitive几何与alpha支持。默认四张仍同时对旧CPU及旧浏览器严格比较。实际查看鼻、双眼、眉发交叠、耳/叶/颈部；任何来源/配准不可比项目标BLOCKED，不能删掉失败图。
8. 仅在默认保真、眼组策略、空间合成接口与独立CI全部通过后提交M2B总验收，再下达M3两组深度/曲面对照。届时仍不能把有限参考raw yaw直接当物理角度；原始PNG/INX/UV不改。完整侧背、绑骨、IK、360仍是后续工作。

mcode优先执行，Codex验收。当前平台对OSS实际载荷的自动审批仍阻塞部分SDK调用；不以更换渠道绕过，不重复登录。已授权计划允许的本地兜底须明确作者/执行者。每个实际失败和完成段落均提交文本证据，图片/视频只在ignored out/和owner-only Draft。

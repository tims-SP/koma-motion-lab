# CORE-024 监工返修：收尾，不再安装模型

执行者 mcode；监工 Codex。只修改本工单列出的文件。禁止委派、联网、安装、提交；不要后台运行，不要逐行反复检查。

目前 native_layers.py 已实际导出62层；白底阈值W245可作临时预览，XGEN明显白边，生成式原图RGB偏移，均不可当贴图验收通过。

请用一次集中修改、一次前台运行完成以下事项（最多14步）：

1. native_layers.py：fidelity 的 max_abs 现在错误地取三通道绝对差之和，改为真正单通道最大误差；可另存 max_rgb_sum_abs。遇到 leaf errors、不是62层、任一PNG不等于SDK RGBA时必须非0退出。不能把强制合成称为已验证完整前视/UV parity。保留原生alpha/混合模式信息。
2. cutout_white_canvas.py：运行前验证 C SHA=66d661022b811874afb68ac9a033e8cede5d591d005503e4d023702de5424169 和 imagegen SHA=220ee4ff62baae15aa0fa14f9dfb967c74ad14028f902699df2562c1aa9e8f25；不符立即失败。alpha统计拆分zero/partial/255，原先opaque_px其实是nonzero，应更名。保留RGB逐像素断言。移除sleep与无必要PNG重试，用一次PNG保存再验证即可；不必扩大重构。
3. workflow .github/workflows/koma-reference-factory-022.yml 在prepare之后加前台 python native_layers.py；把out/core024/native-v2/native-export.json纳入text artifact；Draft Release现有zip自动包含native-v2的PNG，release描述加62原生RGBA导出/原生alpha透明前视，并明确不包含本地C候选图和自动语义分解，禁止生产已通过的描述。
4. 用本机python前台跑两个脚本一次（不安装）；不要tail隐藏状态；记录真实exit。创建 docs/research/CORE-024-native-alpha-results.md 和 CORE-024-white-canvas-results.md，中文短报告：真实测量/方法/运行方式/风险。native说明原始叶PNG未烘焙multiply/opacity/mask/clipping；forced composite存在外溢shadow不能等同修好rig。W245临时预览可用但细白边硬边；XGEN拒绝：漂移白边；imagegen RGB重绘不验收；rembg安装BLOCKED且推理没有执行。不能把这些都叫成功。

不动CORE023已验收文件、依赖锁、原图及source。最后汇报确切修改文件/exit，无需新增测试套件。全部完成再停止。

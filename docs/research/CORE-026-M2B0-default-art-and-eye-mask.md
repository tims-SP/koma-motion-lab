# CORE026 M2B0：真实默认画面与眼罩失败反例

2026-10-31 Asia/Shanghai。状态PASS_DEFAULT_ART_ONLY；代码edb696f经监督CI41174418164及旧回归41174418131全部success。下载20份纯JSON产物，ZIP SHA69647af42995086adad36cfdedcdfddb61acf983f7655dbd0fec908d599c7abb与job日志一致；CI截图SHA与已人工查看的本地图逐张相同。[CI验收](../../experiments/reference-factory/evidence/core026-M1/m2b0-ci-acceptance.json)。完整M2B未通过，M3仍阻塞，不能把本报告当作空间深度、动态遮挡或自然转头通过。

## 实际执行与分工

用户已明确允许mcode项目操作包括上传，本轮没有加载旧的禁止上传guard。官方SDK首轮完成14次工具调用后8分钟超时，无运行时文件。改成固定工单后，mcode实际用bash应用Codex设计的三个文件，JS语法exit0；首次截图因Playwright Chromium缺失exit1。mcode后续安装系统依赖因容器不允许apt setgroups/seteuid失败；再改为浏览器下载时，平台自动审批仍以OSS目的地/实际载荷未明为由拒绝。这些实际结果分开记录，没有把CLI对话exit0当作截图命令成功，也没有重新登录或换SDK执行渠道绕过拒绝。

之后Codex单独下载公开的固定Playwright Chromium（无系统包修改），完成本地截图和独立验收。代码设计为Codex，初始补丁应用为mcode，成功截图/独立验收为Codex。原始SDK流不进入git/artifact/Release。

## 新管线实际做了什么

浏览器以无损RGBA8 PNG解码读取并校验62张raw_source_texture；不读取CORE025烘焙层或整头图作为候选颜色。按原始顺序实时计算Normal/Multiply在先前透明艺术背景上的有效RGB，按已固定的旧量化约定输出每源图层GPU绘制。62个source draw共享19个接收几何，25项逻辑painter pass可追踪，晚画58/59及60/61眉的背景混合仍在头发之后。

当前Multiply计算在源画布域，不是转头后的screen-space背景；几何沿用未拟合的CORE025高度剖面，depthTest=false。只支持0姿态，非零yaw明确拒绝。它是后续空间合成的默认颜色基线，不是完整接收曲面/深度方案。

独立浏览器阻止旧烘焙/基线颜色输入，实测请求62张原始PNG；重新捕获12图（8默认、局部偏移/复位2图、错误眼罩反例/策略复位2图）。检查真实62次source draw、固定相机/投影、PNG SHA及来源。候选自己的10图捕获与监督捕获分开运行。

## 找到并保留了真实失败

第一版把4项原生ClipToLower直接解释为raw EyeWhite alpha乘法。真实截图中虹膜下缘被切掉：每张beauty有1219个差>16像素，最大差182，虽然平均误差很小，仍被严格门禁拒绝。失败代码/文本证据保存在707cc6c7，现有运行时保留eye_white_only反例分支，CI必须继续把它按原阈值判失败。

核对锁定的[原生OpenGL实现](https://github.com/Inochi2D/inox2d/blob/d4dd9dd7f16b775042cbda44370570abf9a8cf81/inox2d-opengl/src/lib.rs#L299)与[Composite绘制上下文](https://github.com/Inochi2D/inox2d/blob/d4dd9dd7f16b775042cbda44370570abf9a8cf81/inox2d/src/render.rs#L311)，ClipToLower使用DST_ALPHA/ONE_MINUS_SRC_ALPHA因子，作用于当前Composite目标；其alpha保持Ad。仅乘source alpha再做Normal不等同于该方程，raw PNG也尚未建立原生GPU裁剪域配准。[原始来源与推导](../../experiments/reference-factory/evidence/core026-M1/native-eye-primary-source-review.json)。

默认策略改为明确的原画兼容paint-domain cap：眼白、虹膜、高光的原始alpha最大值作为已画覆盖域，上限裁剪而不重复乘自身alpha，保证0姿态原画不丢失。该策略是原画域提案，**不声明为原生GPU眼罩或解剖眼球边界**。原眼白单独支持假设仍标BLOCKED；局部偏移有533个改变像素位于该错误假设之外，报告没有隐藏这个事实。

## 当前通过范围与未变阈值

source/clean×白黑底同时对旧真实浏览器与旧CPU参考检查。最大实际结果：对旧浏览器全图RGB MAE0.018680、前景并集MAE0.049236、最大通道差3、差>16像素数0；对CPU最大通道差2。alpha最大差1，前景支持像素数与原参考一致。

原门禁不变：RGB全图≤0.10、前景并集≤0.50、最大≤4、差>16为0；alpha≤0.50/最大4。左虹膜28偏移8源像素实测改变9681像素，所有改变在已画眼域+固定1像素滤波支持内，复位恢复原SHA。额外伪造一个前景像素、同步更新其文件SHA和repeat字段后，平均误差仍很低，但最大差门禁照样拒绝；这证明没有靠哈希或平均值掩盖缺陷。

Codex实际查看默认头图及鼻/眼/眉发/耳叶/颈局部，默认还原通过。偏移图中高光29没有随28联动，因此本次参数测试不作为自然眼动通过。完整M2B、原生眼罩一致性、空间深度测试和自然转头继续未验收。

恢复：`node capture_core026.mjs`，`node capture_core026_supervisor.mjs`，`python verify_core026_compositor_supervisor.py`，`python run_core026_default_art_regressions.py`。JSON进入artifact，实际图片仅ignored out/与owner-only Draft。[本地机器验收](../../experiments/reference-factory/evidence/core026-M1/m2b0-local-acceptance.json)。

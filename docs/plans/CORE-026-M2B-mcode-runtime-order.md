# CORE026 M2B0：mcode真实默认姿态合成工单

2026-10-31 Asia/Shanghai。用户已明确允许mcode项目操作，包括上传。使用已登录的官方SDK，不加载旧的禁止上传临时guard，不修改SDK、不换端点，不重新登录。M2A代码ff2fe1a两套CI均成功。只实现并验收默认姿态；M3深度与转头尚未开始。

## 交付文件与分工

mcode编写experiments/reference-factory/core026.html、core026.js、capture_core026.mjs；必要时新增prepare_core026_runtime.py、config/core026-runtime.json、diagnose_core026_runtime.py。输出媒体和调试数据只在ignored out/core026/runtime/。Codex单独编写verify_core026_compositor_supervisor.py并检查真实像素、截图和来源。mcode不得修改该独立验收程序、CORE025代码/配置/基线、原始资产、已有constraints/review/compositor受控配置、依赖锁或workflow。提交由Codex在验收后进行；不写生产仓库，不发布正式Release。

## 明确执行步骤

1. 读取AGENTS.md、CORE-026-M2-local-compositor-order.md、core026-compositor-contract.json、core025-layer-contract.json、core025-render.json、core025.js及prepare_core025.py的真实混合公式。运行prepare_core026_compositor.py --verify和verify_core026_compositor_contract.py，任一失败停止。
2. 候选颜色只能来自62个raw_source_texture.file。out/core025/assembly的baked layer PNG、CPU整图和out/core025/render旧截图只作只读基线，不得进入候选渲染器。不把完整头图当单张贴图，不把所有眼层永久烘死。
3. 保留62个native_uuid/psd_order及其19个接收面/嵌套眼画布去向，按25个painter pass原顺序处理。Face13基础区段13..43、头发44..57、Face晚画58/59与Multiply眉60/61的顺序不得改变。runtime跨组Multiply要使用当时的场景背景，不能预烘到Face底色后改用Normal覆盖头发。
4. source保留原始alpha；clean仅增加契约中的9个shadow→base alpha乘法裁剪，source/clean均保留原始blend。原生4个ClipToLower与派生9阴影裁剪分列。眼部局部UV偏移接口和眼白遮罩保留为实时可修改状态；初始偏移为0。遇到原生clip与PSD默认艺术差异应记录实测，不得静默修改基线或隐藏失败。
5. 使用固定1630×1630 source坐标、center815、正交相机(-1,+1,+1,-1,near.1,far20)，position[0,0,5]、target[0,0,0]，与CORE025默认视图一致。0姿态不靠新猜测的Z或整层深度跳变解决混合。可以使用动态局部Canvas/texture或GPU合成；每层操作、接收面及blend均须可追踪，材质仍保留局部UV接口。不得修改原始UV或原图文件。
6. 暴露window.core026Ready=true，以及window.core026.render({version:'source'|'clean',background:'white'|'black',pass:'beauty'|'alpha'|'part_id',size:1630})、metadata和setLayerUvOffset(order,[dx,dy])（源像素单位）/reset方法。只接受默认姿态，非零yaw须拒绝，不能把raw yaw控制值标为物理角度。
7. capture_core026.mjs使用真实Vite+Playwright Chromium/SwiftShader截图。捕获4张source/clean×white/black beauty，每张重复一次并核对SHA；另捕获source/clean各自alpha和part_id，合计8张默认图。alpha诊断须来自透明渲染/实际像素alpha并显示为灰度，不能用亮度或白/黑背景猜测。
8. 额外验证局部状态：在source默认姿态把pupilL28的UV偏移改为[8,0]后真实捕获一张，再reset为0捕获一张。偏移图必须与默认图不同，reset图必须恢复默认SHA；不得移动整个头、相机或其他接收面。记录使用的遮罩及支持范围。没有实现有效局部运动就标FAIL，不用静态图伪装。
9. 写out/core026/runtime/manifest.json：schema、实际camera/projection矩阵、62个来源及SHA、19接收面、25pass实际操作、每图params/file/sha256/repeat_sha256、实际UV状态、错误和限制、全部渲染程序/配置SHA。清楚记录几何使用何种接收曲面、是否depth-tested以及尚未实现的物理深度/动态遮挡。不把仅0姿态的合成通过写成三维转头通过。
10. 运行node capture_core026.mjs，修复实际报错后重新截图。自行计算4张beauty与旧c00..c03默认图和CPU基线的误差，保存diagnostic JSON。原定门禁为全图RGB MAE≤.10、前景并集MAE≤.50、最大通道差≤4、差>16比例=0，四张均须通过。禁止调整阈值；失败保存具体值和差分，交由Codex复核。alpha及source/clean透明边缘另报。
11. 完成后停止在M2B0，返回实际生成文件、真实命令/退出码、截图数量、指标和未通过项目。不自行开始转头、生成新资产、提交/push或改验收程序。Codex实际看鼻、眼、眉/头发、耳根与颈部局部，通过后才保存检查点并接下一工单。

W3C式直通sRGB数值域Multiply参考（旧prepare_core025.py已有）：effective RGB=Cs*(1-Ab+Ab*Cb)，premult out=As*effective+(1-As)*Ab*Cb，Ao=As+Ab*(1-As)。不能直接套不匹配的线性域或双重预乘。旧baseline是先量化烘焙再Normal，新的原始混合路径允许出现差异，但必须实测并服从上述门禁。

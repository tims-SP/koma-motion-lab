# CORE026 M2B1B：投影空间合成与真实深度通路

日期：2026-10-31 Asia/Shanghai。前置为M2B1A的代码b622107；独立CI实际产物验收后开始本单。生产库不改。mcode优先，若已记录的OSS自动审批仍阻塞，按已授权本地兜底并记录实际作者/执行者；不重复登录或绕过审批。

本单目标：去掉“默认源域CPU求背景可用于任意投影”的假设，证明19接收面、62来源、25逻辑pass能够进入真实空间合成与depth-test路径。几何深度仍是未拟合候选，不将测试物体或PSD顺序当角色物理深度。

1. 保存M2B1A检查点，复用其只读默认基线。新增`core026_spatial.html`、`core026_spatial.js`；保持`core026.js`作为旧已验收默认oracle。不得修改原PNG、INX、UV、CORE025保护文件或基线图。
2. 在新入口只读62张原始RGBA、19接收面映射与25项逻辑pass；逐项记录来源、共享几何、UV、shader、GPU调用及SHA。原始RGBA必须无损解码。局部眼组沿用已明确的artist override及联动，不声称原生ClipToLower通过。
3. 接收面先使用统一源坐标采样网格，确保默认重叠区域的coplanar插值一致；保留来源到接收面的映射，禁止每个绘画附着偷偷加Z偏移。默认camera/projection与既有1630画布固定，不先开放非零yaw。
4. 将每个源操作投影成premultiplied RGBA，再与同一屏幕位置的真实前序背景合成。使用GPU framebuffer/ping-pong或等价可审查实现。Normal及Multiply必须保留透明度方程和原有8位effective RGB量化约定；不得把CORE025烘焙层、整头图或0姿态CPU缓存当旋转背景。明确区分62来源draw、深度prepass和全屏合成draw，不能混算。
5. 单独建立小尺寸合成fixture：固定相机下，前层红色卡片包含透明孔/半透明边缘，后层蓝色卡片位置已知；故意以前后相反的提交顺序绘制。开启深度时红色不被后层覆盖、孔中显蓝；关闭深度的真实截图必须不同。用实际像素证明GPU深度生效，不只检查开关或metadata。
6. 在另一个明确标synthetic的fixture中改变接收面投影位置与屏幕背景颜色，独立计算几个不在边缘的Normal/Multiply像素，证明取样来自投影后的可见背景。固定透明度、位置、RGB及误差界限；保留错误“复用0姿态背景”的实际反例。
7. 分开实现有效alpha核心深度写入与透明边缘绘制。透明孔不得写深度；部分透明重叠的排序假设明确列出。原画艺术覆盖例外逐项分列，保持晚画face/跨组Multiply。测试通过仅证明通路，角色前后关系的拟合属于M3，不能在本单声称恢复。
8. 写`capture_core026_spatial_supervisor.mjs`与`verify_core026_spatial_supervisor.py`。独立限制候选颜色输入；默认source/clean×白/黑仍同时对只读旧CPU和旧浏览器按原阈值验证，真实alpha和ID不得空白。核对19共享接收面、62来源及25逻辑pass完整，保留原默认图和M2B1A眼动回归。几何/相机/UV不能仅从候选自报值放行。
9. 实际查看默认鼻/双眼/眉发、耳/叶/颈及fixture透明孔/边缘。失败保留截图和数值。接入干净CI，artifact只传明确白名单JSON；媒体仅ignored out/及owner-only Draft Release。每个可恢复完成段提交，不把临时SDK流上传。
10. 独立下载并核对CI产物、媒体SHA和实际像素。只有默认保真、投影背景、真实depth-test/透明孔、来源/几何及眼组策略全部清楚后，才讨论M2B总验收。原生EyeComposite注册不可比项继续明确BLOCKED，必须作出有证据的范围选择；完整M2B未过前不启动M3拟合。自然转头、31姿态遮挡、97帧视频和360资产不在本单通过范围。

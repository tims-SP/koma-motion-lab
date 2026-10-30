# CORE-025-M2：Three.js 原生部件前视与曲面

仅在M1经监工验收并提交后执行。执行mcode，监工Codex。现有依赖 three0.180.0/playwright1.56.1/vite7.1.12，不安装、不联网、不委派、不改原图/旧代码/依赖锁、不git提交，不运行后台任务。只新增下列文件与相应out输出。

## 允许新建

- experiments/reference-factory/core025.html（独立入口）
- experiments/reference-factory/core025.js（场景与明确渲染API）
- experiments/reference-factory/capture_core025.mjs（前台Vite/Chromium捕获，finally关闭）
- experiments/reference-factory/qa_core025.py（独立读取真实输出执行门禁）
- experiments/reference-factory/config/core025-render.json（固定配置）
- docs/research/CORE-025-M2-results.md
- 所有输出：experiments/reference-factory/out/core025/render/。

## 1 输入与颜色合同

读取M1实际的out/core025/assembly/assembly.json，使用source/clean两版本各62张独立NORMAL烘焙纹理。先查看实际schema，再接线，禁止猜测不存在字段。source代表PSD默认组合，clean为9阴影裁剪派生；写入输出manifest及UI标签。不要加载候选C，不请求生图，不将整头合成PNG当作人物mesh纹理。

M1当前实际schema入口：`assembly.layers`是62项数组；每项`source_texture.file` / `clean_texture.file`是相对reference-factory根目录的`out/...png`，浏览器URL为`'/' + file`。CPU参考为`assembly.comparisons.source.cpu_composite.file`和`assembly.comparisons.clean.cpu_composite.file`。bounds=[left,top,right,bottom]。不需要改M1字段或重写M1代码。

本次目标为PSD源sRGB数字域的无光照保真：使用RawShaderMaterial、texture.colorSpace=THREE.NoColorSpace、禁toneMapping，着色器输出不再做sRGB/linear往返；颜色管理可在独立页面显式关闭。说明这是源图合成管线，不是物理照明。使用Pillow/SDK对照来决定是否正确，不凭画面“差不多”。

纹理建议premultiplyAlpha上传+线性过滤，shader使用预乘RGB，材质premultipliedAlpha=true，源alpha不能乘两次。透明边应按预乘RGB插值，避免在转头时产生新白边。

## 2 几何与UV（逐层执行，共62个独立geometry）

源canvas1630。像素EDGE坐标(sx,sy)映射 `X=(sx-815)/815, Y=(815-sy)/815`。每层只覆盖其原始bounds矩形；按≤12源像素格距构造规则三角网格，原bounds四边必须保留，UV为 `u=(sx-left)/width, v=1-(sy-top)/height`。Texture flipY与UV必须配对验证，无擅自裁剪/拉伸/左右翻转。

共同曲面深度：
`h(X,Y)=0.12*exp(-(X/0.75)^2-((Y+0.10)/0.85)^2)+0.02*exp(-(X/0.15)^2-((Y+0.28)/0.15)^2)`；
`Z=h+order*0.001`，order1在后、62在前。depth=flat诊断模式只去掉h，保留order*0.001。XY与UV在0°不能因加深度而改变。此为推断的开放式表面，不是恢复出的真实3D/闭合头模。

每层需有正确深度遮挡：推荐共享geometry的两pass材质，opaque core(alpha≥0.9999)写depth，soft fringe(0<alpha<0.9999)测试depth但不写depth；用shader丢弃另一pass像素。source painter order作用于层内/软边排序，禁止全关depthTest以伪装物理遮挡。允许62几何对应124绘制mesh，但报告须区分两者计数。

全部部件位于共同head Group，以+Y旋转；相机始终固定，不能靠移动相机/图片模拟。正交相机[-1,1]×[-1,1]，位置[0,0,5]看原点，near0.1/far20。1630×1630门禁截图，DPR1、无MSAA；视频后续640×640。

## 3 API与诊断

初始化完成设置window.core025Ready=true。window.core025.render 接受 version(source|clean)、yaw_deg[-15,15]、depth(curved|flat)、background(white|black)、pass(beauty|silhouette|part_id|wireframe)、size(1630|640)，非法参数抛错。返回真实相机矩阵、group矩阵、几何计数与锚点投影。

锚点为诊断性的source-attached anchors，不是图像检测真值：nose(order21,[815,1040])、eyeL(28,[660,1000])、eyeR(38,[960,1000])、earRootL(1,[550,700])、earRootR(2,[1070,700])、neck(11,[810,1400])、leaf(62,[780,480])。记录source坐标、world坐标、投影pixel和NOT_VISIBILITY_TESTED标记。

导出geometry.json：62份order/name/positions/uv/indices及原bounds，供独立QA验证UV、XY和真实非平面深度，不能只报“存在曲面”。wireframe/part_id真实渲染，不用Pillow手绘冒充GPU结果。

## 4 前台捕获（本工单只anchors，不生成连续视频）

capture_core025.mjs --anchors：由Vite createServer root=本脚本目录，端口4175 strictPort；Chromium使用已安装SwiftShader参数。pageerror/资源加载失败必须使脚本失败；finally关闭浏览器及server。

捕获0°source/clean各自white/black beauty，共4张1630截图，并在同进程重复每张，记录实际PNG SHA一致性。捕获clean曲面−15/0/+15的beauty、silhouette、part_id、wireframe三角网格图。捕获clean flat +15 beauty消融对照。保存所有实际参数/矩阵/锚点/环境（Three/Node/Chromium/renderer）、assembly/config哈希及输出文件哈希到manifest.json。

## 5 独立QA门禁

qa_core025.py读实际PNG、geometry.json、manifest、M1 CPU PNG：

- 62几何、order唯一1..62、名称/bounds对应M1；position/uv/index全有限且索引有效。
- 在0°从positionXY反推源坐标，与UV*原bounds重建源坐标最大误差≤0.001源像素；不可只检查配置值。
- Face(order13)内部Z范围>0.02世界单位，拟合最佳平面后的最大距离>0.005；证明曲面不是仅有层偏移的平面卡片。
- 四张0°图分别与相应M1 CPU合成在同底比较；前景使用CPUalpha>0。RGB MAE≤1.0/255，>16像素比例≤0.001；不满足则FAIL非0，不放宽门槛。生成0°reference/GPU/差异放大对照图。
- 所有0°重复哈希一致；相机矩阵在三个角度保持一致；group的Y旋转与请求角度一致。clean曲面+15与flat+15图片不能相同，诊断锚点相对平面平均投影差>0.5px（640等效尺寸）。
- 输出qa.json与labeled review-sheet.png，clean_visual_gate=NOT_REVIEWED，监工负责目视验收。所有结构PASS只能称PROTOTYPE，不得称骨骼、蒙皮、IK、真实3D、多视图或生产已完成。

## 6 实际执行和报告

在experiments/reference-factory前台运行 `node capture_core025.mjs --anchors`，再 `python qa_core025.py`；记录真实退出码。失败保留输出，定位根因后修复，不能跳过检查。中文报告写真实指标与已知外溢/穿插/开放表面风险。不要先写M3/M4，不要改已有requirements/package锁。

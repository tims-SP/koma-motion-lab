# CORE-025-M3：连续转头、真实视频编码与抽帧

仅在M2前视/曲面门禁通过并提交后执行。执行mcode，监工Codex。只扩展capture_core025.mjs、qa_core025.py，新增docs/research/CORE-025-M3-results.md；输出只写out/core025/turntable/。不改M1、依赖锁、旧工厂或原图，不安装、不联网、不委派、不后台运行、不git提交。

## 步骤1：扩展捕获模式

保留已通过的 `--anchors` 行为。新增互斥 `--video` 模式；对未知CLI参数报错，不能把错拼参数当默认模式。

读取已验收M2场景，使用已有window.core025.render API。97帧，编号0000..0096；每帧实际调用renderer，参数明确：version=clean，depth=curved，pass=beauty，background=white，size=640，yaw_deg=15*sin(2*pi*i/96)。绝对值<1e-10的yaw设成0。首尾0°、024帧+15°、048帧0°、072帧−15°、096帧0°。固定相机，不新增自主动画循环，不用已有图片重复拼出角度。

逐帧保存out/core025/turntable/frames/%04d.png，必须是真实GPU canvas截图，尺寸640×640。每帧记录实际render返回的camera/group矩阵、yaw、锚点投影、PNG SHA。video-manifest.json记录97项、输入assembly/config/场景代码SHA及Node/Chromium/renderer版本。比较三种0°的原始截图，检查往返稳定。

另外捕获clean曲面±15°黑底图（black-minus15.png / black-plus15.png），用于暴露发丝/耳根/颈部的白边或穿插；不改变主视频的白底合同。finally关闭浏览器与Vite。

## 步骤2：前台编码

用现有ffmpeg在前台执行，所有命令保留真实exit（Python subprocess列表参数+check=True或等效）：

`ffmpeg -y -framerate 24 -i out/core025/turntable/frames/%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart out/core025/turntable/core025-head-yaw-15deg.mp4`

文件必须是新编码的视频，不能只改已有MP4名字。用ffprobe实际解码计数，取得codec、width/height、rate、nb_read_frames、duration；要求h264、640×640、24fps、97帧、时长97/24秒±1帧时间。

## 步骤3：视频QA与真实抽帧

扩展 `python qa_core025.py --video`，保留M2无flag的QA。读取实际97张PNG及manifest：帧号连续、全部尺寸640、PNG哈希与manifest相符、至少35种不同图像哈希、camera矩阵不变、group角度正确、帧0/48/96的RGB平均差≤0.01/255。用白底颜色差得到外轮廓bbox（注明这是粗略外轮廓检查，不是alpha真值），全部帧主体与图像边界至少2px间隔。±15°相对0°必须有实际像素变化。任一硬门禁失败应非0退出，不放宽阈值。

用ffmpeg从**编码后MP4**每8帧提取一次，共13张（索引0,8,..96），保存decoded-review/。使用这13张解码图生成labeled decoded-review-sheet.png；标签包括原帧号和实际yaw，不能拿原PNG冒充解码抽帧。

用解码后的0/+15/−15图生成detail-review-sheet.png：眼睛、耳根、刘海/脸缘、颈部各3角度的放大对照。裁剪坐标以640画布明确固定并记录在report中，图片拼接后标签不可遮住角色。若追踪ROI，记录实际投影锚点及坐标，不使用生成式修图。

固定ROI为eyes=[200,340,440,445]、ear_roots=[150,135,490,310]、fringe_face=[155,275,500,540]、neck=[245,500,390,610]，格式[x0,y0,x1,y1]；取解码后的原帧0/24/72，按2倍NEAREST放大以检查实际像素，不拉伸宽高比例。角度标签来自对应帧的manifest，不能用解码序号猜角度。

video-qa.json包含所有实测门禁、真实ffprobe结果、13解码图SHA、输出视频SHA、visual_gate=NOT_REVIEWED。不将数字门禁通过写成生产质量通过。

## 步骤4：执行与报告

前台依次运行 `node capture_core025.mjs --video` 和 `python qa_core025.py --video`，保留实际退出码。新增中文结果报告，明确这是原始PSD62部件的推断浅曲面±15°原型，不是完整Inochi运行时、不含新增侧/背素材、不含骨骼蒙皮/IK、不证明360°。

报告中分开写：M1默认姿态烘焙局限、结构门禁结果、待监工逐帧检查项。mcode不得自行把visual_gate改为PASS。完成后监工会独立重算几何/矩阵、抽检实际视频、决定返修或提交。

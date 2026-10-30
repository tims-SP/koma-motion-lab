# M3视频QA：只创建qa_core025_video.py

**所有权及执行入口已更新**：由Codex监工独立编写并运行 `verify_core025_video.py`，避免让渲染实现自行决定通过。本文件的数字门槛/编码/解码/裁剪要求保持不变，旧qa_core025_video.py文件名不再作为实际入口。

新建独立QA以保持M2文件不变。本工单替代原M3修改旧QA的部分。只创建experiments/reference-factory/qa_core025_video.py，建议≤230行；输出out/core025/turntable/。使用已安装Python/NumPy/Pillow/ffmpeg/ffprobe，无安装/联网/后台/委派/git提交；不得修改旧文件或降低门槛。

1. 读取M3录像工单的实际video-manifest.json schema；验证5项输入SHA与当前文件一致、97帧index连续0..96、文件SHA/640尺寸相符、yaw按正弦计划（零值归零）一致。
2. 检查真实pose.camera_matrix/projection_matrix固定、group_matrix为对应+Y旋转（column-major按Fortran reshape，元素误差≤1e−6）。至少35个不同原始PNG SHA；raw帧0/48/96 RGB平均差≤0.01/255。±15原图应与0°不同。
3. 白底差粗略外轮廓（任一RGB通道离255超过3）记录每帧bbox，非空且距离四边≥2px；明确这不是alpha真值。验证两个黑底检查图的SHA和尺寸。
4. 前台subprocess列表参数+check=True执行ffmpeg：24fps输入frames/%04d.png，libx264、yuv420p、crf18、movflags+faststart，输出core025-head-yaw-15deg.mp4。真实ffprobe -count_frames读取codec/width/height/r_frame_rate/nb_read_frames/duration，要求h264、640×640、24fps、97帧、97/24秒±1帧时间。不能用文件扩展名冒充编码检查。
5. 从编码后的MP4实际每8帧解码一次（0,8,..96，共13张）至decoded-review；ffmpeg filter可用select=not(mod(n\,8))、fps_mode vfr。每张记录对应原帧号、yaw、解码文件SHA；禁止原始PNG冒充解码抽帧。
6. 用13张真实解码图生成decoded-review-sheet.png（图片外标签原帧号/yaw，保持宽高比）；用原帧0/24/72对应的解码图生成detail-review-sheet.png：eyes=[200,340,440,445]、ear_roots=[150,135,490,310]、fringe_face=[155,275,500,540]、neck=[245,500,390,610]，2倍NEAREST，不拉伸比例，标签不覆盖角色。
7. video-qa.json记录全部实测/阈值、真实ffprobe结果、视频与13张解码图SHA、失败清单、numeric_gate PASS/FAIL、visual_gate=NOT_REVIEWED、production_gate=NOT_ACCEPTED。失败非0，不跳过缺失项。
8. 只先py_compile，不在没有97张真实PNG时生成假PASS；监工录像完成后实际运行 `python qa_core025_video.py`，完成编码/QA/解码。不要顺便改旧的M2 QA或场景。

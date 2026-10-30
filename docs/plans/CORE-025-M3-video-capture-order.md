# M3录像：只创建capture_core025_video.mjs

M2的17张真实截图/几何/矩阵已由监工独立验收并保存检查点。为保持M2输入SHA稳定，本阶段**新建独立脚本**，不修改capture_core025.mjs或qa_core025.py。此工单替代原M3中修改旧捕获程序的部分；目标97帧、24fps及视频质量边界不变。

只创建experiments/reference-factory/capture_core025_video.mjs，建议≤160行；输出out/core025/turntable/。不修改场景/M1/配置/旧捕获/QA/依赖锁，不安装、不联网、不委派、不后台、不git提交。先集中写代码，再node --check；监工将真实运行。不要在本任务写编码或QA，它们由独立视频QA脚本负责。

1. 复用已通过的Vite/Playwright启动和finally清理，端口4175 strictPort，固定现有Chromium/SwiftShader参数，访问core025.html等待Ready。收集pageerror/console.error/请求失败/HTTP≥400，除favicon外不忽略实际错误。
2. 对i=0..96，计算yaw=15*sin(2*pi*i/96)，abs<1e−10设0。实际调用window.core025.render，参数明确：version=clean、depth=curved、background=white、pass=beauty、size=640。相机保持固定，不新增自主动画。
3. 每帧保存canvas#stage的真实PNG至frames/0000.png..0096.png；保存index、file（相对turntable）、yaw_deg、完整params、真实pose、PNG sha256。首/024/048/072/096分别0/+15/0/−15/0。禁止复制已有图代替渲染。
4. 额外实际捕获clean/curved/±15/black/beauty/640，命名black-minus15.png和black-plus15.png，保存params/pose/SHA到black_checks数组。
5. video-manifest.json固定schema如下：

`{schema:"koma-core025-video-capture/1",fps:24,width:640,height:640,frame_count:97,inputs:{assembly_sha256,config_sha256,scene_sha256,anchor_manifest_sha256,video_capture_sha256},environment,frames:[{index,file,yaw_deg,params,pose,sha256}],black_checks:[{file,params,pose,sha256}]}`。

inputs分别对当前实际M1 assembly、M2 render config、core025.js、out/core025/render/manifest.json、本录像脚本计算SHA。environment含实际Three/renderer、Node和Chromium版本。保存完97帧后才写manifest；出错必须非0退出，finally关闭browser/server。
6. CLI不接受多余参数。node --check通过后汇报代码完成但实际录像NOT_TESTED；监工将运行 `node capture_core025_video.mjs`。不得将结构成功写成艺术级转头或生产通过。

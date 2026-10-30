# CORE-025-M4：干净环境复现、媒体归档与恢复说明

仅在M1/M2/M3各自已由监工验收或明确记录失败并提交后执行。执行mcode；监工负责提交、观察Actions及补齐实际run/release链接。禁止部署生产仓库、安装新依赖、修改已验收源算法/依赖锁、委派、后台运行或git提交。

允许修改3个文件：.github/workflows/koma-reference-factory-022.yml、README.md、experiments/reference-factory/README.md。报告和状态由监工维护，不自行把pending CI写成PASS。

## 步骤1：接入现有Actions

保留现有源码锁定下载、49数学/边界回归、45结构图独立进程复现与视频检查。工作目录仍为experiments/reference-factory，所需ffmpeg已在既有apt步骤安装。

在 `python native_layers.py` 后按顺序插入前台步骤，均依赖真实exit码，不能加 `|| true` 或用tail管道吞掉失败：

1. `python prepare_core025.py`（M1）
2. `node capture_core025.mjs --anchors`
3. `python qa_core025.py`（M2）
4. `node capture_core025_video.mjs`
5. `python qa_core025_video.py`（M3，包含编码/解码/视频QA）

若某阶段只有结构通过、视觉失败，CI只验证数值/结构，不得把这种状态改成视觉通过；发布说明应准确反映监工报告。只允许阶段任务规定的原型验收，生产门禁保持NOT_ACCEPTED。

## 步骤2：Artifacts仅放文本

保留现有公共安全的JSON，并加入：out/core025/assembly/qa.json、out/core025/render/qa.json、out/core025/render/manifest.json、out/core025/turntable/video-manifest.json、out/core025/turntable/video-qa.json。若已验收实现采用不同的文件名，先读取真实脚本并使用实际文件名，不创建伪造的同名PASS文件。禁止PNG/视频/纹理二进制进入公共Artifacts。

## 步骤3：媒体只进Draft Release

既有zip遍历out/机制会包括原始来源、62层、124派生纹理、曲面检查图、97帧、编码视频与解码抽帧。将证据zip名明确改为CORE025-layered-turn-evidence.zip，SHA256SUMS同步改名；release标题注明CORE-025及run_number。仍使用 `gh release create --draft --target "$COMMIT_SHA"`，不能改成公开发布。

release说明必须包含：Aka/seagetch/CC-BY-4.0；62原生部件；默认姿态multiply→normal烘焙局限；推断的开放式浅曲面±15°原型；本地AI候选C不在CI包中；原始Inochi运行时全前视、骨骼蒙皮/IK、真实侧背与360°未验收。不得使用“所有素材已齐”或“生产可用”。

## 步骤4：更新恢复文档

根README顶部新增当前CORE-025检查点，链接docs/STATUS.md、M1/M2/M3监工报告（只链接实际存在文件）。原CORE-022当前标题改为历史基线，保留原始run/release链接。CI新run链接在监工验证后补齐，现在只能写PENDING。

reference-factory/README追加完整恢复命令：已有requirements/npm锁安装→prepare.py→native_layers.py→prepare_core025.py→node capture_core025.mjs --anchors→python qa_core025.py→node capture_core025_video.mjs→python qa_core025_video.py。说明本地模型/生图配额不影响此确定性源码复现；新视角资产仍未齐。

## 步骤5：本地静态核对

用现有Python yaml库读取YAML（注意YAML1.1的on键解析差异，不能凭键名误报），检查run命令路径确实存在、引用输出文件名与已验收实现一致。`git diff --check`通过。不要安装软件、不要重跑昂贵的既有全量渲染；本阶段由监工提交后在干净Actions环境实际复现。汇报真实修改与本地核对，CI保持pending直到观察到成功。

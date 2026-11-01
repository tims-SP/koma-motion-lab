# P0 · 原画与语义图层源素材批次

生成基准：`p0_character_001` 的粉紫齐颈短发、单根呆毛、紫粉双眼、深蓝金边制服、酒红蝴蝶结和固定解剖侧的金色交叉发夹。

## 批次内容

本次建立 134 个独立透明 SVG 源文件及一份 JSON 清单，按视角源图、现有源图可见分层、器官研究、口型、左右眼内层和附加饰品拆分保存。所有文件路径见 [manifest](../experiments/p0-assets/atomic-batch/manifest.json)，全部图层可通过 [离线审图页面](../experiments/p0-assets/atomic-batch/review.html) 逐个浏览。

结构来源分为：从原 mcode 角色设计稿真实提取的各可见 SVG group；重新绘制的眼部、口腔、鼻部、耳朵和服饰的独立矢量设计；原有的四视角 SVG 设计参考。它们保留真实透明背景和逐文件语义身份。

两张 ChatGPT 角色原画设计总览图已在聊天中生成，适合作为色板和资产结构构想；总览图缩略内容不视为独立高分辨率角色原画。

## 验收边界

本批文件状态为 **VECTOR_DESIGN_PROVISIONAL**。源 SVG 是可复用的结构草稿，并未证明与已批准 Hero 原始像素一致，也未证明已补画遮挡后皮肤、双侧发根与服装内部。尤其需要原作一致的独立左右 45°、135°、225° 原画及未参与调参的独立留出角度参考。面向 ArtMesh 生产的逐部件 RGBA PNG、精细边缘、绘制前后顺序、关键点坐标和最终人物视觉验收属于下一道正式资产门禁。

运行环境分工：远程 mcode 和原设计工程用于创作，GitHub 用于保存源文本与资源传输。最终图像 QA、Alpha、PNG 转换和 HTML 验收须在当前隔离容器完成；本次本地执行容器暂时不可用，故源素材只完成创建与 GitHub 保存，不报告像素或视觉验收通过。

## 完整性与包访问

下载资源：[P0 artwork source delivery](https://github.com/tims-SP/koma-motion-lab/actions/runs/41284883483/artifacts/13074717963)。解包后从 `experiments/p0-assets/atomic-batch/review.html` 打开逐文件审阅界面。生产仓库 `tims-SP/koma-motion` 保持独立。

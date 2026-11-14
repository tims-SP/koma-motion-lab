# P15-06 · P0 独立中间视角原画合同

角色：p0_character_001
试验：experiments/gif-multiview-keyparts-mvp/
验收基线：P8 语义 ArtMesh + 已登记 0°/45°/90° P0 原始视角

## 目的与产物

独立制作 65° 和 77.5° 两组真实原创二维视角，作为不使用 VDD 推导出的独立留出角真值。每角度包含 13 个可单独复用的语义 RGBA 部件，总数 26 张。原画为日式电视动画细线稿、稳定赛璐璐明暗和相同人物身份，并维持头部中心、镜头距离与角色左右关系。

输入身份为前期批准的原创 P0 角色，其正式 Hero 来源合同记录在 /root/koma-p0-designs/identity_spec.json，当前工作资产原始尺寸 1122×1402 RGBA，预期源文件 hero/hero_master.png 的 SHA-256 为 e95a4b694777f4dcd2e085b25b10d76058d65cd1f8c6ef46971caa8005cb7e54。

可直接读取、已实际检查的来源：

- 三个原始 P0 0°/45°/90° 的头肩参考图，每个具备真实 PNG 文件和独立 SHA-256。
- 相同三视角中的 ArtMesh 语义层、P5 解剖位置锚点与 P10 已确认的高置信候选笔触。
- P14 67.5°/72.5° 两组生成式视角，只用于诊断交叠、角度和线条对应，不视为 65°/77.5° 的独立真值。

当前目标主机与文件库未取得上述原始 Hero PNG 的字节，因此正式身份母图门禁保持待核验。重新查找或从之前批准的原始文件恢复同 SHA-256 字节，才可宣告 Hero 身份源核验通过。原图源不存在时，仍可根据已验证的 0°/45°/90° 资产准备生成输入，但其艺术来源身份验收必须独立记录。

## 生成输入合同

规范文件：experiments/gif-multiview-keyparts-mvp/metadata/p15-holdout-generation-contract.json

逐角度固定：

- 65°：与 P0 原始 45°、90° 的眼鼻、嘴唇、耳根、发束层级和肩领结构对应。注意刘海对眼睑的遮挡，前额转至侧脸的连贯轮廓。
- 77.5°：更接近原始 90° 侧脸，重点控制鼻梁、近侧眼、下颌线、侧耳与前/后发的细线稿，以及呆毛的真实根部。
- 每角度按同一 1024×1024 全局画布分别输出 body.reference、hair.back、face.skin、ear.far、ear.near、hair.side、eye.far、eye.near、nose、mouth、hair.front、hair.ahoge、hair.clip.cross_gold。
- 每个 PNG 为 native RGBA8、具细腻半透明边缘，一图一部件；显隐部件按角色物理侧与相机角度登记，不能把远侧遮挡部件误绘为正面。
- 记录关键点、语义 ID、深度序号、bbox、原画来源 SHA、生成记录与单帧 SHA。原始已批准 Hero 与三个关键视角为优先参考，禁止以动画插值画面代替独立留出角绘制。
- 成果二进制文件继续放在私有资源路径，GitHub 保留脚本、合同和来源校验文本。

## 核查与准入

在 P0 工作环境内运行：

    KOMA_P14_PYTHON=/path/to/vision-venv/bin/python \
    KOMA_P0_DESIGN_ROOT=/root/koma-p0-designs \
    bash scripts/run-p15-holdout-source.sh

来源预检程序会重复核查 0°/45°/90° 原始视角的 SHA、P5 锚点登记、P14 候选引用及 P0 身份 Hero 候选，生成：

- evidence/p15-06-source-readiness.json
- metadata/p15-holdout-generation-contract.json

一旦 65°/77.5° 独立 RGBA 26 层全部到位，先执行逐部件排他性/源哈希/重建合成，再对 P8 的 65°/77.5° 动画画面执行独立轮廓对照、五官锚点、头发笔触与遮挡对照；轮廓 IoU 参考门槛 ≥0.90、相对面积偏差 ≤8%，并需人工检查线条、眼鼻、呆毛、前后发无重影。

## 门禁状态

- [x] P15-06-A：定位并核验原始 P0 0°/45°/90° 三个关键角及其 SHA。
- [x] P15-06-B：冻结 65°/77.5° 的 26 张独立语义 RGBA 原画合同和来源哈希。
- [x] P15-06-C：建立正式 Hero 原文件 SHA 核验及可重放输入预检。
- [ ] P15-06-D：恢复批准的 Hero 原文件并验证预期 SHA-256。
- [ ] P15-06-E：生成、细化和登记两个新角度的 26 张独立 RGBA 原画。
- [ ] P15-06-F：独立留出角对照与 0°–90° 正式视觉质量签收。

采用的正式渲染器保持 P8 基线；P15-04/05 的锚点与笔触候选用于生成质量诊断及下一阶段视觉修正。

## P15-06 · 实际 ArtMesh 导入验收

已实现新视角原画导入器 scripts/p15_holdout_import.py。导入 13 张独立 RGBA 透明图层，按 P0 原始 45°/90° 图层深度叠合，与单独提供的原画整图逐像素比较，记录每层源 SHA、alpha 覆盖、bbox、分层深度和总图 SHA。正式模式只接受 65°/77.5° 且保留模型/绘制来源与种子。可使用现有 P14 67.5°/72.5° 已知真实素材进行工程回归，但两者都不是新独立视角真值。

- [x] P15-06-G：验证 67.5°/72.5° 两组真实 13 层 RGBA 经独立导入后可逐像素重建其原画源图。两组透明 alpha 与可见 RGB 最大差异均为零。
- [x] P15-06-H：实现独立原画导入器、原图 SHA 校验、全局画布/语义深度/部件边界约束，回归覆盖 PNG 非 RGBA、源目录逃逸及像素重建等情形。

复现：

    KOMA_P14_PYTHON=/path/to/vision-venv/bin/python bash scripts/run-p15-holdout-import-smoke.sh

独立 65° 与 77.5° 的 26 张原画由同一导入器验证，正式验收需要完整原图和 13 张独立部件的来源与视觉对应证据。


## P15-06 · 独立原画与语义 ArtMesh 候选实测

已从同一批准的 P0 原画来源生成 65°、77.5° 两个独立绘制的 RGB 候选。生成使用 Hugging Face Qwen-Image-Edit-2511 的 Multiple-Angles 模型配置；65° 基于原始 45° 输入，随机种子 65022；77.5° 基于原始 90° 输入，种子 77522。源照片 SHA、模型、视角及随机种子均保存在私有资源中的 provenance.json，并由公开 QA 对应到源 SHA。

使用 rembg isnet-anime 提取原生 1024×1024 RGBA，再结合 P0 原始 90° ArtMesh 的语义图层所有权、DIS 光流和独立视角面部 ROI，生成 26 张 PNG（每角度 13 张独立文件），保留眼、鼻、嘴、耳、刘海、侧发、后发、呆毛和制服等固定语义角色。所有部件在原始深度序列按 alpha 重建后，与对应的独立原画完全一致：alpha 与可见 RGB 的最大差异均为零。

采用 SIGGRAPH 2026 See-through 分层技术（https://github.com/shitagaki-lab/see-through；论文 https://arxiv.org/abs/2602.03749）处理 77.5° 原画，得到 768 分辨率分层 PSD，来源 See-through Hugging Face demo。由 PSD 的 back hair、face 等带补绘的层，在 P0 1024×1024 ArtMesh 中注入 81,594 个严格被上层完全遮住的额外像素。可见原画保持逐像素不变，补绘资产保留原始 PSD SHA，适合继续做视角相关遮挡和变形验证。

浏览器独立源验收：HTML 工作台 review/p15-06-keyview-art.html，8 张真实 Chromium 截图、32 次 SHA-256 PNG 源校验，通过，无 JavaScript 或请求失败。

本阶段工程验收重点：
- [x] P15-06-E1：65°、77.5° 两张独立绘制的完整角色视角、原始来源哈希登记
- [x] P15-06-E2：两视角原生 RGBA 透明抠图、26 张一图一语义部件 PNG
- [x] P15-06-E3：13 层深度叠合、原画逐像素重建、正式 importer 双角度接收
- [x] P15-06-E4：77.5° See-through PSD 提取及被遮挡区域可追溯补绘
- [x] P15-06-E5：HTML 逐部件审查、Chromium 8 个画面和来源完整性验证
- [ ] P15-06-E6：逐部件绘制边界、眼鼻口、发束笔触、实际 65°/77.5° 视角精度的艺术验收
- [ ] P15-06-E7：批准 Hero 源 SHA 对照与 0°–90° 连续动画视觉签收

绘制候选保留原生整图及独立 PNG，但当前 ArtMesh 图层的可见像素来自算法语义分配。对于高质量 VDD 生产，需继续校准刘海/头顶、脸部细线、眼耳分界，并增补 65° 隐藏区域补绘。每个关键图层必须通过独立视觉审查，不以逐像素重建通过作为最终质量判定。

固定可重放命令（需 Vision Python、psd-tools、Playwright 和现存私有源图）：

    KOMA_P14_PYTHON=/path/to/vision-venv/bin/python \
    KOMA_PLAYWRIGHT_MODULE=/path/to/node_modules/playwright \
    bash scripts/run-p15-06-generated-review.sh

See-through 独立 PSD 生成脚本：scripts/p15_seethrough_demo.py，基于原画 PNG 及 upstream demo 接口执行；生成结果和浏览器截图均保留 private-assets。

公开证据：evidence/p15-06-generated-keyviews-qa.json；真实绘制像素、 PSD 和逐部件图保持在 private-assets/p15-independent-candidates/。

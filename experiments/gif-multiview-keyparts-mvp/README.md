# p0_character_001 · 多视角 ArtMesh 与 VDD

## 身份与目标

正式素材唯一角色是此前已批准的 p0_character_001；规范见 contract.json。复用 R1999 已有的视角语义键、拓扑对应、深度与遮挡、smoothstep/VDD 逻辑。旧实验只作为运行时的技术参考。

每个主视角登记十个基础语义槽：0°/45°/90° 共三十槽。两眼属于不同物理对象，正面须追加 eye.far；同理，远侧耳需根据原画补绘和显隐关系登记。发夹固定在角色左侧，90° 对应视角需要正确遮挡。

## 私有资产目录

    private-assets/
      hero/hero_master.png
      whole/head-turn-8view.gif
      whole/yaw000.png … yaw315.png
      gifs/face.gif
      gifs/hair.gif
      gifs/identity.gif
      parts/yaw000/face.skin.png
      parts/yaw000/eye.near.png
      parts/yaw000/eye.far.png
      ...
      parts.json
      qa.json

每张正式 PNG 是 1024×1024 原生 RGBA；所有组共享同一个固定相机和全局坐标，不允许对每个部件重新居中。源 GIF 的每帧只画一个指定语义 ID，保留像素清场及 SHA-256 证据。

parts.json 须声明 schema=KOMA-P0-ARTMESH-MANIFEST-V1、characterId、canvas=[1024,1024]、wholeViews 和 parts 数组。每条部件包含 yawDeg、semanticId、path、sourceGif、sourceGifSha256、frameIndex、frameSha256、sourceRole、visibility、depthOrder、occludes、anchors、mesh、semanticReviewed、visualReviewed 和 bbox。mesh 使用 vertexIds、vertices、triangles：跨视角同部件共用顶点身份及三角索引，坐标独立。

## 校验与预览

仓库根目录执行：

    python3 -m unittest discover -s experiments/gif-multiview-keyparts-mvp/tests -v
    python3 experiments/gif-multiview-keyparts-mvp/scripts/verify_bundle.py --root experiments/gif-multiview-keyparts-mvp/private-assets --output experiments/gif-multiview-keyparts-mvp/private-assets/qa.json
    python3 -m http.server 5181

访问 http://127.0.0.1:5181/experiments/gif-multiview-keyparts-mvp/review/index.html

HTML 仅在真实来源与质量报告均校验通过后加载正式素材。22.5°/67.5° 是中间视角视觉检查点，最终应按图像审查脸型、眼鼻、发夹、呆毛、头发遮挡和重影，并制作浏览器真实截图及视频。

Git 保留计划、脚本、合同、QA 与来源哈希；大 GIF、PNG、PSD、截图和视频保存在私有目录或受控 Artifact/Release。private-assets 须排除于 Git 跟踪。

## 原始 GIF 的逐帧审查

原始四组 GIF 先通过以下工具解码，保留来源尺寸和帧在原始画布内的位置，生成 38 帧对照 PNG、每组可视接触板与完整 SHA-256。只有新一轮原生 RGBA 独立部件才能进入生产层：

    python3 experiments/gif-multiview-keyparts-mvp/scripts/extract_keyparts.py --root experiments/gif-multiview-keyparts-mvp/private-assets --output experiments/gif-multiview-keyparts-mvp/private-assets/extracted/extraction-qa.json

各组均按视角优先排列；face 的前五张属于 0°，第六张才是 45° 的 face.skin。0°→90° 朝角色解剖学右侧转动，近侧眼和近侧耳属于角色物理右侧，交叉发夹属于物理左侧。每帧的语义正确性需要对真实图像逐张审查，GIF 解码本身不证明语义排他。

## 浏览器自动截图

在存在经 SHA-256 验证的生产 PNG、parts.json、qa.json 后运行：

    KOMA_PLAYWRIGHT_MODULE=/absolute/path/to/playwright node experiments/gif-multiview-keyparts-mvp/scripts/capture_review.cjs

输出默认写入 /tmp/koma-gif-review，包含 0° / 22.5° / 45° / 67.5° / 90° 实际浏览器截图、SHA-256 与 browser-qa.json。源素材验收未满足时输出本地准入页面截图及状态记录。截图不能代替对轮廓、五官和层次质量的人工或视觉模型审核。

## 2026-11-05 · 原画来源恢复与预览

已恢复 `gif_multiview_asset_review_2026-11-05.zip`（53 项、4 GIF、38 帧），SHA-256：`8ce3596f60a01b82df49926304c47041d8a8734689ae2a3126acada583666547`；分片恢复见 `private-assets/transport/asset-transport-manifest.json`。独立 GIF 实际画布为 443²、313²、418²、418×627。已批准 P0 hero 的历史 SHA 为 `e95a4b69…e54`，恢复包内生成主图 SHA 为 `7868cdc…e9b`，两者身份来源分开登记。

源码 `scripts/build_semantic_partition.py` 将已生成的 0°、45°、90° 整头独立视角来源像素注册成 39 张互斥候选 RGBA PNG（30 个原有语义槽与 9 个补充槽）。三个原画端点合成像素差异均为 0。该像素登记用于验证身份、布局和合成引擎；隐藏几何及生产级独立 ArtMesh 原画另行验收。

    /root/koma-motion-r1999/work/r1999-vision-venv/bin/python experiments/gif-multiview-keyparts-mvp/scripts/build_semantic_partition.py --root experiments/gif-multiview-keyparts-mvp/private-assets
    KOMA_PLAYWRIGHT_MODULE=/root/koma-motion-r1999/work/browser/node_modules/playwright KOMA_CANDIDATE_MODE=1 KOMA_QA_OUT=/tmp/koma-p0-candidate-v2-browser node experiments/gif-multiview-keyparts-mvp/scripts/capture_review.cjs

浏览器预览：`http://127.0.0.1:5181/experiments/gif-multiview-keyparts-mvp/review/index.html?mode=candidate`，须先从仓库根目录启动 `python3 -m http.server 5181`。真实 Chromium 已导出 0°、22.5°、45°、67.5°、90° 共 5 张截图并保存哈希。视角质量结果见 `evidence/2026-11-05-recovered-p0-review.json`；插值区域的裂缝与纹理误差仍需通过新的关键部件原画与形变拓扑修复。

从已有真实视角计算的光流转向作为诊断对照，可运行：

    /root/koma-motion-r1999/work/r1999-vision-venv/bin/python experiments/gif-multiview-keyparts-mvp/scripts/flow_render.py --root experiments/gif-multiview-keyparts-mvp/private-assets --out experiments/gif-multiview-keyparts-mvp/private-assets/flow-sharp --mode dis_sharp

私有预览包路径为 `experiments/gif-multiview-keyparts-mvp/private-assets/exports/p0-character-001-multiview-review.zip`，19,084,223 字节，SHA-256：`b62d060d908f10c6ade86bb2baa9fb18b9199324f7753583976406ab90b07002`。含原始 38 帧包、候选分层、HTML、实际浏览器截图与诊断 GIF。新生成的 22.5°、67.5° 原生 RGBA 原画和 `eye.far` 部件另见 `evidence/2026-11-05-native-rgba-views.json`。

## 连续形变与时间一致性 QA

`scripts/flow_render.py` 现提供 `dis_smooth_sharp` 作为统一形变场对照：在真实 0°、45°、90° 原画间计算 DIS 光流，并对光流坐标使用标准差为 12 像素的空间平滑，尽量维持面部与发丝锐度。输出 37 个角度候选画面及 GIF。

    /root/koma-motion-r1999/work/r1999-vision-venv/bin/python experiments/gif-multiview-keyparts-mvp/scripts/flow_render.py --root experiments/gif-multiview-keyparts-mvp/private-assets --out experiments/gif-multiview-keyparts-mvp/private-assets/flow-smooth --mode dis_smooth_sharp
    /root/koma-motion-r1999/work/r1999-vision-venv/bin/python experiments/gif-multiview-keyparts-mvp/scripts/qa_temporal.py --frames experiments/gif-multiview-keyparts-mvp/private-assets/flow-smooth --output experiments/gif-multiview-keyparts-mvp/private-assets/flow-smooth/temporal-qa.json

五角度抽检画面已检查。37 帧相邻 RGB 平均绝对差的中位数约为 5.42，20°→22.5° 与 65°→67.5° 的差异高于参考阈值，反映身份纹理跨源切换仍需要正式补绘及拓扑连续约束。诊断见 `evidence/candidate-temporal-qa.json`。

本次完整私有审查包保存在 `experiments/gif-multiview-keyparts-mvp/private-assets/exports/p0-character-001-multiview-review-v2.zip`，19,022,502 字节，SHA-256：`d0b68de1589ba65a5f2db49ad7a3604d2f9f36d2fd8fc65fccff34067ed43fac`，包含光流预览、时间一致性 QA、候选透明部件、来源 GIF 和实际浏览器截图。历史资产恢复与验收信息保留在仓库证据目录中。

## P1 · 正面独立 ArtMesh 审查

以 P0 的恢复原画和原有语义 GIF 为来源生成 13 个 1024×1024 RGBA 图层，保存各来源的 SHA-256、解剖身份和 7×7 可编辑网格。
面部遮挡与发夹背后的纹理基于原画颜色和独立部件修复，后续动态效果需要继续做视觉验收。

在测试仓库根目录执行（Python 环境包含 Pillow、OpenCV、NumPy）：

    python experiments/gif-multiview-keyparts-mvp/scripts/p1_front_semantic.py --root experiments/gif-multiview-keyparts-mvp/private-assets
    python experiments/gif-multiview-keyparts-mvp/scripts/qa_p1_front.py --root experiments/gif-multiview-keyparts-mvp/private-assets --output experiments/gif-multiview-keyparts-mvp/private-assets/p1-front/engineering-qa.json
    python -m unittest discover -s experiments/gif-multiview-keyparts-mvp/tests -v
    KOMA_PLAYWRIGHT_MODULE=/absolute/path/to/playwright node experiments/gif-multiview-keyparts-mvp/scripts/capture_p1_front.cjs
    python experiments/gif-multiview-keyparts-mvp/scripts/package_p1_front.py --output experiments/gif-multiview-keyparts-mvp/private-assets/exports/p0-character-001-front-artmesh-review.zip

运行 `python -m http.server 5181` 后打开 `http://127.0.0.1:5181/experiments/gif-multiview-keyparts-mvp/review/p1-front.html`，可逐层显示及移动眼睛、前发。

本轮实机结果：150/150 个结构门禁通过，17/17 项工程测试通过，三个浏览器实机截图经 SHA-256 验证。正面重组轮廓 IoU 1.000，完全不透明源画区域的透明孔洞数为 0。独立动作美术验收与批准角色母图 SHA-256 验证仍需单独完成。
大型原画及截图存于私有 `private-assets/`，其 SHA 和技术验收结果写入 `evidence/2026-11-06-p1-front-artmesh.json`。

### P3 · 参考图生图视角与 P0 身份保持验证

使用真实 P0 0°、45°、90° 原画作为三图条件，生成 22.5° 和 67.5° RGBA 全画面候选，并用已有原画检查头部轮廓变化和视觉身份一致性。已生成可人工检查的五视角 Storyboard GIF 和源图 PNG。

生成模型输出经 JPG→背景移除转换为 1024×1024 RGBA。文件源哈希、透明边缘、角度变形与原画来源均在 `private-assets/p3-native-source-trial/` 对应 QA 文档中登记。

头部轮廓中点进度在两个目标角分别为 0.063、0.183（目标应接近 0.5），所以当前图片用于身份和透明度验证，完整角度标注仍需进一步姿势约束。另一次基于侧脸的姿势引导生成也已保留作对照。

从测试仓库根目录执行 `scripts/build_p3_generated_view_review.py` 和 `scripts/qa_generated_yaw_progress.py`，验证图像哈希、合成对照和角度变化，再运行 `scripts/package_multiview_review.py` 构建私有审查包。29/29 项工程回归通过。

审查包：`private-assets/exports/p0-character-001-multiview-source-review-v4.zip`，27,528,797 字节，SHA-256 `10e17c51a0953f6c15c292fcf4127203a7f393c26adaae57dcf786584c9849e7`。代码证据见 `evidence/2026-11-06-p3-reference-guided-source.json`。

### P4 · See-through PSD 原画分层与三视角 ArtMesh 审查

使用真实 P0 正面原画，通过 See-through 生成 768×768 13 层 PSD，导出至 1024×1024 RGBA 注册空间。原画可见像素持续作为真值来源，新补绘用于前后发、面部、耳朵与五官被遮挡区域。

静态轮廓 IoU=1；前发水平移动 16px 的不透明区域穿孔从 3169 降至 429。HTML 正面、单眼动作和发层检查均有真实浏览器截图。三视角 39 个 ArtMesh 语义槽保持独立来源和 SHA-256。

浏览器打开：/review/p1-front.html?source=seethrough 以及 /review/index.html?mode=candidate&source=seethrough-front。GIF：private-assets/p4-see-through/mv-candidate/p0-psd-front-vdd-turn.gif。

质量门禁：采样中间角面部透明度连续，跨角纹理对应仍待优化。本轮测试 37/37 通过，源码与证据分别保存在 scripts、tests 和 evidence/2026-11-07-p4-seethrough-artmesh-qa.json。

私有审查包：private-assets/exports/p0-character-001-artmesh-psd-review-v5.zip。SHA-256：08761e4f7e2412d83deac685ed40b516dc917d4ea3abd1160c214cd89faf0cde。

### P5 · 0°/45° 语义 PSD 与物理锚点对应

使用已经批准的 P0 原始 0° 和 45° 原画分别生成独立 See-through 13 层 PSD。将两组原生 PSD 语义层归一化为 1024×1024 RGBA，并保留 P0 90° 的原画部件作为第三个姿态端点。共登记 39 个 ArtMesh 槽，统一语义 ID 与网格拓扑。

45° 新增 260870 个隐藏补绘像素；原画静态轮廓 IoU 1.000，差异像素 50，不透明穿孔 0。13 条可追溯物理地标跨 0°、45°、90° 登记，其中 0° 与 45° 双眼虹膜中心由真实 PSD 图层像素分量提取。

三视角 HTML 为 /review/index.html?mode=candidate&source=seethrough-paired 。私有预览 GIF 为 private-assets/p5-see-through/mv-candidate/p0-psd-paired-vdd-turn.gif。由真实 Chromium 输出 37 张 RGBA 后生成 72 帧往返动画，中间角的跨视角纹理验收需要进一步几何对应约束。

来源与完整 QA 见 evidence/2026-11-08-p5-two-psd-view-correspondence.json。回归测试 46/46 通过。私有审查包为 private-assets/exports/p0-character-001-two-psd-artmesh-review-v6.zip，SHA-256 3e8d97b676511d382d8cab1efcc47c0e3058ca3a8929634646c95d53b2799482。

### P6 · 原画物理锚点流场驱动的 ArtMesh

从已登记 P0 原画 0°、45°、90° 与 0°、45° 独立 See-through PSD 生成的语义部件，提取 13 条物理解剖轨迹和 2548 个带原始来源哈希的 ArtMesh 流场顶点位移。三个参考关键角与固定 ArtMesh 身份保持一致。

22.5°、67.5° 的面部纹理边缘密度比值：原矩形网格 8.96、3.20；物理锚点流场 0.61、1.78。全 37 帧 temporal QA 对比：原矩形网格两处跳变、物理流场两处跳变、源窗口过渡 0 处跳变。源窗口过渡画面有跨原画重影，仍作为时间连续性研究对照。实际脸部、发束与服装的独立视觉质量验收继续以原画为准。

交互 HTML：review/index.html?mode=candidate&source=seethrough-paired&warp=flow。对照过渡：增加 &blend=window。原生 1024 PNG、两份 See-through PSD、三份 72 帧 GIF、所有结构化 QA 与哈希均随隔离审查包交付。

私有 ZIP：private-assets/exports/p0-character-001-flow-correspondence-review-v7.zip。SHA-256 325fb28989a1b26820f43c7581335cfa5ec70b13c0e22f852a48e84b30d48326。证据：evidence/2026-11-08-p6-flow-artmesh-visual-qa.json。本轮整体回归 53/53 通过。

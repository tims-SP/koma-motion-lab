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

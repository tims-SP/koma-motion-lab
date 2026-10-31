# MVP-001 · V2 统一主计划：现有资产驱动的多视角 2.75D 动画（2026-10-31）

**状态：规划冻结候选 / NOT IMPLEMENTED / NOT ACCEPTED。** 本文件在目标、优先级、路线和阶段划分上**取代**早期 `MVP-001-multiview-anime-plan.md`、`MVP-001-M1-plan.md` 中冲突的描述；旧文档保留历史，不删除已有实验与失败证据。

## 0. 最终产品结果与不可变边界

用**同一个可复用角色数据包**产出三段 1920×1080、24fps 的日式动漫高质量视频：
- A = 水平全身 360° 转身：8s / 192 frames，额外独立采样 360° 与 0° 接缝；并有可交互 yaw 预览。MVP 只验证水平 Yaw 一周，**不冒称任意 Pitch/Roll 的全空间旋转**。
- B = 全身动作：6s / 144 frames，迈步、躯干/头部转动、抬手伸向目标、手臂 IK、脚部接地、发丝/衣摆少量次级运动；与 A 同一骨架/角色外观。
- C = 人物高保真特写：4s / 96 frames，转头、眨眼/嘴形/表情、画师风格的脸部阴影变化（SDF 或 key masks）、头发局部法线及轮廓光、少量前后景粒子；与 A/B 同一个角色包。

全部自有应用代码/资产转换/测试/渲染脚本：**TypeScript strict**；Node 22 + `tsx` + Vite + Three.js/WebGL2 + Playwright + FFmpeg。依赖外部官方软件、SDK 或已有科学代码进行**参照验证**允许，但生产核心不引入自写 Python/Rust/Dart，也不要求运行旧 Rive/Godot/统一 UV 曲面路径。

**画质优先于真实物理**。允许 art-directed 局部视角形变、手工纠正的关键姿势、局部可见性切换及镜头专用原画；不能以这些机制掩盖整身卡片、全身 PNG 跨淡入淡出、重复眼睛或时间上跳变。**研究阶段不是商业分发许可**；公开源代码/报告为文本，第三方原画和派生视频只在经验证限制访问的存储保存，不公开分发。

## 1. 从资产出发，而不是先造角色

| 资产 / 已核查信息 | 定位 | 先验证 | 不应该推断 |
|---|---|---|---|
| [myssal/Reverse-1999-CN-Asset](https://github.com/myssal/Reverse-1999-CN-Asset) `roles/300401_hongnujian`：`.skel`、`.atlas`、`.png`、bloom | **主画质/动作候选** | 官方匹配的 Spine 4.2 TS Runtime 播放 room/fight/UI 并保留 bones/slots/weights/FFD/IK/constraints/原动作 | 骨骼动作等于 360° 多视角素材 |
| 同源 `live2d/roles/300401_hongnujian`：`.model3.json`、`.moc3`、两纹理、25 motions 与 expressions | **同角色面部及局部形变参考** | 官方 Cubism Web TS SDK + Core 原生表情/动作、drawable 顶点/UV/顺序/可见性 | `.moc3` 等于可编辑 `.cmo3`；可自动无损并入 Spine 网格 |
| 同源 `rolesstory/rolesprefab`、其他 `roles` | **其他姿势/可能不同构图或角色候选** | 静态目录/版本/实际预览对照 | 不据 `_s`/`_z` 或目录名猜测是真背面 |
| [EsotericSoftware/spine-runtimes 4.2/spine-ts](https://github.com/EsotericSoftware/spine-runtimes/tree/4.2/spine-ts) 和 [Spine Examples](https://esotericsoftware.com/spine-examples) | **骨骼正确性基准** | 原运行时对照、约束/蒙皮数值一致 | Spine 示例的风格能代表目标动漫画质 |
| [Live2D/CubismWebSamples](https://github.com/Live2D/CubismWebSamples) 官方样例 | **表情、遮挡和法线等视觉基准** | 模型参数、Mesh/Blend/DrawOrder/动作 | Cubism 本身实现了真正 360° |
| [852wa/Anime2.5DRig](https://github.com/852wa/Anime2.5DRig) | **PSD 自动绑定/ArtMesh/物理/遮挡设计参考**，MIT 许可证需按具体文件核实 | PSD parse、landmark/mesh/rig 生成，JS 思路翻为 TS | 单 PSD 能无损生成后视角 |
| [shinshin86/psd-motion-lab](https://github.com/shinshin86/psd-motion-lab) | **九方向局部形变、mesh、时间轴/帧间补全基准** | Miko 九方向/面颈/上身与 RIFE 影片效果对照 | 九方向等于横向全身 360°；RIFE 等于可编辑 rig |
| [without-paper/2.5d_cartoon_model](https://github.com/without-paper/2.5d_cartoon_model) SVG 示例 | **2010 论文 Orientation Space / Anchors 算法校准** | front/right/top 带分组 SVG，TS 重实现数值与视觉对照 | 简单矢量头像证明高画质全身 |
| [Ariakage/live2d-agent-kit](https://github.com/Ariakage/live2d-agent-kit) | **Agent 原画→拆层→Live2D 验收流程参考** | 源层/模型/动作/失败报告质量；依赖许可和非 TS 编译工具隔离 | 模型封装可以直接作为多视角 360 运行时 |

候选策略：
1. **主候选 `300401_hongnujian`**：因为同一个角色同时有 Spine、Live2D，可尽量复用真实画风与动作。先检查它们的版本/造型/姿势差异；**相同角色名 ≠ 相同几何/同一张皮肤**。
2. **另选两个候选**：一个头发服装较简单的 `roles`，一个在 `live2d` 中有清晰面部动作且在 Spine/剧情目录有对应资源的角色。输出客观打分表，不按喜好盲选。
3. **明确视角缺口**：AssetInventory 中 `hasFront`/`hasSide`/`hasBack` 分为 `verified`/`absent`/`unknown`；没有原画证据不能填 true。
4. 正背左右方向缺失时**先用已有角色作为锁定参考**定向生成或补画；只对失败部件/角度增加视角原画。单张图生成不是先决条件、也不是可用性证明。
5. 用高画质角色做终极验收，用 Spine/Live2D/论文官方样例做**技术对照**，不能拿低画质测试图代替终极画质标准。

## 2. 融合方案：单一逻辑角色，分层外观

### 2.1 统一资产 IR / Scene

角色逻辑信息：
`characterId, sourceProvenance, skeleton, timelineClips, parts[], keyViews[], expressions, materialLayers, corrections, qualityRecords`。

每个 `Part` 至少：
`id, parentBoneId, bindPose, pivot2D, anchor3D, sourceAttachmentId, deformerStack, keyViews[], correspondenceGroups[], visibilityRules[], occlusionConstraints[], normals?, faceShadowMask?, sprite/atlas metadata`。

每个 `KeyView`：
`yawDeg, pitchDeg, referenceCamera, texture/atlas+SHA, triangles/uv/landmarks, contour, depthHint, visibility, correctiveDelta, source/edited/procedural status`。

**稳定的角色解剖 ID**（如 `eye.left`）与源 Spine attachment ID、Cubism Drawable ID 必须分开映射。映射不成功须留 `unmapped`，不允许默默把不同资源当同一图层。不同视角允许部件 split/merge，必须记录拓扑转变、出现/消失条件。

### 2.2 正确的求值顺序（每帧确定性）

```
scene time, animation clips, camera
 -> evaluate skeleton pose + IK + optional deterministic physics
 -> for each part: compute LOCAL observer rotation (bone-relative)
 -> select per-part adjacent key views in cyclic orientation space
 -> 3D-anchor projection + VDD artist positional / contour correction
 -> compatible mesh correspondence, warp, pose/form/expression correction
 -> per-view visibility + occlusion constraints / topology switches
 -> paint-registered RGBA + line/alpha/depth
 -> optional normal/SDF/art shadow -> effects/compositing
 -> WebGL frame; deterministic frame seek; FFmpeg encoding
```

动作层借鉴 Spine 骨骼/约束、2016 Puppeteering 2.5D、Live2D 二维 Warp/Glue/Blend Shape；外观层借鉴 Euclid、SIGGRAPH 2010 anchors、2014/15 depth billboards、2022 VDD。动作逻辑是**3D 关节/锚点 + 视角相关 2D 造型**；不要求完整 3D 实体头模、不强制统一 UV 皮肤。

**纹理是最大风险**：先建立每个 Part 的形状与纹理关键点对应，再形变采样；不对整脸/全身图做简单 alpha crossfade。局部拓扑不一致时使用 split/merge/occlusion/额外 view，ARAP 仅用于相比简单三角形 warp 明显提升质量的区域。

### 2.3 风格与光照

- 默认原画颜色、描边、阴影保真（unlit）。
- 面部：关键视角的 SDF/画师阴影 masks 控制光照边界，避免通用 Phong/PBR 把动漫脸照坏。
- 发丝/服装：选定部件具有可选 normal map，必要时由原稿/局部几何推断 + 人工修正；随着 mesh/bone 局部坐标变换，不能拿世界空间常量法线冒充细节。
- 轮廓光、颜色分级、粒子、运动拖影和镜头修形是独立 compositing layers。
- 真实物理、NPR/PBR、完整三维网格都**不是**最终呈现必须要有的东西。

### 2.4 运行时与外部依赖

- 主生产路径为 TS + Three.js；**保留官方 Spine TS/Cubism Web TS 作原生参考播放器**，不在运行时强制把所有东西转换为 `.riv` 或 `.moc3`。
- Cubism Core 并不在 GitHub 开源，需从官方下载并遵守许可证；如果不可用，MVP 使用 Spine 来源进行进度，Cubism 渲染标记 `BLOCKED_CORE`，不能假称 Live2D 兼容。
- Spine 必须使用与导出文件相同 major.minor 的 Runtime（4.2 对 4.2）。
- 外部 RIFE/See-through/MV-Adapter 在需要时作为**资产生成/候选质量实验**，自有生产服务和任务脚本仍用 TS；不把 AI 插帧当作可编辑动画模型的证明。

## 3. 先最小杀手实验，再扩大投资

**K0 骨骼源验证**：原始高画质 Spine 角色原生 TS renderer 的 idle 与一个动作，保存参考帧、骨架、Mesh、约束与 FFD/DrawOrder 验证；Cubism 面部原生对照。
**K1 视角形变验证**：选同角色头+肩+衣服关键部件，先做 0°→90°，独立采样 0/15/30/45/60/75/90，保持高画质并修复眼睛和发丝遮挡；输出 no-VDD 与 VDD 对照。此处 FAIL，暂停昂贵的 360 全身扩图，分析拓扑和纹理成本。
**K2 统一资产验证**：同一个角色 JSON/TS runtime 中完成头部转动 + 一只手抬起，手部根据 bone-local view 查自己的 keyViews；同时载入可动眼嘴与脸阴影。在此处证实三项能力真的可共存，而不是三段不兼容视频。
**K3 全身水平 360°**：在 K1/K2 成立后才扩为 4 个基本方向（缺失角度定向补图），必要时添加 45° 中间 keyviews；192 帧 1080p。
**K4 全身动作与特写**：完成下列三段验收影片，不要求为每一帧重绘角色。
这些是成本控制顺序，**最终 MVP 三片同时通过才 PASS**。

## 4. 明确任务队列与检查点（每个 task 完成一次提交）

| Task | 输入和精确执行 | 输出证据 / PASS 定义 |
|---|---|---|
| T00 | 将 M0 `main.js/smoke.mjs` 迁至 TS；锁定 npm/版本、`tsc --noEmit` 严格校验；运行 Chromium/WebGL/FFmpeg 原 M0 冒烟；保留老输出用于对照 | TS 工程、CI、24 帧截图/MP4 parity，原 M0 全部通过 |
| T01 | TS `asset-inventory.ts` 仅读取特定 commit 的三类 Reverse1999 资源；再选两个候选，扫描 Spine/Cubism/剧情资源路径、大小、hash、视角数量、许可状态。禁止全量 clone 巨型仓库 | candidates.json 和 source matrix；真实 verified/unverified view gap |
| T02 | TS 版官方 Spine 4.2 参考播放测试（idle+1 action+4 poses）；并行独立 Cubism TS 模型/表情测试；测试 Anime2.5DRig 样例 PSD 与 2.5d_cartoon_model 三方向 SVG | 各自播放器的实际参考帧、约束覆盖、bug list、license audit；哪些能导出不是靠推测 |
| T03 | 选主角并建立同一角色外观规范与源附件→语义 Part ID、骨骼、face variant 映射；确认是不是不同版本造型，是否适合融合 | character-selection.md；每个部件 match / split / unmapped 记录；M1 缺图清单 |
| T04 | TS 资产 IR schema + importer + validator；保留 source rig/slot/weight/deform、参数动画、纹理、骨骼；生成可复合 RGBA layer bundle 和 debug overlays | 与原 Spine/Cubism 参考关键视角画面比较，源纹理坐标/遮挡/权重至少通过预定基线；无丢部件或假匹配 |
| T05 | 用头/肩/外套进行 K1 0→90 高质量试验；建立 Anchor、per-Part cyclic viewSpace、triangle warp、VDD、visibility/occlusion；只为真实缺角补关键层 | 7 张独立角度、网格/深度、no-VDD/VDD 同帧比较；决定插值与纹理策略是否值得扩张 |
| T06 | 在统一骨架上做 K2：头部随视角转、抬手/头骨架局部旋转、眼嘴独立参数；SDF face-shadow test；每帧姿态可任意 seek | 1 个共用角色包、至少 2 种动作姿态与数个观察方向，无错位/叠眼/关节断裂，特写阴影可关/开 |
| T07 | 根据实际参考角度做全身 0/90/180/270；如关键部件的 45/135/225/315 不合格则补该部件的 view；扩展遮挡、纹理 correspondence 与局部 mesh warp/ARAP | 四基本方向准确重构、24×15° 网格视角、错误角度/人工补图次数明细 |
| T08 | 生成 A 片：8 s 192 帧 1080p；额外 0/360 同姿势测试，fixed camera；输出对照组与 debug video | 人物整体与部件模型实际旋转，No pop/tearing/flip/blur/crop，FFprobe 验证 192 帧 |
| T09 | 生成 B 片：6 s 144 帧；迈步、全身转身、手部 IK reach、脚锁定、少量 head/hair physics；动作修正层 | 原骨骼基准动作 vs 融合视频；接触帧手目标误差 <=12 px、静止脚漂移 <=8 px 初始门限，视觉检查仍独立 |
| T10 | 生成 C 片：4 s 96 帧；眼嘴表情/头部局部变形、原画阴影/SDF、可选 hair normal、rim/light、粒子；无特效/有特效对照 | 清晰五官/描边/发丝，不可出现重影、色偏、阴影翻转；unlit 对照 |
| T11 | 总验收 + 决策；全视频 432 帧解码、逐 15° 角度、关键 pose、随机跳帧、最差片段、修复成本、可复现 CI | QA JSON + artifact manifest + 3 MP4 + contact sheets + defect log；人工/独立审查同意才 PASS |

### Task 状态制度

`NOT_STARTED -> IN_PROGRESS -> FAIL/BLOCKED/PASS_ENGINEERING -> PASS_VISUAL`。
- `PASS_ENGINEERING` 仅代表代码、文件和数值通过，不等于画质验收。
- K1 连续多角度失真且多次局部修正无效，停止增加复杂大模型，调整 view/mesh/texture 表示。
- 如果每个中间角度都要重绘大部分角色，标记 `NO_GO_ECONOMIC`，即使能凑出 8 秒视频也不宣称生产方案成功。
- 如角色已有动作无法准确由原生 TS runtime 还原，不能使用旧 Rive/Spine Python bake 的视频冒充新的模型验证。
- 在 M1 或 M2 失败时，保存可视化的失败资产和定位到 Part ID 的日志；必须显式对比相同输入修正前/后。

## 5. 统一数据与代码目录（拟新增，尚未建成）

```text
experiments/mvp001/
  src/
    main.ts
    core/{types,scene,clock,rig,ik,physics,part,mesh,view-space,anchor,vdd,warp,occlusion,material,compositor}.ts
    adapters/{spine42,cubism,psd}.ts
    scenes/{turn360,fullbodyAction,faceFX}.ts
    ui/preview.ts
  scripts/{m0-smoke,asset-inventory,asset-fetch,source-reference,build-character,render,inspect-frames}.ts
  schemas/{character,asset-provenance,quality-report}.schema.json
  tests/{asset-inventory,source-parity,part-correspondence,angle-wrap,occlusion,rig,ik,render-determinism}.test.ts
  package.json
  tsconfig.json
.github/workflows/mvp001-v2.yml
docs/experiments/MVP-001-V2-master-plan.md
docs/experiments/MVP-001-V2-status.md
```

- Git 只存 TS/JSON/YAML/MD 和许可证与来源清单，不存受版权保护的 PNG/PSD/.skel/.moc3/.mp4。
- 大型预览文件使用**真正受限访问**的存储；GitHub Draft Release 只作为条件性选项，必须验证可见性、下载者和内容许可，不能把 Draft 视作法律授权或无条件私有。
- CI 输出真实视频与 contact sheets 后必须进行独立实际图像/视频内容核验，不能只看 Exit 0。
- 每个阶段更新单一状态文件：输入 source SHA、commit SHA、workflow run URL、输出 artifact URI、PASS/FAIL 与屏幕截图/视频人工评审意见。

## 6. 决策/退出标准

### 素材选择
保真与真实分层 > 现成动作/IK  > 面部可编辑性 > 视角覆盖 > 风格可改造性 > 获取/验证成本。画质须足以与正式动漫目标比对。原始角色存在 Spine 和 Live2D 不等于二者可共用一张模型，需要逐部件映射。

### 动画质量
不允许纸片翻转、整身方向 sprite carousel、整身 cross-fade、双眼重影、关节脱离、网格倒置、错层、持续闪烁、涂抹与原画细节丢失。不要求所有风格动作符合物理写实；**允许美术定向修形**，并需保存修正工时。

### 动态光照
优先保留原画色彩与线条；对照 mode: `unlit`, `SDF-face-shadow`, `normal-local-hair-cloth`, `composite-rim`，若哪项破坏画质就关闭，不为了堆技术而保留。

### 拍摄与覆盖
A 仅 360 水平 yaw；B 动作的每个局部肢体观察方向必须落在可用/可修正的相应 keyViews 中；C 应在近景检验轮廓、睫毛、嘴和发丝。保证 A/B/C 均基于同一个角色 IR。

### 版权
研究用材料如需个人临时使用，应审查原作者/项目条款；第三方游戏 dump 不能因非商业用途就自动公开发布。对外项目说明不附原画或派生视频。

## 7. 上游资料（优先读取源码和论文）

- SIGGRAPH 2010 2.5D Cartoon Models: https://alecrivers.com/2.5dcartoonmodels/
- 2014/2015 2.5D Modeling from Illustrations: https://www.jstage.jst.go.jp/article/adada/18/4/18_74/_article/-char/en
- 2022 VDD / key-view exaggeration: https://pubmed.ncbi.nlm.nih.gov/35544514/
- 2016 Puppeteering 2.5D: https://www.brunodorta.com.br/publication/puppeteering-cartoon/
- Live2D Cubism Core vertex data: https://docs.live2d.com/en/cubism-sdk-manual/cubism-core-api-reference/
- Live2D Euclid suspension/cost issue: https://www.live2d.jp/news/euclid_suspension/
- Spine version match: https://uk.esotericsoftware.com/spine-versioning
- 852wa/Anime2.5DRig MIT automatic rig: https://github.com/852wa/Anime2.5DRig
- shinshin86/psd-motion-lab nine-direction mesh/motion: https://github.com/shinshin86/psd-motion-lab
- live2d-agent-kit Rig/Agent workflow: https://github.com/Ariakage/live2d-agent-kit
- See-through: https://github.com/shitagaki-lab/see-through

## 8. 当前已知状态与下一动作

- [M0 Actions](https://github.com/tims-SP/koma-motion-lab/actions/runs/41188109729) 仅 WebGL 程序化图层视频的基础设施 PASS；它不等于 VDD、Spine 转换、360、全身动作或动漫画质通过。
- 旧 [PROD-009](../production/PROD-009.md) 仍有动作和产物验收失败，不能用于新的成功声明。
- **T00 起执行**：TS 迁移并回归 M0；**T01**：按需扫描和下载 `300401_hongnujian` 相关 Spine/Cubism/剧情资源和两个对照角色，制作可核实的素材覆盖表；**T02**：执行原生 TS 参考渲染并形成源模型对照；**T03**：基于真实结果选角色、定补图范围。
- **本文件仅为规划，不代表 T00—T11 已执行。**

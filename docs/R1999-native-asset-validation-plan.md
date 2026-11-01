# R1999 · 原生角色资产驱动的 2.75D 技术验证计划

日期：2026-11-01
状态：PLANNED / SOURCE INVENTORY VERIFIED / RUNTIME BASELINES PENDING
实验仓库：`tims-SP/koma-motion-lab`
生产仓库：`tims-SP/koma-motion`
上游资产：`myssal/Reverse-1999-CN-Asset`（默认分支 `master`）

## 1. 目标与技术决策

直接使用《重返未来：1999》已有的 Cubism/Spine 人物骨骼、贴图、原生网格、动作和表情作为真实输入，以原生动画为视觉基准，验证：

1. Native Fidelity：原生解析、骨骼/网格/贴图/遮挡/动作在正确运行时重现。
2. Import & Control：脚本可访问部件与参数、读取动态姿态、复用数据而非重新手动绑定。
3. Novel View：头部 0–90°、背面/头部 360° 镜头扩展所需资产、画面质量和实际新增制作成本。
4. Animation & Output：头、表情、全身动作和镜头组合，可重复导出视频和图像诊断。

**先完成原生基线，随即进行 90°/180° 高风险可行性验证。** Cubism 与 Spine 是两套不同角色表示；同一角色的立绘和战斗小人也不能视为可直接互换的皮肤/骨骼。

## 2. 已核查的最小资产集合

主样本：`302301_shisihangshi`（十四行诗 / Sonetto）。

### Cubism 立绘
- `live2d/roles/302301_shisihangshi/302301_shisihangshi.moc3`（1,006,080 B）
- `live2d/roles/302301_shisihangshi/302301_shisihangshi.model3.json`（4,011 B）
- `live2d/roles/302301_shisihangshi/302301_shisihangshi.cdi3.json`
- `textures/302301_shisihangshi_00.png` 和 `_01.png`（相对于角色目录）
- `motions/`：22 个 `motion3.json`，包括 `b_idle`、`b_diantou`、`b_yaotou`、`t_idle`、`t_kaixin`
- `expressions/`：6 个唯一 `exp3.json` 文件；`model3.json` 中有重复表达式引用，导入时规范化且不得丢失原顺序语义
- `model3.json` 中 `Physics: null`；眨眼、口型目标 ID 为 `PARAM_EYE_L_OPEN`、`PARAM_EYE_R_OPEN`、`PARAM_MOUTH_OPEN_Y`；参数 ID 必须按实际模型读取，不以标准命名猜测
- `b_idle` 已检查：11.87s、30fps、循环、217 条曲线，含 `PARAM_ANGLE_X/Y/Z` 与多个自定义参数

### Spine 全身战斗/房间/UI 动画
- `roles/302301_shisihangshi/302301_shisihangshi.atlas`
- `roles/302301_shisihangshi/302301_shisihangshi.png`
- `roles/302301_shisihangshi/302301_shisihangshi_fight.skel`
- `roles/302301_shisihangshi/302301_shisihangshi_room.skel`
- `roles/302301_shisihangshi/302301_shisihangshi_ui.skel`
- `atlas` 已确认 512×1024、`scale: 0.7`，有头、发、身、手臂、腿等独立区域和 `rotate` 贴图标记；具体动画与骨骼数量须由匹配版本的 Spine Runtime 实测

角色可从 `mappings/ArcanistMap.json` 建立角色名称 ↔ Cubism/Spine 文件路径的关系。

**资源获取策略：只按 manifest 精确下载以上单角色必需文件，记录上游 commit、raw path、SHA-256、大小、实际格式、可读状态；不克隆全部大型资源仓库。**

## 3. 选型与现成工具

- Cubism 基线：优先 Live2D 官方 [CubismWebSamples](https://github.com/Live2D/CubismWebSamples)、[CubismWebFramework](https://github.com/Live2D/CubismWebFramework) 和匹配 SDK 的官方 Cubism Core，直接加载 `.moc3`。Core 具有专有许可，必须由官方渠道取得。
- Spine 基线：优先 [EsotericSoftware/spine-runtimes](https://github.com/EsotericSoftware/spine-runtimes) 的 `spine-ts` 和 Skeleton Viewer；先解析 `.skel` 的导出版本并锁定主次版本匹配的运行时，再读取骨骼、slot、skin、权重和动画。只有基线通过才评估转换。
- 2.75D 扩展：沿用现有 `experiments/head009` 的 Three.js / TypeScript / WebGL / Playwright 与 Beauty、ID、Depth、Alpha 四通道 QA。构建适配层读取 Cubism 动态 Drawable/参数或 Spine 骨骼/mesh/attachment，保持源纹理和部件语义。
- 先判断“原生动态网格采样 → Three.js”能否保持贴图位置、蒙版与排序，再增加独立视角资料、3D Anchor 与 View-Dependent Deformation（VDD）。不得将二维原生 head angle 当作水平空间 360°。
- 新增代码放 `experiments/r1999/`；现有 `head009` 保留为独立几何及诊断对照。生产仓库仅接收通过视觉与结构验收的通用引擎能力。

## 4. 执行任务与阶段门禁

| ID | 实施任务 | 必须提供的真实产物 | 门禁 |
|---|---|---|---|
| R00 | 精准下载十四行诗双格式资产、静态依赖审计、记录源 hash、辨识 Spine 导出版本与 SDK 许可 | `source-manifest.json`、`compatibility.json`、输入资产检查报告 | 引用、解析、SHA、路径完整 |
| R01 | Cubism 官方运行时：展示原生立绘、播放 idle/点头/摇头、表情、眨眼、口型、参数面板 | 实际逐帧 PNG、10–20s 视频、参数/Drawable 清单、运行日志 | 无纹理错位/穿帮、动作真实播放；人工审看 |
| R02 | Spine 官方运行时：还原 `fight`/`room`/`ui`，列出 bones/slots/skins/weights/animations，测试两段原生动作 | 原生动画视频、骨骼/mesh/动画统计、atlas 装配核验 | 用正确版本解码、装配及蒙皮正常；人工审看 |
| R03 | **前置 360° 可行性判定**：测量 Cubism 头部有效角度、盘点侧面/背面可见源层；尝试 0/45/90/180 多视角原型，并比较「原画分层 VDD」与「局部 3D 几何补强」 | `view-coverage.json`、0/45/90/180 截图和缺失区域清单、两方案成本/质量表 | 明确哪些角度有真实数据、哪些必须新增原画；先决策再扩展 |
| R04 | 从原生 Cubism Drawable 与 Spine 槽位/蒙皮构造只读标准部件表，接入已有 QA；帧采样与 3D Anchor 标定 | `parts.json`、`anchor-calibration.json`、原生与适配结果逐帧对比 | 导出姿态与原生基线一致，身份、透明、裁剪、层级正确 |
| R05 | 实现头部连续 0–90°，独立新视角作为真值，重点验证眼、耳、鼻、发、口和局部遮挡 | 0/15/30/45/60/75/90 PNG、角度连续视频、独立参考对照、错误图板 | 未授权的新侧面几何不得算作原画保真；机器和视觉双通过 |
| R06 | 根据 R03/R05 结果补充背面与左右视图，验证头部水平 360° 及接缝 | 0–360° 视频、36 点抽帧、0/360 同姿对照、遮挡错位报告 | 90°/180°/270° 轮廓可信、360° 无角度接缝或漂移 |
| R07 | 两轨动画整合：Cubism 立绘头部/面部，Spine 全身动作；选择经证据支持的最终单角色表示，补充 IK、动态遮挡和角色-镜头调度 | 原生/增强 A-B 视频、动作与足部 QA、可复现时间轴 | 不强行将风格不同的两个 rig 叠成一个角色 |
| R08 | 一键再现、集中验收、向本体仓库迁入可复用能力 | build/test 脚本、HTML、MP4、QA JSON、来源清单、验收记录 | 用户可核查最终效果，所有关键异常明确可追溯 |

每个任务状态使用：`PENDING` → `RUNNING` → `ENGINEERING_PASS` → `VISUAL_PASS`，有阻塞则 `BLOCKED`，并记录 SHA、运行时版本、证据地址与失败原因。后续任务可以在独立轨道上并行，但 R06 依赖 R03/R05 对源视角不足的真实结论。

## 5. 最小演示与优先级

**第一可视里程碑（R00–R02）**：同角色 Cubism 原生立绘动作预览 + Spine 原生骨骼动作预览，分别导出视频；先证明源动画和蒙皮确实能复用。

**第一技术决策里程碑（R03）**：0°/45°/90°/180° 试验图板，清楚区分源自模型的真实可见数据、工程推断和后续需要单独绘制的部分。这个结果直接决定 360° 的资产成本。

**第一核心 MVP（R04–R06）**：可控制的头部连续转向、正确遮挡、360° 循环和动画组合，截图和视频由同一渲染流程生成。

统一验收维度：
- 重现：原生官方运行时画面与适配画面，在相同姿态、时间、分辨率和色彩设置下逐帧比较，记录像素、轮廓、关键部件差异。
- 几何：每个部件 ID、UV、mask、skinning、draw order、深度、alpha 与锚点的数值检测；测试数据须经过真实 renderer。
- 新视角：独立绘制/合法取得的关键视图与留出视图作为外部真值；没有真值时只能标记演示/技术可行，不能称为原画保真成功。
- 时序：0/360 接缝、关键角度附近 frame delta、眼鼻嘴耳连续性、动作足部是否滑动。
- 视觉：每阶段本人可打开的 MP4/HTML 和抽帧拼图，人眼可否决机器 PASS。验收视频必须展示完整人物而非单独数据图。

## 6. 存储、权利和仓库职责

- 上游仓库不包含可视为转载许可的授权声明；游戏原画及动画仍受权利人保护。仅用于本地个人技术实验；第三方素材及其衍生画面通过私有路径保存和预览，不进入公开 Git、公共 Actions Artifact 或公开 Release。
- Git 留存通用代码、结构化 manifest、校验方法、无侵权的合成测试数据和文本报告。私有资源缓存采用路径清单与 SHA 进行复现。
- `tims-SP/koma-motion-lab`：所有源资产适配、实验、截图/视频抽检与阶段证据。
- `tims-SP/koma-motion`：只迁移复用性强、通过门禁、与第三方内容解耦的引擎代码。
- 每次阶段完成即记录 commit SHA、输入哈希、工具版本、脚本命令、完整真实结果及下一阶段状态。

## 7. R00 的具体第一批动作

1. 固定上游 `master` commit；只下载 `302301_shisihangshi` 的 Cubism model/moc/textures/motions/expressions 和 Spine skel/atlas/png。
2. 验证 Cubism `model3.json` 全部相对路径，并实际检查 `.moc3` 读入；清点 22 个 motion 文件、6 个 expression 文件和重复引用。
3. 解析三份 `.skel` 的版本与文件头，锁定对应的官方 `spine-ts` 分支；核查 512×1024 Atlas 坐标、旋转、缩放与图像尺寸。
4. 建立只读缓存、SHA-256、SDK 版本锁、功能清单及可重复执行的输入审计脚本。
5. 直接进入 R01/R02 原生运行时预览；每个独立轨道通过后即可继续，不用等待另一轨全部完成。

## 8. 已研究的上游依据

- [《重返未来：1999》资产库](https://github.com/myssal/Reverse-1999-CN-Asset)
- [Live2D 官方 Web Samples](https://github.com/Live2D/CubismWebSamples)
- [Live2D 官方 Web Framework](https://github.com/Live2D/CubismWebFramework)
- [Live2D SDK 下载与条款](https://www.live2d.com/en/sdk/download/web/)
- [Spine 官方 Runtimes](https://github.com/EsotericSoftware/spine-runtimes)
- [Spine 主次版本匹配要求](https://us.esotericsoftware.com/spine-versioning)
- [Spine 原生 Skeleton Viewer](https://us.esotericsoftware.com/spine-runtimes)

此计划记录经 GitHub 源码及文件清单核实的资产事实；动态加载、逐帧真实画质、二进制版本、360° 视觉能力均按上述任务实际测试后再给出验收状态。

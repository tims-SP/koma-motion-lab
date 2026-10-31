# MVP-001 / M1 现有资产调查与选择（2026-10-31）

状态：静态目录与文本配置已核实；尚未下载/解码原始二进制并进行独立逐帧视觉验收。**以下不能被解读为已验证 360° 数据。**

## A. 优先级

1. **P0 真实动漫角色、原有骨骼**：[myssal/Reverse-1999-CN-Asset](https://github.com/myssal/Reverse-1999-CN-Asset)（default: `master`）。
2. **P1 官方校准 Spine 绑定和 IK**：[EsotericSoftware/spine-runtimes](https://github.com/EsotericSoftware/spine-runtimes/tree/4.2/spine-ts) 的 4.2 TS Runtime / [Spine Example Projects](https://esotericsoftware.com/spine-examples)，只用作转换基准，不作为角色品质标准。
3. **P1 官方校准 Live2D 动画/形变**：[Live2D/CubismWebSamples](https://github.com/Live2D/CubismWebSamples) 的 Haru/Hiyori/Mao/Natori 等与 [Live2D 官方 Sample Models](https://www.live2d.com/en/learn/sample/)，只用作 reference runner 与参数/遮挡示例；需要官方 Cubism Core/相关许可。
4. **P1 多视角算法测试**：[without-paper/2.5d_cartoon_model](https://github.com/without-paper/2.5d_cartoon_model) 的 `data/head_{front,right,top}.svg` 与 `yellow_head_{front,right,top}.svg`。其代码为 Python 实验参考，**新项目不能复制它的 Python 实现作为运行依赖**；通过论文本身复现 TS 版本，先核查许可证再考虑代码移植。
5. 其他网络资产按需继续搜索：必须优先包含已绑定骨骼/网格、多姿态或可共享语义 ID 的多视角原画。**不是**为了寻找而漫无目的批量下载素材。

## B. 已核实原始路径与数据

### Reverse-1999

- 仓库 [README](https://github.com/myssal/Reverse-1999-CN-Asset/blob/master/README.md)：明确称 CN 版本 dump 资产；没有在已检查的仓库根级文件中发现一份可直接据此授权再分发的许可证。公开可见 != 已获再分发授权。
- 顶层：`roles/`、`live2d/roles/`、`rolesstory/rolesprefab/`、`mappings/`。
- `roles/300401_hongnujian/300401_hongnujian.atlas`：真实图集文本已读取，含 `lian`、`liuhai`、`zuodatui`、`youfa` 等命名部件，并包含 `bounds`、`rotate`、`offsets` 数据。
- 同目录 `300401_hongnujian.png`、`300401_hongnujian_room.skel`（310,845 bytes）、`300401_hongnujian_fight.skel`（496,071 bytes）、`300401_hongnujian_ui.skel`（198,448 bytes）、`*_bloom.png` 等。
- `rolesstory/rolesprefab/300401_hongnujian_p/` 还有 `.skel`、`.atlas`、`.png` 和 bloom 图，可能用于剧情演出，**尚未证明有独立侧/背面模型**。
- `live2d/roles/300401_hongnujian/300401_hongnujian.model3.json`：确证引用 `300401_hongnujian.moc3`、两张 textures、25 条 `.motion3.json` 文件、表情文件，包含 `ParamEyeLOpen`/`ParamEyeROpen` 与 `ParamMouthOpenY`。
- 其 `.moc3` 是编译的 Cubism 模型；仅靠 model3 JSON **不能还原编辑器原始 Warp Deformer 或提取完整可编辑图层数据**。需要官方 Cubism SDK/Core 读取运行时可见的 drawable 顶点、网格、参数效果，且必须遵守授权。Spine/Live2D 不应假定可一键融合成同一套部件和骨骼。
- 实验仓库的 PROD-008 曾使用 `300401_hongnujian` Spine 4.2.36 解析得到 85 bones、101 source mesh attachments、8 actions，旧 Rive bake 的一部分通过基础渲染，未实现完整 IK/FFD/constraints；旧 PROD-009 画质门禁失败。这是旧资料，不代表新 M1 的任何 PASS。

### 官方基准

- [Spine 官方 Examples](https://esotericsoftware.com/spine-examples)：Spineboy（Mesh/IK/Clipping）、Raptor（权重 Mesh/IK）、Diamond（透视/拟 3D）等。首选用 **4.2** 格式与 4.2 TS Runtime 对照并验收参考帧，不盲用最新版 4.3。
- [Spine TypeScript 4.2](https://github.com/EsotericSoftware/spine-runtimes/tree/4.2/spine-ts)：包含 `spine-core`, `spine-webgl`, `spine-threejs`。可用于源骨骼、插槽、attachments、曲线、原本的 mesh 权重验证；**可选隔离解析适配器**，不要强制绑定到最终 2.5D 引擎核心。Spine Runtimes 有其自身许可，非普通 MIT。
- [Live2D/CubismWebSamples](https://github.com/Live2D/CubismWebSamples/tree/develop/Samples/Resources)：确证提供 Haru、Hiyori、Mao、Mark、Natori、Ren、Rice、Wanko 等，可作为参数/口型/变形质量对照。官方 `CubismWebSamples` 有 TypeScript 示例，但 Core 为专有二进制且需按 SDK 许可证取得。
- [2.5d_cartoon_model sample SVG](https://github.com/without-paper/2.5d_cartoon_model/tree/main/data)：正面、右面、顶部三方向 SVG 可用作**数学正确性**测试。注意先确认该仓库默认分支/实际下载路径，再固定 SHA。

## C. 资产优选准则（必须打分并核实）

给每个候选分配 `candidateId`、`sourceUrl`、`sourceCommit`、`licenseStatus`、`sourceType`（Spine / Cubism / SVG / layered PSD）、`viewCoverage`（explicit keyviews / implied changes / unknown）、`artQuality`、`rigCompleteness`、`meshAccess`、`referenceRuntimePass`、`occlusionDifficulty`、`missingViewCount`、`estimatedRepairHours`。

- **画质门槛**：角色须达到高质量二次元画风，不能选一个低精度示例人物充当最终验证。
- **可复用度**：保留现有 Spine bones/weight/skin attachment 与 Cubism motion/expression 对 M2/M3 有用的数据，但转换成自有 schema，不继承原运行时作为唯一技术路线。
- **视角真实性**：Spine walk/turn 动画或 Live2D AngleX 参数不是背面原画的证据；命名后缀 `_s`、`_z` 也不能未经核实就当侧面和背面。
- **一致性**：若缺少真实侧面/背面，在现有角色基础上补画/生成相关 keyviews，仍必须保留其骨骼、颜色和细节 reference。不能做整身贴图轮播。
- **合规**：仅供个人内部技术研究；公开 Git 库只记录代码、清单、散列、非版权性诊断文本。不得把第三方游戏原画、派生视频发布到公开 Git、公开 Artifact 或公开 Release；需要预览时使用严格未发布的 Draft Release / 经确认非公开存储，并核查实际权限。不得假设“个人研究”自动带来公开再分发权。

## D. 下一轮必须做的可重复调查

1. 用 **TS 编写** `asset-inventory.ts`，按指定 URL / commit 仅查询 `roles/300401_hongnujian`、同角色 `live2d/roles`、`rolesstory` 和两个官方对照样例；不克隆 30GB 级别整仓。
2. TS 引导程序保存 `asset-candidates.json`，列出实际资源大小、路径、版本、许可判定、缺失文件、 SHA-256；只下载所选单角色的少量必要文件到暂存目录。
3. TS 使用版本匹配的 Spine 4.2 loader，独立解析并渲染 **至少原有 idle 一段** 和 4 个关键姿势，输出部件数、骨骼数与渲染画面；与官方/原版源渲染做逐帧对照，不再使用旧 Python 烘焙的结论代替验证。
4. Live2D 通过合规官方 Web SDK TS 示例建立原生基准，验证眨眼/点头/转头等参数与真实 drawable 变化；如果 Core 无法取得，标记 `BLOCKED_CUBISM_CORE`，继续 Spine 路径，不偷换功能定义。
5. TS 对 SVG 学术三视角实现形状/锚点基线测试；结果只说明算法数学工作，不说明动漫画质。
6. 用上述结果决定最终 M1 角色，先检查源文件是否已经包含**真不同方向**数据；无则把“基于现有资产补全缺失视角”列为新的可量化任务。

## E. 语言与代码规则（强制）

所有本项目 **新增和维护的应用源码、资产解析器、转换工具、校验器、测试、浏览器 Playwright 和 Node 渲染脚本都使用 TypeScript**（`.ts` / `.tsx`）。Node.js + TS + `tsx`/TypeScript typecheck + Vite + Three.js + Playwright + FFmpeg 工具链。

- 旧 M0 的 `src/main.js` 与 `scripts/smoke.mjs` 必须在实现前**迁移为 `.ts`**，跑同样截图/编码回归，防止破坏已通过的基础设施。
- 禁止新编写的 Python/Rust/Dart 解析器和基于 Python 的运行依赖；可阅读或测试学术项目的现有 Python 代码来核对输出，但新核心必须是 TS 自己实现。
- JSON / PNG / `.skel` / `.moc3` / Markdown / YAML 是资源或配置文件，不受“源码必须 TS”的扩展名约束； FFmpeg / Chromium/官方 SDK 作为外部工具不要求重新用 TS 开发。
- 不直接复制第三方 Python 代码或专有 SDK 源码到我们的新架构，需核查授权，优先使用合法版本的 adapter；保留来源、版本和依赖许可证审计。

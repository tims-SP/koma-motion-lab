# PROD-008 — Spine 多动作 / 多变换通道 → Rive 生产验收

日期：2026-10-29（日本时间）
执行：[GitHub Actions #31](https://github.com/tims-SP/koma-motion-lab/actions/runs/40773868508) **SUCCESS**
证据：[仅包含元数据的 Actions artifact](https://github.com/tims-SP/koma-motion-lab/actions/runs/40773868508/artifacts/12853941910)

## 输入及工具
- 源：`myssal/Reverse-1999-CN-Asset`，固定提交 `45e75248ba3b25053fd32e63ab13c2f9f54dd9df`。
- 角色：`300401_hongnujian`（红弩箭），`room.skel`，Spine **4.2.36**。
- SkelToJson：`.skel → Spine JSON`；官方 Rive CLI：生成 RML、验证、逐帧渲染；FFmpeg：编码临时 MP4。
- 所有原游戏图片、生成的 RML/.riv、Rive 画面及角色 MP4 均只留在一次性 GitHub Runner。公开仓库只保存源代码和无图像诊断信息。

## 已运行的结果

原始动画集合包含 8 项，本轮选取四项实际逐帧制作：

| 动作 | 读取的骨骼关键帧条目 | Rive 帧 | 去重后不同画面 | 顶点发生变化的帧间隔 | 临时游戏素材 MP4 (字节) |
| --- | ---: | ---: | ---: | ---: | ---: |
| `idle_room` | 3072 | 12 | 12 | 11/11 | 73809 |
| `walk` | 842 | 12 | 12 | 11/11 | 55880 |
| `sleep` | 828 | 12 | 12 | 11/11 | 46585 |
| `hit` | 730 | 12 | 11 | 11/11 | 71549 |

**状态：`PASS_PARTIAL_MULTICHANNEL`。**

输入动作通道情况：
- `idle_room`：rotate=1902, translate=591, scale=340, shear=239
- `walk`：rotate=372, translate=186, scale=142, shear=142
- `sleep`：rotate=361, translate=183, scale=142, shear=142
- `hit`：rotate=292, translate=154, scale=142, shear=142

这里的关键帧条目数不是 Rive 原生关键帧数：它们是源 Spine 动作曲线的条目。

## 相对于 PROD-007 的新增能力

1. 复用真实骨骼层级、原始 UV/三角面、权重映射和变形网格。
2. 将源 `rotate`、`translate`、`scale`、`shear` 通道在多个时间点应用到源骨骼，再重新计算带权顶点。
3. 将每次计算的 Mesh 顶点数据写入 RML，由 **Rive CLI 实际渲染**，再将逐帧画面编码为临时 MP4。
4. 分别记录每个动作的源曲线条目数、有效顶点变化帧数、不同渲染画面数及视频体积。
5. 验收不将“唯一画面数”解释成实际骨骼及约束的源 Runtime 保真度。

## 重大限制，必须保留

- 该方法是**原始 Spine 权重参与计算的逐帧烘焙**，不是把完整 8 套动作的关键帧和约束无损导入一个可编辑 Rive 工程。
- 本轮画面的源插槽、Mesh 覆盖范围沿用此前的子集（上轮验证 51 个 Mesh、27 个带权附件、843 个顶点）；尚未覆盖所有 101 个源 Mesh。
- Spine 的精确 Bezier 曲线插值未复现（采样器明确记录了 `source_curve_not_exactly_preserved`）。
- 尚未实现原版 IK/Transform/Path 求解、顶点 FFD、动态贴图/附件切换和 Draw Order。
- 仅对当前转换路线做了内部比较，没有与官方 Spine Runtime 逐帧比较。因此不可使用“原版等效”“100% 兼容”“商业动画级还原”等结论。
- 本轮渲染规模为每条动作 12 帧；不能以此替代 24 FPS 全长镜头的质量验证。

## 下一生产闸门：PROD-009

对照官方 Spine 4.2 Runtime 的动作求解，建立两个独立渲染分支，再对同一时间点计算：

1. Mesh 顶点几何差异（归一化坐标 RMS/max）。
2. 角色轮廓/遮挡/附件变化差异。
3. 动作曲线与约束驱动（Bezier/IK/Transform/Path/FFD）遗漏覆盖率。
4. 24 FPS 全长片段，单镜头动作与渲染性能。

仅在许可允许、且不会把第三方游戏美术推送到公开仓库的前提下执行原生 Runtime 的渲染和私有媒体保存。

## 可复现入口

- [生产工作流](../../.github/workflows/spine-to-rive-video.yml)
- [真实多通道动作 Rive 烘焙](../../scripts/spine_multitrack_bake.py)
- [源 Spine Binary 解析](../../scripts/spine_binary_conversion.py)
- [Mesh / UV / Skin 适配](../../scripts/spine_textured_rive.py)
- [原生 Rive Skin 与烘焙对照](../../scripts/spine_skin_parity.py)

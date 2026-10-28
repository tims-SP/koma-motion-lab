# PROD-010 · Spine → Rive 骨骼与蒙皮独立排错（2026-10-29）

## 纠正历史结论

PROD-009 的 MP4 通过逐帧删除 Rive `Skin` 与 `Weight`，然后覆写 Mesh 世界顶点生成。它**完全没有验证实际 Rive 骨骼驱动蒙皮**。因此不得再以帧数、非空 MP4、内部 Rive 双分支轮廓相似度宣布转换完成。

## 实际发现的错误

1. `spine_textured_rive.py` 原先把 Spine 区域局部 UV 直接传给全尺寸 Rive 图集，未使用 `.atlas` 的 bounds、offsets、旋转信息。红弩箭图集包含 107 个区域，旋转情况：0°=61、90°=22、180°=14、270°=10。
2. 当前 Python `world_transform` 未完整处理官方 Spine 约束与继承规则。在原始 setup pose，51 个活动 Mesh/843 个顶点的全局位置相对官方 Runtime RMS 误差为 **8.96634** 个源坐标单位、最大 **33.20850**；贴图形变严重有明确的数值根源。
3. 顶点的最多骨骼影响数是 8，有 20 个顶点超过当前 Rive 四骨权重打包容量，直接截断不能称无损转换。
4. Rive 骨骼/皮肤结构存在（51 个 Mesh 的 Skin），但既往视频没有启用其动态变形。原生 Rig 与导出动画是不同层次。

## 已实施与实际验证

- UV 修复：`scripts/spine_atlas_uv.py`；8 个 unit tests PASS；使用官方 `@esotericsoftware/spine-core@4.2.120` 逐区域独立检验 642 个坐标，最大误差 **0**。证据：[UV Action 40786840283](https://github.com/tims-SP/koma-motion-lab/actions/runs/40786840283)。
- 全局几何：官方 Spine 4.2 Runtime 与 Python 转换器相互独立比较；**FAIL_RIG_FIDELITY**，明确暴露当前算法误差与超四骨权重损失。证据：[几何 Action 40787196240](https://github.com/tims-SP/koma-motion-lab/actions/runs/40787196240)。
- 官方 Spine setup 顶点作为 Rive Rig 静止参考：原生 Skin 与无 Skin 控制组轮廓 IoU **1.0**，平均 RGBA 误差约 **0.000617**。
- 动态绑定探针：旋转 Rive Bone `hnj_z_hit`（13 个 Tendon 引用），启用 Skin 的画面前景改变约 **24.91%**，移除 Skin 的控制组改变 **0%**；证明该骨骼与蒙皮确实发生动态关联。证据：[原生蒙皮探针 Action 40787621454](https://github.com/tims-SP/koma-motion-lab/actions/runs/40787621454)。

## 闸门定义

- **PASS_UV_MAPPING**：已验证。
- **FAIL_SOURCE_GEOMETRY**：旧 Python Solver 严重不符合官方 Spine。
- **PASS_NATIVE_SETUP_AND_BONE_POKE**：只表示官方顶点锚定的静止 Rig 以及被抽测骨骼的动态绑定成立。
- **FULL_RIG_AND_ANIMATION_FIDELITY：FAIL / NOT_TESTED**。其他骨骼、所有动作的逐帧顶点保真、IK/Path/Transform、剪切、FFD、附件/绘制顺序、超四骨权重都尚未全部解决。

媒体仅存在临时 Runner 或访问受限的 GitHub **Draft Releases**；Git 仓库仅保存源代码、工作流和此类纯文本 QA 数据。未向 `tims-SP/koma-motion` 本体仓库写入任何内容。

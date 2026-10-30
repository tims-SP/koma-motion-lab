# CORE-025：原生部件 → 前视复原 → 轻量曲面 → ±15°转头

用户授权：继续执行已提出的 CORE-025，工单必须逐步明确，每个完成阶段提交仓库，保存恢复入口。执行者 mcode；监工 Codex。仅操作 `tims-SP/koma-motion-lab` 的 `feature/koma-25d-core-021`；生产仓库不在范围内。

## 起点

- 已验收代码起点：`494d50b01c7594d631c5a93da0dd469f44b5dbb8`（CORE-024）。
- PSD：seagetch / Aka，CC-BY-4.0，SHA256 `979fa62702b25f8af25414637d9ba6c36cbc9eb03bfa0c454470c73bdf51e55e`，1630×1630，62叶层。
- 原生导出：`experiments/reference-factory/out/core024/native-v2/`。干净环境依次运行 `python prepare.py` 和 `python native_layers.py` 恢复。
- 原始图层含51个NORMAL、11个MULTIPLY；9个阴影层需要独立检查外溢。正面62层不代表侧面、背面素材已齐。
- 本阶段不用生成式侧脸作为 UV 皮肤，不请求新的生图或模型推理。

## 阶段及提交点

1. **M1：组装与阴影修整**。执行 `CORE-025-M1-mcode-order.md`。保留源图忠实复原和阴影裁剪派生版本；导出可逐层渲染的纹理、62层元数据、CPU对照及QA。监工重新计算对照并看黑底/棋盘图。代码、工单、结果、文本证据、状态一并提交。
2. **M2：Three.js 前视与曲面**。在已锁定 Three.js 0.180.0/Playwright/Vite 环境新增独立入口，62层各有独立网格；保留源像素XY/UV，添加可检查的非零深度场和共同头部旋转节点。0°与CPU参考对照；导出网格/UV检查图与投影锚点。验收后提交。
3. **M3：连续转头和抽帧**。0°→+15°→0°→−15°→0°，固定相机，97帧/24fps；输出真实视频与抽帧图。检查眼球、刘海、脸缘、耳根、颈部，分别报告几何、保真与视觉质量，不将结构通过写成生产通过。验收与失败项都提交。
4. **M4：干净环境复现和归档**。接入 Actions，以真实退出码运行准备/渲染/QA/编码；仅文本进入git与Actions artifacts，媒体进入Draft Release。记录run、release及恢复命令，提交最终检查点。

若某阶段失败，先提交故障证据和准确恢复步骤，再明确返修范围；不得直接把后续阶段标为完成。所有媒体/模型/依赖目录保持在被忽略的 `out/` 或既有node_modules中。

## 共同验收要求

- 原始PSD、INX、VRM、候选图、既有相机和依赖锁不得覆盖或改写。
- source 模式用于原图对照；clean 模式明确标为DERIVED_REFERENCE，不能冒充source逐像素真值。
- Multiply烘焙只能保证默认姿态等效，换底/遮挡关系变化的局限必须记录。
- 不接受整头PNG一张平面旋转来证明62部件曲面绑定。
- 每个通过或失败的阶段均有仓库提交与 `docs/STATUS.md` 的恢复入口。

## 参考依据

- W3C source-over与multiply公式：https://www.w3.org/TR/compositing-1/
- Three.js颜色管理（本地以锁定0.180.0源码为准）：https://threejs.org/manual/pages/color-management.html
- psd-tools合成接口（本地以锁定1.10.9接口为准）：https://psd-tools.readthedocs.io/en/latest/reference/psd_tools.composite.html

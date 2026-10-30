# CORE-024 原生图层与原生 Alpha 导出结果

状态：**PASS（仅限“原生图层导出与原生 alpha 前视”这一有限范围）**。生产级前视/UV parity 仍是 **NOT_TESTED**，自动语义分解仍 **NOT_TESTED**，rig 仍 **未完成**。

## 运行方式

```
cd experiments/reference-factory
python3 native_layers.py     # 前台单次运行，真实 exit code = 0
```

无安装、无联网、无模型推理、无白底抠图、无重绘。依赖仅为仓库既有的 psd-tools 1.10.9 / Pillow 12.3.0 / NumPy 2.3.5。

## 真实测量

源文件：`out/source/tutorial-aka.psd`，运行前先校验 SHA256 与 `sources.lock.json` 一致，不符直接退出。

| 指标 | 实测值 |
| --- | --- |
| 画布 | 1630 × 1630 |
| 叶图层数量 | 62（期望 62） |
| 叶导出错误 | 0 |
| PNG 与 SDK `topil()` RGBA 逐像素一致 | 全部一致（`all_topil_pixel_equal = true`） |
| 前景像素数（native alpha > 0） | 1,008,000 |
| `mae_rgb`（三通道平均绝对差，前景） | 0.1602 |
| `mae_max_channel`（逐像素最大通道差均值） | 0.3109 |
| `max_abs`（**单通道**最大误差，0–255） | 3 |
| `max_rgb_sum_abs`（三通道绝对差之和，仅参考） | 6 |

`max_abs` 已修正为真正的单通道最大误差（逐像素取三通道 |diff| 的最大值），原先错误地取了三通道之和；`max_rgb_sum_abs` 另存，仅作参考。

原生合成（`composite-transparent.png`，`psd.composite(force=True, alpha=0.0)`）alpha 统计：

- `opaque_px = 868,038`（32.67%）
- `transparent_px = 1,648,900`（62.06%）
- `partial_px = 139,962`（5.27%）
- alpha 取值覆盖 0–255 共 256 级；缓存合并图 `composite-cached.png` 为全不透明（alpha 恒 255）。

## 硬门禁行为

脚本在以下任一情况以非 0 退出：叶图层数 ≠ 62；存在 leaf 导出错误；任一导出 PNG 与 SDK RGBA 不逐像素一致。本次运行三者均通过，exit = 0。

## 风险与限制（务必保留）

1. **原始叶 PNG 未烘焙 multiply / opacity / mask / clipping**。`leaf-*.png` 是 `topil()` 的原始 RGBA，带蒙版、混合模式、不透明度、剪切的图层单独看并不等价于它在合成中的外观；报告的 `groups`/`leaves` 段保留了 `opacity`、`blend_mode`、`has_mask`、`mask_bbox`、`clipping` 等原生信息，供下游自行烘焙。
2. **forced composite 是强制图层渲染，不等于已修好的 rig**，也不等于完整前视/UV parity。强制合成会把阴影/光晕溢出到主体轮廓之外（composite-transparent 的 alpha 边缘可见外溢），因此不能把 `composite-transparent.png` 当成干净的抠好前景贴图直接验收。
3. 本次只产出**原生 alpha 透明前视**与 62 层原始图层，**不含**任何本地 C 候选图，**不含**自动语义分解结果。
4. 该导出尚未与任何多视图/绑定流程验证，前视之外的其他视角完全 **NOT_TESTED**。

## 产出物

- `experiments/reference-factory/out/core024/native-v2/layers/leaf-01..62-*.png`（62 个原始 RGBA 叶）
- `.../composite-transparent.png`、`.../composite-cached.png`
- `.../qa-backgrounds.png`（黑/棋盘/白三底 QA）、`.../contact-sheet-layers.png`（62 层接触表）
- `.../native-export.json`（机器报告，已纳入 CI text artifact）

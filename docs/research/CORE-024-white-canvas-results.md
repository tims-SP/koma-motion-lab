# CORE-024 白底抠图基线（white-canvas）结果

状态：**部分可用**。W250/W245 可作**临时预览**用的硬 alpha 抠图；XGEN **拒绝**；imagegen 变体 **不验收**；rembg **BLOCKED**。本节任何一条都**不能**被称作“已完成贴图验收”。

## 运行方式

```
cd experiments/reference-factory
python3 cutout_white_canvas.py    # 前台单次运行，真实 exit code = 0
```

无安装、无模型推理、无 API 调用、无 sleep、无 PNG 重试循环：每个变体只保存一次 PNG，随即做完整性校验与逐像素 RGB/alpha 断言。

## 输入固定与失败策略

运行前校验两个固定输入的 SHA256，不符立即失败（exit 2）：

| 输入 | 期望 SHA256 | 实测 |
| --- | --- | --- |
| `out/candidates/pilot-C-001.png`（本地 C 候选） | `66d661022b811874afb68ac9a033e8cede5d591d005503e4d023702de5424169` | 一致 |
| `out/core024/imagegen-cutout-C.png` | `220ee4ff62baae15aa0fa14f9dfb967c74ad14028f902699df2562c1aa9e8f25` | 一致 |

原图 RGB 逐像素保持不变：保存后重新读回，断言 RGB 三个通道与 alpha 与输入完全相等（`assert np.array_equal`），并做 PNG chunk 级完整性检查（截断写入会被发现）。

## 真实测量

原图 1254 × 1254。alpha 统计已按 **zero / partial / full(255)** 三个桶拆分；原先的 `opaque_px` 实际统计的是 alpha > 0，已更名为 `nonzero_px`（`transparent_px = total - nonzero_px`）。

| 变体 | 阈值 | 方法 | zero_px | partial_px | full_px | nonzero_px | coverage | 边缘接触像素 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| W250 | ≥250 | 边界连通近白去除 | 1,027,647 | 0 | 544,869 | 544,869 | 0.3465 | 0 |
| W245 | ≥245 | 边界连通近白去除 | 1,032,571 | 0 | 539,945 | 539,945 | 0.3434 | 0 |
| XGEN | — | imagegen alpha 迁移到原图 RGB | 993,799 | 577,634 | 1,083 | 578,717 | 0.3680 | 36 |

bbox：W250 = [208, 23, 790, 1180]，W245 = [210, 24, 784, 1178]，XGEN = [0, 10, 1240, 1244]。

## 结论与风险

1. **W250 / W245：仅可作临时预览**。二者 alpha 均为纯 0/255 硬边（partial = 0），阈值只影响主体外轮廓一圈像素，W245 比 W250 多抠掉约 4,924 px；实际肉眼仍有**细白边与硬边残留**（阈值化的固有产物），不满足贴图验收，不能作为 rig 或贴图资产交付。
2. **XGEN：拒绝**。迁移过来的 imagegen alpha 与原图 RGB 不同源，存在**漂移白边**（边缘接触像素 36，且 bbox 覆盖整幅图），沿 alpha 边界有明显的原图→生成图错位；不能作为抠图结果使用。
3. **imagegen 原图变体：RGB 重绘，不验收**。生成式原图存在 RGB 偏移，与 source 不同源，不能当验收基准。
4. **rembg：BLOCKED**。模型未安装、推理未执行，不存在任何结果，不能算作成功或失败的数据点。
5. 本节全部内容都只是**实验性抠图**：不是语义分解，不是 rig，不是精确 alpha ground truth，不是已验收的多视图角色。

## 产出物

- `experiments/reference-factory/out/core024/white-canvas/white-canvas-W250.png` / `-W245.png` / `-XGEN.png`
- `.../qa/{W250,W245,XGEN}_{on_black,on_checker,on_white,crop_sheet}.png`
- `.../report.json`

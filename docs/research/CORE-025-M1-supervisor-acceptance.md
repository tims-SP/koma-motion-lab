# CORE-025-M1 监工验收

执行mcode 0.7.2；独立检查Codex。日期2026-10-30。结论：**M1默认姿态部件组装与9层阴影裁剪PASS，限原型范围**。曲面、连续转头、生产级绑定和360°尚未验收。

## 数值和像素检查

- 真实PSD：1630×1630，62叶层。运行时同时核对固定PSD SHA与锁文件，并逐层对SDK和CORE024导出核对RGBA、顺序、名字及边界。
- 51个NORMAL层RGB原样保留；11个MULTIPLY层按默认下层背景烘焙成等效NORMAL贴图。两版本均为DERIVED_REFERENCE，不是原始源图字节副本。
- source全部62层alpha未改；clean只对9个指定阴影层裁剪alpha；53个其余层alpha保持原样，眉毛60/61未误裁。
- 导出的量化PNG重新合成后，对SDK透明合成：白底前景RGB MAE **0.125177/255**，黑底 **0.144745/255**，最大单通道差2/255，alpha MAE **0.025776/255**。原门槛0.5/255保持不变。
- 监工另用Pillow的独立alpha_composite实现重组实际导出PNG：source RGBA MAE **0.00392014/255**，clean **0.00515518/255**，最大通道差均为1/255。
- 9层clean alpha按原始基础层alpha独立重算，全部逐像素相等；原始/派生共186个纹理文件SHA均核对有效。
- 全部49个单元测试真实exit0（包括3个新合成数学用例）；监工重新执行prepare_core025.py，真实exit0。14个既有受保护输入、相机及依赖锁未变。

## 目视检查与限制

已检查黑底、棋盘及完整9组阴影对照。背发和脸外的指定阴影外溢已按合同裁剪；角色主体、眼白、眼球、发束、耳内白毛保留。源图本身仍有颈部软边及一个小的游离alpha片段，当前版本不将它们偷偷擦除，记为后续素材修整项。因此clean视觉PASS仅指本工单规定的9层处理，不代表最终贴图或完整rig。

Multiply→NORMAL的等效依赖默认下层背景；部件发生相对位移、遮挡变化后，阴影不保证物理正确，M2/M3必须另外检查。当前结果不证明Inochi2D完整默认姿态运行时一致性，也不代表侧面/背面资产已完成。

## 恢复

在experiments/reference-factory安装已有锁定依赖后依次：`python prepare.py`、`python native_layers.py`、`python prepare_core025.py`。无需生图或GPU模型。输出out/core025/assembly；完整机器证据见evidence/core025-M1-2026-10-30。下一步执行明确的M2工单。

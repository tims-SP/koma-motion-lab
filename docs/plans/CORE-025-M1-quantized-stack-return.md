# M1真实纹理合成返修（四项）

3个blend数学测试已真实PASS，但整流程source白底MAE3.782183、黑底3.802845，仍FAIL。监工已定位，不要再检查SDK/ICC/层序，不放宽阈值。

1. **必须先修这一行**：`composite_over`明确返回straight RGB和Ao。build_version中当前写法 `premult_out, ao = composite_over(...); acc_premult[reg] = premult_out` 错把straight放进premult缓冲。替换为 `out_rgb_straight, ao = composite_over(Cb, Ab, cs_q, as_q, "NORMAL")`，然后 `acc_premult[reg] = out_rgb_straight * ao[..., None]`，`acc_alpha[reg] = ao`。不要改已通过测试的blend核心数学。
2. shadow-cleanup-sheet每组实际宽300，却按150宽排5列，存在重叠和截断。改3列，每组宽2*cell、标签区≥44，x/y步长按完整组尺寸；先paste图片再画标签；完整显示9组source/clean对比，不重叠。
3. 输入verify时记录每个经过SDK像素比对的原始CORE024 PNG的相对file与SHA，写入assembly.layers对应项的raw_source_texture。config和assembly的source版本属于DERIVED_REFERENCE（默认姿态下multiply→normal烘焙）；不能写成每层原始RGB不变。明确51个NORMAL原始RGB不变，11个multiply RGB改变，原始PSD/CORE024 PNG仍是原始来源。
4. 原样重跑3测试及prepare_core025.py。用实际新的qa.json写docs/research/CORE-025-M1-results.md，记录source gate；clean_visual_gate维持NOT_REVIEWED。一次集中修改，一次前台运行即可；禁止再进行无关诊断/安装/后台/联网/提交。

内存可以顺便避免为所有62层各分配1630² alpha，clean只需3个基础层的alpha画布；非必要时不扩大重构范围。

# P15-63 · 右向近眼局部 Mask 神经补绘

## 目标
从 P15-56 的 1024x1024 右向候选制作真正的近眼隐藏皮肤，使眼部单独平移 18px 不出现透明洞，且非编辑区域 RGBA 完全一致；验证是否达到 ArtMesh 的视觉门槛。

## 实际调用与来源
- Git 基线：P15-62 / 1ae6cc0。
- 输入：P15-56 candidate-erode-2.png；P15-62 多边形基础上调整近眼 Mask。
- 固定裁切：原图 (385,290)-(897,802)，512x512 RGB，单独的 512x512 灰度 Mask。
- 初试 mkings/simple_lama LaMa（ZeroGPU）真实上传成功，但排队后显示“90s requested vs. 65s left”，未产生输出。
- 随后改用**运行在 CPU 的** Hugging Face Space pg56714/Inpaint-Anything，调用 get_inpainted_img 并保存真实 LaMa 神经网络返回的 512px 图。这个模型不需要 GPU 授权，并不是纹理复制或提示词扩散模型。
- 生成结果经过 hard Mask 与原始 RGBA 复合，严格保留所有 Mask 外源像素，输出 underpaint-full.png，同时保存原模型输出与单独眼部 ROI。
- 近眼单独右移 18px 后保存 eye-shift18.png。无透明孔。

## 独立验收
- Mask 内像素发生变化：11,423。
- Mask 外 RGBA 像素发生变化：0（逐像素测试，而不仅比较 alpha）。
- 移动 18px 的近眼区域明显透明孔：0。
- P15-62 局部纹理复制产生的粉红补片得到明显改善：新的无遮挡皮肤连续，原发型、远眼和脸型未改变。
- **视觉问题仍存在：** ROI 并非真正干净的眼部语义 Mask，眼睛移动后左侧出现被携带的发丝/皮肤岛，眼睫毛上沿有不自然亮边。不能只凭无洞和像素约束就放行正式 VDD。
- 正式 P0 Hero、65° Keyframe、ArtMesh 完全未修改。

## 代码与复现
- scripts/p15_63_prepare.py 生成固定裁切及遮罩，来源 SHA 写入 QA（重新运行会重置 QA，需再次 finalize）。
- scripts/p15_63_cpu_lama.py 真实提交到 CPU LaMa Space。
- scripts/p15_63_finalize.py 只使用保存的模型结果做强制 mask 合成与数值验收。
- scripts/test_p15_63_masked_lama.py 检查真实模型输出 SHA、近眼 18px 位移、外部 RGBA 完全不变、正式准入禁用。
- 交互审查以 HTML 文件和原图/遮罩/模型图/位移图的静态对比为主。

## 下一阶段 P15-64（最短路径）
**只改近眼层语义边界**，不要重新生成皮肤。利用已经得到的神经无遮挡底图、现有 45° 语义层与当前候选，拆分眼睛/睫毛与头发覆盖关系，清理当前被一起带动的肤色及发丝碎片；优先验证眼睛右移 18px 时没有明显亮边/皮肤岛，再考虑 VDD 多角度插值。

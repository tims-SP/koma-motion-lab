# P15-40 · P0 45°–65° 侧脸与发夹视觉审查

## 当前来源与实现

源素材为 P15-38 13 帧 × 13 部件的 443×443 RGBA 原画，存储在 VPS `experiments/gif-multiview-keyparts-mvp/private-assets/p15-38-p0-registered-arc`。源文件 SHA 在 `evidence/p15-40-profile-qa.json` 逐角度登记。现阶段保持全部源图像原字节，另输出可逆候选。

执行 `scripts/p15_40_profile_visibility.py`：

1. 将 45°–60° 原有远眼完整 RGB/Alpha 保持，61.25°–65° 根据侧脸方向，对完整眼睛采取朝眼外角锚点的几何收缩，对应可见面积比例实际为 0.640488、0.360204、0.122947、0。保留完整远眼原图作为独立 underpaint，不把其判定为已经新绘的真实隐藏笔触。
2. 发夹保留原始金色交叉笔触，在 ±3 原生像素内优化与 `hair.front` 的局部接触，逐帧平移结果及接触率写入 QA。实际 13 帧接触指标均改善；尚不等于画师确认的发夹穿发与背侧夹臂结构。
3. 生成 13 帧独立的 `source.png`、`candidate.png`、`far-eye-visible.png`、`far-eye-underpaint.png`、`difference-x4.png`、`face-zoom.png`；由浏览器 `index.html` 对照审查。

## 本轮证据

- `scripts/test_p15_40_profile.py`：8/8 回归通过；源 SHA、RGBA、原眼字节保存、单调面积、发夹接触不回退、画质签收独立等验收。
- `scripts/p15_40_browser.cjs`：Chromium 桌面与移动各 13 角度 × 3 模式，78/78 实际检查成功，8 张截图，JavaScript 与请求错误为 0。
- `evidence/p15-40-profile-qa.json`、`evidence/p15-40-browser-qa.json`：完整角度、来源 SHA、改动区域、视觉审核与浏览器截图证据。
- HTML 审查入口：`private-assets/exports/p15-40-profile-review/index.html`。
- ZIP：`private-assets/exports/p15-40-profile-review.zip`，87 项 SHA/CRC 可验证，8,346,369 字节，SHA-256 `384de6be8598e7363634ba34672df0a6d433e0b4f243257fe98e9336575af23e`，存储于项目 Draft Release。

## 视觉验收与下一关键工作

已人工观察实际 Chromium 的 57.5°、60°、65° 整图截图。60° 保留完整瞳孔和眼睑，金色发夹接触更稳定；但 65° 原始脸部即存在不自然的大片面部空白和零散笔触，现有局部几何操作不能补足合理的脸型、侧脸远眼/鼻梁和隐藏发束。

**视觉签收：当前侧脸全貌不通过；仅工程候选通过。** 下一步首要任务是独立取得符合 `p0_character_001` 身份的高保真 65° 侧脸关键原画及局部隐藏图层，连同已批准 P0 Hero 原图 SHA 验证，再在 ArtMesh + VDD 中逐层替换候选和逐帧审查。眼的面积连续性指标只能作缺陷诊断，不能替代原画质量。项目始终保持 TypeScript/WebGL 与原画分层路线。

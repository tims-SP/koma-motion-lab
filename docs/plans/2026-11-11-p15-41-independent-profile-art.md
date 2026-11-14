# P15-41 · P0 原生侧脸原画与 ArtMesh 准入

本阶段在 VPS 真实读取并视觉比较已有独立侧脸 RGB/RGBA 原画、P15-38 注册 60°/65° 与 P14 67.5° 候选，检查朝向、角色特征及面部透视。直接检查 Chromium 截图确认：原 P15-38 65° 面部有明显空白和笔触碎片；既有独立 Qwen 侧脸来源画质更完整，但呈接近纯侧面的右朝向，与当前 65° 登记角度不一致。

以 `private-assets/p15-independent-candidates/yaw065-artmesh/` 已存在的 SHA 登记 13 层为唯一独立绘画语义源；通过 `scripts/p15_41_profile_candidate.py` 重组 RGBA 并把当前 P0 65° 金色交叉发夹独立挂到右侧刘海（测试性二维坐标 690,295）。重组关键画面 SHA 为 `8bd6de05424261393c0dbe71e20d64ddaedb80006bc8cb66b3342c854172a403`。这些是单独候选，不能误称为正确的 65° 新画。

`private-assets/exports/p15-41-profile-candidate/index.html` 比较当前 60°、65° 和独立候选，提供近眼、前发、发夹的真实 RGBA 层检查。`scripts/test_p15_41_profile.py` **7/7** 通过；`scripts/p15_41_browser.cjs` 真 Chromium 桌面/移动共 **4 组**、12 次图片加载与 **4 张截图**、错误 0。证据：`evidence/p15-41-profile-qa.json`、`evidence/p15-41-browser-qa.json`。

审查 ZIP `private-assets/exports/p15-41-profile-candidate.zip`：23 文件、4,483,290 字节、SHA-256 `e96376d3f99f134ac505d1e5119bcdb9e252f5d042154780322671a288f372c6`，已上传 GitHub Draft Release。

## 下一关键瓶颈

1. 以 P0 Hero 原图和 45° 正式身份源为共同参考，制作真正处于 60° 与严格 90° 之间的 65° 右朝向原画。现有纯侧脸质量可以作为侧脸结构参考，但不能直接替换 65° keyframe。
2. 正式 65° 绘画需要眼鼻、脸颊、前发及发夹的正确相互遮挡，独立 RGBA 的隐藏线稿而不是仅拆分可见像素。当前这套 13 层属于像素分配候选。
3. 重新验证 60°→65°→90° 的相机角度和视觉连续性后，才可升级 VDD 关键帧；保留全部已冻结 P15-38 来源。

结论：本阶段完成真实独立原画回收、语义合成、HTML 浏览器审查。独立原画质量相较当前残缺脸型更完整，但正式 65° 角度准入与身份 Hero SHA 尚未通过。

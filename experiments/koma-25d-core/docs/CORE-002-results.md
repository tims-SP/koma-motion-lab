# CORE-002 · Real source animation + out-of-plane skinning (2026-10-29)

## Evidence
- [Successful workflow #40901702062](https://github.com/tims-SP/koma-motion-lab/actions/runs/40901702062)
- Draft Release tag `koma-25d-core002-40901702062`, containing `yaw.mp4`, `walk.mp4`, `reach.mp4`, `contact.png`, JSON diagnostics
- Real source: MIT-licensed Godot Skeleton2D GBot at pinned upstream commit `b761b4cd5718a7118f2c95eb55f181d0a5f004f1`
- Source character input: **7 Polygon2D meshes, 16 Bone2D joints, 110 original mesh vertices**, 8 parsed Animation clips
- Output: Three.js WebGL2, Chromium SwiftShader, **48 frames × 3 scenarios**, 960×540, 24fps

## Measured machine checks

Image difference is measured on full RGB output after cropping away the top HTML overlay, not subjective visual acceptance. Background/foreground threshold=24; motion difference threshold=18.

| Scenario | Visible geometry fraction at 0/12/24/36/47 | Sample-to-sample changed pixel fraction |
|---|---|---|
| Camera yaw | 9.10%, 9.44%, 8.16%, 5.60%, 2.65% | 7.00%, 9.92%, 9.65%, 7.19% |
| Source walk clip, fixed camera | 8.65%, 7.52%, 9.29%, 7.73%, 8.65% | 6.52%, 8.18%, 6.00%, 4.30% |
| Out-of-plane arm reach, fixed camera | 8.46%, 8.41%, 8.46%, 8.42%, 8.46% | 0.48%, 0.56%, 0.60%, 0.44% |

### Verdict

**PASS: structural, source-clip and spatial-axis motion smoke validation.**

**NOT ACCEPTED: anime visual quality; original Godot renderer pixel/animation parity; coherent 360-degree surface; side/back drawn appearance; complex 3D reach.**

Out-of-plane reach affected only ~0.6% of pixels in one sample step; do not confuse any detectable change with convincing pose quality. Neutral backside and side proxies remain visible at rotation, so these videos are deliberately diagnostic, not final assets.

## Critical technical issues for CORE-003

1. Original texture alpha and UV require an independent pixel-wise comparison with an original source runtime render; preserving numeric UVs is not sufficient.
2. Source sample clips currently use linear keyframe interpolation. The original Godot AnimationTree blending/state machine and transition values are not reproduced.
3. Side/back geometry is a stitched neutral proxy, with no valid original artwork, normals/style or independent occlusion control.
4. Mesh/skinning limits require per-joint local-space correctness tests, including contact, elbow and shoulder silhouette.
5. Need real, licensed multi-view artwork or generated-but-verified side/back appearances before claiming quality gains.

Do not merge this experimental PR or promote any code to `koma-motion` based solely on these checks.

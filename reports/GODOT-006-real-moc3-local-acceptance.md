# GODOT-006 · Real MOC3 isolated-container acceptance (corrected by GODOT-007)

> **2026-10-29 correction:** The previous claim of misplaced mouth/eye deformation and a confirmed production-blocking mesh-binding error was **invalid**. It mixed pixel coordinates from the full-body 1080p camera with a *different 2.75× facial zoom* image. GODOT-007 independently checked both on the **same** 1920×1080 camera; changed pixels are within the correct visible lips and eyes. See [GODOT-007 corrected report](./GODOT-007-face-parameter-roi-correction.md) when merged. Do not reuse the previous annotated image, its incorrect ROI=0 score, or the previous blocker claim.

Date: 2026-10-29. GitHub Actions [run #99](https://github.com/tims-SP/koma-motion-lab/actions/runs/40851922127) passed. Local Godot `4.7.2.stable.official.ed1daf0bf`, Linux x86_64, Xvfb + Mesa llvmpipe. Original personal-research asset: `myssal/Reverse-1999-CN-Asset/live2d/roles/301003_x`. Real `gd_cubism` v0.9.1 / PurismCore v5 ABI retrieved from a short-lived Actions artifact. All six source files matched source SHA-256 manifests; no original assets or binaries committed.

## Independent local acceptance

| Gate | Result |
| --- | --- |
| Godot import, native GDExtension load and MOC3 model load | PASS |
| 1080p nod @ 30fps | PASS, 90/90 frames, 3s H.264 |
| 1080p idle @ 30fps | PASS, 270/270 frames, 9s AVI/MJPEG then H.264 |
| 1080p face_idle @ 30fps | PASS, 90/90 frames; **visible mouth change confirmed** after corrected ROI check |
| 540p idle @ 30fps | PASS, 270/270 frames |
| 1080p idle PNG-sequence path | INCOMPLETE, timed out at 261/270 frames; switch to native AVI |
| Local vs Actions nod/idle samples | Similar; mean head ROI RGB differences roughly 1.97–2.18/255 (includes H.264 loss), **not** official Cubism parity |

## Corrected parameter-to-mesh observation

Using **the same 1080p full-body camera** for both comparison frames and measurement ROIs:

| Probe | True ROI (full-resolution pixels) | RGB mean absolute difference | Changed pixels (max-channel difference >10) | Corresponds to |
| --- | --- | ---: | ---: | --- |
| ParamMouthForm -1 → +1 | x935:995, y183:217 | **1.409/255** | 58 | Visible lips |
| ParamMouthOpenY 0 → 1 | x935:995, y183:217 | **5.987/255** | 326 | Visible lips |
| ParamEyeLOpen 0 → 1 | x955:1008, y142:196 | **7.229/255** | 439 | Visible left eye |
| face_idle frame 0 → 40 | x935:995, y183:217 | **1.930/255** | 88 | Visible lip movement (subtle) |

Independent Purism Core C-ABI mesh diff: `ParamMouthForm` affects 4 drawables, `ParamMouthOpenY` affects 5 (ArtMesh191–195); `ParamEyeLOpen` affects 8. Godot-only isolate rendering of ArtMesh191–195 shows a visible mouth piece **at the real lips** on the identical camera. No parameter-to-mesh spatial misregistration has been demonstrated.

**Remaining limitation:** parity with the proprietary official Live2D Cubism Core/renderer has **not** been tested; the native Core cannot be assumed identical from self-consistent local tests. No general rig/skin quality certification.

## Evidence policy

Only source scripts and Markdown diagnostics belong in Git. Original model, textures, derived screenshots/videos and native shared library remain local or short-lived artifact storage; avoid public releases for game-derived artwork.

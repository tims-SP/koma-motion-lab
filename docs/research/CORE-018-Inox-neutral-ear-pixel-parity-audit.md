# CORE-018 · Source Aka original-UV ear parity against REAL Inox2D OpenGL

**2026-10-30 · actual reference rendering PASS; 0-degree whole-puppet pixel parity NOT ESTABLISHED; art quality FAIL.**

## Grounded original reference

- Inochi2D original Aka.inx by seagetch, CC BY 4.0, full 17,731,911 bytes, pinned SHA256 dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f.
- Actual Inox2D Rust OpenGL source pinned d4dd9dd7f16b775042cbda44370570abf9a8cf81. This is a supported experimental port, NOT official D-SDK pixel certification.
- [GitHub Actions #41011328118](https://github.com/tims-SP/koma-motion-lab/actions/runs/41011328118) SUCCESS: built Rust, rendered complete Aka in Mesa/Xvfb with fixed native HeadYaw=(0.50,0.50) and (1.00,0.50), obtained **real lossless 720x880 PNGs**. Regular downloadable Actions artifact CORE018-pinned-Inox2D-real-render-reference, not a hidden draft release.
- Native neutral PNG SHA256 9ee4ac4804e8cb1a147b0ab257b253d4bc04f82d9966c91ad21647d973646a23. Native maximum PNG SHA256 4a0a1c1d69d58e3873c5bfb084a0e8f728a2c3731c462777c2fec6c95d7a16e3. Real source change area between these frames at >16 RGB delta: 2.0694% of screen. No physical degree claim.

## Authentic source-UV independent ear reconstruction

The local reference rendering used original **57/59 vertices**, **89/93 triangles**, unchanged native UV arrays including out-of-[0,1], original RGBA TGA, original Root/Body/Neck/Face/Back Side Hair/Ear parent transforms and 12 affecting HeadYaw bindings, at source pitch center .5. Independent Python source mesh renderer used the same nominal native orthographic camera scale .15 and viewport 720x880.

**Reference is full native character with hair/face/overlapping masks. Comparison renderer draws only ears. An exact full-model pixel parity metric is mathematically NOT meaningful, so parity is NOT certified.** Only the upper ear-tip region was measured: image-left x250:365 and image-right x365:455, y30:110, limiting hair occlusion.

Fit ONE 2D pixel translation to source at neutral only, and use exactly the SAME translation for maximum pose. Global result **(-10,+4) px**. No per-pose refitting.

| Native pose | Image-left ear upper silhouette IoU | Image-right ear | Mean |
|---|---:|---:|---:|
| Neutral 0.50 raw, no correction | 0.3849 | 0.2552 | 0.3201 |
| Neutral 0.50 fixed common offset | **0.8965** | **0.8965** | **0.8965** |
| Maximum 1.00 raw | 0.3850 | 0.4552 | 0.4201 |
| Maximum 1.00 same NEUTRAL offset | **0.7461** | **0.8143** | **0.7802** |

An earlier initial check found ~95% when shifting each ear separately; those are per-ear best-case numbers, **not** the rigorous one-common-camera result of 89.65%. At maximum the same camera offset leaves real nonrigid/occlusion mismatch, only 78.02% mean.

Color MAE over intersection of upper-ear region after fitting: 10.85/15.12 RGB units (left/right neutral), 15.31/16.67 (maximum), out of 255. These are **not full original raster parity** because real native renderer draws many extra occluding parts and uses GPU blending/filtering.

## Actual local encoded video and independent visual review

A distinct independent **97-frame, 24fps, 1530x500 H.264 MP4** was encoded, SHA256 ff00b43eee88f29ff63dcafb2905aa1a4b99e43b7d18df6195b9efe41f826c70. It has:
- LEFT: one of the TWO genuine FIXED native full-model reference PNG states (nearest endpoint hold, NOT a continuous native rendered video);
- CENTER: independent animated original INX ear-only HeadYaw with authentic source UV/TGA and hierarchy;
- RIGHT: blended alignment diagnostic, NOT a parity proof.

Decoded FINAL MP4 frames 0,12,24,36,48,60,72,84,96 with FFmpeg; actually opened and inspected resulting JPEG contact. Additional red/green/cyan upper-ear comparison (red=native only, cyan=custom only, green=overlap) visually checked. It shows neutral coordinate improvement and surviving maximum HeadYaw shape differences.

Full reproducible package in conversation: /mnt/data/core018/CORE018_original_Inox_neutral_ear_alignment_QA.zip, size 5.96 MB, SHA256 f6ab2138f24ae6c35509065c7d26f2caddf1266f303d0cc16b9cbdc6d59b864b. Includes two actual upstream PNG screens, original ear source art/UV/bindings, three Python source scripts, real MP4, nine decoded screenshots, metric reports and runnable README. **No binary was committed as Git blob or represented as produced by Actions beyond original upstream two PNG reference captures.**

GitHub text code: .github/workflows/koma-25d-core-018.yml; experiments/koma-25d-core/tools/qa_native_baseline18.py; experiments/koma-25d-core/tools/diagnose_ear_tip_alignment18.py.

## Honest acceptance

| Gate | Outcome |
|---|---|
| Real pinned Inox2D OpenGL neutral/max source PNG | PASS in Actions |
| Source INX ArtMesh ear vertex, UV, TGA and original HeadYaw interpolation | PASS independent local test |
| ONE neutral camera calibration, reused for max | PASS (method) |
| Near-neutral upper ear silhouette agreement | 89.65% mean, still NOT exact pixel parity |
| Maximum parameter upper ear agreement | 78.02% mean, below target |
| Whole original Aka 0-degree pixel parity | NOT PROVEN |
| Original-authored side and rear ear art | MISSING |
| Original side/rear skin UV on 3D | NOT IMPLEMENTED |
| Continuous anime-quality 180/360-degree turn | FAIL / NOT BUILT |

## CORE-019 recommended task

Use the **same native Inox2D renderer but isolate just two source ears as drawables**, retaining their original ancestor hierarchy and HeadYaw parameters. Render unoccluded RGBA into exactly the same camera at original neutral and max, then compare original GPU pixels with independent original INX ear mesh UV/TGA. Diagnose fragment texture filtering, UV wrap/clamp and premultiplied alpha, source z-order, and 2D deform interpolation separately. No more guessed 3D thickness or blind AI sheets until 0-degree true component parity passes. Even source ear pixel parity would not imply full 360 skin completeness. Main production repo untouched; keep Draft.

Mature references: [Inox2D](https://github.com/Inochi2D/inox2d), [Inochi2D parent transforms](https://docs.inochi2d.com/en/latest/creator/nodes/node.html), [original mesh UV specification](https://github.com/Inochi2D/inochi2d/wiki/JSON-Data-Specification).
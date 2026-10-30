# CORE-021 · Native true-default Aka ears — original source UV/ArtMesh pixel parity

**2026-10-30. THIS IS A REAL EXECUTED SOURCE COMPONENT FIDELITY TEST. Verdict: source ear 2D parity passes bounded thresholds at all seven same-pose original parameter points; exact pixel equality and 360° artwork DO NOT pass.**

## Why this matters, and what previous CORE-020 numbers were NOT

The original Aka INX \`Head:: Yaw-Pitch\` external *authoring API* has **min [-1,-1], max [1,1], default [0,0]**; normalized interpolation grid x: 0/.125/…/1 and y: 0/.5/1. Earlier CORE-020 raw (.5,.5) screenshot was **not actually neutral**, mapping to normalized (.75,.75). Those mismatched-pose metrics are historical diagnostics only, not valid measurements of source neutral fidelity.

This round uses **pitch raw 0** and raw yaw \`-1,-.5,0,.25,.5,.75,1\` matched exactly between GPU and CPU; default is **(0,0)**.

## Real original and upstream assets

- Actual original full Aka INX by **seagetch, CC BY 4.0**, SHA256 \`dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f\`.
- Real [Inox2D Rust OpenGL renderer](https://github.com/Inochi2D/inox2d), pinned \`d4dd9dd7f16b775042cbda44370570abf9a8cf81\`. This is an *experimental Inox2D implementation*, **not official D-SDK reference parity**.
- Two original source INX ears: 57/59 original ArtMesh vertices and 89/93 original triangles; unchanged original UV (including out-of-[0,1] source positions), original TGA pixels, original entire INX parent hierarchy and source HeadYaw bindings.
- Native OpenGL test filter suppresses **draw calls** of non-ear ArtMeshes while still evaluating other original puppet nodes and parameters. Nothing is pruned from the actual original rig.

## GitHub Action execution, actual H264 and a FIRST strict failure

Run [#41018637196](https://github.com/tims-SP/koma-motion-lab/actions/runs/41018637196) produced all 13 real PNGs and H264, then **FAILED** a byte-identical screenshot-return assertion for repeated raw yaw=-1. This was not swept under the rug.

Root of fail: PNG SHA256 equality is too strict for independent, time-separated GL screen captures. The revised source-pixel repeat check measured all six pairs of identical input poses; **three are byte-identical, three differ by trace pixel values, with changed fraction >16/255 in foreground equal to 0.00 for ALL six**, one foreground RGB MAE ~0.001/255. This is **not evidence of a visually unstable rig**. The two follow-up Actions runs [#41019136981](https://github.com/tims-SP/koma-motion-lab/actions/runs/41019136981) and [#41019158937](https://github.com/tims-SP/koma-motion-lab/actions/runs/41019158937) **SUCCESS** with real PNG artifact and no claims of exact source pixel identity.

- **13 original independent GPU OpenGL 720×880 screenshots** (7 source input poses, reverse 6).
- Actual encoded native \`actual_native_default_13frame_GL_H264.mp4\` — **78 H264 frames, 24fps**, representing exactly **13 original GPU screenshots held at 4fps**, NO optical flow or invented in-between head poses. SHA256 \`0f00e9a0d5af77442604d2c9690cc7bbab9b15567ab0191621b663194086\`.
- The encoded final H264 was independently decoded at frames 0/12/24/36/48/60/72/77. Contact picture visually inspected.
- GitHub Actions artifact includes actual PNG, H264, decoder images, QA JSON and pixel-variance measurements; no paid OpenAI API or GPT generation was used.

## Independently executed CPU original-ArtMesh replay and parity

Local CPU software renderer actually consumed the exported source original INX ear TGA/UV/triangle arrays and all original ear ancestors, uses original *authoring* [-1,+1] input → normalized [0,1] x/y bilinear grid conversion, and explicitly respects the native renderer skip-if-default ([0,0]) parameter. It rendered **seven independent RGBA PNGs**, each at the same raw yaw and pitch0 as real GPU frames.

The same shared camera required **(0,0) pixel offset** for every pose — **NO per-ear/per-pose fitted shift**. We tested both a warm-color-limited source threshold and a **more complete all-ink mask**, which compares any nonblack native ink (RGB max >16) to original source ear alpha (>16), within fixed x95:590 / y0:290, and reports premultiplied alpha RGB over the overlap against the native black background.

| Raw Yaw, raw Pitch=0 | Normalized grid x | All-ink silhouette IoU | Overlap premultiplied RGB MAE /255 |
|---:|---:|---:|---:|
| -1 | 0.0 | **0.993172** | **0.8686** |
| -0.5 | 0.25 | **0.995381** | **0.8503** |
| **0 (TRUE DEFAULT)** | **0.5** | **0.993311** | **0.7434** |
| +0.25 | 0.625 | **0.995831** | **0.8445** |
| +0.5 | 0.75 | **0.994354** | **0.8531** |
| +0.75 | 0.875 | **0.993601** | **0.7169** |
| +1 | 1.0 | **0.993757** | **0.8381** |

**PASS bounded source ear component fidelity**: all seven exceed IoU>=0.9900 AND overlap RGB MAE<=1.0/255. Residual fringe antialiasing/alpha threshold differences remain, so DO NOT claim exact pixel-for-pixel or any full character parity. Manual inspection of complete seven-line green=overlap / red=GPU-only / cyan=CPU-only image independently confirmed the same ears, actual original painted source and no large source pose mismatches.

Correctly matched core source UV, parameters and camera — not more guessed Z geometry — caused the major improvement over prior 80–94% misparameterized cases. But raw pitch 0 differs from CORE-020 raw .5, so **DO NOT directly attribute all numeric improvement to only one algorithm change or claim a controlled A/B**.

## Secondary actual H264 and visual inspection

Encoded an independent **78-frame 24fps 1368×360 H.264 GPU/CPU side-by-side video**, SHA256 \`57b8c32dececed7933bbf1b9ba4eb0518cc86140a9a44ed947811aecd02bfabf\`, at actual 13 GPU snapshot poses, corresponding seven independent CPU images and overdraw mask; no video generation model and no invented intermediate poses. FFmpeg decoded final encoded frames 0/12/24/36/48/60/72/77; inspected the actual contact PNG/JPEG visually. The results are genuinely source-ear component 2D animation, **NOT source 3D/360 character rotation**.

## Local self-contained test package and code policy

[Downloadable in this conversation] \`/mnt/data/CORE021_Aka_true_default_INX_GPU_CPU_parity_FULL_QA.zip\` **72 entries, ~1.58 MB, SHA256 \`8100988cb0a9df530bc7e5976213a59031b1203c458928a2721cd9fd9a4ce47f\`**, verified ZIP CRC. Includes:
- exact original 2 source ear TGA/UV/mesh JSON and native parent/parameter JSON, no original full binary or unlicensed reupload,
- 13 real native OpenGL PNGs, first and second H264, 8 decoded frames and contact, native startup logs and stability QA,
- 7 independently painted original UV ear CPU RGBA PNGs, standalone replay and comparison Python scripts, full-color and other QA JSONs,
- both final encoded movies and decoded contact panels with reproducible README.

Git text-only repo:
- \`.github/workflows/koma-25d-core-021.yml\` — real native render/PNG/H264 test and artifact even after failures.
- \`experiments/koma-25d-core/tools/qa_native_default21.py\` — actual source/default and repeated-source-variance QA.
- \`experiments/koma-25d-core/tools/verify_fullcolor_parity21.py\` — independent GPU/CPU all-ink threshold comparator (real PNG inputs; not part of source GPU CI).

## Acceptance status and next action

| Gate | Core 021 |
|---|---|
| Genuine original Aka raw (0,0) default camera/rig, source 2-ear GPU/CPU matched | **PASS** |
| Source ArtMesh 57/59 mesh, TGA and exact original UV unchanged | **PASS** |
| Seven actual source input poses and full-ink compare | **PASS (>99.3% IoU, <0.87 RGB MAE)** |
| Native source 78-frame H264 encode/decode and actual visual inspection | PASS |
| Exact byte-for-byte shader pixel identity | **NOT PROVEN / not required for current bounded gate** |
| Official original Inochi D renderer parity | NOT VERIFIED |
| Original full 76-node character source 0° parity with same 2D renderer | NOT TESTED |
| GPT side and 180 rear art mapped to 3D side/back ear/face/hair UV | **NOT DONE** |
| 2.75D head and 360° high-quality continuity | **FAIL / NOT BUILT** |

**CORE-022 recommended:** stop polishing source 2D ear CPU parity once bounded gate has passed. Return to actual **view-dependent 3D ear shell art/UV**, starting with artist-compatible ear rear and true profile painting; ensure **front native ArtMesh/UV at raw (0,0) remains immutable**, side/rear patches genuinely populated rather than synthetic-magenta. Add independent hair and face parts only after profile ear passes decoded-video visual QA. Production repo \`tims-SP/koma-motion\` untouched. Draft R&D only.

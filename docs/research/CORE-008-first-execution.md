# CORE-008 · actual first execution, source pack, native rig and rejected AI candidate

**2026-10-30. Verdict: SOURCE ASSETS & PARAMETER DISCOVERY PASS; GENERATED VIEWS REJECTED.**

## Verified run and release
- CI (with actual downloads, hashing and image audit): https://github.com/tims-SP/koma-motion-lab/actions/runs/40973355001
- The first successful source pack: https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-bd72b741a30e24a6493d (DRAFT)
- The newest CI run with Head Yaw binding inspection has a separate, later Draft Release.
- Source binaries are not in Git; publication restricted to legally reusable preview images and metadata in Draft Releases.

## Source originals successfully generated and independently viewed

- Official PSD: Inochi2D/inochi2d-docs pinned commit \`593c657855d5679f01443ef311346298fd25e117\`, SHA256 \`979fa62702b25f8af25414637d9ba6c36cbc9eb03bfa0c454470c73bdf51e55e\`.
- Author seagetch, Aka model CC BY 4.0 as stated by Inochi2D/example-models.
- \`source_A_aka_front.png\` (1024×1024) from actual original composite, SHA256 \`c22f2af3f426d4e79745e28a1244750d1c46b41d82f46570be63b9543aedb4e4\`.
- \`source_B_aka_parts.png\` 4×4 contact sheet of 16 **original PSD source parts** (not generated art), SHA256 \`8689d1763a73a52b98202d088e93683c27065d63fb043b2d781709e8014b72a2\`.
- Actual image check in CI logs: Aka has **golden-orange bob haircut**, magenta-red eyes, huge amber fox ears with white interior, warm orange side locks, burgundy leaf on bangs, violet choker. These traits are ground-truth character identity. No ornate shrine outfit or pink hair is present in the official Aka head illustration.

## Unexpectedly important native model discovery

The full separate \`Inochi2D/example-models/Aka.inx\` was fetched from Git LFS using \`media.githubusercontent.com\` at pinned commit \`cd95dd00ddff63b1f7d2b84a19914c3c70d05945\`. This is NOT the tutorial02 layout-only INX.

- Full binary **17,731,911 bytes**; verified SHA256 \`dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f\`.
- **34 native parameters** actually parsed. \`Head:: Yaw-Pitch\` exists with **114 binding objects** across 9 horizontal × 3 vertical parameter samples (axis sample arrays: [0,.125,...,1] and [0,.5,1]).
- Also \`Head:: Roll\`, \`Body:: Yaw-Pitch\`, eye blink/move, mouth, physics for hair/ears/sleeves etc.
- The first inspected bindings are real node transform channels \`transform.t.x\`, with 9×3 sample values and \`Linear\` interpolation. Source data can be reused; the original model already has pose-dependent 2D art mesh deformation information.
- **Native runtime pose rendering not executed.** The parameter grid is normalized, not equivalent to calibrated physical 30°/45° yaw; do not invent degree semantics or claim native visual parity.

## Rejected first GPT image generation attempt

The image generation attempt produced a 4-panel white/pink-haired shrine-style fox girl with labels, ornament bells/ribbons; actual Aka original has golden-orange short hair, red-magenta eyes, giant amber fox ears and a burgundy leaf, neck-only source portrait.

- Candidate status: \`REJECTED_CHARACTER_IDENTITY_DRIFT\`.
- It is **NOT Aka** and is NOT a side-angle image usable for the original character.
- It has multiple panels and labels, contrary to the one-angle one-asset contract.
- No accepted 30° or 45° generated original exists.
- No generated preview was ingested as an official PNG, exported to a release, segmented, UV-registered or presented as successful material.
- Root limitation: the current image-generation invocation did not use an actual original Aka image as an enforced edit reference, despite a source reference being visualized to the assistant. Do not continue generating new views text-only.

## Updated next task — source assets before invented views

1. **Use full native Aka.inx as the primary deformation reference**, evaluate \`Head:: Yaw-Pitch\` in the actual Inochi2D renderer (or faithfully validated equivalent); inspect angle-specific art changes, layering and source UV.
2. Establish which target 15/30/45° character viewpoints the native parameter can actually represent; normalized param=1 is NOT automatically 45°.
3. Feed the real PNG \`source_A_aka_front.png\` as an **actual supported image attachment/edit reference** to the image-generation engine. The exact image should be used as image-to-image edit input, not as a description, or fail closed.
4. Generate only one +30° candidate first, validate same character by direct image comparison; cap further generation unless identity passes. Then generate +45°.
5. Preserve source front UV; register generated view UVs per original hair/face/ear component; produce video only after view material acceptance.
6. Inspect actual MP4 decoded frames as in CORE-007; do not equate structural success or parametrized grid presence with visual quality.

## Quality status

| Check | Result |
|---|---|
| Actual front PSD & 16-part atlas | PASS / VISUALLY VERIFIED |
| Full Aka INX file authenticity via Git LFS hash | PASS |
| Head:: Yaw-Pitch sampled param and 114 bindings | PASS (data inspection) |
| Official native Inochi2D pose replay | NOT EXECUTED |
| True 30°/45° missing-view AI illustration | FAIL / NOT ACCEPTED |
| Real original-art UV/mesh map of generated new view | NOT STARTED |
| 0–45° continuous **new** video in CORE-008 | NOT STARTED |
| Anime production appearance | NOT ACCEPTED |

**Repo discipline:** Git only code and reports, preview raster images in draft release. Do not promote to tims-SP/koma-motion.

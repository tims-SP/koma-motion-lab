# CORE-011 · GPT 90° profile / 180° rear creation and actual acceptance results

**Round date:** 2026-10-30. **STATUS: ALL NEW GENERATED ART REJECTED.**
**Output type produced:** 4 multi-panel 360° character-sheet **ILLUSTRATIONS**, not standalone source-paint or rig/mesh/UV/video files.

## Real inputs and observed generation attempts

Previous user-generated Aka-like reference images (both 1254×1254 RGB, not independently the real original PSD):
- \`金色狐耳少女肖像.png\`: SHA256 \`48647551a17ea5216d9af9703f01f37873c412fe9d9d331bb7210027022193a4\`
- \`三分之四侧颜狐耳少女.png\`: SHA256 \`59ad8cfa30575a59b959339e9f38c5c112b0b9ef966b9fed9948a80abe73745a\`

Four actual new image-generation outputs, **each 1536×1024 RGB**, not correct 90°/180° standalone outputs:

| Run | Local generated image | SHA256 | Artwork decision |
|---|---|---|---|
| 1 | \`a_clean_anime_character_turnaround_sheet_asset_ill.png\` | \`4bf12820aeedf2b0a1621d05d8ebec2dbaa3d30a0306a2f88b923ad2c3d8c0a0\` | REJECT |
| 2 | \`a_detailed_character_turnaround_rotation_reference.png\` | \`a619b0330fb88e10918ba2776f3eee2471fce7fe807e6af689e2b143397c7c7f\` | REJECT |
| 3 | \`wide_clean_infographic_style_character_sheet_m.png\` | \`f8df114dfca5ed470de81aa5116c2387ef84b5436b96c5f28e6fc06add4f4bc0\` | REJECT |
| 4 | \`a_clean_professionally_designed_character_referen.png\` | \`33c4004a987010fdac9d2fda59fc59ac227b11109c83d7a39e8b3d297055db42\` | REJECT |

**Direct image review** of all four real files:
- Rather than one 90° side or one 180° rear on a clean canvas, the generator repeatedly returned eight-view **turnaround-infographic montages**.
- The character drifted: original Aka-like input has simple short gold bob, tall amber ears, small red leaf at top bangs and black choker; generated panels invent **braided rear locks**, **large ribbon/tassels**, costume redesign and bell collar. These are NOT authenticated side/back depictions of source Aka.
- Some 90° panels point the nose to IMAGE LEFT despite asking for nose toward IMAGE RIGHT.
- The labels “UV,” “transparent layer,” “192 frames,” “8s 24fps,” “62.5% finished,” “PR #22,” etc. are **raster text hallucinated inside the generated picture**. No actual UV map, mesh metadata, temporal video, Github PR or auto extraction is created by generating a picture.
- Cropping each 1536px-wide sheet into 8 nominal columns produces only **192×325** screenshots, not plausible high-resolution standalone skin references. Upscaling cannot restore original hair/face/ear details.
- **There is no evidence the image generator actually used the genuine official Aka PSD as an explicit attached image-edit conditioning input.** The previously accepted GPT composites are also not an equal replacement for source original PSD.

## Actual production artifacts created and inspected locally

- \`core011/audit_generated_views11.py\` processes all four actual 1536×1024 generated binaries; records image hashes, text/visual rejection decisions, clips 90°/180° evidence and makes reference contact image.
- \`core011/identity_contact_4runs.jpg\`: visual comparison of real user-provided front / three-quarter GPT portraits vs the actual four generations' extracted side/back panels. **Visual inspection completed.**
- \`core011/identity_qc.json\`: four generated attempts all \`REJECTED_NOT_INGESTIBLE\`. Eight crop evidence images saved, explicitly not accepted artwork.
- \`core011/single_view_asset_gate11.py\`: reusable local precheck. Whole 1536×1024 sheet rejected for wrong aspect ratio; 192×325 crop rejected for missing resolution. A plausible 1024×1024 single-view image would be only \`PENDING_VISUAL_IDENTITY_REVIEW\` and not automatically accepted.
- \`CORE011_rejected_imagegen_QA_bundle.zip\`: actual generated binary sheets and diagnostics, **delivered in conversation runtime**. No binaries committed to Git or added to private Releases. A zip of rejected output is **not** a skin library.

## Text code and CI in GitHub

- \`experiments/koma-25d-core/tools/precheck_generated_view11.py\`: automation for geometric/aspect/resolution preflight and must remain conservative.
- \`.github/workflows/koma-25d-core-011.yml\`: synthetic Pillow-generated input fixture tests. The CI images are **NOT** Aka and do not establish generator art quality; the tests verify that multi-panel/low-res input is rejected and any dimensionally valid image is **not automatically accepted**.

## Actual 360° status relative to CORE-010

| yaw reference anchor | 2026-10-30 status |
|---|---|
| 0° | Real original Aka PSD and original INX front exist |
| +45° | 1 provisional, uncalibrated GPT user candidate; NOT source UV registered |
| +90°, +135°, 180°, -135°, -90°, -45° | **NO ACCEPTED ART** |

Thus **6 of 8 nominal anchor views are still wholly missing**. Source count is one verified original front + one *provisional GPT near-front* candidate, not 25% finished 360° animation. New accepted +90° images: **0**. New accepted 180° images: **0**. This round achieved **input QA regression and explicit generator failure detection**, not 360° head asset completion.

## Next hard requirement

The next image generation must be an **actual image-to-image EDIT of the real official Aka original reference**, with an explicit attached source image (not just an image visible in a chat UI, text citation, or prompt). Generate exactly one head profile pointing IMAGE RIGHT on plain background, not a contact sheet. Then separately generate a face-free rear view, both high-resolution. Use independent true 0° Aka source, existing genuine native INX HeadYaw frames, and approved +3/4 as *secondary*. Fix original-visible hair/leaf/ear identity **before** segmentation or 3D reconstruction.

If the current generator integration cannot prove the reference image was ingested and consistently returns infographic collages, **STOP / FLAG BLOCKER**. Repeating unlimited calls or cropping sheets must not count as progress. Do not merge CORE-011 into production.

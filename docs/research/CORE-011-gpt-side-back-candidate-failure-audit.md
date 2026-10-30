# CORE-011 · GPT 90° profile / 180° rear creation and actual acceptance results

**Round date:** 2026-10-30. **STATUS: ALL NEW GENERATED ART REJECTED.**
**Output type produced:** 5 multi-panel 360° character-sheet **ILLUSTRATIONS**, not standalone source-paint or rig/mesh/UV/video files.

## Real inputs and observed generation attempts

Previous user-generated Aka-like reference images (both 1254×1254 RGB, not independently the real original PSD):
- \`金色狐耳少女肖像.png\`: SHA256 \`48647551a17ea5216d9af9703f01f37873c412fe9d9d331bb7210027022193a4\`
- \`三分之四侧颜狐耳少女.png\`: SHA256 \`59ad8cfa30575a59b959339e9f38c5c112b0b9ef966b9fed9948a80abe73745a\`

Five actual new image-generation outputs, **each 1536×1024 RGB**, not correct 90°/180° standalone outputs:

| Run | Local generated image | SHA256 | Artwork decision |
|---|---|---|---|
| 1 | \`a_clean_anime_character_turnaround_sheet_asset_ill.png\` | \`4bf12820aeedf2b0a1621d05d8ebec2dbaa3d30a0306a2f88b923ad2c3d8c0a0\` | REJECT |
| 2 | \`a_detailed_character_turnaround_rotation_reference.png\` | \`a619b0330fb88e10918ba2776f3eee2471fce7fe807e6af689e2b143397c7c7f\` | REJECT |
| 3 | \`wide_clean_infographic_style_character_sheet_m.png\` | \`f8df114dfca5ed470de81aa5116c2387ef84b5436b96c5f28e6fc06add4f4bc0\` | REJECT |
| 4 | \`a_clean_professionally_designed_character_referen.png\` | \`33c4004a987010fdac9d2fda59fc59ac227b11109c83d7a39e8b3d297055db42\` | REJECT |

**Direct image review** of all five real files:
- Rather than one 90° side or one 180° rear on a clean canvas, the generator repeatedly returned eight-view **turnaround-infographic montages**.
- The character drifted: original Aka-like input has simple short gold bob, tall amber ears, small red leaf at top bangs and black choker; generated panels invent **braided rear locks**, **large ribbon/tassels**, costume redesign and bell collar. These are NOT authenticated side/back depictions of source Aka.
- Some 90° panels point the nose to IMAGE LEFT despite asking for nose toward IMAGE RIGHT.
- The labels “UV,” “transparent layer,” “192 frames,” “8s 24fps,” “62.5% finished,” “PR #22,” etc. are **raster text hallucinated inside the generated picture**. No actual UV map, mesh metadata, temporal video, Github PR or auto extraction is created by generating a picture.
- Cropping each 1536px-wide sheet into 8 nominal columns produces only **192×325** screenshots, not plausible high-resolution standalone skin references. Upscaling cannot restore original hair/face/ear details.
- **There is no evidence the image generator actually used the genuine official Aka PSD as an explicit attached image-edit conditioning input.** The previously accepted GPT composites are also not an equal replacement for source original PSD.

## Actual production artifacts created and inspected locally

- \`core011/audit_generated_views11.py\` processes all five actual 1536×1024 generated binaries; records image hashes, text/visual rejection decisions, clips 90°/180° evidence and makes reference contact image.
- \`core011/identity_contact_4runs.jpg\`: visual comparison of real user-provided front / three-quarter GPT portraits vs the actual four generations' extracted side/back panels. **Visual inspection completed.**
- \`core011/identity_qc.json\`: five generated attempts all \`REJECTED_NOT_INGESTIBLE\`. Ten crop evidence images saved, explicitly not accepted artwork.
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

## Verified alternate input chain (separate successful CI; still no image edit)

Following five failures from the in-chat implicit-reference image-generation route, a direct **OpenAI Images Edit** path was implemented, following the official October 2026 docs: https://developers.openai.com/api/reference/resources/images/methods/edit . The selected explicit-edit model is \`gpt-image-2.5-sunburst\`, quality high, one 1024×1024 output, **one attached source image, not a text-only prompt**.

- \`experiments/koma-25d-core/tools/edit_real_aka11.py\`: reads actual image bytes, checks immutable SHA256 of original Aka PSD-derived \`source_A_aka_front.png\`, constructs ONE +90 or ONE 180 single-view editing prompt and \`client.images.edit(model=...,image=infile,...)\`. API response, if ever returned, is **PENDING_DIRECT_IMAGE_VISUAL_REVIEW**, not a real rig or successful 360 skin. API key never committed.
- \`.github/workflows/koma-25d-real-image-edit-011.yml\`: FREE source integrity check on pushes; optional paid edit behind manual workflow_dispatch boolean \`paid_image_edit=true\` and securely configured \`OPENAI_API_KEY\` GitHub Secret.
- [GitHub Actions #40994420605](https://github.com/tims-SP/koma-motion-lab/actions/runs/40994420605) **SUCCESS**: actually downloaded original 1024×1024 Aka front PNG from owner-only earlier draft release, checked SHA256 \`c22f2af3f426d4e79745e28a1244750d1c46b41d82f46570be63b9543aedb4e4\`, successfully constructed 90/180 edit request manifests. No paid API call was made and paid job was SKIPPED.
- Locally, the script was intentionally pointed to an old GPT-generated front composite; it correctly STOPPED with \`CORE011_REF_SHA_REJECTED\` instead of silently treating a new synthetic front image as canonical Aka.

**NEW status distinction:** explicit image-reference provenance **verified**. Model-side conditioning result, accepted side/back art, true layers, original 2D mesh UV binding and 360° video **NOT VERIFIED**. The next real image generation is correctly guarded by deliberate manual API authorization rather than more repeated prompt-only sheet attempts. No paid action was triggered or charged by these tests.



## Additional current-chat image generation trials: two more rejected (CORE-012 probe)

After the user requested a **single +90° Aka side profile in ChatGPT itself**, not an API call, an authoritative official Aka frontal PSD-derived **JPEG preview** was retrieved from the earlier pinned source CI log and actually visually inspected in the conversation. The user-supplied 1254×1254 three-quarter image was also available. Two new `image_gen` calls attempted to generate a **single right-facing +90° image**, the second explicitly referencing the user image. Both instead returned **multi-panel turnaround/part sheets** with fabricated accessories, no actual source INX UV, and no standalone head texture. The source-preview's presence in a prior tool result **did not prove the image editing engine ingested it as an attached image-to-image reference**.

| Current-chat attempt | Actual returned binary | Dimensions | SHA256 | Result |
|---|---|---|---|---|
| 6 | `a_clean_character_reference_sheet_turnaround_ill.png` | 2172×724 | `b259b8e3757e1c41414a6156286cf0a7d4392112ee425968d1f062e70b99882d` | REJECTED: multi-view/extra ornaments |
| 7 | `a_clean_character_reference_sheet_collage_in_a_stu.png` | 1774×887 | `9a318c7bd877ee7cdd01bc7ae9e2cf465e6644cfff73e048a65fe3c97cd85661` | REJECTED: multi-view/extra ornaments |

Diagnostic crop of the alleged side pose has only **310×420** and **221×328** source pixels respectively, no new hidden face/ear/hair painting separate from infographic and no verified source likeness. Crops, screenshot comparison and machine-readable fail audit reside in current conversation output at `/mnt/data/core012/`, **not GitHub**.

**Result:** after these two further trials, still **0 accepted new +90°**, **0 accepted new 180°**, **0 new native side/back UV**, **0 production-quality new video**. No further blind current-chat image-gen retries. The next step requires a **real original PNG attached as an editable image in a fresh, narrow image-edit interaction** with one-view-only user instruction; should this fail again, pursue explicit API image edit when user authorizes it. Uploaded official PNG is stronger than model-visible CI-log preview but still requires output visual QA.


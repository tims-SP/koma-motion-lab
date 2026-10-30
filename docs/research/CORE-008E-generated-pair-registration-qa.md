# CORE-008E · User GPT-generated Aka-style candidate pair, actual image registration test

**Execution state:** local 2D image-space UV prototype produced, video rendered and visually inspected. **True 2.75D rig/skin acceptance: FAIL / NOT TESTED.**

## Exact actual inputs

Two user-provided RGB PNG images, each 1254×1254. These are **GPT-generated composites**, NOT the original Aka PSD or separated INX layers:

1. Front-ish generated portrait: \`金色狐耳少女肖像.png\`, SHA256 \`48647551a17ea5216d9af9703f01f37873c412fe9d9d331bb7210027022193a4\`.
2. Three-quarter candidate: \`三分之四侧颜狐耳少女.png\`, SHA256 \`59ad8cfa30575a59b959339e9f38c5c112b0b9ef966b9fed9948a80abe73745a\`.

Aka's ORIGINAL PSD / full INX baseline was validated in earlier CORE-007/008 runs but was not available in this local runtime; the two GPT raster images are not guaranteed pixel-identical to the official PSD. Their nominal viewpoint difference **is not camera-calibrated** and must not be labeled exact 45°. Both include a white/off-white background; no original per-part alpha or UV.

## Implemented and actually executed

- Foreground alpha estimated by chroma difference from white plus exterior-connected flood fill, with antialiasing.
- 33 manually reviewed source/target facial/hair/ear/neck correspondence landmarks (2D image coordinates).
- Smooth thin-plate-spline displacement field from these pairs; source and target have separate 2D UV sampling maps.
- 76 diagnostic Delaunay triangles between matched landmarks; **these are a 2D image-space mapping mesh only**, not original INX ArtMesh UV or a reconstructed 3D volume.
- 5 experimental alpha-cutout proxies per image: orange hair, ear area, face area, eye area, red leaf; **color/spatial masks, not production-grade non-overlapping PSD layers**.
- 96 frames (24fps, 4s), normalized 0→1→0 transition. Video 1440×760 side by side: landmark registered texture warp vs naive whole-image crossfade baseline.
- Video encoded as H.264 then actual MP4 was re-decoded; frames 0, 24, 48, 71, 95 compared visually and contact sheet exported.

## Measured smoke results

- Each input source 1254×1254 RGB, 33 image landmarks, 76 mapping triangles.
- H264 comparison video: 96 frames, 24fps, 1440×760, ~806KB (depends on exact local encoder).
- 5 final encoded MP4 samples correctly decoded. Consecutive sampled images differ by ~0.085–0.090 of RGB channel sample elements at >22/255 change.
- No claim that numeric pixel change demonstrates good anime art.

## **DIRECT VIDEO VISUAL REVIEW**

Result: **LANDMARK REGISTRATION BETTER THAN NAIVE CROSSFADE but ART FAIL**.

- Naive crossfade produces strongly doubled eyes, mouth, cheek and hair tips at intermediate angles.
- Landmark registered view clearly reduces the overall double-image displacement and retains a more coherent outline at transition midpoint.
- Still **visible detail ghosts and smoothing near far eye, face edge and front bangs**; motion looks like 2D morphing, not a validated spatial head rotation.
- Both are blended whole composite textures. The proxy masks have obvious spatial/color leakage: hair mask omits bright fur and includes some face shading; eye-region mask is a rectangular crop; ear mask contains the top hair, not a precise fox ear alpha.
- Thus original official PSD parts, INX UV and native deformers have **NOT** been transferred into these generated images. This is an image-space registration NEGATIVE CONTROL and does not meet the user's 2.75D production criterion.

## Deliverables created in conversation runtime, not committed as repo binaries

- \`core008_pair/two_method_comparison.mp4\`
- \`core008_pair/decoded_review.jpg\`
- \`core008_pair/assets/front_uv_mesh_diagnostic.png\`
- \`core008_pair/view_correspondence.json\`
- \`core008_pair/parts/*.png\` (ten explicitly PROXY RGBA candidates)
- \`core008_pair/part_masks_manifest.json\`
- \`core008_pair/qa.json\`
- \`core008_candidate_pair_QA_bundle.zip\` containing source and diagnostic output.

Binary files are accessible as sandbox conversation artifacts. **No binary was pushed to GitHub**; Git remains text only. Local experiment not falsely described as a successful GitHub Actions test, and no remote release URL is invented.

## Next actual engineering gate

1. Reconcile this exact generated pair against source PSD and native INX ArtMesh boundaries (source attribution must be explicit).
2. Replace crude color/spatial semantic masks with real per-part registered cutouts; each component must be re-composable without transparency holes.
3. Register new-view per-component UVs to original native INX nodes separately; DO NOT overwrite source front UV.
4. Establish actual shallow Z-surface, occlusion and head-pose correspondence using native INX Head Yaw as angle-limited baseline.
5. Only then re-render actual 2.75D movie; visually audit encoded frames at 0/15/30/45 degrees after calibration.

**Current non-negotiable conclusion: two user-provided pictures are useful for registered view-conditioning but do not yet satisfy original-art, true 3D skin or animation QA.**

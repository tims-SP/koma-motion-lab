# CORE-014 · Actual 0°→180° partwise image-space rig experiment and video QA

**Executed locally in sandbox on 2026-10-30.** 
**Result: VIDEO ENCODE/DECODE PASS; 45°/135° ANIME APPEARANCE FAIL; TRUE INX UV / 2.75D NOT IMPLEMENTED.**

## Original source assets actually consumed

- Official Aka front composite, user-uploaded 1536×1536 RGB. SHA256 \`edb4c6d78874c95cca8e6d0b8398be457b40ddcb7fb93bd5d5087e3b02f1b21d\`. Aka original © seagetch CC BY 4.0.
- GPT Aka-like nominal right-facing 90° side, 1254×1254 RGB, SHA256 \`330a90c6819f6e74bcb5af33f9cca27441f9dedefae97d7371c4f5c6c7d25c81\`. Uncalibrated.
- GPT 180° back candidate (source from CORE-012, ear/crown locally repaired by CORE-013), 1254×1254 RGB, SHA256 \`127430a3e41ae0f8376b62428830c73ecdcd1d03348473c3e6391a8c57e04a1d\`. Uncalibrated.
- Existing CORE-009 INX asset audit: authentic full Aka model has 76 ArtMeshes, 3,427 original vertices, 5,353 triangles, 76 textures. The original mesh UV and all deformation bindings have **not** been replayed/applied to this experiment's GPT art.

## Mature reuse research

- Stretchy Studio (https://github.com/skyiron/stretchystudio2DtoMesh): supports editable semantically layered parts, deforming meshes and a render ordering workflow; relevant tool direction, **not used as this round's runtime**.
- Iki (https://github.com/zeikar/iki): existing WebGL warp meshes, color texture parts, masks and physics; candidate for subsequent rig integration, **not used in current execution**.
- Yoon et al. 2026, *3D Character Reconstruction from Hand-drawn Model Sheets* (https://onlinelibrary.wiley.com/doi/10.1111/cgf.70323): hand-drawn view-dependent linework/blending problems; explains why simple full-image texturing damages anime art fidelity.

## What was actually programmed

- 3 actual images normalized to equal head/ear scale on 540×540 study canvas.
- Per-view **manually defined visible-only IMAGE-SPACE semantic proxies** for face, near/far eyes, two ears, neck and residual hair (NOT independent complete original Aka PSD layers).
- 13 source image control point correspondences plus 7 additional front→side eye/cheek/forehead anchors. Interpolated 2D deformation field using thin-plate spline (SciPy RBFInterpolator), then OpenCV remapping of each visible proxy region.
- Different part visibility rules: far eye progressively suppressed, nearest eye separately blended within its patch; side face visibility reduced toward rear; side/back hair repainted as a depth-ordered occluder, not as a fully opaque whole-image alpha mixture. Inferred face eye underpaint remains a **flat approximate local color**, not artist-authored hidden art.
- Two fixed-control comparisons in one frame: left = image-space multi-part compositor; right = original whole-image crossfade (negative control).
- Wrote actual 97-frame 24-fps 1080×588 H.264 MP4, 4.04 s. **Exact MP4 SHA256 \`216ed56b513ca016e290c67e64e2d96b00dbd5d7413a1c8e0eb8145e548c363f\`.**
- Re-decoded actual finished MP4 frames 0,12,24,36,48,60,72,84,96; inspected a contact image. All decoded samples nonblank and have visible motion. Individual 45° and 135° intermediate predictions were exported from the actual encoded MP4, **not newly generated GPT artwork**.
- Manual proxy mask diagnostics generated. The union of approximate masks covers source foreground, but this DOES NOT mean component identity, mutual exclusivity, underpainting or original UV precision are correct.

## Direct visual QA (actual decoded frames)

| Gate | Result | Visible evidence |
|---|---|---|
| Actual 0°, 90°, 180° input anchor pictures | PASS: correct image pixels displayed as inputs | endpoint frames |
| Different per-part visibility / depth order is active | PASS: distinct from whole crossfade | altered midframes |
| Far eye and side face disappear towards rear | Partial improvement | 112.5°–157.5° |
| 45° anime eye + fringe silhouette | **FAIL** | eye partly doubled and pale face/bang seam |
| 135° back-facing cheek/hair/ear | **FAIL** | off-white/skin-tone patch intrudes and hair edge dislocation |
| True original Aka INX (76 mesh) UV registration | **NOT EXECUTED** | source UVs remain separate |
| Actual shallow Z face/hair/ear geometry | **NOT EXECUTED** | only image-space manually labeled masks |
| 45° or 135° independent painted source art | **MISSING** | both are interpolated predictions |
| 360° character animation | **NOT ATTEMPTED THIS ROUND** | only 0→180 forward diagnostic |

No pixeldelta/art metric is treated as visual-quality pass; changing 30% of a screen vs crossfade proves difference, **not superiority**. At true 45° and 135° the drawn intermediate image fails direct human/agent image review. Some 135° face leakage disappeared; residual pale paint patch did not.

## Missing-content handoff linked to real original INX nodes

- 45° rightward view requires per-layer eye visibility/masks for \`Eye:: Left::...\` and \`Eye:: Right::...\`, with separately painted hidden eye/cheek and \`Face\`, \`Nose\`, \`Lip\`, \`Mouth Inner\`. A single generated 'face' region is not sufficient.
- Hair cover: \`Front Hair:: Center\`, \`Front Hair:: Left1/Right1/Left2/Right2\` and their shadows/light overlays must each have source-to-side part correspondences, not a single 'hair' color region.
- 135° needs rear \`Back Side:: Hair\` and associated Left/Right branches, plus two \`Ear:: Left/Right\` rear-facing fur/root layers and hidden nape textures.
- Anatomical left/right vs image left/right must be resolved before binding. The original UV may have non-[0,1] ranges; never clamp them for convenience.
- Status preserved in \`experiments/koma-25d-core/config/core014-result-and-bridge-gates.json\`.

## Artifact disposition

**Actual downloadable local conversation sandbox package** \`/mnt/data/core014/CORE014_Aka_partwise_occlusion_repro.zip\` contains:
- three exact source raster inputs with provenance,
- complete Python program \`partwise_motion14.py\` and further QC program \`make_review14.py\`,
- final encoded MP4, contact sheet from *decoded* MP4, independent nominal 45°/135° debug frames,
- manual semantic proxy masks, sampled TPS image-space displacement mesh data, reproducibility README,
- QC manifests and exact input/output hashes.

**Binary assets NOT in GitHub repository/Release.** This branch contains source research/code or text QA manifests only. This local run does NOT pretend to be a GitHub Actions video test; user-facing downloadable artifact is via conversation sandbox.

## Next actual step

The right solution now is not more full-image blending variants. Precisely segment original/GPT *hair, eyes, ear and face subparts* with hidden underpainting at 45° and 135°, supply real independent author-quality view art, register each new view's UV to source \`uuid\` mesh and deformers, and THEN attempt an actual shallow 3D head/ear/hair with pose-dependent art. Keep Draft; production repo \`tims-SP/koma-motion\` unchanged.

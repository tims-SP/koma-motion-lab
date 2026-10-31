# MVP-001 — Art-Directed Multi-View 2.75D Anime (2026-10-31)

Status: M0 INFRASTRUCTURE SMOKE PASSED (2026-10-31); M1-M4 CHARACTER QUALITY NOT IMPLEMENTED / NOT VERIFIED

> **2026-10-31 资产/语言修订（覆盖早期描述）**：M1 **从现有资产入手**，首选 `myssal/Reverse-1999-CN-Asset` 的 Spine + Live2D 同角色资源；以 Spine 4.2 TS runtime、Cubism Web TS 官方样例及 SIGGRAPH 2010 多视角 SVG 为对照。仅在核实原始角色缺少真正侧/背等关键视角时才进行定向补画/生成，不再从零创作人物作为先决条件。所有新增/维护的自有源码、Node 脚本、渲染器与测试统一 **TypeScript**；M0 旧 JS 迁移为 M1-00，迁移前保留回归。参见 [M1 修订执行计划](./MVP-001-M1-plan.md) 与 [现有资产调查](./MVP-001-assets-research.md)。本段优先于本文较早的旧任务描述。\n\n
M0 verified: [Actions #41188109729](https://github.com/tims-SP/koma-motion-lab/actions/runs/41188109729) SUCCESS, Chromium WebGL 2.0, 25 original procedural parts, 24 frame-accurate PNG screenshots at 640x360, one MP4 (15,700 bytes), 0/360 transform seam check, and independent non-background pixel checks. Preview assets are retained in [DRAFT Release](https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-0ce02cee0dc27dfc74db) (owner access). This proves WebGL export pipeline only; **DOES NOT** prove multi-view interpolation, 360° anime fidelity, IK, normals, SDF, or 1080p video quality. Earlier two FAIL runs identified edge-on blank output and invalid center-pixel QA; they were repaired in the latest run.

## 0. Decision

The previous **lightweight 3D surface + single continuous UV skin** approach is abandoned as an architecture. The previous Rive/Spine conversion and Godot experimental path are **not dependencies** for this MVP. Preserve their historical artifacts; do not delete prior experiment evidence or rewrite git history.

**New architecture**: keyed 2D multi-view art + per-part ArtMesh/deformer + 3D anchors + view-dependent correction (VDD) + hierarchical 3D skeleton/IK + illustrative shading + per-shot form corrections. Cubism/Live2D and Inochi2D are *conceptual references*, not runtime dependencies. Do not claim Cubism project-file interoperability.

**Ultimate test**: one consistent character asset must generate (A) full-body 360-degree loop, (B) an articulated full-body action shot, (C) a high-fidelity anime-style face/effect shot. This is a feasibility experiment, not a reusable universal 360 engine. The finished visual is the criterion, not geometric realism.

## 1. Deliverable contract

- 1 existing character sourced from a verifiable Spine/Live2D/layered asset (original replacement only if evidence proves required and approved); identifiable costume / hairstyle / silhouette across all shots. No unlicensed commercial-game artwork.
- 1 versioned editable character manifest and actual layered transparent source art; output from the *same underlying character package*, not three independent flat videos.
- A: 8 s / 192 frames / 24 fps / full-body actor rotates yaw 0..360 with fixed camera; loop seam 0/360; minimum 8 review directions at 45-degree increments, and all intermediate frames. No plane or whole-character-image card flip. Do not swap entire character sprites to fake this.
- B: 6 s / 144 frames / 24 fps / full-body step, upper-body turn, arm reach and brief target contact, with both hand target and grounded feet. Root, head, upper/lower limbs must independently articulate. Hair/cloth secondary response.
- C: 4 s / 96 frames / 24 fps / closeup blink + subtle smile + head turn, painted face shadow under changing light, restrained rim light, foreground/background particles. No blurred face, doubled eyes or uncanny line quality.
- Browser interactive preview: yaw slider 0..360, pitch -15..15 (pitch is diagnostic, not an MVP-quality guarantee), pose timeline scrub, visibility/depth/mesh debug overlays, lighting toggle, deterministic frame seek.
- 1920x1080 H.264 MP4 at 24 fps for all 3 shots; PNG contact sheets at A: every 45 degrees plus ±15 around problematic transitions; B/C: key poses; render metadata JSON and defect report.
- Binary images/videos/source-art archives go to **GitHub DRAFT Release** (or private user-provided storage); only source, manifests with paths/hashes, schemas, reports and CI workflows stay in Git history. Do not publish licensed art or binary assets to public Releases.

## 2. Scope boundary (keep MVP small)

### In scope
1 character, 1 costume, 1 simple environment/backdrop, 3 scenes, enough key view coverage to avoid visible gaps, 1 arm IK reach, foot-ground constraint, limited physics, face SDF and normal-driven/rim-light comparison.

### Out of scope
General-purpose artist UI; generic arbitrary-character import; procedural full-3D body reconstruction; universal auto-360 conversion from one image; production cloth simulation; PBR materials; speech/lip sync; walk/run library; multi-character interactions; full ARAP implementation before a baseline deform method is validated.

## 3. Asset contract

Start with a **verified existing high-quality anime character asset**, using its original rig/textures and existing angle coverage as the locked art reference; document asset provenance and privately store licensed copies. First audit available real keyviews, then supplement only the missing yaw 0, 90, 180, 270 and draft 45/135/225/315 as intermediate images, and **promote to edited keyviews** if interpolation cannot preserve silhouette and semantics. Do not assume that four views suffice for quality.

Minimum consistent semantic parts: face, eyes.l, eyes.r, brow.l, brow.r, mouth, front-hair, side-hair.l/r, back-hair, neck, torso, pelvis, upper/lower arms.l/r, hands.l/r, upper/lower legs.l/r, shoes.l/r; optional skirt/accessory chunks (approx. 25+). **A completely flat character sprite does not qualify**.

For each part, store: stable id, parent bone, 3D anchor, per-keyview visible/occluded state, RGBA art, local mesh positions/UVs, key control points, consistent contour correspondence, art correction offsets, layer/depth hints, optional normal/SDF. Document explicit split/merge cases where topology changes; not all views need identical visible part counts, but every transition must have a rule.

Source art can be produced by AI but must pass separate identity/geometry/occlusion QA. See-through is an optional segmentation/inpaint sidecar, MV-Adapter an optional candidate multi-view generator. Neither automatically guarantees topology correspondence or quality.

## 4. Runtime and evaluation (new independent implementation)

- Typescript, Three.js/WebGL2 for camera, transforms, 3D bone hierarchy, layered textured triangle meshes, masking/compositing and shaders; Vite for preview.
- Custom part-level 2.5D evaluator: (1) transform pose/IK and each part's local camera direction; (2) select/interpolate relevant key views with angle wrapping; (3) calculate anchor + VDD / corrective transforms; (4) apply local warp/morph; (5) decide visibility and depth/occlusion; (6) render the corresponding mapped RGBA textures and outline/shadow layers.
- Never interpolate RGB textures before obtaining compatible correspondence: do shape registration/warping first; if correspondence fails, keyview transition, controlled replacement, manual split or extra view. No whole-body alpha crossfade or blurry double edges.
- Use a simple well-defined landmark/triangle warp as the first evaluator. Integrate ARAP only for parts where a reference-vs-baseline comparison demonstrates a real benefit. Prefer precomputing expensive solvers.
- 3D rig with head/neck/spine/pelvis/limbs and local view-dependent forms; target arm with CCD/FABRIK, foot locking/root correction. Camera-space appearance must be evaluated **per bone/part**, not one global head/body yaw.
- Original painted colors/shadows remain the reference; face SDF / view-keyed shadow masks for stylized face-light response; optional per-part normal map in local deformation coordinates for hair/body light; rim lighting and particles in compositing. Do not turn the character into generic 3D cel shading.
- Fixed-timestep deterministic evaluate(frameIndex) on a pinned dependency version, Playwright/Chromium WebGL rendering; FFmpeg for encoding. Initial CI render at 960x540 is allowed for debugging, but acceptance must use 1920x1080. Detect and fail blank/WebGL-null frames.

## 5. Phases (each stage must produce a commit and verification evidence)

| Phase | Specific execution | Required evidence / gate |
|---|---|---|
| M0 — base & license | M0 rendering infrastructure PASS; freeze baseline. For M1 use TS-only new code, migrate M0 JS/smoke to TS with parity, inventory existing character source and record provenance and rights. | CI renders real layered geometries in Chromium; 3 reproducible screenshots; codec probe; input/reference links and SHA. No claims of anime fidelity. |
| M1 — 360 body baseline | Start with source Spines/Live2D rig and any existing genuine views; inspect original native reference; supplement missing cardinal views, build semantic part decomposition/correspondence and anchors, then add keyviews as necessary; 8-direction review. | 8s 360 full body MP4 + 24 angle samples; 0/360 wrap check, visibility/occlusion logs, human visual review. |
| M2 — full-body articulation | Introduce bone hierarchy and part-local view transforms, arm IK and feet lock, action timeline; add action-specific art corrections. | 6s scene + pose contact sheet, 3D target/foot constraints and deformation diagnostics, human pose quality gate. |
| M3 — anime facial FX | Animated face parts, mouth/eye/warp, face shadow mask/SDF, optional hair normal, lighting, rim and depth particles. | 4s scene + unlit vs lit comparison PNGs, visual QA for line/face sharpness and lighting. |
| M4 — closed-loop QA | Fixed resolution export, deterministic frame sampling, generate 3 videos and contact sheets, independent QA, classify failures, make corrections. | Draft release containing A/B/C + full QA JSON; owner review. All three scenes must pass. |

Phases M1/M2/M3 may iterate on art correction in parallel *after* M0; each must cite the same character package.

## 6. Hard-fail acceptance gates

A. 360: visible actual part rotation/deformation at every 15-degree sample, **not** just complete sprite replacement; no sudden extra limb, eye duplication, hair clipping through face, wrongly flipped costume details, excessive blur, or silhouette discontinuity. A numeric seam test compares frame 0 with equivalent 360 pose and reports per-part transforms / image difference. If character has asymmetric motifs, auto mirroring is forbidden unless manually approved.

B. Motion: arm joint reaches target (initial engineering tolerance <= 12 screen pixels at 1080p in designated contact frame), feet remain on contact surface when flagged stationary (<= 8 px drift); no dislocated hand/limb, rubber bending, cropped body, fake motion from whole-card translation alone. Numeric thresholds are *initial test criteria*, not guarantee of visual acceptability.

C. Face/FX: no visible doubled eyes/eyelashes, face color or line degradation, broken mouth shapes, inverted light mask, or unmotivated specular effect. Compare to the authored front/three-quarter keyview at same pose and neutral light. No "high fidelity" PASS without frame-by-frame independent visual sampling.

All: 1920x1080, 24 fps, 432 decoded frames total, no black/blank frame, consistent identity, deterministic frame index evaluation, no source/video binary in Git, documented costs and manual corrections. Automated tests never override a failed human visual review.

## 7. Failure branches (do not endlessly polish the wrong approach)

- If 4-view interpolation fails at 45°: add a native 45° key view or manually split the affected component; test targeted part-level repair, not a full-character redraw.
- If topology/texture interpolation breaks: preserve keyview images and use masked part swaps with overlap and occlusion handles; do not blend two visible faces across the whole body.
- If bone movement ruins appearance: add one corrective pose/form at the problematic joint and action direction. Ensure bone pose and view correction are evaluated separately.
- If dynamic normals degrade the painted face: turn dynamic normals off for face and use art-authored face shadow masks/SDF only.
- If A works but B fails due to incompatible viewpoints: restrict motion to supported local views only *for diagnosis*, and mark whole MVP FAIL until required motion succeeds; never claim full-body success from a head-only demonstration.
- If three real scenes require the equivalent of individually painting most frames: technically feasible but economically **NO-GO**, log manual hours / per-frame fixes, stop and redesign.

## 8. Implementation starting files (not yet created)

- experiments/mvp001/package.json / src/runtime/{viewSpace,partMesh,visibility,rig,corrective,shading,renderer}.ts
- experiments/mvp001/src/scenes/{turn360,bodyAction,faceFX}.ts
- experiments/mvp001/assets/schema/character.schema.json
- experiments/mvp001/test/{seam,parts,rig,render}.test.ts
- .github/workflows/mvp001-render.yml
- docs/experiments/MVP-001-status.md and Draft Release with MP4, contact sheets and diagnostic JSON

No reuse of old scripts without re-evaluating their suitability. No previous experimental run counts as M0 or higher.

## 9. Source references

- Rivers, Igarashi & Durand, 2.5D Cartoon Models (2010): https://alecrivers.com/2.5dcartoonmodels/
- Kitamura et al., 2.5D Modeling from Illustrations of Different Views: https://kanamori.cs.tsukuba.ac.jp/publications/adada2015/kitamura_adada_2015_vol.18_no4.2.pdf
- Fukusato & Maejima, VDD / View-Dependent Formulation (2021 preprint / 2022 publication): https://arxiv.org/abs/2103.15472
- Dorta et al., Puppeteering 2.5D Models: https://www.brunodorta.com.br/publication/puppeteering-cartoon/
- Live2D Cubism blend shapes: https://docs.live2d.com/en/cubism-editor-manual/blend-shape/
- Third-party 2010 replication: https://github.com/without-paper/2.5d_cartoon_model (study; license to be checked before vendoring code)
- Anime decomposition: https://github.com/shitagaki-lab/see-through
- Multi-view generation: https://github.com/huanngzh/MV-Adapter
- Three.js IK: https://threejs.org/docs/pages/CCDIKSolver.html

## 10. Immediate next action

M0 infrastructure has passed: https://github.com/tims-SP/koma-motion-lab/actions/runs/41188109729 . Next implement M1-00/01 as specified in M1 plan: migrate maintained M0 JS and smoke scripts to TypeScript with parity, inventory existing assets in TS, verify source 4.2 Spine/Cubism reference renderers, then establish real view coverage before supplementing missing views. Do not claim high-quality 360° prior to visual verification.

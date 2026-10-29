# CORE-008 · GPT-assisted missing-view skins for an original 2D rig

**Status: PLAN ONLY — no generated side artwork has been accepted.**
**Scope:** personal / non-commercial research; Aka head, yaw toward IMAGE RIGHT, 0°–45°.
**Working repo:** tims-SP/koma-motion-lab; production repo tims-SP/koma-motion unchanged.
**Binary policy:** source PSD/INX downloaded from pinned upstream, generated PNG/PSD/GLB/MP4 and visual comparisons saved in draft GitHub Releases; Git tracks only text code/config, hashes, QA, prompt plans.

## Research and reuse decisions

- Inochi2D official 2D source truth: Aka tutorials PSD and tutorial-aka02.inx. Tutorial02 is a layout exercise, **not established to be a complete HeadYaw native deformation rig**.
- Inochi2D/example-models also lists \`Aka.inx\`, but its repository stores Git LFS pointers; obtain actual full model through a supported source, verify model hashes/parameters before trusting it.
- Attribution: Aka design and rigging © seagetch, CC BY 4.0. Record source and generated derivative status in every release.
- Native Inochi2D SDK remains reference renderer. Inox2D is a secondary reader/rendering candidate: its README warns animation and mesh groups are still in progress.
- ModelSheetTo3D (Eurographics 2026): reference for model-sheet correspondences, separately modeled artistic details and multi-view material alignment; its Blender/CUDA GPU pipeline is not the first implementation target.
- See-through (SIGGRAPH 2026) and SAM2 are optional for generated-view segmentation; original PSD layers must be used as semantic references before adding new segmentation.
- From CORE-004–007: reject whole-image crossfade/optical flow, slab extrusion, single whole-body visual hull and naively reassembled PSD layer order as production solutions.

## Coordinate convention — immutable across pipeline

- FRONT = 0°: the *exact original front PSD* reference.
- +YAW = the subject's nose turns toward **IMAGE RIGHT**, with fixed orthographic camera. Do not describe angles as camera motion in prompts.
- 30° and 45° are nominal design targets; image generation cannot guarantee physically exact degrees. Preserve the tagged target angle, register landmarks/contours, and reject unpersuasive poses.
- Use SAME scale/pivot/neutral expression/lighting and complete fox ears + back hair in all samples; no cropping, no arbitrary mirroring of asymmetric accessories/hair.
- Counterclockwise/mirrored (-yaw) is a separate follow-on track, not automatically obtained by horizontal flipping.

## Deliverable A — source and rig truth

- Fetch pinned \`tutorial-aka.psd\` and \`tutorial-aka02.inx\` and, where possible, actual complete \`Aka.inx\`.
- Parse and verify layer order/opacity/clipping, original RGBA, actual texture-atlas ArtMesh UV, triangles, node hierarchy and **existing** deformation parameters (do not infer a parameter exists from a field name).
- Generate \`source_front.png\`, per-part source patch references, a role/palette/feature-reference sheet and a plain-text machine-readable manifest.
- Obtain reference renders from the native Inochi renderer if possible. Keep separate tags: ORIGINAL_PSD_REFERENCE, NATIVE_INX_RENDER, KOMA_REPLAY.
- **Gate A:** all input files fingerprinted, attribution verified, PSD composite and reassembled layers visually checked; native rig parameter inventory completed or explicitly marked absent.

## Deliverable B — GPT missing-view master illustrations

- Always provide *actual Aka front illustration* as image reference, with optionally a feature crop montage: front hair / side hair / ears / eyes / mouth and the rest view.
- Primary candidate set: **30° × 4 images; 45° × 4 images**. Source front (0°) is NEVER regenerated; 15° is initially held out for interpolation QA.
- Generate each 30° candidate from source front alone (avoid cross-candidate drift). Generate each 45° candidate from source front plus independently selected 30° as secondary *structure* reference if the system accepts two references. If not, source front is authoritative.
- Each output = full head + ears + neck tip, with neutral image-space coordinates, orthographic anime linework, solid neutral background (or true alpha only if supported); **NO** rig, UV, semantic segmentation or alpha-mask claim.
- Save outputs as \`generated/aka/yaw_plus_030/cand_001..004.png\`, \`yaw_plus_045/cand_001..004.png\` in a Draft Release, with a text manifest recording prompt revision, engine/source hashes, exact requested target yaw, references, decisions and rejection reasons.
- **Gate B:** subjective identity and pose check (human/agent image audit) is mandatory. Compare eye color, hair mass and asymmetry, highlights, fox ear placements, face shape, accessories and palette to the same original Aka. Filter candidates that depict changed expression, impossible occlusion or unstated new items. The surviving 30° and 45° images remain GENERATED_UNREGISTERED, not original art.

## Deliverable C — layer segmentation and counterpart matching

- Segment selected views into at least face base, front-hair groups, near/far side hair, rear exposed hair, near/far eyes, brows, nose/mouth, fox ears and visible neck.
- Establish a many-to-many cross-view \`part_id\` mapping to the original PSD and corresponding INX nodes. New hidden-only patches require a distinct generated-part ID and parent association, not impersonation of an original node.
- Prefer original PSD layer contours/masks as segmentation priors. Evaluate SAM2 or See-through for view-dependent alpha separation and occluded-area inpainting; neither is assumed perfect.
- Store alpha masks, cutout patches and a structured \`part_correspondence.json\`. Register explicit face landmarks (nose, pupils, chin and ears) and hair silhouette/roots.
- **Gate C:** all cutout parts recompose their selected full view without significant holes/stray double layers, and mapping coverage for face/eyes/ears/hair has no dangling/unmapped key nodes. If a segmentation is wrong, correct only that part before retry.

## Deliverable D — 2.75D geometry and view-dependent artwork

- Preserve **original source front UVs**, original original art texture and source mesh/weights on the original front-facing ArtMeshes. Do not overwrite them with generated view artwork.
- Extend front vertices into shallow world surfaces in rest pose by preserving frontal orthographic projection. Build independent shallow surfaces for face; separate curved patches/strips for front hair, sides, back hair, ears. Keep eye/nose/mouth decals registered with face anchors. Do NOT force all art onto one visual-hull shell.
- Each newly generated 30/45 view has its **own registered patch UVs** and visibility/occlusion map. Source front \`UV_0\` is NOT assumed valid for every new view.
- Optimize curvature, feature registration and blending in that order; treat lines/highlights/painted shading as view-dependent decals or patches if needed. Blend only matching semantic parts, not whole reference images or all pixels.
- Fill unknown side/rear only from ACCEPTED_GENERATED_AKA art; any missing part is flagged \`MISSING_SIDE_ART\`, never silently painted as a production-ready flat proxy.
- **Gate D:** 0° original front remains unchanged relative to the same native/reference rendering contract; 30° and 45° reproduce their accepted source drawing under the registered texture setup, with no visible front-hair-to-face/bang-edge mismatch.

## Deliverable E — actual motion videos and independent encoded-video audit

- Deterministic fixed-camera yaw cycle 0°→15°→30°→45°→30°→15°→0°, 24 fps, 96 frames = 4 s, 720p work-in-progress then 1080p review.
- Render comparison modes: source 2D/native baseline, CORE-007 flat/curved controls, generated whole-picture interpolation negative control, CORE-008 proposed per-part registered 2.75D.
- Save MP4, reference images, sampled video frames and contact sheets to DRAFT Release; decode final MP4 with FFmpeg and audit **actual decoded frames**, not only pre-encode PNG.
- Required keyframes: 0/15/30/45 plus interstitial 7.5/22.5/37.5 and reverse. Check face identity, nose/gaze direction, hair-over-face order, ear asymmetry, alpha holes, temporal popping and image-to-original deviations.

## Gates and fail-closed conditions

| Gate | Acceptance target | Failure response |
|---|---|---|
| 0° source | No material change when adding extra surfaces; native original is separate parity task | Regression, never count copied 0° source anchor as successful novel-view mapping |
| 30°/45° silhouette | Aim for >=0.90 IoU against accepted generated anchor after registration; includes real alpha segmentation and camera scale agreement | Refit geometry/landmarks, not just enlarge depth |
| Feature landmarks | Aim <=2% of head bounding-box width per critical anchored point at its own key angle | Correct registration/part maps, reject invalid image |
| Layer/occlusion | No visible wrong-way overlaps (back hair over face, double eyes, false ear) | Block visual acceptance |
| Temporal | No unexplained part swaps/pops; test every frame, not just sparse pixel difference | Freeze release candidate for diagnosis |
| Source provenance | Every original/AI/derived patch has role, hash, source, license and QA status | Block acceptance |
| Anime look | Explicit direct image review is PASS; mere structural CI success is insufficient | Keep PR DRAFT; do not merge |

Quantitative targets are proposed engineering gates, not verified achievable numbers; calibrate with native reference after source assets are actually loaded.

## Cost/iteration control

1. 0° original and 30°/45° anchors only; do not spend on 15° until interpolation fails.
2. Start with four candidates per anchor (8 total), accept one per angle; don't generate 8 for every single component.
3. Generate component inpainting *only for diagnosed failures* (typically far eye, front hair exposed zone, ear or cheek).
4. On severe identity drift: do not solve by more rigid geometry or optical flow. Rerun view-specific image reference with clearer Aka feature crop.
5. On medium-angle ghosting with consistent endpoint images: solve registration/surfaces and view-conditioned occlusion before generating additional angles.
6. On lack of accepted 45° views: cap usable yaw at previous accepted angle; do not pretend 45° works.

## Ownership and commands

- Agent: source inventory, prompt packaging, candidate catalog, segmentation/QC, registration/mesh, render, frame-level and direct visual audit, release/PR tracking.
- GPT image generation: candidate views/hidden patches only — not structured UV, native rig, semantic part mapping or reproducible engine shader source.
- Human intervention: optional final preference/ambiguous character design judgement, not required for every intermediary step.
- This PLAN does not itself create candidate images, side-painting files, rigged meshes or videos.

## References

- Official Aka tutorials: https://github.com/Inochi2D/inochi2d-docs/tree/main/docs/source/creator/first-model
- Aka CC BY attribution and full-model LFS pointer: https://github.com/Inochi2D/example-models
- Inox2D status and limitations: https://github.com/Inochi2D/inox2d
- Yoon et al. 2026 ModelSheetTo3D: https://github.com/hjyoon02/ModelSheetTo3D
- Shitagaki et al. 2026 See-through: https://github.com/shitagaki-lab/see-through
- SAM2 segmentation: https://github.com/facebookresearch/sam2

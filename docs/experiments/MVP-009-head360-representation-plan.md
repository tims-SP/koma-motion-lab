# MVP-009 — 头部 360° 表示重建与可信验收

Status: **PLAN / NOT IMPLEMENTED / NOT ACCEPTED**
Date: 2026-11-01
Owner repo: `tims-SP/koma-motion` (暂不写入；本仓库仅用于实验与验收)
Lab repo: `tims-SP/koma-motion-lab`
Existing baseline: [MVP-008 P0 geometry audit](../archive/pre-mvp009-2026-11-01/experiments/MVP-008-P0-root-cause-geometry-audit.md), render [Actions #41206130892](https://github.com/tims-SP/koma-motion-lab/actions/runs/41206130892).

## 0. Decision / non-negotiable contract

**Owner decision 2026-11-01: implement B first. This supersedes the former A-first execution order but preserves earlier planning records. Detailed contract: [MVP-009-Plan-B](./MVP-009-plan-b-multiview-depth.md).**

Objective: one *same* anime character head remains visually coherent through real camera-relative yaw 0..360, including convincing nose/profile/ears/chin, hair/skin depth order, and smooth interpolation. Full-body pose, art polish, production movie are OUT of scope until head is accepted.

We will test two honest representations, not claim that any zero-thickness 2D representation is intrinsically invalid:

- **A / geometry-first:** anatomically meaningful coarse 3D face, cranium, nose, ear, front/side/back-hair surfaces plus optional view-dependent shape corrections. Geometry owns depth/visibility; 2D painted RGBA textures and material-space UV own appearance, not a global toon renderer.
- **B / paper-inspired layered 2.5D:** independently authored 0/90/180/270 face/profile/ear/hair parts; coherent semantic correspondences, 3D anchors and per-part depth layers, authored appear/disappear transitions, view-dependent local morphs. May use depth-varying patches instead of full volume but MUST produce the right visible side silhouettes/depth ordering. Refer Rivers-Igarashi-Durand and Kitamura-Kanamori-Tsuruno.
- B is now the OWNER-SELECTED PRIMARY experiment. T03-B runs first and independently gates T04; A is DEFERRED and is only reopened when a documented B no-go condition occurs. Preserve the same independent character reference and camera calibration if comparison with A becomes necessary. Never treat B's planar parts as inherently invalid; reject only a demonstrably incorrect silhouette, anchor projection or occlusion result.

Important technical distinction: fixed camera + physically rotated model is equivalent to camera orbit around stationary model under matched lighting/local-view conditions. The current problem was flat camera-facing ArtMeshes, not using a fixed camera per se. Both camera orbit and model rotation are explicit regression modes, compared with consistent view direction and locked world/character lights.

No claim of lossless painting transfer to a single UV, nor that an AI-generated side view preserves identity automatically. UV is a mapping to geometry; independently authored texture regions and view-conditioned corrections are allowed where one painting cannot cover all sides.

## 1. Upstream evidence and exact applicable claims

1. [Rivers, Igarashi, Durand 2010, 2.5D Cartoon Models](https://alecrivers.com/2.5dcartoonmodels/): multiple vector drawings mapped into orientation space; 3D positions for constituent strokes/anchors; NOT just four whole-body sprite swaps. Reimplementation reference: [without-paper/2.5d_cartoon_model](https://github.com/without-paper/2.5d_cartoon_model) reports orientation space, shape interpolation, grouping, 3D anchors (some output defects remain; not a production engine).
2. [Kitamura, Kanamori, Tsuruno 2014, 2.5D Modeling from Illustrations of Different Views](https://www.jstage.jst.go.jp/article/adada/18/4/18_74/_article/-char/en): depth-arranged deformable billboards, corresponding regions, manually assigned contour feature points, and authored appearance/disappearance completion. This justifies comparing B, NOT reusing our current flat-card version.
3. [Fukusato, Maejima 2022, View-Dependent Deformation](https://pubmed.ncbi.nlm.nih.gov/35544514/): artistic violations of strict 3D projection corrected from keyed 2D drawings; VDD is appearance correction, not an automatic generator of missing face anatomy.
4. [Three.js Material depth rules](https://threejs.org/docs/pages/Material.html): disabling depthTest also disables depth writes; global face/front-hair overlay cannot prove physical occlusion.

Read source/implementation before coding; do not copy upstream code without license check. Cite pinned upstream SHAs in audit outputs.

## 2. Prototype asset / coordinate system

One **original, deliberately simplified** head. No third-party copyrighted source needed for engineering tests; only upgrade to actual art after structural pass.

Coordinates: right-handed, head-local +Y up, +Z forward, `yaw=0` front; explicit per-part local frame and camera `viewDirLocal`. Character pose fixed, mouth neutral, eyes open. Distinct L/R ears & hair asymmetry; keep an obvious asymmetrical marker to expose accidental mirroring.

Minimum landmarks: skull.front/skull.back, brow.left/right, nose.bridge/nose.tip/nose.base, cheek.left/right, jaw.left/right, chin, mouth.center, ear.left/right, hairline.left/right/center, frontHair/sideHair/backHair attachment curves. Semantic identifiers stable across keys. No requirement all viewpoints show all parts; record `visible`, `occluded`, `disappears`, `split`, `merge` states.

Input bundle:
- `reference/manifest.json` metadata; source hashes and licenses.
- `reference/angles.json` and independent left/right orthographic visual references (front 0, right 90, back 180, left 270; optional diagonals 45/135/225/315). Don't generate "independent" references from the exact same renderer being evaluated.
- `reference/landmarks.json`, depth ordering graph and hair/face/ear occlusion semantics per view.
- Geometry candidate A mesh as runtime vertices/indices + consistent UV; B per-part RGBA/contour/depth topology.
- Keep image/video binaries OUT of Git history. Store in Actions artifacts or owner Draft Releases and only hashes/paths/metadata in Git.

## 3. Work packages — execute strictly in order

| ID | Exact work | Expected output | PASS gate / stop condition |
|---|---|---|---|
| **T00** Baseline freeze | Record current exact source SHA, original 192-frame MP4, 0/45/90/135/180/225/270/315 face crops, known pixel defects and no-volume geometry. Do NOT patch old MVP-008 in place. | `docs/experiments/MVP-009-baseline.json` | Current `FAIL_VISUAL` replicated in evidence. |
| **T01** QA truth repair | Build shared alpha/discard logic for beauty/part ID/depth coverage (identical materials/function incl. six-row matte or replace it), and negative controls: flip depth order, remove side face, replace face with flat sprite. Add side yaw 75/90/105/255/270/285 to test. No 10/10 PASS from wrong shader or 0 overlap. | `src/head009/qa/pass-parity.ts`, `scripts/head009-qa.ts`; images + JSON | Actual silhouette/coverage mismatch <=0.5% of relevant opaque pixels with <=1px edge tolerance; artificial faults MUST FAIL. Any missing sample => BLOCKED. |
| **T02** Independent head reference | Create one stylized yet unambiguous model/illustration key set with asymmetric ears, visible nasal profile, hairline shape, layer order. Distinguish artwork source vs renderer-produced diagnostics. | `reference/head009/*` manifest + semantic points, private art binaries in artifact | Review confirms actual 90° and 270° profile and 180° cranium, not recolored frontal face. |
| **T03-A** Volumetric head MVP (**DEFERRED; fallback only**) | Implement low-poly cranium+cheek/jaw+NOSE TIP+2 ears+front/side/back hair surface, face UV, normals and Z data; remove facial `depthTest:false` for geometry. Real camera orbit, no animation, no crossfade. | `src/head009/variants/volume.ts`, `scripts/render-head009.ts`, 17+ angle passes | True camera-space depth field; anatomical front/side/back silhouette; nose/ears/hair ordering follow relative view; beauty/ID/depth parity PASS. |
| **T03-B** Layered 2.5D head MVP (**PRIMARY; execute first**) | Using SAME reference head, implement explicit corresponding 0/90/180/270 facial and hair pieces, separate semantic left/right ear, depth placement and view-dependent appear/disappear. No old `fixed renderOrder` face overlays. | `src/head009/variants/layered.ts`, same renderer and QA | Same visual gates as A, without requiring per-vertex Z span on every billboard; per-part depth order and silhouette must be convincing. |
| **T04** B-specific head decision | Review B at 0/45/75/90/105/135/180/225/255/270/285/315/360. Independently inspect 86–94 and 266–274 transition strips and hidden/visible layer IDs. Estimate extra key art and correction cost. | `out/head009/B-review.png`, `B-metrics.json`, `docs/experiments/MVP-009-decision.md` | If B PASS_VISUAL continue T05. If B FAIL because meaningful view cannot be resolved without excessive manual drawings, record no-go and reopen T03-A/hybrid; no unrequested A-first implementation. |
| **T05** Artwork and VDD | Map genuine key-view 2D art to winning geometry/layers. Test front, both exact profiles, rear reconstruction FIRST, then 45° transitions. Apply VDD only after geometry/depth pass; first compare no-VDD to VDD. | UV seam/texture checks, before/after screen images, real 360 short MP4 | Identity and silhouette hold across 13+ views, no texture stretch/ghost edge, no unregistered hair/face seam; independent visual acceptance. |
| **T06** Head+neck movement | Integrate independent head local yaw, pitch diagnostic ±15°, blink, hair shift, head/body relative motion; ensure masks remain coherent through motion. | short dynamic head clip, pose/depth/part-ID passes | Motion+camera concurrency and face/hair ordering PASS. |
| **T07** Full-body integration | Only after T05/T06 pass: torso/limbs, 3D IK and foreshortening, stable foot contacts, final 8s/192 frames. | video+trace+artifacts; new full-body matrix | Real visual PASS; no promotion from head-only PASS to full-body PASS. |

### Named files and scripts

- `experiments/mvp002/src/head009/{types.ts,reference.ts,renderer.ts,view-state.ts}`
- `experiments/mvp002/src/head009/variants/{volume.ts,layered.ts}`
- `experiments/mvp002/src/head009/qa/{coverage-parity.ts,depth-order.ts,landmarks.ts,temporal.ts}`
- `experiments/mvp002/scripts/{render-head009.ts,audit-head009.ts}`
- `.github/workflows/mvp009-head360.yml`
- `docs/experiments/{MVP-009-baseline.json,MVP-009-qa.json,MVP-009-decision.md,MVP-009-visual-review.md}`

Create only the files actually needed by the current gate. Do not prematurely build a generic production engine.

## 4. Hard acceptance — *not* the old 11/11

**S00 Source separation:** target reference images/landmarks are not generated by the tested renderer, provenance and SHA pinned. Otherwise UNTESTED.

**S01 Genuine profile:** for right AND left 90° the nasal bridge/tip, chin, mouth and ear are visibly in coherent profile; independent left/right hair/ear asymmetry preserved. Machine checks are landmark presence/order, side-oriented projected positions and mask connected components; final visual PASS required.

**S02 Depth layering:** hair occludes the correct facial region, face hides the correct rear volume, ear appears at side/3-quarter and hides behind hair as specified. Measured at [0,45,75,90,105,135,180,225,255,270,285,315,360]. No 0-sample PASS. Use known intentional depth conflicts and negative controls.

**S03 Exact pass parity:** Beauty, ID, depth and alpha obey the SAME geometry and discard/clip. Raster comparisons exclude intentionally shaded RGB differences. Coverage mismatch budget <=0.5% interior pixels, <=1px silhouette tolerance; report counts & mismatched images. A missing ID pixel where visible is a test failure.

**S04 Real camera relation:** camera orbit and model rotation verified at same relative yaw with controlled light/camera transforms and unchanged pose; report actual matrices, view-local angle and difference, rather than checking only `yaw` state. Don't claim pixel equality if fixed world illumination differs.

**S05 Seam and continuity:** 0°/360° same-pose geometry, UV and pixel mask equality; near-90/270 interpolated frames do not show disconnected floating features, pop-in of unmasked rectangles, inverted ear, or instantaneous silhouette jumps. Frame-difference peak is only a diagnostic, not a PASS by itself.

**S06 Artwork preservation:** at cardinal views, compare against independent intended original head art (pixel aligned/segmented): silhouette/landmark tolerance declared before looking at output. Quantitative preliminary target: silhouette IoU >=0.93 in each authored key view and landmark position error <=2% of rendered head height. **Do not optimize only to these thresholds**; separate vision/human review still required.

**S07 Visible independent review:** inspect full-size front/right/back/left and key 3/4 view, plus contiguous 1° neighborhoods at 90° and 270°. Reviewer records frames and exact part/landmark failures; no blanket PASS from 192 output frames.

**S08 Scope truth:** no claims of portrait/full-body/production pass without independent art and movement acceptance, respectively. Status values: `PASS_STRUCTURE_PENDING_VISUAL`, `FAIL_STRUCTURE`, `FAIL_VISUAL`, `BLOCKED`, `PASS_HEAD360_VISUAL`.

## 5. Evidence, resource limits and rollback

GitHub Actions on Linux Node 22, TS strict, Chromium WebGL, Playwright screenshot, FFmpeg, ffprobe. Per single candidate, render diagnostic angles and transition strips before continuous movie. Produce:
- beauty, depth, ID, alpha, normals or surface-wireframe for exact same frame;
- 13-angle board + 90/270 narrow continuous strips;
- `frame-metrics.json`, `qa.json`, reference SHA/commit/run URL, actual MP4 **only after** S00–S05 pass;
- 2-variant A/B side-by-side screenshot from same pose/camera.
Video PNG/MP4/large originals remain in Action artifacts / Draft Releases; repository contains text-only descriptors and code. Every phase commits its actual code+FAIL/PASS and CI run URL. Never rewrite historical failures.

**Stop rules:** if side anatomy is not visible, do not tune alpha, colors or frame-rate; return to T02/T03. If candidate A has unacceptable texture distortion even with geometry, explore B's view-specific key art. If B needs one independent hand-painted view for most intermediate angles, prefer A/hybrid. If both exhibit the same scene/asset error, correct reference and correspondence rather than adding extra parts.

## 6. Immediate next action (T00 then T01, no asset-generation detour)

1. Freeze exact `main` MVP-008 before changes; retain existing 90/270 FAIL screenshots and record source hashes. Do NOT patch the old flat-proxy runtime as a shortcut.
2. Isolate `head009` head-only demo: static pose, fixed camera, no IK or FX. Build shared Beauty/ID/Depth/Alpha coverage code, with deliberate bad-depth and stale-mask negative tests that MUST fail.
3. Prepare independently authored 0°, 45°, 90° **right-facing head** source art, with face profile/nose/chin/one visible eye/ear/front-side-back hair, named matching landmarks and actual per-angle occlusion layers. 30°, 60°, 75° references must be HELD OUT from interpolation to score quality.
4. Implement **B first**: angle-local 3D anchor projection + 2D landmark/mesh warp + view-dependent layer order/visibility and coverage-consistent depth. Render 0/15/30/45/60/75/90 at 512px+ head crop. Reject copied frontal face or simple full-image crossfade.
5. Independent model+program review of 90° anatomy, 30/60/75 holdouts and mask/depth graph. On FAIL, add only necessary semantic parts or exactly one corrective keyview, then re-evaluate. On PASS extend the SAME head to 180°, 270° and wrap, then head motion. A/hybrid is backup only after documented B no-go.

### Historical project decision

MVP-001 explicitly discarded `lightweight 3D surface + single UV`; V2 then explicitly waived complete 3D head; MVP-002 cancelled reference experiments and rushed integrated flat proxy. MVP-009 is **a corrective experiment**, not a claim that one global UV surface can perfectly reproduce all original art. If selected, geometry defines physical structure; keyed layered art remains authoritative for aesthetic appearance.

Do not promote this plan to the production repository until T04 B has a visually supported head and the architecture decision is recorded. A candidate remains optional fallback only.

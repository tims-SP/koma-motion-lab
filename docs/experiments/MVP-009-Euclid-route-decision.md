# MVP-009 · Euclid 研究核对后的技术选择与执行顺序

Date: 2026-11-01  
Status: **SELECTED B / DESIGN ONLY / NOT IMPLEMENTED / VISUAL FAIL inherited**  
Lab: `tims-SP/koma-motion-lab` · Production `tims-SP/koma-motion` remains untouched.

## 0. Decision — do not restart architecture selection

**Preserve the already recorded owner-selected Plan B** in [MVP-009 head360 representation](./MVP-009-head360-representation-plan.md), [detailed B implementation](./MVP-009-plan-b-multiview-depth.md) and [machine-readable tasks](./MVP-009-gates-and-tasks.json).

The chosen product architecture is a Euclid-inspired **hybrid appearance system**, but the **first implementation experiment is Plan B**: true independent multiview layered art, semantic key registration, 3D anchors, camera-relative depth and occlusion, view-dependent local ArtMesh warping/VDD. It **does not** require a conventional full-volume head or one continuous 3D-UV painting.

**Conditional enhancement, NOT prerequisite**: small real 3D patches (nose, ears, face-hair contact/scalp, later shoulders) may be evaluated *only* when B demonstrates a specific, recorded inability to maintain coherent depth/silhouette at reasonable key-view/repair cost. Do NOT replace B with global curved-UV reconstruction just because flat billboards were broken in MVP-008.

The old MVP-008 was **not a valid test of B**: it lacked independently authored right/left profile anatomy, actual semantic inner-hair/face correspondence, credible per-view depth, and matching beauty/ID/depth shaders. Those missing inputs cannot be reconstructed by changing alpha.

## 1. Research sources and interpretation boundaries

1. **Live2D Euclid** historic product design: [2016 4Gamer engineer demo](https://business.4gamer.net/article/1607/16070401/). Head 2D-expression plus 3D-body hybrid and view-dependent layered painting are relevant. One demonstrator used 7 authored drawings across a wider viewpoint grid; this is **not** a general guarantee that every character needs only seven drawings. Euclid internal source/render formulas are unavailable; do not claim exact reimplementation.
2. **Euclid discontinuation**: [Live2D official 2018 announcement](https://www.live2d.jp/news/euclid_suspension/). Officially cited production cost and difficulty applying the technology; thus Euclid Editor/SDK is **not a runtime dependency**, and authoring hours/needed corrective keys are architecture-level metrics.
3. **Rivers/Igarashi/Durand 2010** [2.5D Cartoon Models](https://alecrivers.com/2.5dcartoonmodels/) and [exploratory reimplementation](https://github.com/without-paper/2.5d_cartoon_model): grouped strokes/shapes, orientation space, 3D anchor constraints; not equivalent to interpolating one face rectangle.
4. **Kitamura/Kanamori/Tsuruno 2014** [2.5D Modeling from Illustrations of Different Views](https://www.jstage.jst.go.jp/article/adada/18/4/18_74/_article/-char/en): explicitly depth-arranged deformable billboards, correspondence and hand-authored hidden-area completion. Most directly useful structural starting point for B.
5. **Fukusato/Maejima 2022** [View-Dependent Deformation for 2.5-D Cartoon Models](https://pubmed.ncbi.nlm.nih.gov/35544514/): guided cartoon exaggeration at given view keys; it does **not** synthesize anatomically missing side-profile illustrations.

Before importing any third-party code, pin source commit, inspect license and run upstream sample. Reference articles provide technical direction, **not** evidence of implementation parity.

## 2. Architecture split and unambiguous ownership

- **Appearance:** real independent front/3/4/profile/rear image layers, source textures and feature landmarks own anime anatomy and linework.
- **Spatial skeleton:** 3D head/body anchors + local camera viewing direction own projection, relative movement and initial depth.
- **View transitions:** per-part keyed geometry and VDD corrections own intermediate silhouette; feature identities must remain stable, with explicit split/merge and appearing/disappearing rules.
- **Occlusion:** camera-space depth AND region-aware visibility graphs own face/ear/side-hair ordering. Do not blanket `depthTest=false` or put all facial parts into fixed `renderOrder`.
- **Diagnostics:** exactly the same render geometry and clip/alpha coverage logic must be evaluated for beauty, ID, depth and alpha. The old stale `wipeBounds` QA shader is a confirmed invalidating bug.
- **Animation:** bone/IK/foreshortening only after static head angle acceptance. A fixed camera + rotated model is valid if the result matches an equivalent relative camera orbit with controlled lighting.

## 3. Execute the current MVP-009 plan, not a parallel rewrite

| Step | Input and mandatory action | Exit / reject criterion |
|---|---|---|
| T00 baseline | Freeze previous MVP-008 source, real right/left failures and art hashes. Keep separate `head009`; do not patch old full-body runtime as a shortcut. | Existing side failure is visibly reproducible and archived. |
| T01 truthful QA | Unify beauty/ID/depth/alpha coverage. Inject deliberately wrong depth and stale masks, assert they FAIL. Probe actual 75/90/105 and 255/270/285. | Any zero-overlap pass or coverage discrepancy BLOCKS. |
| T02 reference assets | Create distinct same-character 0°, 45°, **true 90° profile** layered head with nose bridge/tip, chin, mouth, ear and multiple hair parts. Independent 30/60/75° references must be held out from the renderer. Stable landmark IDs and source hashes are mandatory. | A squashed front picture does not count as side art. Source and held-out art are separately reviewed. |
| T03B spatial layering | Implement per-part anchors and view-dependent depth, topology changes, correct masking in dedicated TS `head009`; draw **one head**, no full body, hand IK, lighting FX or video first. | Image/depth/ID pass at 0/15/30/45/60/75/90. Source texture & side anatomy judged independently. |
| T04 go/no-go | Compare intermediate holdouts and side anatomy; record number of missing keyviews, manual changes, split/merge errors and fixed source sha. | PASS => extend B to 180/270/360. FAIL => repair semantic asset and retry once; repeated expensive interpolation/occlusion failures => isolate candidate limited 3D patch A/B on same references. |
| T05 360 and VDD | Add independently authored 180° rear and 270° true left, then only required 135/225/315 correctives; compare no-VDD/VDD. | All 13 canonical angles, dense 90/270 bands, stable part-depth and 0/360 wrap visual PASS. |
| T06 head motion | Independent head yaw, blink, hair and pitch diagnostic, preserving semantics and coverage parity. | Short head motion accepted in both geometry/vision; pitch is diagnostic only. |
| T07 full body | Body part/skeleton/3D IK and meaningful foreshortening + planted foot; original art upgrade and full animation. | Full 192-frame video requires **independent visual signoff**, not numerical gates alone. |

## 4. Non-negotiable evidence and measurable targets

- Original authored side profile and back skull; right/left profile cannot be mirrored or squeezed copies. The ear and nose must be in correct silhouette and occlusion layers.
- At authored keyviews, initial **silhouette IoU >=0.93** and landmark reprojection error <= **2% of cropped head height**, with independent artist/vision review. These thresholds do not mean anime aesthetic PASS.
- Same source/pose/frame for beauty/ID/depth/alpha; opaque interior coverage mismatch <= **0.5%** and boundary tolerance <= **1 px** (provisional thresholds; measure actual antialias/raster variance).
- No `UNTESTED` passes at 90° or 270°, no zero-overlap passes, no undocumented opaque/transparent geometric tricks.
- Head-only crop >= **512px** high; review 0/15/30/45/60/75/90 and full 13-angle 360 grid after local pass. Dense strips at yaw 86..94 and 266..274 must be inspected.
- Explicit source/commit/renderer SHA + full art provenance, independent heldout images, actual viewer-review JSON. Do NOT reuse stale MP4 from previous SHA.
- **Cost stop rule:** if correct transition needs manually authored keyview at most every 15° or repeated local masking without generalizable correspondence, B is no-go for that part; record cost and compare a limited 3D patch, not further alpha tweaks.
- `PASS_HEAD90_VISUAL` is not `PASS_HEAD360_VISUAL`; neither implies full-body 360 or free-camera production readiness.

## 5. Immediate next action

**Do T00 + T01 + T02, then T03B through 90°**. Stop. Review real references vs rendered 30/60/75/90 before generating further full-body videos. If validated, complete 360 and motion in the existing MVP-009 task graph.

No code is asserted as implemented and no visual quality PASS is claimed by this decision document.

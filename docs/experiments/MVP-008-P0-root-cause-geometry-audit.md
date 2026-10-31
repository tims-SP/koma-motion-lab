# MVP-008 P0 root cause audit — "the camera spins but face/parts remain flat"

Date: 2026-10-31
Source audited: `main@ba3d42bd4bb67c2b40d60a709bc4229cc35562d7`.
Observed render: [192-frame Actions #41206130892](https://github.com/tims-SP/koma-motion-lab/actions/runs/41206130892); [same-source-frame review #41206308861](https://github.com/tims-SP/koma-motion-lab/actions/runs/41206308861).
Status: **P0 architecture/representation defect CONFIRMED**. This audit changes NO rendering code and claims NO new visual pass.

## Executive conclusion

The existing prototype is **camera-facing 2D triangulated ArtMeshes + four view-dependent 2D shapes/textures + rotating 3D anchors**. It is NOT the promised "3D curved surface + continuous original-art UV skin". Part centers have Z and hands have 3D IK, but individual head/face/torso ArtMeshes have zero thickness. They are rebuilt facing the fixed camera for every frame. A computed yaw cannot reveal physically meaningful profile anatomy, true parallax, nor a skin/hair contact surface that does not exist.

A fixed camera itself is not wrong: **rotating a truly volumetric character relative to a fixed orthographic camera is valid**. The failure is that the geometry is still flat sprites, with yaw spent on 2D interpolation, not 3D orientation of an actual surface.

## Confirmed source-level findings

| Severity | Finding | Reproduction / code |
|---|---|---|
| **P0-A** | Face, scalp and all main ArtMeshes have a *constant Z for every vertex inside each part*. Fan geometry is created using `V(..., ..., center.z)`. Shape morphs only X/Y. No volumetric facial or rear-head surface can project into profile. | `experiments/mvp002/src/integrated.ts:239-254`, `228-237` |
| **P0-B** | Rendered yaw is converted to two adjacent planar keyviews and linear/smoothed X/Y interpolation, not to surface normals / per-vertex depth under rotation. The scene's `root` is never rotated; the camera remains at `(0,eyeLevel,15)`. Only the anchors use `transform(...,rootYaw)`; all ArtMeshes themselves remain parallel to the image plane. | `integrated.ts:50-53,95-105,239-259,327-352,367-383`; `scripts/render-dynamic360.ts:42-44` |
| **P0-C** | Face/eyes/fringe turn **off depthTest and depthWrite**, then are artificially forced to render order 100/110/120. This overrides the only usable part-center depth. Face/hair correctness is therefore an X/Y clip, not physical per-pixel occlusion. | `integrated.ts:175-180,228-237,209-216` |
| **P0-D** | Four "independent" views are procedural paintings clipped to the **front keyview's canonical UV mask**, and side-specific face features are small path/eye variations. Independent 270-degree contour points exist, but there are no registered ear, facial surface, face/hair inner interface or depth coordinates. A 90-degree "texture distinct" test cannot establish a 90-degree *anatomical view*. | `src/rgba-view-art.ts:16-31,41-66,116-137`; `src/anime-ink.ts:116-133,160-170`; `src/left-keyviews.ts:21-38` |
| **P1-E** | Face/hair/eyes are switched off by yaw range 110-250° and revealed around 90-110° / 250-270°. The V05 6-row curved matte scans the **OUTER face contour** rather than registering the **INNER skin-to-hair occlusion boundary**. It cannot create missing anatomy or real depth. | `integrated.ts:106-120,123-151,209-216` |
| **P0-F (QA invalidation)** | The *beauty* shader now applies 6-row `matteLeftA/B` etc., but **`idShader` still reads removed `wipeBounds` and runs the former straight-X wipe**, using fallback [0,1]. So beauty != part ID != depth/alpha mask under partially occluded facial yaw. Earlier "10/10 occlusion" is a test of mismatching pixels and must not be advertised as facial depth correctness. | `integrated.ts:153-225`; `src/qa/turn360-runtime.ts:117-155`; `src/qa/occlusion-audit.ts:21-49` |
| **P1-G (QA gap)** | The dynamic local-occlusion aggregator explicitly **filters yaw=90°** from rule evaluation, and the 180° path tests torso/arms only. Existing automated checks primarily assert number of frames, IK targets, yaw metadata, continuity and select 2D overlaps. No gate verifies nose projection, cheek-to-hairline depth, ear visibility, side-silhouette correctness, or single-face connected components at 75/90/105/255/270/285. | `scripts/audit-dynamic-occlusion.ts:27-61`; `scripts/render-dynamic360.ts:116-208` |

## Deterministic mathematical evidence

- Face front contour X spans `[-0.82, +0.83]`, width `1.65`; its 90° right contour X spans `[-0.60, +0.90]`, width `1.50`. Face part width `0.42` thus gives planar projected widths `0.693` and `0.630` (about 91% of frontal width), before compositing. This is *not* volume-based foreshortening.
- Face and back-hair local anchors differ by Z `0.13 - (-0.21) = 0.34`. Rotating centers with `transform` makes their center-depth separation `0.34 cos(yaw)`. At exactly 90° and 270° these centers have equal Z: there is **no per-vertex depth field** to resolve the scalp boundary at profile angles. For the front face, depth test is disabled anyway.
- The latest V05 machine `D12_CONTOUR_MASK_BEND` checks only `bend > 0.008`; a curve can have a nonzero bend while still depicting a face as a flat cutout.

## Actual pixels and scope of observation

Review artifact #13044364166 includes the real encoded-video frame board. At approximately 90° the face is a narrow sliver against the hair; at 270° head-local turning changes the side appearance abruptly, not by projecting a continuous face surface. Earlier V05 visual reviews at frames 40, 132 and 134 identify a nearly vertical cut and slice-like reveal. These observations are consistent with P0-A through P0-E. Frame visuals alone cannot identify which code branch is wrong; the renderer source above does.

## Required order — STOP polishing flat masks as a substitute for volume

1. **Isolate head MVP**: one fixed pose, 0/45/75/90/105/135/180/225/255/270/285/315/360° turntable. No arm IK, hair animation, shadow effects or aesthetic tuning until real volume/depth is demonstrated.
2. **Introduce a small but actual 3D head/face/hair geometry**: depth-varying face surface with forehead, brow, nose bridge, nose tip, cheek, jaw/chin, ears and separate back-hair/front-hair surfaces. Keep semantic landmarks and coherent UV coordinates. 3D surface may be coarse; it cannot remain constant-Z per ArtMesh.
3. **Use the renderer's real depth** for per-pixel occlusion. If view-dependent texture layering needs manual compositing, ensure it is limited to well-defined artwork effects and cannot override facial geometry. Remove front face global `depthTest=false` dependency. The test of correctness is the visible side silhouette and occlusion, not the number of parts.
4. **Repair diagnostic shaders before trusting numeric gates**. Beauty/ID/depth/alpha must share the exact same discard and alpha test. Compare their silhouettes and per-pixel coverage at critical yaws, and fail on mismatch. Explicitly evaluate 90° and 270° (do not filter out side cases).
5. **Then map authored face/profile/texture** to the curved UV surface, verify anatomical identity and L/R asymmetry; only afterward restore independent head yaw and arm/foot motion.

## Minimal mandatory acceptance before resuming full-body 192-frame video

- Every face ArtMesh's **camera-space per-vertex depth span** is nonzero for nondegenerate turned views, with anatomically coherent silhouette at 90° and 270°. Numerical nonzero depth is *necessary but not sufficient*.
- True side view visibly has nasal protrusion, mouth/chin/ear structure, and consistent hair/face/ear occlusion; both left/right remain distinct and no rectangular face reveal.
- Depth/ID/beauty silhouette masks agree for matching renderer frames; no `UNTESTED` at side angles.
- Independent visual check of actual 0/45/90/135/180/225/270/315/360 portraits and connected transition strips. Final visual status remains **FAIL_VISUAL** until review confirms improvement.

No render implementation has been changed in this investigation.

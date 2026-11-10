# P15-33 · Semantic-anchor-constrained 2D mesh VDD

Executed 2026-11-11 UTC+08 on target VPS via ChatGPT VPS Bridge Worker. Source repo `tims-SP/koma-motion-lab`, feature branch `feature/gif-multiview-p0-ingestion-20261105`.

## Goal and actual implementation

P15-32 moved three ArtMesh roles with unconstrained optical-flow-derived 7×7 (72 triangle) warp meshes. P15-33 adds **explicit semantic position constraints to those triangle vertex maps** before inverse warping each source texture.

- `eye.far`: registered P15-12 projected iris anchor, plus automatically extracted left/right alpha-support proxies. The latter are not independently approved eyelid corners.
- `hair.clip.cross_gold`: registered P15-12 clip center, plus two alpha-support diagonal-extreme proxies. These are not independently approved crossed-bar endpoints or a named hair lock.
- `hair.side`: registered P15-12 side-hair camera point, plus alpha-derived lowest-strand proxy. These are not independently approved physical root / tip correspondences.

For each adjacent pair of source keyframes, build forward and backward Farneback flow sampled on the 7×7 mesh. Compute candidate features from each endpoint, interpolate their positions to the midpoint, and apply a Gaussian radial-basis correction to the mesh vertex displacement so the *estimated* feature mappings satisfy the desired intermediary positions. Piecewise-affine triangle inverse mapping deforms both source textures; they are then composited over the unchanged remaining ten roles in canonical P15-21 depth order.

The P15-32 five source keyframes are copied byte-exact. This is **image-derived 2D geometry, not validated 3D facial topology**. It does not create independent paintings.

## Real results

| Check | Result |
|---|---:|
| View sequence | 55°, 56.25°, 57.5°, 58.75°, 60°, 61.25°, 62.5°, 63.75°, 65° |
| Five source keyframes | Byte-identical to P15-32 |
| Constrained mesh midpoint frames | 4 |
| Mesh roles | 3 |
| Per-role grid / triangles | 7×7 / 72 |
| Max feature tracking residual | 0.06298 native pixels |
| Max mesh-vertex correction | 2.77203 native pixels |
| Triangle reversals | 0 |
| Minimum triangle area ratio | 0.606919 |
| Distinct role-layer pixels vs P15-32, each midpoint | 22,510 / 22,832 / 21,859 / 25,663 |
| Full output pixels differing vs P15-32, each midpoint | 117,641 / 120,617 / 115,358 / 131,735 |

All 10 non-mesh layers are **byte-identical** to P15-32. The changes originate from exactly the three constrained roles and their scene composites.

Tests: 8/8 Python unit tests PASS. Chromium desktop 1440×900 and mobile 390×844: 18 viewport/frame interactions, 108 image loads, 0 JS or network errors. Offline interactive HTML compares the P15-33 scene against P15-32 and displays the three transparent roles and enhanced RGB difference. ZIP integrity checked.

## Acceptance scope

**PASS**: engineerable semantic-anchor constraint solve for 2D mesh warping; source identity and keyframe stability; tracked feature residuals; no inverted triangles; output and browser execution.

**FAIL / PENDING**: physical far-eye occlusion behind 3D nose, clip attached to a specific near/far hair lock, independently approved eyelid/crossbar/hair-tip landmarks, independent original-view painting, formal Japanese anime visual quality. The proxy features are inferred from alpha support and may not correspond to anatomical or artistic landmarks. This method is *not* a physical 3D world model or the final Euclid-style view-dependent deformation.

Production P15-21 `anatomy` remains untouched. Neither P15-32 nor P15-33 candidate is promoted to production.

## Reproduction

Run in `/root/koma-motion-r1999/work/koma-motion-lab` with the existing Python venv:

`/tmp/koma-see-through-client-venv/bin/python experiments/gif-multiview-keyparts-mvp/scripts/p15_33_semantic_vdd.py`

`/tmp/koma-see-through-client-venv/bin/python experiments/gif-multiview-keyparts-mvp/scripts/p15_33_review.py`

`/tmp/koma-see-through-client-venv/bin/python -m unittest experiments/gif-multiview-keyparts-mvp/scripts/test_p15_33_anchor_vdd.py`

`node experiments/gif-multiview-keyparts-mvp/scripts/p15_33_browser.cjs`

Review ZIP: `experiments/gif-multiview-keyparts-mvp/private-assets/exports/p15-33-anchor-vdd-review.zip`. QA: `evidence/p15-33-anchor-vdd-qa.json`, `evidence/p15-33-browser-qa.json`.

## P15-34

Replace alpha-inferred endpoints with deliberately painted / manually calibrated P0 semantic landmark keyframes; verify source-consistent side hair-tip, crossed-bar endpoint and named hair lock attachment; establish camera-depth-driven near/far occlusion using real face geometry. Then connect the constrained vertex-grid interpolator to the TypeScript/WebGL HTML runtime and perform visual frame review, not only numeric QA.

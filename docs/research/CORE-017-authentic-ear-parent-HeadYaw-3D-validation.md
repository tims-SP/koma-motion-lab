# CORE-017 · Authentic INX ear hierarchy/HeadYaw and source UV ↔ synthetic 3D shell

**Date: 2026-10-30 · Actual execution · Result: genuine source chain PASS; production art FAIL.**

## Mature reference

Original Inochi2D docs specify transforms on a node are inherited by children; translation, rotation and scale are relative to the parent. https://docs.inochi2d.com/en/latest/creator/nodes/node.html .
The experimental supported Rust runtime [Inox2D](https://github.com/Inochi2D/inox2d) implements INX parsing, 2D transform and vertex-deform parameter bindings. We reused original data rather than inventing a transformation schema; this Python ear-only evaluator is an **independent limited-scope replay**, not the official D SDK or full Inox2D renderer.

## Actual original binary and discovered hierarchy

Downloaded and SHA256-verified full 17,731,911-byte original Aka INX: \`dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f\` by seagetch, CC BY 4.0. The complete source ear node chain is:

\`Root → Body → Neck → Face → Back Side:: Hair → Ear:: Left/Right\`

Actual local transform translations (native units):
- Body (-84,-790), Neck (0,-529), Face (-9,-371), Back Side:: Hair (+42,-15).
- Ear:: Left (+175,-462); Ear:: Right (-298,-420).
- Both source ears' transform rotation = 0, scale = (1,1) in original neutral pose.
- Source UV, native TGA and exact original ArtMesh mesh data from CORE-016 remain unchanged: Left 57 verts/89 triangles, Right 59 verts/93 triangles. UV values outside [0,1] are **not clamped**.

## Actual HeadYaw channel findings

Original \`Head:: Yaw-Pitch\` has **114 real bindings** over nine horizontal normalized samples [0,.125,.25,.375,.5,.625,.75,.875,1] × three pitch samples [0,.5,1].

**Four bindings directly target the two ears**: each has \`transform.t.x\` and one per-vertex \`deform\` binding. Accounting for the ancestor nodes gives **12 original binding records** involving the ear chain (including \`Face\` / \`Back Side:: Hair\` and a \`Body\` per-vertex deform which does not represent an ear-local deformation). These are original INX data, not new hand-authored keyframes.

Successful independent real-data GitHub Actions **[#41009942405](https://github.com/tims-SP/koma-motion-lab/actions/runs/41009942405)**:
- Evaluates exact native grid samples at x=0.50 (neutral), x=0.75, x=1.00, fixed original normalized pitch=0.50.
- Computes inherited local translation/rotation/scale matrices and genuine ear-local per-vertex deform offsets, source UV and source topology unchanged.
- The mean ear positions at native x=1 vs x=.5 move by **(-91.00, 0.00)** native XY for \`Ear:: Left\`, **(-70.758, +0.1479)** for \`Ear:: Right\`. These are **native model units, not pixels or physical degrees**.
- Keeps emitted original-parent/HeadYaw JSON in a downloadable Actions artifact; no original INX binary re-shared.

## Actual encoded videos and independently decoded images

The complete local test actually loaded source ear TGA images and native ArtMesh UV arrays, then evaluated parent and direct HeadYaw bindings.

**Video A (ear-only native 2D pose replay):**
- \`CORE017_original_INX_ear_HeadYaw_native_chain_DIAGNOSTIC.mp4\`: 97 frames, 24fps, 1440×720, from normalized HeadYaw x=.5→1→.5 with pitch=.5. Left real ear-paint/mesh only; right canonical user's front illustration as reference (other head parts are deliberately not replayed).
- Final encoded H264 MP4 SHA256 \`15038ba5359745b578e175e6d147cf2c96b6f1b8dcc268faef5b67336c2121ae\`. Re-decoded and **visually inspected frames 0/12/24/36/48/60/72/84/96**.
- Source-space screen mapping in the diagnostic is an **approximate fit** from original native coordinates to the provided 720×720 user raster (x=.43*worldX+398, y=.36*(worldY+2682)), NOT the official renderer camera transform. Approx original image ROI mean RGB difference: left ear 22.16/255, right 28.06/255, **not pixel parity; ROIs also contain underlying source/hair colors**.
- Screen pixel-change (native neutral vs native max, >20 threshold): entire ear canvas 10.15%, per-ear crops about 51.05% / 46.82%. Pixel movement **does not guarantee good character art**.

**Video B (same true INX parameter mesh + synthetic 3D depth):**
- \`CORE017_original_EarMesh_native_pose_3D_missing_sides.glb\`: 4 separate nodes, two original front ArtMesh triangle/UV/TGA surfaces and two synthetic shallow rear/side shells. GLB SHA256 \`30a6b3990b8a0ad145fd218f0ff435d3cadadb6a75f27889e0a82e3c3d6eeed2\`.
- \`CORE017_native_yaw_plus_3D_orbit_MISSING_BACK.mp4\`: actual depth-buffered triangle raster, 97 frames/24fps 480×480. Native normalized HeadYaw and independent 0–180° camera orbit both vary; **no semantic mapping between native parameter and physical yaw**. MP4 SHA256 \`537414db7865797f72f9f4a98bbf7b7990503bbb08dbcd45b5490e0dad4086b3\`.
- Again independently decoded frames 0/12/24/36/48/60/72/84/96; actual contact JPEG opened and inspected. Magenta is **intentional NOT-PAINTED** for both ear shell sides and rear. At 0° there is also magenta edge leakage, a clear 0° raster art-quality FAIL.

| Synthetic orbit | Authentic ORIGINAL front TGA coverage of *visible ear proxy geometry* |
|---:|---:|
| 0° | 69.23% |
| 45° | 57.19% |
| 90° | 0% |
| 135° | 0% |
| 180° | 0% |

These percentages are **only source-provenance fractions inside this artificial ear volume**, NOT full character 360° completion, not quality scores, not absence of seam/identity drift, not physically calibrated source view angles.

## Precisely what is and is not solved

| Test | Status |
|---|---|
| Genuine full INX ear parent chain and Head Yaw 12 binding records | PASS |
| Source original ear mesh topology / UV / actual TGA colors | PASS |
| Native sampled parameter transforms and per-vertex ear deform in independent code | PASS / Github CI |
| Actual local MP4s encoded, decoded, and visually reviewed | PASS |
| Synthetic 3D ear thickness and GLB integrated with native sampled 2D pose | PASS **as debug** |
| Exact zero-pose pixel parity vs official Inox2D / Inochi2D reference | **NOT VALIDATED** |
| True authored side/back ear UV/texture and acceptable volume thickness | **MISSING** |
| Complete 76-part original INX scene renderer with new side artwork | NOT IMPLEMENTED |
| 45°/135° face/hair/ear overlap, 180°/360° character-quality | **FAIL** |

The source-parameter code is in text-only Git:
- \`experiments/koma-25d-core/tools/inspect_ear_ancestry17.py\`
- \`experiments/koma-25d-core/tools/evaluate_ear_chain17.py\`
- \`.github/workflows/koma-25d-core-017.yml\`

**Local binaries**, original source input subset, the full diagnostic video generation Python scripts, GLB, actual MP4s, decoded contact images and QA are in \`/mnt/data/core017/CORE017_Aka_native_ear_HeadYaw_trueUV_QA.zip\`. They were produced in the conversation runtime, **not** in this GitHub CI. No generated binary is stored in Git.

## CORE-018 recommendation

**Stop adding guessed geometry or any more whole-image interpolation** until full 0° original-art parity is measured against the actual source Inox2D renderer. Next obtain identical camera settings and integrate the source original ear nodes into official Inox2D rendering test; compare model's exact raster and custom source-UV 3D front under the same orthographic camera. Then create **separate true 90° ear exterior and 180° rear** source paintings with actual reference edit, segment each side/back ear independently and register new-view UV. Only after rear skin exists should we expand real 3D onto face/hair and evaluate full 0–360°.

**Production repo \`tims-SP/koma-motion\` untouched; this remains R&D Draft.**
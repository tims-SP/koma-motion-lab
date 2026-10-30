# CORE-013 · real Aka rear candidate repair and 0°→180° actual video QA

Date 2026-10-30. **Status: technical repairs and encoded video PASS; true anime-quality continuous turn FAIL.**

## Actual assets and verified provenance

- Aka official PSD-derived front, **user-uploaded 1536×1536 RGB**, SHA256 `edb4c6d78874c95cca8e6d0b8398be457b40ddcb7fb93bd5d5087e3b02f1b21d`. Original official artwork © seagetch CC BY 4.0.
- Single GPT right-facing 90° side: **1254×1254 RGB**, SHA256 `330a90c6819f6e74bcb5af33f9cca27441f9dedefae97d7371c4f5c6c7d25c81`. Nominal pose only, not camera-calibrated.
- CORE-012 GPT rear version: **1254×1254 RGB**, SHA256 `5f016f460c5632366e5c1dfbfc74d33de79d93faa1d4b71a027ef5fc0ba0d965`. Two defects were already flagged: excessive white ear interior and invented curl at top of rear scalp.

## Attempted image editing

Two new calls to image_gen **failed the specific edit**: instead of a faithful edit of the single existing rear image, it produced additional character sheet / front-side-back montage output and exaggerated new costume/hair identity details. Both were REJECTED from the actual source texture set, **not counted as accepted back art**.

An explicit local raster-repair script, which preserves the original candidate, then:
- Adjusted cream-toned interior ear fur to orange rear-ear tones using bounded polygons and source luminance.
- Removed the additional top curl by localized OpenCV inpainting.
- Wrote `aka_180_back_LOCAL_REPAIR_CANDIDATE.png`, SHA256 `127430a3e41ae0f8376b62428830c73ecdcd1d03348473c3e6391a8c57e04a1d`.
- **46,588 pixels (2.96%)** differed by more than 10/255 from the source rear PNG, all changes limited to technical repair regions.
- The exact same algorithm was rerun locally and its resulting 1254×1254 rear PNG was verified **pixel identical** across two runs.

**Direct visual review:** invented curl largely removed, white ear interiors changed to warm orange. Top of head has a visible repair/seam, and ear-back anatomy is still painterly approximate. Final image **not accepted as original/author-quality view skin**.

## Actual encoded video generated and independently decoded

- `aka_0_90_180_TRANSITION_DIAGNOSTIC.mp4`, SHA256 `673cc257ead3518c957b95873509ce10f17c4bbdd293f7c68bd3d3d54716fc03`.
- **193 frames**, 24 fps, **1440×760**, ~8.04 seconds: nominal headings 0°→90°→180°→90°→0°.
- Same image-alignment transforms were applied across all three references to provide full-size head/ear/neck comparisons.
- **LEFT**: full-image alpha blend negative control, expected ghosting. **RIGHT**: nearest-keyframe cut/hold negative control, expected temporal pops.
- Final H.264 MP4 was decoded at **frames 0/24/48/72/96/120/144/168/192**, and the real encoded frames were inspected, not just pre-encoded raster arrays.
- **Visual FAIL**: strong duplicated eyes/ears and hair ghosting around the missing 45°/135° intermediate views in the blended control; cuts produce unnatural pose jumps. Image warp alone does not solve actual perspective-aware part visibility.
- A successful video container and observable frame change **does not imply successful 2.75D animation**.

## Output disposition

Local conversation artifacts exist:
- `/mnt/data/core013/aka_180_back_LOCAL_REPAIR_CANDIDATE.png`
- `/mnt/data/core013/rear_before_after_review.jpg`
- `/mnt/data/core013/aka_0_90_180_TRANSITION_DIAGNOSTIC.mp4`
- `/mnt/data/core013/encoded_MP4_contact.jpg`
- `/mnt/data/core013/core013_qa.json`
- `/mnt/data/core013/repair_and_preview13.py`
- `/mnt/data/CORE013_Aka_rear_repair_180_transition_bundle.zip`

These binaries are in the **conversation sandbox**, not published to GitHub Draft Release or committed as repo blobs. Main repo `tims-SP/koma-motion` remains unchanged.

## Acceptance matrix

| Gate | Verdict |
|---|---|
| Real original Aka front, user accepted GPT 90° side, GPT rear candidate assets loaded | PASS |
| Stable local rear image repair output | PASS / provisional artistic result |
| 180° back ear anatomy and hair-root continuity against 90° | NEEDS_REPAIR |
| Native original INX UV, 3D depth/surfaces and parameter rig applied to new views | NOT IMPLEMENTED |
| 45°/135° hidden features, per-part occlusion and no ghosting | FAIL |
| Actual encoded MP4 generated and independently decoded | PASS |
| High-quality 0°→180°/360° anime turn | **FAIL** |
| Complete 360° yaw anchors | INCOMPLETE |

**Next substantive work:** get independently consistent 45° and 135° painting/structure (or real registered part-wise deformation / geometry), then map to original 76 Aka ArtMesh nodes, build view-conditioned UV plus independent ear/hair surfaces, and repeat final encoded-video visual QA. Do not claim that a simple image blend or ellipse pass is 3D production animation.

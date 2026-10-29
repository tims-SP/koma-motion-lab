# CORE-005 · 2D Silhouette Visual Hull + Original-View Skin Projection

**Status: geometric hypothesis supported; original-art continuity / anime quality FAILED.**
Recorded: 2026-10-30

## Reproducible evidence

- Final verified CI: https://github.com/tims-SP/koma-motion-lab/actions/runs/40940530631 (SUCCESS)
- Source/lab code: https://github.com/tims-SP/koma-motion-lab/pull/15 (DRAFT)
- Actual videos, encoded MP4 contact audit, GLB description and numbers:
  https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-bcef2ca533a01b5582fb (DRAFT)
- All test binary blobs are release-only, not stored in Git.

## Source scope

One matching-character CC0 VRoid beta example \`Sendagaya_Shino.vrm\`,
pinned source repo commit \`e16eb187100149a315ad92c3c9968f1d5baa6c7d\`.
The full original 3D source is rendered **only as independent reference**
and the provider of calibrated 2D image sheets. Reconstruction code does
NOT load the original 3D mesh, skeleton or skinning weights.

Given just 2D front (0°) and side (90°) binary masks, construct candidate
volume from front/side silhouette intersection, and use scikit-image
Marching Cubes to produce true 3D triangles. Fixed-depth front-silhouette
extrusion is the controlled geometry baseline. Actual front/side/back 2D
PNG views are mapped onto curved geometry through per-face UV projection.

This DOES NOT constitute arbitrary commercial Live2D conversion or
single-drawing full 360° reconstruction. This source has no original 2D
ArtMesh or deformable rig in the 2D input.

Existing research foundations:
- Laurentini, "The visual hull concept for silhouette-based image
  understanding," IEEE TPAMI 1994, DOI 10.1109/34.273735.
- Standard voxel silhouette intersections and Marching Cubes;
  Python scikit-image and trimesh used instead of a new renderer.

## QA process and visual review

1. Initial custom material rendered **all-black silhouettes**: discovered
   by manually inspecting the 4-row montage from the final encoded MP4
   clips, despite structural CI being green.
2. Replaced the custom ShaderMaterial with established Three.js
   MeshBasicMaterial + explicit triangular UV mapping on a three-view
   PNG texture atlas. Added a fatal QA gate if the subject is mostly black.
3. Actual film frames then showed significant *white seams* at side
   projection transitions. Added nearest-foreground color padding
   outside the 2D silhouette to reduce background leakage.
4. Re-inspected the final MP4 decoded-frame montage. Source colors now
   appear, but **hair/arms/clothes/legs are stretched or duplicated
   and have projection seams / smeared strips**. Still NOT art-accepted.
5. Crucial measurement correction: instead of thresholding the colored
   frames to infer geometry, independently render all 73 yaw views with
   uniform black, unlit matte materials, and score those silhouettes.
   This prevents color errors from manipulating the geometry IoU.
6. Independently decode actual MP4s at frame indices 9, 36 and 63;
   require visible subjects, and visually review the encoded contact JPEG.

## Final results

73 frames from 0° to 180° at 2.5° spacing, 640x640, 24fps. 68 withheld
views are used for aggregate metrics.

| Method | 90° geometry silhouette IoU | 68-view mean silhouette IoU | 68-view mean subject RGB MAE |
|---|---:|---:|---:|
| Fixed extruded silhouette | 0.5374 | 0.6117 | 65.68 |
| Front + side visual hull | **0.8692** | **0.7803** | 51.53 |
| Five-view image crossfade | 1.000 (supplied anchor) | 0.8922 | **21.66** |

**Not a fair same-view-budget image-quality contest:** crossfade consumes
five 2D reference views, while visual hull geometry uses two silhouette
views and its appearance is projected from three views. These comparisons
provide different controls: geometric vs image-space interpolation.
Crossfade still contains severe mid-angle ghosting, even though MAE is
lower than the geometry reconstruction in this benchmark.

No 3D skeletal IK, no re-targetable bones, no true ArtMesh preservation,
no dynamic hair/cloth deformation, and no professional anime frame QA.

## Assessment

- Actual, view-constrained 3D curve/volume from TWO 2D silhouettes:
  **WORKS as geometry**, strongly outperforms fixed extrusion in matte IoU.
- Original front view artwork: **NOT PIXEL-FAITHFUL** yet.
- View-conditioned 2D image mapping: **FAILED VISUAL QUALITY**.
- No evidence of a useful, free-rotation animation-quality character.
- Promotion to main Koma repo is PROHIBITED until art/rig gates pass.

## Next prioritized technical hypothesis (CORE-006)

Build per-part surfaces (head, front/back hair, torso, arms, legs,
skirt/sleeves) rather than a single intersected whole-body volume.

For each part, preserve original 2D source UV *as its zero-angle visible
raster layer*. Generate only missing-side surfaces. Use explicit
front/side/back part correspondence, seam placement, occlusion and
view-conditioned facial details rather than face-normal-only atlas
selection. Test actual 2D skeletal source rig deformation at arm joints
and independently compare original front source pixels.

First verify a single head/hair + one elbow at multiple poses before
expanding to full-body skeleton and animation.

# CORE-007 · Real anime PSD / INX source and head-turn video audit

**Status: real layered source + encoded video path PASS; realistic novel-view skin quality FAIL.**

Date: 2026-10-30. Do not merge into production.

## Evidence
- Final successful workflow: https://github.com/tims-SP/koma-motion-lab/actions/runs/40963607445
- Verified final DRAFT Release (two MP4s, source raster, encoded frames, QA):
  https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-ad5d649d369a04ad948d
- Experimental PR: https://github.com/tims-SP/koma-motion-lab/pull/17
- Original source: https://github.com/Inochi2D/inochi2d-docs/tree/593c657855d5679f01443ef311346298fd25e117/docs/source/creator/first-model
- Attribution: Aka design and rigging by seagetch, Creative Commons Attribution 4.0,
  based on Inochi2D example-models README. Include artist and source in preview use.

## Source data actually inspected

- Official tutorial Aka head PSD: 1630×1630; **62 leaf layers**.
- Separate tutorial Aka02 INX authoring rig: **62 TGA texture slots** plus real
  INX mesh node hierarchy, metadata and animation/parameter sections.
- Actual source-layer names include Face, Front Hair, Back Side Hair,
  Side Hair, Eyeball/Eyelashes/Eyelids, Nose, Mouth, Fox Ears.
- Of the 62 PSD layers, 57 produced nonempty raster parts in this study.
- The *source PSD binary and INX are not committed to Git*; fetched from
  pinned official tutorial on every CI run.
- The real INX UV meshes and native param/deformation runtime have **not yet
  been connected to the head-motion renderer**. Do not suggest otherwise.

## Video experiments

Actual 62-layer PSD artwork at 640×640, 36 frames, 24 fps:
1. flat.mp4 — 2D perspective-like horizontal compression and part translation.
2. curved.mp4 — same original raster layers with an additive, shallow
   cylindrical per-part depth projection.

Both test 0° -> 34° -> 0° head-turn values. No authentic new profile or
backside art was supplied. This is **NOT** full 3D or complete Live2D
conversion, only a controlled 2.5D/parametric visual experiment.

## Serious defect discovered through actual encoded-video inspection

**First experiment:** The back hair was drawn in front of the entire face at
mid turn, falsely producing a rear-facing head. A structural CI pass missed
this. Immediately recorded it as visual FAIL.

**Second experiment:** A separate layer-composite quality gate initially
reported source RGB MAE of ~162 even when the PSD source and a proposed
layer order looked nearly identical. Image debugging revealed a measurement
mistake: the source preview included opaque white background but reconstructed
individual layers retained transparent backgrounds. Directly comparing
unassociated RGB bytes in transparent regions made the metric invalid.

**Correct gate:** composite both candidates on the SAME white background,
score only pixels where subject paint appears, and select source part order
by observed fidelity.

- Original draw order: **subject RGB MAE 5.0118/255** vs PSD source.
- Reversed draw order: 26.6920/255 and the face becomes obscured.
- Automated fail-closed gate now rejects PSD layer-parity MAE >48.

Note 5.0118 is *independent PSD layer compositing accuracy*, not pixel
equivalence with the original INX runtime.

## Final verification

- GitHub Actions #40963607445: SUCCESS
- Both actual final MP4s encoded successfully and **decoded from the finished
  file**, samples at frame indices 0,18,35.
- I independently viewed actual decoded-video contact image: the original
  face and bangs remain visible; no more rear hair covering face.
- Flat midway vs original changes ~16.89% of output pixels.
- Curved midway vs original changes ~17.88% of output pixels.
- Flat vs curved midpoint differs on ~13.28% of output pixels.
- Maximum full-sequence adjacent-frame changed area: flat 5.29%; curved 5.85%.
- Initial and final frames exactly equal to the PSD source raster
  **by explicit copying of the source keyframe**. This is NOT proof
  the curved transformation algorithm has lossless zero-angle mapping.
- Source PSD and 62 INX texture slots are real authored illustrations,
  not generated VRM snapshots, screen-space checkerboard or pseudo-art.

## Direct visual verdict

**Art FAIL** despite technical smoke PASS:
- At the 34° mid frame, the face is still predominantly front-facing;
  facial features and silhouettes squash rather than showing genuine
  perspective contour and other-angle facial design.
- Hair depth movement remains approximate with visible minor seam /
  uneven strands; no backfilled hidden profiles.
- Flat vs curved produces different pixel patterns but **not a proven
  preference, and not production-grade Japanese animation**.
- Full native INX mesh/parameter runtime fidelity is NOT tested.
- Real 3D skeleton / IK / head rotation is NOT present.

## CORE-008 decision

Stop trying to approximate original INX artist rig layering through a
DIY alpha-blending engine. Next compare directly against the **official
Inochi2D/Inox2D renderer and actual INX ArtMesh binding**, extracting
rest mesh positions, texture UVs, parameter keyframes, local transforms and
per-part masking. The 5.01 MAE source replay is a good baseline but not
native runtime parity. After obtaining a native head-rotation reference,
add one separately licensed side-view painting or controlled generated
profile view with explicit contour registration and validate 0°/15°/30°/45°
with all novel-view frames inspected.

Binary previews in DRAFT Releases only; no main-repo changes.

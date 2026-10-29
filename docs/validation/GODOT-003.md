# GODOT-003 — Independent visual audit and full-body nod proof

Date: 2026-10-29
Repo: `tims-SP/koma-motion-lab`
Target model: `myssal/Reverse-1999-CN-Asset/live2d/roles/301003_x`
Status: **PASS — full-body playback framing & video; NOT CERTIFIED — official Cubism parity**

## Provenance

- Source model: authentic `301003_x.moc3` with original texture atlas and `b_diantou.motion3.json` original curve points/time/interpolation.
- Motion3 `Meta.TotalPointCount` and `Meta.TotalSegmentCount` were corrected **in CI's transient copy only**, as documented in `GODOT-002.md`.
- Godot 4.7.2 stable, GDCubism v0.9.1, PurismCore v5, CubismNativeFramework 5-r.1, Xvfb and Mesa llvmpipe.
- No 3D replacement, AI-generated portrait or re-rigging was used in any of the visual evidence.
- No game artwork, video or binaries are committed to Git.

## What failed in the previous successful movie

Run 75 produced real images but independent visual review revealed **the character's face and head were outside the camera**. The original crop-based auto-framing algorithm zoomed around already visible legs, not the full model extent. Runtime checks and temporal pixel delta alone therefore overstated usefulness.

- [Run 75](https://github.com/tims-SP/koma-motion-lab/actions/runs/40818255083): rendered real character and motion; **FAIL human visual framing**.
- Diagnostic static/dynamic images showed head outside viewport, the character bounding box touching both top and bottom edges, and only 39–40% of visible foreground belonging to the largest connected region. Fragmentation is not conclusive proof of mask corruption (thin ropes and disconnected clothing pieces also contribute).

## Real nine-camera sweep

[Run 81](https://github.com/tims-SP/koma-motion-lab/actions/runs/40818768162) rendered nine genuine 1-frame alternatives using zoom `0.85/1.0/1.15` and vertical position offsets `+180/+250/+320` from the base Godot pose. Geometry inspection and actual rendered contact sheet confirmed that `zoom 1.0`, `shift_y +180` or `+250` showed the complete head and body, while several larger/cropped offsets clipped boots or hair. A camera near the midpoint was selected for motion verification.

## Verified full-body nod movie

- [Run 84 — successful GitHub Actions](https://github.com/tims-SP/koma-motion-lab/actions/runs/40819030925)
- [Run 84 — owner-visible draft Release](https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-a86cc539116ceba7bcb5)
- Camera: `zoom = 1.0`, `position_y_offset = +210`, as applied to the real GDCubism model.
- Original `301003_x.moc3` with authentic point/segment curves: **loaded and played**.
- Independent same-camera static control: 8 frames; average frame delta = **0.0**.
- Animated result: **90 PNG frames**, encoded **960×540, 30 FPS, 3.0 seconds H.264 MP4**, decoded 90 frames with FFprobe.
- Character visible bounding box **[380, 40, 540, 488]** (subject fully within image, with 40px top margin and 52px bottom margin).
- Approximate visible-foreground coverage: **2.1%**. This is low primarily because the full standing character is relatively narrow in a wide 16:9 frame; it is NOT a fidelity percentage.
- Relative full-frame RGB means vs same-camera static control at frames 0,22,45,67,89: `[0,0.2455,0.2366,0.0730,0.0303]`.
- Subject-only rectangle RGB means vs static: `[0,1.7239,1.6617,0.5192,0.2171]`.
- `GODOT003_FULLBODY_VERIFICATION`: **PASS_FRAMED_CHARACTER_AND_VISIBLE_MOTION_NOT_PARITY**, zero verifier errors.
- Separate manual inspection of 0.0/0.6/1.0/1.4/2.0/2.8-second extracted frames found the head, clothing, hands and boots present with visible small head/face movement. No obvious mesh tearing in this limited inspection; this is NOT a formal mask/deformation proof.

## Remaining gates

1. **Official Cubism reference-frame comparison** using the exact same MOC3, transient normalized original motion, playback timestamps and transform; no official reference footage has been obtained or tested yet.
2. **Full-resolution face/coat/alpha mask review** at 1080p or higher with high-contrast background and UV/mesh inspection; 960×540 full-body footage cannot certify fine hair edges or alpha layering.
3. **Additional motions**: verify idle, blink/expression/physics, multiple longer animations, and ensure motion meta normalization is general and never silently drops curves.
4. **Rig generalization**: at least 3 different MOC3 models and multi-masked/draw-order edge cases before making engine-wide claims.
5. **Runtime validation**: test Godot + GDCubism with the official Live2D Core (where licensed and available) separately from PurismCore. Existing result is an open-compatible rendering path, not proof of official SDK equivalence.

## Decision

GODOT-003 removes the camera framing blocker and confirms that authentic Live2D artwork can be rendered as an entire standing figure and animated by its original motion in CPU-only Linux CI. Continue on the test branch. **Do not promote this as production-grade visual fidelity or merge it into `koma-motion` until reference comparison and multi-model tests pass.**

Game-derived preview assets are confined to a draft Release. CI artifacts are temporary inspection copies (one-day retention); no blobs in Git history.

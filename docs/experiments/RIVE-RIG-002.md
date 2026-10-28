# RIVE-RIG-002 — RGBA Image Mesh + Bone Skin Validation

Date: 2026-10-28. Runner: GitHub Actions ubuntu-24.04. Rive CLI: 1.8.0. No GUI, Editor, Rive account or third-party art used.

[Run #11 — full logs and artifacts](https://github.com/tims-SP/koma-motion-lab/actions/runs/40692278294)

## Procedure

- Generate an original 200x44 RGBA PNG strip inside Actions using only Python's standard library.
- Use `rive create` scaffold to ensure correct RML root and backboard.
- Attach `ImageAsset file="arm.png"` to the RML root.
- Add to artboard a two-bone chain `RootBone > Bone` and a skinned `Image > Mesh` with six `ContourMeshVertex`, six `Weight`, two `Tendon`, and `Skin`.
- Build/verify/inspect/screenshot four independent angle fixtures at 0°, 45°, 90°, and 135°.
- Decode raw pixels from the four headless 480x320 PNGs and reject blank or identical outputs.

## Results

| Gate | Result |
| --- | --- |
| Linux CLI install/headless | **PASS** |
| Synthetic image imported as ImageAsset | **PASS** |
| UV Mesh and per-vertex explicit Weight data | **PASS** |
| Rive compile and verify (four poses) | **PASS**; 0 errors/warnings |
| Rive inspect structure | **PASS**; includes Image, ImageAsset, Mesh, six ContourMeshVertex, six Weight, Skin, 2 Tendon, 2 bones; empty problems |
| Headless screenshots | **PASS** |
| Pixel raster difference | **PASS** (45° = 9,069; 90° = 10,127; 135° = 10,140 changed pixels relative to straight pose) |
| Automatic inference of joints/mesh/weights from arbitrary anime art | **NOT_TESTED** |
| Natural silhouette/joint appearance, clothing, full-character performance | **NOT_TESTED** |

**This validates the scripting interface for Image + Mesh + Skin. It is not yet an automatic character rigging demonstration.**

## Follow-up: RIVE-RIG-003

Replace the fixed six-vertex handcrafted fixture with a reproducible auto-mesh and auto-weight generator for a controlled PNG input, and separately assess the quality of inferred poses. For complex anime art, compare existing DWPose, mesh generation and weight diffusion solutions before authoring any general solution. Never equate simple geometric weights with production-grade anime skinning.

## Files

- [Image mesh experiment](../../scripts/rive_image_mesh.sh)
- [Pixel validation](../../scripts/assert_pose_pixels.py)
- [Unified Rive Actions workflow](../../.github/workflows/rive-rig-001.yml)
- [Full CI artifact](https://github.com/tims-SP/koma-motion-lab/actions/runs/40692278294/artifacts/12817133947)

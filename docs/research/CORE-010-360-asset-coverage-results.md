# CORE-010 · How far from real 360° Aka rotation?

**2026-10-30 · Local actual-art diagnostic rendered and visually inspected; CI geometry-only smoke independent.**

## Results summary

This round intentionally separated **(a) can 3D geometry rotate 360°?**, **(b) is painted skin actually available at the displayed surfaces?**, and **(c) does the result look like a high-quality anime character?** Confusing these three measures previously inflated apparent progress.

- True 3D XYZ ellipsoid ray/surface intersection, fixed character, orbiting camera 0°→360°, **120 encoded frames @24fps, 5s**. This is only a diagnostic proxy head ellipsoid, **not** original Inochi ArtMesh, not actual hair/fox-ear geometry, and does NOT replay INX or original PSD UV.
- Both real user-provided GPT 1254×1254 RGB composites passed as textures: generated frontal image + GPT three-quarter image. View camera for the second art provisionally **assumed +40°** (unmeasured). Front art in the local test is also GPT composite, **NOT official Aka PSD**.
- Actual pixel-space visibility masks came from CORE-009's 11 semantic visible-region PNG files. These masks are not complete underpainting, original PSD layers or native INX skin.
- The 3D renderer DOES NOT fill unknown surfaces with reflected/mirrored imagery or invented hair. Missing areas are clearly rendered with magenta/black checkerboard.
- MP4 encoding and post-encode FFmpeg extraction of frames at 0/45/90/135/180/225/270/315 passed. Direct visual inspection of the decoded contact sheet: extreme face distortion at front/side and **large missing back region**. **Character-quality QA: FAIL**.

## Actual generated-art projection diagnostics

| Orbit angle | Projected eligible current art on visible ellipsoid | MISSING |
|---:|---:|---:|
| 0° | 69.5% | 30.5% |
| 45° | 68.1% | 31.9% |
| 90° | 32.4% | 67.6% |
| 135° | 4.0% | 96.0% |
| 180° | 0.0% | **100.0%** |
| 225° | 0.0% | **100.0%** |
| 270° | 11.0% | 89.0% |
| 315° | 45.8% | 54.2% |

These figures are **projection/foreground diagnostic coverage within one assumed ellipsoid/camera configuration**, NOT the percentage of source original skin, not physical view-angle calibration, and **not usable anime artwork fraction**. Under a purely mathematical visibility upper-bound that ignores real image foreground alpha, coverage numbers are different; this expected difference is checked in a separate CI geometry-only script.

## Current 8-view 360-degree reference inventory

| Nominal yaw | Asset status | Main missing content |
|---:|---|---|
| 0° | Authentic official Aka PSD / full native INX front exists | Matching projection in a joint renderer |
| +45° | 1 user GPT three-quarter *candidate*, not measured or registered | Semantic independent hair/eyes, precise view calibration |
| +90° | **MISSING** | Exact same-character right profile; jaw, nose, near eye/ear, strand depth |
| +135° | **MISSING** | Rear-side head/hair, ear back, occlusion |
| 180° | **MISSING** | Back scalp, root directions, rear hair, back ears, neck |
| -135° | **MISSING** | Opposite rear-side with original left/right asymmetry |
| -90° | **MISSING** | Opposite true profile |
| -45° | **MISSING** | Opposite front three-quarter |

**Inventory conclusion:** 1 confirmed source-facing view, 1 provisional GPT 3/4 candidate, **6/8 nominal yaw anchor reference illustrations wholly missing**. Two raster composites do not imply 25% fully prepared rigging, and 360-degree art quality progress is NOT established. If 360° means FULL BODY, existing missing apparel/back/arms/pants/skirt/leg perspectives add an even larger independent asset scope.

## Engineering blockers before 360 degree anime-quality production

1. Generate **reference-constrained +90° and 180°** genuine Aka views with artwork identity and fixed-camera ortho alignment. Use the **actual original official Aka PSD PNG reference** as a native image-edit input, not text-only prompt. Continue -90°, ±135°, -45° after validating these.
2. Recover true semantic/art-layer masks for eyes, bangs, side hair, back hair, left/right fox ears and face, including occluded underpaint. The previous 11-color-spatial partitions recomposed pixels but FAILED real ArtMesh segmentation.
3. Map separately to **real original 76 Inochi ArtMesh source UV/node** from CORE-009 for original-front, and register view-specific new UVs for generated patches. The original source UV must not be destroyed.
4. Replace debug ellipsoid with actual head/ear/hair surfaces using real 3D occlusion; account for reverse direction. The shader must show no missing surface around a full 360° turn.
5. Reuse INX pose/blink and correct eye/hair overlap, then final 0-360° H264 video with human-direct image quality review at each 45° anchor AND halfway pose; no ghosting/pop/holes.
6. Independent official D SDK parity and production character style are separate gates; *no head-turn animation has passed a 360° art-quality check yet.*

## Tested/recorded artifacts

**Real local artifact files (conversation sandbox, NOT GitHub Release):**
- \`/mnt/data/core010/coverage_360_probe.py\` actual script using 2 GPT composited input raster files and CORE-009 masks.
- \`/mnt/data/core010/xyz_turn_360_DEBUG.mp4\` true XYZ ellipsoid projection, not actual Aka 360 skin.
- \`/mnt/data/core010/decoded_360_review.jpg\` 8 **decoded encoded MP4** views, inspected.
- \`/mnt/data/core010/view_coverage_audit.json\` actual RGB foreground projection metrics and SHA256.
- \`/mnt/data/core010/asset_coverage_360.png\` eight-angle inventory poster.
- \`/mnt/data/CORE010_360_coverage_debug_bundle.zip\` minimal reproducible package; user supplied source images remain referenced by source hash.

**GitHub branch:** \`feature/koma-25d-core-010\`, text/code-only.
- \`experiments/koma-25d-core/tools/coverage_geometry10.py\`: independent synthetic geometric visibility test. The CI check does **not** pretend it consumed user images.
- \`.github/workflows/koma-25d-core-010.yml\`: CI verifies no valid source behind the character and publishes a small JSON Draft Release.

## Mature research used

- [ModelSheetTo3D / Eurographics 2026](https://github.com/hjyoon02/ModelSheetTo3D): uses multiple orthographically calibrated views, separate decal masks, 3D base-mesh optimization and multi-view geometry/texturing. It explicitly needs source images from meaningful different views. Its full pipeline demands CUDA/Blender and is not a drop-in head-curve solution.
- [Inochi2D SDK](https://github.com/Inochi2D/inochi2d): native 2D deformation rig remains appropriate to preserve the original facing texture but does not supply missing 180° real-painted anatomy.
- [video-to-3d angle verified reconstruction](https://github.com/enwong93-sketch/video-to-3d): highlights angle calibration and opposing-view error checks.

**Do not claim:** that a rotating primitive or a synthetic CI smoke test proves full 360° anime production, or that the demo has complete Aka back/side skin.

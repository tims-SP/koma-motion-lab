# SPINE-RIVE-PROD-004 — Native weighted-mesh transfer proven

Date: 2026-10-29 (JST). Validation: [PROD-002 workflow run #27](https://github.com/tims-SP/koma-motion-lab/actions/runs/40772061444), **successful**. Source `myssal/Reverse-1999-CN-Asset` at `45e75248ba3b25053fd32e63ab13c2f9f54dd9df`. Character `300401_hongnujian` (红弩箭), Spine `4.2.36` room variant.

## Actual achievement

1. Read real Spine binary (`.skel`), decode via MIT-licensed `BastienGimbert/SkelToJson`.
2. Transfer **85** original bone nodes (plus Rive-only offset bones), **51** source mesh attachments, **27** originally weighted mesh attachments and **843** vertex/weight records into RML.
3. Retain source UVs and triangles for selected attachments, original texture atlas, and source `idle_room` rotation data for **81** bones.
4. Fix the blocking Rive native Skin/Tendon transparency issue: source Spine-world bind matrices are invalid for the newly constructed Rive bone hierarchy. Compute each **Rive-authored Bone's actual local rest-pose matrix** and use this for the corresponding `Tendon`.
5. Render 24 original-art-containing frames with native Rive Skin (24 distinct), then encode MP4 via FFmpeg on disposable GitHub Actions runner.

### Root-cause evidence

[Run #26](https://github.com/tims-SP/koma-motion-lab/actions/runs/40771775279) isolated the issue:

| Bind pose variant | Visible pixels at setup |
| --- | ---: |
| Original Spine-world matrix | 0 |
| Rive-native bone local bind matrix | 61,974 |
| Rive-native bind without group scaling | 15,485 |
| Isolated single source mesh, Rive-native bind | 17,992 |

[Run #27](https://github.com/tims-SP/koma-motion-lab/actions/runs/40772061444) integrated the fix: **PASS_SUBSET** (not merely static texture preview). Original source mesh output varied between 29,049–80,909 non-background pixels across its 24 frames. Private animation MP4 size: 287,494 bytes.

## Independent motion-baking route

`scripts/spine_baked_mesh_motion.py` builds a frame-specific Rive Mesh using the original Spine per-vertex bone weights and sampled original bone rotation. Independently renders all 24 frames without Rive Skin:

- 51 mesh slots; 27 originally weighted;
- 843 source-derived vertices;
- 23/23 sequential frame steps changed vertices;
- 24/24 Rive rendered frames were unique;
- private encoded MP4: 170,350 bytes.

This route is a deterministic fallback, **not** a reusable native Rive rig.

## Production readiness

**Working:** Original-game Spine 4.2 binary → decoded skeleton → native Rive 85-bone scene + selected textured Mesh and Skin; original source key sampling; Rive CLI headless frame/video export.

**Unverified/unsupported:** exact Spine 4.2 animation fidelity, IK/transform/path constraint results, runtime FFD timelines, attachment/skin switches, exact Bezier curve shape and rotation inheritance, remaining slots and frame-by-frame source-runtime parity. Real footage has not been reviewed for artistic quality.

**Security and rights:** upstream has no observed express license allowing redistribution of art. All original game images, derived RML/`.riv`, visual frames and source-art videos stay in runner temporary directories and are **not** uploaded to this public repository or downloadable artifacts. Action artifacts contain neutral skeleton debug videos and nonvisual reports only.

## Reproduction

- [CI workflow](../../.github/workflows/spine-to-rive-video.yml)
- [Spine binary parser front end](../../scripts/spine_binary_conversion.py)
- [Native weighted Rive converter](../../scripts/spine_textured_rive.py)
- [Skin bind matrix differential experiment](../../scripts/spine_skin_diagnostics.py)
- [Source weighted-vertex bake](../../scripts/spine_baked_mesh_motion.py)
- [Main successful run #27](https://github.com/tims-SP/koma-motion-lab/actions/runs/40772061444)

**Conclusion:** The real source's bones, mesh UVs, per-vertex weights and sampled animation rotations can be transferred into an executable native Rive scene, rather than merely extracting the game's static image. It is **a verified subset conversion**, not yet a complete high-fidelity production migration.

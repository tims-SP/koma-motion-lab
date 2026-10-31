# REVERSE1999-PROD-001 — Real game assets, production intake

Date: 2026-10-28. Source repository: https://github.com/myssal/Reverse-1999-CN-Asset (commit `45e75248ba3b25053fd32e63ab13c2f9f54dd9df`).

### Actual GitHub Actions result

[Production run #1](https://github.com/tims-SP/koma-motion-lab/actions/runs/40699614245) **PASS**.

The workflow was executed on `ubuntu-24.04` using actual downloaded game files, official Rive CLI and Python/Pillow. No Rive Editor was used.

- Source files live under an ephemeral `out/private-production/input` directory. The 33GB upstream repository was **not** cloned.
- `live2d/roles/300401_hongnujian/300401_hongnujian.model3.json` and `300401_hongnujian.moc3`: downloaded, config and MOC3 signature validated. 25 referenced motion files across 25 groups, 12 expression entries, 2 textures; actual idle/drink motion files were fetched and parsed.
- `roles/300401_hongnujian`: downloaded three .skel variants (fight, room, ui) and the .atlas/.png pair. Atlas contains 107 named regions.
- Atlas cropping succeeded for actual region `hnj_c_lian` (100×118).
- A new Rive .rml/.riv project with **real cropped game image**, `ImageAsset`, `Image`, `Mesh`, `ContourMeshVertex`, `Skin`, `Tendon`, `RootBone`, `Bone` and `Weight` was generated automatically.
- Rive CLI verify/build and screenshots at 0°, 50°, 100° passed. Generated raster pixels differ at each angle.
- No character art, original textures, .moc3, .skel, .riv derivative or game-derived screenshots were uploaded to public CI artifacts.

[Sanitized metadata-only artifact](https://github.com/tims-SP/koma-motion-lab/actions/runs/40699614245/artifacts/12821241750).

### Actual compatibility decision

| Source type | Native preservation | Conversion to Rive | Production path |
| --- | --- | --- | --- |
| Spine (.skel + .atlas + PNG) | Existing skin, meshes, constraints and animation data are available in native files (runtime rendering not yet executed) | Image atlas parts can be imported and re-skinned, **original Spine animation is not imported** | Use official Spine runtime if preserving original performance, or Rive for *new* rig/animation |
| Live2D Cubism (.moc3 + .model3.json + motion3 + textures) | Existing model and parameter-based motion available for official Cubism runtime (runtime rendering not yet executed) | No validated .moc3 → .riv converter | Use Cubism for original performance; Rive only after rebuilding rig |
| Static background / atlas PNG | Reusable as layered/image input | Can import as ImageAsset | Rive static scenes / camera / VFX |

### Non-negotiable production safety

This is a public GitHub test repository. The original upstream is a game asset dump and **contains no root LICENSE file granting redistribution**. Publicly readable content is not equivalent to copyright permission. Do not push game asset bytes, derived screenshots, exported animations, textures, or full .riv files containing this art here. Future reviewable video output should be stored only in a user-controlled **private** destination after rights checks. This lab commits only the adapter scripts and metadata/logs.

### Next production step (not another synthetic rig experiment)

Build a 5-10 second **full character** shot with the original idle/drink motion:
- Cubism native path for `b_idle.motion3.json` and `b_hejiu.motion3.json`, OR
- Spine native path for `300401_hongnujian_room.skel` with atlas and skeleton version-compatible official runtime;
- retain source actions where possible, add controlled camera and scene, inspect frame continuity.
- Production system should support `source_backend=spine|cubism|rive` and use Rive only when the agent needs a **new** rig that does not already exist.
- Neither original animation playback nor a finished short scene has been demonstrated by PROD-001. No claim of full character conversion.

Source installation/runtime licensing are **separate** from the upstream game's artwork copyright. Check official runtime terms before broader use.

### Reproduction

- [Workflow](../../.github/workflows/reverse1999-production.yml)
- [Production asset intake script](../../scripts/production_reverse1999.py)

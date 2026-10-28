# Reverse:1999 asset production intake — verified 2026-10-28

**Outcome: usable as source image/atlas assets in a no-Editor Rive adapter, but not as ready-made native Rive animation rigs.**

Upstream: [myssal/Reverse-1999-CN-Asset](https://github.com/myssal/Reverse-1999-CN-Asset) at immutable commit `45e75248ba3b25053fd32e63ab13c2f9f54dd9df`. The repository is very large; tests fetch specific files by HTTPS rather than cloning the full history/tree.

**Latest successful Action:** [PROD-001 #2](https://github.com/tims-SP/koma-motion-lab/actions/runs/40704832638). [Metadata/log evidence](https://github.com/tims-SP/koma-motion-lab/actions/runs/40704832638/artifacts/12821829969). The run executed on ubuntu-24.04 and had no GUI.

## Representative native source

Production test sample: `300401_hongnujian` (红弩箭). This sample is deliberately distinct from the earlier `300301_hujisheng` (槲寄生) directory inventory, which was *not* used in this production run.

| Original asset | Verified result |
| --- | --- |
| `roles/300401_hongnujian/*.atlas/*.png` | Can read texture atlas, 107 region definitions; can crop named face region |
| `roles/300401_hongnujian/*.{skel}` | Fight, room, UI binary files can be downloaded and pass nonempty integrity check |
| `live2d/roles/300401_hongnujian/*.model3.json` | Model manifest parses as Version 3 |
| `live2d/roles/300401_hongnujian/*.moc3` | Binary header is `MOC3` |
| Cubism motions/expressions | 25 motion group references, 12 expression entries, 2 texture references in model manifest |
| Atlas extracted sprite | `hnj_c_lian`, 100×118 cropped PNG exists in runner |
| Rive Image / Mesh / Skin | Newly authored, rigged, compiled and headlessly rendered at 0°, 50°, 100° |

## Verified Action checks

- `live2d_model3_valid`: **PASS**
- `cubism_core_binary_present`: **PASS**
- `spine_atlas_target_region_found`: **PASS**
- `spine_binary_files_present`: **PASS**
- `spine_atlas_crop`: **PASS**
- `rive_coded_mesh_renders`: **PASS**
- `rive_pose_images_differ`: **PASS**
- `rive_rasters_contain_actual_subject`: **PASS** (non-background pixels: 9043 at 0°, 8900 at 50°, 7048 at 100°)
- Native `.skel`/`.moc3` rig imported into Rive with original constraints/motions: **NOT IMPLEMENTED / NOT VERIFIED**

The Rive demo has one **real game sprite** as its image source. The bone chain, UV mesh and weights are **newly generated**, not an import of the source Spine skeleton or original source motion curves. Distinct pixels and nonblank screens prove textured mesh activity, not cinematic pose quality.

## Suitability for Koma Motion

| Intended use | Decision |
| --- | --- |
| Atlas sprite extraction and texture input to Rive | **Technically feasible** |
| Rive Agent generates its own deformation of extracted character parts | **Technically feasible, demonstrated on one part** |
| Existing Cubism `.motion3.json` for reference/analysis | **Metadata parse feasible; pose remapping needed** |
| Existing Spine `.skel` used directly as native Rive rig | **Not supported by this test** |
| Retain original complete Spine/Cubism motion quality | Prefer testing native dedicated runtimes rather than assuming Rive preserves their proprietary rigs |
| Full character, seating, reaching, reclining, prop handling | **Not demonstrated** |
| Redistribute character sprites/animations in a public repository or public review artifact | **No license grant established** |

## Production policy and rights

This is a third-party dump of game assets; GitHub availability does not establish permission to redistribute, license, or commercially reuse the game art. The upstream repository does not provide a root LICENSE and GitHub reports `license: null`.

The public `koma-motion-lab` workflow **does not upload** original images, `.skel`, `.moc3`, cropped derivative images, generated `.riv` files containing game art or rendered frames. They exist only on the temporary Actions runner. Only metadata, file hashes, command logs and results are uploaded.

For director-reviewable video output, use an appropriately permissioned private storage location or assets the user has rights to use. Do not turn on public screenshot/video artifacts without checking permissions.

## Reproduce

- [Production Action](../../.github/workflows/reverse1999-production.yml)
- [Actual source-to-Rive test code](../../scripts/production_reverse1999.py)
- [Successful Actions run, #2](https://github.com/tims-SP/koma-motion-lab/actions/runs/40704832638)

**Gate:** Real art ingestion → mesh build → output **PASS**. Full existing rig import / original motion reuse **NOT DONE**. Next production work is preserving actual character pose/art style with independently authored rig or rendering with the source-native player, not repeating Rive's CLI synthetic feature tests.

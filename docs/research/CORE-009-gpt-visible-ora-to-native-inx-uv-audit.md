# CORE-009 · User GPT art to genuine Aka ArtMesh mapping: executed QA

**Stage:** experimental. **Art merge: FAIL, source native UV export PASS.** Branch: `feature/koma-25d-core-009`, based on CORE-008; production `koma-motion` not changed.

## 1. Genuine source model (GitHub Actions SUCCESS)

Full official `Inochi2D/example-models/Aka.inx` pinned Git LFS SHA256 `dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f`, © seagetch CC BY 4.0. Parsed its actual `TRNSRTS\0` header, real textured hierarchical nodes, TEX_SECT and `mesh.verts`, `mesh.uvs`, `mesh.indices`, textures and node UUIDs. Original arrays not modified.

**Observed:** 76 texture ArtMesh nodes, 76 source textures, 100 total hierarchy nodes, 3,427 original vertices, 5,353 original mesh triangles. This is the full Aka example (including torso/arms/skirt), not the head-only tutorial. Some original UVs are negative or beyond 1.0 and must not be clamped.

Verified GitHub Actions: https://github.com/tims-SP/koma-motion-lab/actions/runs/40984994563

Exact original source vertex, triangle, texture-ID and UV arrays retained in `source_mesh_original.json` in owner-only Draft Release; no INX binary republished. Source exporter: `experiments/koma-25d-core/tools/export_native_uv9.py`.

## 2. GPT 1254×1254 pair segmentation (local, real image bytes)

User original uploaded GPT composites (NOT original PSD): `金色狐耳少女肖像.png` and `三分之四侧颜狐耳少女.png`. Both actually processed; original image files used as RGB truth.

Created **11 mutually exclusive VISIBLE-PIXEL classes per view**: each ear, back hair, front hair, both side hair views, face, both eye regions, neck, burgundy leaf. These are editable isolated RGBA PNG cutouts, and two OpenRaster `.ora` layered projects containing eleven layers each. Verified exact alpha coverage of visible foreground and recompared all outputs on each input background. Composite RGB MAE on 0–255 channel scale:

- generated-front: **0.344**
- generated-three-quarter: **0.369**

The result is strong **raster recomposition parity** but **weak actual semantic extraction**. Direct inspection of partition image and 11-component transparent gallery shows: frontal fringe incorrectly includes cheek/temple pixels, back-hair layer is mostly exhausted by other region ownership, some face/hair boundaries cut across drawn strands, eyes are cut by polygon not by exact eyelid contours, and not one component contains hidden backpainting. All parts should be labeled `VISIBLE_PIXEL_PARTITION_NOT_TRUE_LAYER`. No claim of precise or reversible PSD art-layer separation.

Local deliverables:
- `/mnt/data/core009/front_visible_layers.ora`
- `/mnt/data/core009/three_quarter_visible_layers.ora`
- `/mnt/data/core009/front_semantic_review.jpg`
- `/mnt/data/core009/three_quarter_semantic_review.jpg`
- `/mnt/data/core009/front_parts_gallery.jpg`
- `/mnt/data/core009/three_quarter_parts_gallery.jpg`
- `/mnt/data/core009/semantic_manifest.json`, scripts, source images and PNG layers in `/mnt/data/CORE009_GPT_visible_layers_and_QA.zip`.

Binary assets are **NOT in Git**; links provided via conversation sandbox. These local outputs have not been uploaded to a GitHub Draft Release.

## 3. Actual geometry-to-view bridge audit

The experiment automatically compared the 11 visible classes with exact source node names from the real 76-part native mesh inventory (see `experiments/koma-25d-core/config/core009-bridge-candidates.json`).

The one GPT 'face' region corresponds to multiple actual ArtMeshes (`Face`, `Nose`, `Lip`, `Mouth Inner`). Eye region maps to many layers for `Eyelid`, `Eyelash`, `White`, `Eyeball`, `Light`, plus shadows and masks. The same holds for front/side hair and lighting overlays. Therefore **one user image color partition ≠ one actual rigged native INX component**.

Left/right source node names can be anatomical, while generated candidate partitions are image-space L/R; this orientation remains unverified. As a result, bridge entries are `NAME_MATCH_CANDIDATES_ONLY`, with source UUIDs where present; `REGISTERED_GENERATED_VIEW_UV=false`.

## 4. QA and next gate

| Check | Verdict |
|---|---|
| Genuine Aka mesh/topology/UV and texture IDs extracted | PASS |
| GPT pair split into 11 visible masks per image | PASS, diagnostic |
| Pixel coverage / recompose without major blank regions | PASS (MAE < 0.37) |
| Correct original INX part identities incl. all overlay eyes/hair | FAIL / mapping candidates only |
| Parts contain true hidden hair/cheek artwork | FAIL |
| Native INX original ArtMesh UV to generated view correspondence | NOT IMPLEMENTED |
| Shallow 3D surface / continuous skin projection | NOT IMPLEMENTED |
| New CORE-009 2.75D encoded MP4 inspected | NOT GENERATED |

**Do not mistake ORA packaging for original PSD rigging or successful new-view UV skinned animation.**

Next concrete action should use original source raster/UV projections and the accepted generated view as dual-image constraints, followed by explicit local inpainting of missing occluded side hair and cheeks; map each overlay mesh individually and render real new-view video. A semantic segmentation pass with human/vector corrections is still necessary, not just palette thresholding.

No change to `tims-SP/koma-motion` main production.
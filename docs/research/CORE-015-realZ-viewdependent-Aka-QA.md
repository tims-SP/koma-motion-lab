# CORE-015 · Genuine Z-depth head proxy, view-dependent photo choice, actual MP4 QA

**Date: 2026-10-30 · local execution completed · ANIME ART QA: FAIL.**

## Why this changed course

CORE-014 moved two actual user images through a manual 2D TPS and visibility masks, but 45° and 135° predicted paintings ghosted badly. A new in-chat GPT image generation attempt for missing art AGAIN produced an infographic/multiview sheet, not independent accepted 45°/135° artworks. Rejected. No new view asset was silently counted.

Instead we reused established work:
- [Montage4D, Du et al. I3D 2018](https://research.google/pubs/montage4d-interactive-seamless-fusion-of-multiview-video-textures/): choose meaningful camera textures on a true geometric surface and reason about visibility/seam risk instead of blind pixel blending.
- [Texture Mapping for Cel Animation, Corrêa et al. SIGGRAPH 1998](https://gfx.cs.princeton.edu/gfx/pubs/Correa_1998_TMF/index.php): preserve hand-drawn style through reference-dependent 3D correspondence/contours.
- [Bunraku, Chen et al. 2026](https://arxiv.org/abs/2607.27348): mature direction for semantic alpha layers, occlusion completion, jointly deformed mesh, not adopted as executable in this run.

## Actual local assets consumed

Three genuine bytes from CORE-013 normalization (each 720×720), not substitute images:
1. \`norm0.png\`: official Aka PSD-derived original front (sha256 \`2bb2719541db6e72f977593054dd0e01f6c413ce59fe9c68e46d13ae0a4f48ab\`)
2. \`norm1.png\`: user GPT uncalibrated right profile (sha256 \`958057bfdc3814c302648f371335c321ee9c472a8ecadb0ac6e95aae5d29814b\`)
3. \`norm2.png\`: locally repaired GPT uncalibrated rear (sha256 \`48afe45d526f7e329607c5e5509f923002574a4caa573da6522349a4a0679abd\`)

Aka original author/rigger seagetch, CC BY 4.0; supplementary GPT art is AI-derived candidate.

## What actually ran

- New independent 3D geometries: \`head\` ellipsoid, overlaid \`hair\` shell, two tapered volumetric \`ear\` cones, and \`neck\` cylinder.
- **8,750 actual 3D vertices and 14,753 triangles in 5 separate mesh nodes**; \`core015_real3D_geometry_DEBUG.glb\` exported and loaded again using trimesh for mesh sanity.
- Software triangle rasterization with per-pixel **Z-buffer** using Numba. Camera circles the actual 3D proxy, so ears/hair/face occlude using **real 3D positions**, not merely front-to-back flat raster order.
- For each triangle/pixel, select one of 0/90/180 source raster projections based on proxy-surface facing angle and source-facing constraints. Source camera geometry is **approximate and not physically calibrated**. This avoids alpha-blending two complete eye or mouth images and demonstrates real Z-based texture source selection.
- 97-frame 24fps 520×560 H264 MP4 \`core015_true_zbuffer_multiview_DEBUG.mp4\`, SHA256 \`d9b68be6603590be5bcf442b8863528df7a1bf290e8ffad5d893418df04c8e80\`.
- A second 97-frame actually encoded MP4 \`core015_true_zbuffer_MISSING_HIGHLIGHT.mp4\`, SHA256 \`53494644043740491fa941c72d92c272d74ad4867174bd4493514a0551d64e5e\`, explicitly paints unsampled visible 3D surface pixels in magenta to expose underpainting failures.
- Both encoded videos independently decoded at frames \`0/12/24/36/48/60/72/84/96\`; contact sheets directly opened and visually inspected. Actual comparison JPEG across CORE014/CORE015 45° and 135° was also opened.

## Source coverage numbers, method-sensitive

| Nominal yaw | visible proxy geometry pixels | pixels with no valid art sample | missing fraction |
|---:|---:|---:|---:|
| 45° | 57,447 | 4,442 | 7.73% |
| 135° | 57,444 | 3,823 | 6.66% |

**NOT completion percentages.** The matte rule flags some actual near-white ear fur as empty, and wrongly projected non-white pixels are nevertheless counted as covered. A gap fraction as low as 0% would still **not** prove the original anime face and ear design is correct.

## Direct visual verdict

| Gate | Outcome |
|---|---|
| Independent 3D mesh positions, GLB, z-buffer, camera turn | PASS as technical proxy |
| MP4 produced/decoded, original texture sources genuinely sampled | PASS |
| Severe transparent double-eye crossfade compared to CORE014 | Reduced, but this is not full art parity |
| At 0° reproduce original PSD with same fidelity | FAIL (synthetic geometric approximation) |
| At 45° face profile and eye geometry | **FAIL:** too frontal, wrong cheek/eye proportions |
| At 90° fox ears | **FAIL:** cones become visibly narrow strips |
| At 135° hair/ear texture | **FAIL:** projection seams, malformed silhouette |
| Original full Aka native 76 INX ArtMeshes/UV/deformation data applied | NOT DONE |
| New 45°/135° source art created and approved | NO, imagegen generated only rejected sheet |
| 0–180° artist-quality animation | **FAIL** |
| 360° full model | NOT DEMONSTRATED |

**Important:** This is **a genuine 3D debug proxy**, not a real 3D reconstructed Aka character and not original INX/PSD UV binding. We never use the 8,750 proxy vertices to claim the 3,427 true original INX vertices are mapped or animated.

## Exact produced binaries in conversation sandbox, NOT in GitHub

- \`core015/CORE015_realZ_Aka_multiview_DIAGNOSTIC.zip\` (2.25 MB): input 720² source PNGs, both complete Python renderer scripts, 5-object GLB, final two MP4s, final decoded contact images, 45/135 source-view provenance masks, native debug QA JSON and README.
- \`core015/core015_true_zbuffer_multiview_DEBUG.mp4\`
- \`core015/core015_true_zbuffer_MISSING_HIGHLIGHT.mp4\`
- \`core015/decoded_real3d_contact.jpg\`, \`core015/decoded_missing_real3d_contact.jpg\`
- \`core015/core014_vs_core015_45_135.jpg\`
- \`core015/core015_real3D_geometry_DEBUG.glb\`

The Git repository remains **text only**. **The GitHub Actions policy regression is metadata-only and cannot claim to have run the local binary renderer.**

## Next stage (CORE-016)

The largest bottleneck is no longer a missing Z-buffer. Prioritize:
1. Replace cone proxy ears with separate **asymmetric ear panels** matching the source Aka drawing silhouette and real ear root, plus front/back fur images.
2. Use original actual INX \`Ear:: Left/Right\`, \`Face\`, \`Front Hair:: ...\`, \`Back Side:: Hair:: ...\` mesh identity and stored original UV instead of global texture projection.
3. Fix near-/far-eye contours by obtaining independently accepted real 45° painting or by native parameter shape constraints and **explicit** hidden cheek painting. Do not use whole-face alpha blends or low-resolution AI collage crops.
4. Register each per-view texture to exact original ArtMesh node and sample original UV/offsets without overwriting source front.
5. Re-run encoded video and compare direct facial/ear/hair quality at 0/45/90/135/180 and full interstices. Keep FAIL and Draft until successful.

**Production tims-SP/koma-motion untouched.**
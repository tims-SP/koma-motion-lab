# CORE-016 · Real original INX ear UV → experimental 3D ear thickness

**2026-10-30. Execution completed. ORIGINAL EAR UV/TEXTURE BRIDGE PASS; 180/360 ANIME QUALITY FAIL.**

## 1. Mature projects informing the test
- Inochi2D/Inox2D real INX format and OpenGL renderer: https://github.com/Inochi2D/inox2d — retains original parameter and texture binding semantics; upstream calls its Rust port experimental and incomplete for newer MeshGroups/animation.
- Igarashi et al, Teddy, SIGGRAPH 1999; existing implementation https://github.com/h3902340/tidy — inflation from artist-drawn 2D silhouettes is preferable to generic cones when front appearance matters.
- Yao et al, Front2Back, CVPR 2020 https://www.cs.ubc.ca/labs/imager/tr/2020/front2back/ — front/back silhouette cannot resolve occluded side structure or artwork on its own.

## 2. ACTUAL authentic source ear data validated in GitHub

The pinned FULL 17,731,911-byte Aka.inx downloaded and verified against original SHA256:
\`dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f\`.
Aka original art/rig: seagetch, CC BY 4.0. Extracted ORIGINAL ArtMesh vertices, UV, triangles and original RGBA TGA source ear skins; no LFS pointer mistaken as art.

| Original INX component | UUID | Vertices | Triangles | Original TGA size |
|---|---:|---:|---:|---|
| Ear:: Left | 3424078890 | **57** | **89** | 414×781 |
| Ear:: Right | 3453251657 | **59** | **93** | 334×840 |

Actual UVs include points **outside [0,1]**, e.g. original Left V min -0.0753, U max 1.0809; Right U min -0.1029, U max 1.1053. THEY MUST NOT BE CLAMPED OR REPLACED as convenient.

GitHub Actions [#41008791641](https://github.com/tims-SP/koma-motion-lab/actions/runs/41008791641) SUCCESS for source extraction and **actual GLB construction** from authentic front-ear original TGA + topology/UV (not a metadata-only check). [Owner-only draft artifact release](https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-462a2ab663003ddd65a7). Repro scripts: \`extract_native_ear16.py\`, \`build_native_ear_shell16.py\`; original source INX binary was NOT redistributed. Extractions independently inspected from actual contact JPEG in job logs.

## 3. Local video and 3D geometric comparison: source outline-aware inflation

Earlier CORE-015 proxy ear cones were replaced by two independent manually traced 2D silhouette-constrained, volumetric lofts. The front source 720×720 raster provides the actual ear boundary observations. Back/depth remain synthetic.

| At proxy mid ear height y=1.00 | CORE-015 cone | CORE-016 contour 3D |
|---|---:|---:|
| Projected width from 90° (per ear) | 28.60 px | **65.82 px** |
| Original head/ear quality at physical side | FAIL | **still FAIL** |

Both source views and geometry debug videos are ACTUAL generated 97-frame, 24fps H.264, Z-buffered. The H.264 1040×560 side-by-side comparison of CORE-015 vs CORE-016 was *independently decoded* at frames 0,12,24,36,48,60,72,84,96, then visually reviewed from \`CORE016_vs_CORE015_decoded_contact.jpg\`.

**Direct visual FAIL findings:** the new thickened ears no longer collapse to thin strips in profile, but their upper edges tear, white front ear fur is wrongly reprojected to side/rear, and ear volume sometimes becomes too wide. Hair and cheek errors from CORE-015 remain. No user-approved new 45°/135° art.

This source-traced loft is **not** native INX source mesh. It has 10,838 total vertices / 18,881 total triangles (5 synthetic 3D nodes), vs authentic Aka full INX 3,427 vertices / 5,353 triangles (76 2D parts).

## 4. Local authentic native UV/TGA 3D test — decisive milestone

Downloaded GH Action artifact \`CORE016-true-Aka-native-ear-UV-and-art\` into the conversation sandbox, containing exact original meshes, real TGA textures and unchanged original UVs.

Built \`CORE016_native_INX_EarArtMesh_uv_front_plus_DEBUG_volume.glb\` with:
- two actual original ear **front ArtMesh topologies and exact original UVs** sampling their original INX TGA textures (57/59 vertices; 89/93 triangles);
- separate synthetic 3D side-wall/back geometry **deliberately MAGENTA** where no original side/back ear skin exists;
- approximate SOURCE-IMAGE-BOUNDING-BOX mapping to world XY and experimental Z extrusion. This affine fit DOES NOT reproduce original native scene transformations or Head Yaw parameters and is NOT official 0° pixel parity.

The genuine native source UV/TGA was then applied in an actually encoded 97-frame, 24fps, **480×480** standalone ear turn video. Nine frames 0/12/24/36/48/60/72/84/96 decoded and visually inspected. The color-provenance metric (within this deliberately exposed ear volume, NOT whole-character paint coverage):

| Nominal yaw | Fraction of rendered visible ear volume shaded by original *front* native ear TGA/UV |
|---:|---:|
| 0° | 68.90% |
| 45° | 19.34% |
| 90° | 0.12% |
| 135° | 0% |
| 180° | 0% |

At 0° parts of synthetic side/back leak magenta into silhouette; this means the new shell is **NOT original front source pixel parity**. Metrics are proxy visibility fractions and say nothing about canonical physical angle or anime quality.

## 5. Final evidence and acceptance

Local downloadable conversation package \`core016/CORE016_originalUV_ear_thickness_FULL_QA.zip\`, **2.71 MB**, holds:
- exact 3 original input view PNGs and original native ear layer 2 PNGs / UV & triangle JSON;
- both 3D GLBs (source-front silhouette loft, and genuine native ear UV/TGA front + magenta back shell);
- two 97-frame encoded H.264 MP4s: original native ear UV provenance and comparison vs CORE-015, plus source volume animation;
- source Python, actual MP4 decoded contact sheets, per-ear 90° geometric widths and QA.

| Check | Status |
|---|---|
| Actual original 57/59 vertex mesh + UV + TGA extraction | PASS, Github CI |
| Real original UV/TGA source-front ear GLB construction | PASS, Github CI and separately local test |
| 3D ear thickness geometry, exported GLB and Z-buffer | PASS as proxy |
| 90° ear thin-sheet silhouette | **Improved numerically, still visual FAIL** |
| Official Inochi original face/world transform and HeadYaw pose replay | **NOT DONE** |
| New 45°/135° and original 180° painted side/back ear skin | **MISSING** |
| Full exact source 0° parity | **FAIL** |
| Anime quality 0–180°/360° video | **FAIL** |

## 6. Correct next phase

CORE-017: 1. Add the actual ear-mesh parenting transform (node hierarchy) and ArtMesh parameter bindings from Aka INX rather than manually affine source front bbox; establish native 0° reference parity. 2. Replace magenta missing side/back geometry only with accepted author-compatible view-specific paintings. 3. Use actual source separate front/back ear silhouettes and view-conditioned UV, keeping original front UV immutable. 4. Register eyes, bangs and rear hair parts one at a time, validate encoded 0/45/90/135/180 frames. 5. Keep production repo untouched and Draft open until artist-quality QA passes.

The evidence above is a real native **ear source UV subcomponent** demonstration, **NOT** a full-head 2.75D skin or 360° source asset completion.
# P15-31 · Native 13-role ArtMesh alpha interpolation replaces whole-frame crossfade

Executed 2026-11-11 via ChatGPT VPS Bridge Worker on target VPS, without Desktop Commander or GitHub Actions.

## Implemented

Replaced the P15-30 diagnostic *whole-frame crossfade* at the four 55°–65° intermediate angles with **per-semantic-role premultiplied RGBA interpolation** on 443×443 native ArtMesh layers.

- Five tracked P15-30 keyframes: 55°, 57.5°, 60°, 62.5°, 65°.
- Four additional midpoints: 56.25°, 58.75°, 61.25°, 63.75°.
- 13 independent ArtMesh layers per frame, including far eye, nose, hair, crossed-gold clip, face skin, and original clothes/body: **117 actual transparent 443×443 PNG files** saved under `private-assets/p15-31-per-role-vdd/`.
- Each intermediate layer uses **premultiplied-alpha source interpolation** of the corresponding neighboring P15-30 role keyframes. Once all roles are interpolated, the scene is composited by the P15-21 depth ordering on the native canvas and upscaled to 1024×1024.
- The eye and clip source layers are based on the P15-30 camera-tracked registered P0 originals; the eye still uses P15-29's **unapproved 2D nasal bridge proxy**.

**Five keyframes exactly reproduce P15-30 frames with zero changed pixels**, so the keyframe anchor-tracking corrections were not regressed.

## Measured results

| Metric | Value |
|---|---:|
| Frames | 9 |
| Native ArtMesh layers | 117 |
| New midpoint frames | 4 |
| Source keyframe error | 0 pixels |
| Minimum adjacent-frame Alpha IoU | 0.975401 |
| Maximum adjacent-frame mean channel delta | 4.20709 |

The new actual per-role intermediate images differ from P15-30 legacy full-frame RGB crossfades:

| Midpoint yaw | Pixels different from old whole-frame crossfade |
|---|---:|
| 56.25° | 57,877 |
| 58.75° | 58,451 |
| 61.25° | 59,751 |
| 63.75° | 76,500 |

This verifies the output is materially different from reusing whole-frame blending. These differences are **not quality scores**. Premultiplied-alpha blending improves part-layer compositing semantics but is still **image-level blend interpolation per ArtMesh layer**, *not* geometry-aware vertex mesh deformation or new 60° independent original-art painting.

## Actual verification

- 8 Python unit tests passed: 9-frame manifests, 117 source hashes and native image dimensions, keyframe pixel-exact regression, correct per-layer midpoint provenance, continuity bounds, visual review paths, no misleading final art/3D claims, ZIP integrity.
- Chromium 1440×900 desktop and 390×844 mobile: 18 angle/viewport interactions, 144 images loaded, zero browser errors.
- Offline visual review contains 9 interactive frames; each shows new full-frame role interpolation, old whole-frame crossfade, amplified RGB difference, and five independent source parts (far eye, gold hairclip, side hair, front hair, face).
- Private source artifact root: `experiments/gif-multiview-keyparts-mvp/private-assets/p15-31-per-role-vdd/`.
- Review: `private-assets/exports/p15-31-native-artmesh-review.zip`.
- Evidence: `evidence/p15-31-native-vdd-qa.json`, `evidence/p15-31-browser-qa.json`, `tasks.json`.

## Formal gates

**PASS — actual per-role ArtMesh 443px interpolation, native compositing and P15-30 keyframe exactness.**

**NOT PASSED — vertex/mesh VDD, 3D surface near/far occlusion, hairclip mounting to particular hair lock, independently painted P0 angle source and final Japanese anime line art.**

Production P15-21 `anatomy` baseline is unchanged. No new independently painted original semantic parts were created. The P15-31 outputs are experimental transparent candidates, not final art.

## Next P15-32

Move from per-role RGBA blending to *mesh/geometry driven* shape deformation: use semantic anchors to warp vertex positions or per-part source texture, then alpha composite. Start with far eye and crossed clip within 55°–65°, preserve source identity, and measure continuity and visual change against P15-31. Only promote when actual source-art quality and physical occlusion gates pass.

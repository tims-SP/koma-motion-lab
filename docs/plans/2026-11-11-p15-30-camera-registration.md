# P15-30 · Camera-anchor tracking of P0 eye and crossed gold hairclip

Executed on the target VPS via ChatGPT VPS Bridge Worker, without changing the formal P15-21 anatomy renderer.

## Root cause and implementation

P15-29 restored P0 original eye and hairpin pixels by inverting known P8 opacity fade. But the artwork had nearly static image-space centroids while the P15-12 camera anchors moved across 55–65 degrees.

P15-30 performs subpixel affine translation of recovered original assets using P15-12 2.5D registered camera anchors. The remote renderer uses OpenCV bilinear translation:
- Far eye tracks the relative iris-anchor displacement from 55 degrees. The eye alpha centroid is **not** identified with the iris center; vertical offset is preserved.
- Gold crossed hairpin is moved so its alpha centroid matches the registered hair-clip center. This is an engineering registration hypothesis, not proof of correct physical attachment to a particular lock of hair.
- Eye still uses the P15-29 **unapproved two-dimensional nasal-bridge proxy** for visibility.
- Other parts in the 13-role native ArtMesh stay unchanged. The formal production VDD is untouched.

| Angle | Hairpin centroid-to-anchor before (px) | After (px) | Eye relative anchor motion error (px) |
|---|---:|---:|---:|
| 55° | 12.9029 | 0.0169 | 0.0000 |
| 57.5° | 16.0756 | 0.0119 | 0.0056 |
| 60° | 19.3096 | 0.0160 | 0.0128 |
| 62.5° | 22.5849 | 0.0139 | 0.0128 |
| 65° | 25.8764 | 0.0153 | 0.0085 |

These are pixel-registration metrics, **not** measures of improved artistic quality. Candidate full-frame alpha IoU against P15-21 baseline ranges 0.996657–0.998389. The original P0 texture and identity source are reused, not independently repainted.

## Review assets

Five actual tracked keyframes, each with six diagnostic PNGs, compare original P15-21, eye-only correction, clip-only correction, both corrected, and individual transparent eye and clip.

Nine-frame timeline includes five tracked keyframes and four linearly crossfaded full-RGBA midpoint frames. These four are **diagnostic** and must not be misrepresented as per-role VDD. The captured adjacent frame mean channel differences range approximately 2.846–3.541. A lower mean frame difference does not prove animation quality.

Offline review: private-assets/exports/p15-30-tracked-review.zip.

## Verified

- 9/9 Python tests passed, including source and diagnostic hashes, real registered positioning, alpha retention, 9-frame review provenance, and archive integrity.
- Chromium desktop 1440x900 and mobile 390x844: ten keyframe viewport checks and 18 timeline interactions, 78 image loads, no errors.
- No production source or formal P15-21 VDD replaced; implementation, tests and evidence are committed to Git.

## Acceptance and next

**CAMERA TRACKING ENGINEERING PASS. ART, TRUE FACE OCCLUSION, HAIRPIN PHYSICAL SIDE AND GENUINE PER-ROLE VDD PENDING.**

The clip now follows its anchor to subpixel precision, but its front/back relation to individual hair strands remains unverified. The far-eye proxy is not a geometrically verified head surface. A proper independent original-art and per-role VDD pipeline is still required before visual promotion.

P15-31: use source-tracked ArtMesh rather than full-frame crossfade for in-between poses, validate P0 physical nose/eye occlusion, hairpin mounting to a specific hair lock and continuous anime line-art quality.

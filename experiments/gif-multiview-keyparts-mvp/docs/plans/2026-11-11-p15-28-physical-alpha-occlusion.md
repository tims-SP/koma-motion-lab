# P15-28 · Physical Alpha compositing prototype for far eye

2026-11-11 (UTC+08), executed on target VPS through ChatGPT VPS Bridge Worker.

## Implementation
- Five yaw frames: 55°, 57.5°, 60°, 62.5°, 65°.
- Re-composite the 13 source ArtMesh layers in their registered P15-21 depth order.
- Apply only existing front-hair and nose alpha masks to the far eye.
- Preserve complementary hidden eye pixels as separate transparent underpaint.
- No additional whole-eye opacity multiplier; source artwork and formal production VDD untouched.

## Measured outcome

| Yaw | Eye alpha remaining visible |
|---|---:|
| 55° | 91.837% |
| 57.5° | 90.838% |
| 60° | 90.197% |
| 62.5° | 89.575% |
| 65° | 84.625% |

Exact visible + hidden alpha partition error is zero before serialization. Only 332–363 pixels of the 443×443 complete composite change per angle because the registered occluders overlap only a small portion of the far eye.

## Important limitation
P15-21 eye input may already inherit upstream P8 HIDE_WINDOWS schedule. This stage does not reconstruct the un-faded original eye source; it merely avoids applying another whole-layer fade and performs source-alpha occlusion using existing front-hair and nose layers.

**Result: engineering compositing prototype passes; visual occlusion gate fails.** Existing source masks cover too little of the far eye. Do not claim this solves the eye visibility issue or add a guessed geometric mask. Recover pre-fade original P0 far-eye art and establish the actual face-surface visibility boundary using registered P0 3D/camera anchors or new approved independent key views.

## Validation
- Seven unit tests pass.
- Chromium desktop 1440×900 and mobile 390×844: 10 angle/viewport checks, 70 image loads, zero browser errors.
- Interactive offline HTML: private-assets/exports/p15-28-physical-occlusion-review.zip.

# P15-16 · P5 anchored physical identity and VDD continuity gate

2026-11-10; actual tests on VPS via ChatGPT VPS Bridge Worker.

## Completed

- Detected P15-15's opposite near/far assignment on the 45° PSD. P5 45° near eye and ear project on image-left; far eye projects on image-right.
- Corrected 45° physical near/far identity while preserving the exact original layer alpha/color pixel set.
- Created 39 role slots (0°,45°,77.5°); 0° is only inferred by continuity, 77.5° single-eye source remains unresolved.
- Tests: 3/3 passing. The 45° corrected identity has explicit source-hash and source-anchored checks.
- HTML review includes four corrected 45° eye/ear roles and five original VDD frames. Browser desktop and mobile: 9/9 images per view, zero errors.
- Archive: `private-assets/exports/p15-16-physical-eye-review.zip`.

## Existing P15-10 VDD alpha IoU per 2.5° step

| 55–57.5 | 57.5–60 | 60–62.5 | 62.5–65 |
| --- | --- | --- | --- |
| 0.93808 | **0.79097** | 0.94006 | 0.93804 |

This is an existing-frame diagnostic, **not** proof of an improved production renderer.

## Remaining blockers

- 0°/77.5° eye/ear near-far physical identity requires verified anchors, not a binary raster heuristic.
- No approved independent side hair, ahoge, 77.5° gold cross clip and far-eye hidden-paint art.
- PSD-covered pixels are not evidence of anatomically correct underpaint.
- 57.5°→60° remains a severe topology and frame-continuity failure. Do not certify or promote this animation into final VDD.

## Reproduce

```bash
/tmp/koma-p15-14-venv/bin/python experiments/gif-multiview-keyparts-mvp/scripts/p15_16_physical_identity.py
/tmp/koma-p15-14-venv/bin/python -m unittest experiments/gif-multiview-keyparts-mvp/scripts/test_p15_16_physical_identity.py
/tmp/koma-p15-14-venv/bin/python experiments/gif-multiview-keyparts-mvp/scripts/p15_16_review.py
```

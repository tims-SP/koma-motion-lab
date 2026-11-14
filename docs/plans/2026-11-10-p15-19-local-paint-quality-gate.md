# P15-19 · 55°–65° RGB texture, facial occlusion and hair clip review

2026-11-10, executed on the target VPS through ChatGPT VPS Bridge Worker.

## Source and method

- Character: `p0_character_001`.
- Source ArtMesh: P12 `anatomy` and `stroke-wide`, each 5 frames at 55°, 57.5°, 60°, 62.5°, 65°.
- P5 camera landmarks provide six crop centers: near eye, far eye, nose bridge, front hair, side hair, gold clip.
- 90 local RGBA crops: anatomy / stroke-wide / RGB delta ×4 for 5 frames × 6 regions.
- Compute local color-change pixels and edge disagreement between **two versions**, not a quality score.

## Representative edge disagreement

| Region | 57.5° | 60° | 65° |
| --- | ---: | ---: | ---: |
| Front hair | 47.485% | 48.890% | 66.026% |
| Gold clip landmark neighborhood | 30.588% | 43.652% | 69.231% |
| Near-eye landmark neighborhood | 36.826% | 27.437% | 55.372% |
| Side-hair landmark neighborhood | 0 | 0 | 0 |

P10 stroke-wide causes significant changes near face/front hair/clip landmarks, but no RGB difference in the sampled side-hair neighborhoods. Neither outcome establishes better art. P15-10 older renderer has zero far-eye and clip visible pixels at 60°–65°; **that does not measure visibility in this P12 renderer** and is flagged separately in the QA.

## Test results

- Six unit tests passed: source hashes, five-angle registry, image dimensions, 90 crop files, zero-art-admission check, older-arc visibility flags.
- Chromium 1440px desktop + 390px mobile: 10 view/angle checks, 180 loaded images, 0 page or request errors.
- Offline ZIP: `private-assets/exports/p15-19-quality-review.zip`; includes source hashes, HTML, 90 crops and screenshots.

## Decision

**Keep anatomy as engineering baseline; do not promote stroke-wide** until someone verifies actual eye/clip and hair appearance against approved P0 original art. The current work does not author independent eye, side hair, ahoge, cross-gold clip or hidden underpaint assets. Formal quality acceptance remains blocked.

## Reproduce

```bash
/tmp/koma-see-through-client-venv/bin/python experiments/gif-multiview-keyparts-mvp/scripts/p15_19_quality_region_audit.py
/tmp/koma-see-through-client-venv/bin/python experiments/gif-multiview-keyparts-mvp/scripts/p15_19_package_review.py
/tmp/koma-see-through-client-venv/bin/python -m unittest experiments/gif-multiview-keyparts-mvp/scripts/test_p15_19_quality_region_audit.py
node experiments/gif-multiview-keyparts-mvp/scripts/p15_19_browser_review.cjs
```

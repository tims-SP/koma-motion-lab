# P15-26 · Source-preserving local retouch after independent-part visual failure

2026-11-10. Executed through ChatGPT VPS Bridge Worker on target VPS.

## Decision / implementation

P15-25's wholesale painted side hair, far eye and ahoge failed visual quality: blocky panel over hair and shoulder, displaced enlarged far eye and loop-like thick ahoge. This stage rejects those replacements and uses the P15-21 original ArtMesh source textures as its only raster base.

- Five angles 55°, 57.5°, 60°, 62.5°, 65°; three local roles each = 15 retouched transparent PNG files.
- Side hair: very narrow pale-pink highlight clipped inside the source alpha. Original hair shape and silhouette retained.
- Ahoge: slight edge-alpha reduction while retaining the original strand shape.
- Far eye: subtle orientation-dependent alpha attenuation at nose-facing edge, original colors and eye location unchanged.
- For every angle the untouched 13-part native 443px composition reconstructs P15-21 exactly (zero pixel difference), and modified layers are composed on the same native 443px canvas before 1024px scaling.
- Five full-frame local-retouch diagnostics and offline HTML comparison produced, without modifying formal production VDD.

## Engineering QA

| Gate | Result |
|---|---|
| 15 local source-derived RGBA files | PASS |
| Original source SHA stored and checked | PASS |
| Five-angle source reconstruction | PASS, exact pixels |
| Modified vs baseline Alpha IoU | .99853, .998555, .998554, .998539, .999616 |
| Seven unit tests | PASS |
| Chromium desktop and mobile, 5 angles each | PASS, 60 images loaded / 0 errors |

Alpha IoU here is a *preservation* measure, not an artistic quality score.

## Actual visual review

60° three-way preview comparing P15-21 / P15-25 / P15-26 confirms P15-25's oversized flat side hair, extra-large far eye and thick looplike ahoge are no longer present in the P15-26 candidate. The candidate is very close to P15-21 original by design.

**Formal independent original art approval remains PENDING.** This stage does **not** independently paint side-hair / far-eye / ahoge views and does not verify hidden underpainting or full 360° art quality. It is a corrective engineering baseline, not completed original art.

## Reproduction

```bash
/tmp/koma-see-through-client-venv/bin/python experiments/gif-multiview-keyparts-mvp/scripts/p15_26_local_repair.py
/tmp/koma-see-through-client-venv/bin/python experiments/gif-multiview-keyparts-mvp/scripts/p15_26_review.py
/tmp/koma-see-through-client-venv/bin/python -m unittest experiments/gif-multiview-keyparts-mvp/scripts/test_p15_26_local_repair.py
node experiments/gif-multiview-keyparts-mvp/scripts/p15_26_browser.cjs
```

## Next

Produce real independently painted, transparent, identity-consistent side hair / eye and ahoge, with correct occlusion over 55°–65°. Use original P0 material and camera references; only promote after full-frame visual QA.

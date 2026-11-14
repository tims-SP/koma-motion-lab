# P15-15 native PSD to ArtMesh routing

Actual execution on VPS through ChatGPT VPS Bridge Worker, 2026-11-10.

## Verified engineering outputs

- Source: the three existing PSD files (0°, 45°, 77.5°), rather than any new ZeroGPU extraction.
- Original PSD: 39 RGBA layers; 50 layer-to-role component assignments; 39 output role slots.
- Reversible 2D split on iris/eye/ear source layers. Every split preserves the exact source RGBA pixels when reunited.
- Five automated tests verify source SHA, 13 role slots, native RGBA conservation, output PNG integrity, and non-acceptance of unpainted roles.
- HTML offline viewer tests: Chromium desktop + mobile, 6 views, 78 images loaded; no browser errors.
- Private ZIP: `private-assets/exports/p15-15-artmesh-review.zip`.

## Critical artistic limitations

- This is *not* identity-verified semantic painting. Even where all role slots exist, some roles are geometrically split or composites.
- 0° and 45° lack separately painted side hair/ahoge. 77.5° also lacks independently visible far eye / cross-gold clip in the original PSD.
- Eye and ear left/right assignment is a heuristic raster partition, not a verified 3D anchor identity. It requires manual or physical-anchor QA.
- Covered pixels from P15-14 are evidence of overlap, not correct hidden-paint underdrawing.
- Accepted painted layer count remains **zero** for P15-15.
- The 57.5°–60° high-quality interpolation gate remains unpassed; do not promote the current raster routing into the production VDD renderer.

## Reproduce

```bash
/tmp/koma-p15-14-venv/bin/python experiments/gif-multiview-keyparts-mvp/scripts/p15_15_role_route.py
/tmp/koma-p15-14-venv/bin/python -m unittest experiments/gif-multiview-keyparts-mvp/scripts/test_p15_15_role_route.py
/tmp/koma-p15-14-venv/bin/python experiments/gif-multiview-keyparts-mvp/scripts/p15_15_make_review.py
node experiments/gif-multiview-keyparts-mvp/scripts/p15_15_browser_review.cjs
```

## Next

1. Source-aware 3D anchor assignment for near/far eye and ear identities; validate visual direction.
2. Independent paint and underpaint for front/side hair, ahoge, clip and 77.5° far eye.
3. Recheck per-part visibility in HTML, then test 57.5°–60° on the existing VDD experiment.

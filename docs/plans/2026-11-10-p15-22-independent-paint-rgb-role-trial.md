# P15-22 · Independent painting RGB / derived ArtMesh alpha trials

Date: 2026-11-10. Executed on VPS via ChatGPT VPS Bridge Worker, no GitHub Actions.

## Newly attempted model generation

- Target: original P0 character `p0_character_001` at 60°.
- Qwen-Image-Edit-2511 Anime-V2: real API invocation, rejected: requested 120 seconds ZeroGPU with only 55 seconds remaining.
- FLUX.2 Klein Fast: real API invocation, independently rejected by same remaining quota, no image generated.
- The two attempted inference scripts and failure artifacts are persisted so future sessions know the actual limitation.
- No new 60° source-painting completion claim is permitted.

## Actual image candidates produced

Instead of inventing paint, this trial reuses two previously generated independent RGB paintings at 57.5° and 60° and P15-21 actual 13-role alpha images.
- 2 × 13 = 26 transparent RGBA 1024×1024 candidates.
- Every role's RGB source is the SHA-registered Qwen output, but its silhouette and transparency are inherited from P15-21 VDD, **not independently painted**.
- Original RGB and VDD source SHA-256 values, role hashes and composition SHA values are recorded in evidence.
- No new independent painted semantic role has been accepted.

## Geometry and white-background mismatch

| Angle | Painted foreground / source-derived alpha IoU | Ahoge possible white contamination | Clip possible white contamination |
|---|---:|---:|---:|
| 57.5° | .88356 | 26.377% | 16.474% |
| 60° | .87458 | 17.987% | 8.832% |

Ink-mask / non-ink ratios are heuristic indicators, not objective art quality scores.
The failure in source pose-to-mask alignment is sufficient to **block automatic promotion**.

## Tests and review

- 7 unit tests passed: identity, source hash, all 26 RGBA roles, preserved VDD alpha, visible RGB provenance, white-background risk, false-acceptance regression and archive validation.
- Chromium 1440px and 390px: 4 angle/viewport checks, 64 image loads, 0 errors.
- HTML review: side by side old independently painted RGB, derived-alpha composite, P15-21 baseline, all 13 semantic roles per angle, and white-background contamination indicators.
- Review artifact: `private-assets/exports/p15-22-painted-rgb-review.zip`; private artwork source remains outside git repository.

## Production acceptance

**FAIL for independent keypart source painting and hidden-underpaint art.**
This round delivered real candidate raster files, but not the full original-art quality gate.
P15-21 anatomy renderer remains the engineering baseline.

Next stage must use a model endpoint or account with sufficient inference quota, generate genuinely independent semantic component geometry at fixed camera anchors and paint previously occluded pixels. Validate against P0 canonical 0/45/90 identity and then test P12 scene before promotion.

## Reproduce

```bash
/tmp/koma-see-through-client-venv/bin/python experiments/gif-multiview-keyparts-mvp/scripts/p15_22_painted_rgb_candidates.py
/tmp/koma-see-through-client-venv/bin/python experiments/gif-multiview-keyparts-mvp/scripts/p15_22_package_review.py
/tmp/koma-see-through-client-venv/bin/python -m unittest experiments/gif-multiview-keyparts-mvp/scripts/test_p15_22_painted_rgb.py
node experiments/gif-multiview-keyparts-mvp/scripts/p15_22_browser_review.cjs
```

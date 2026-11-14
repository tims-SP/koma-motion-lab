# P15-27 · Five-angle far-eye and gold-clip pixel-depth occlusion audit

2026-11-11 (UTC+08), executed through ChatGPT VPS Bridge Worker on target VPS.

## Actual findings

Based on original P15-21 1024px ArtMesh RGBA layers at 55°,57.5°,60°,62.5°,65°:

| Angle | Far-eye genuinely visible alpha fraction after front hair + nose | Clip overlapping combined front/side hair |
|---|---:|---:|
| 55° | 91.649% | 95.733% |
| 57.5° | 90.618% | 95.978% |
| 60° | 89.996% | 96.225% |
| 62.5° | 89.375% | 96.520% |
| 65° | 84.505% | 96.695% |

**Eye issue:** previous decrease in far eye visibility largely comes from *whole-layer fading*, not location-specific occlusion behind nose or bangs. That is not sufficient physical occlusion.

**Correction of earlier inference:** overlap of gold clip with side hair alone was zero, but combined front hair / side hair overlap is 95.7%–96.7%. Thus the clip is *geometrically near hair*, not detached. Whether it is attached to the correct hair lock/physical side and properly occluded remains unverified.

## Reusable decomposition

Created, for each of five angles, seven transparent 1024×1024 RGBA diagnostic layers:
- complete original far-eye art (preserves occluded pixels)
- visible far-eye after near-layer hair + nose
- hidden far-eye paint / alpha coverage
- near-hair occluder
- nose occluder
- gold clip overlapping hair
- gold clip outside combined hair

The far-eye visible + hidden alpha exactly reconstructs source eye alpha, max numerical deviation ≤1.11e-16. This provides the actual underpaint preservation check but **does not create new independently painted underpaint**.

## Validation / guardrails

- 7 unit tests PASS, covering source identity, hashes and dimensions, exact partition, visibility trend, hair/clip partition, nonpromotion, archive.
- Chromium 1440 desktop + 390 mobile: 10 view/angle checks, 80 loaded images, 0 JS/network errors.
- Offline HTML review allows selecting five angles and comparing all eight images (including unmodified full frame).
- Bundle `private-assets/exports/p15-27-occlusion-review.zip`.
- Production P15-21 anatomy renderer and source art unchanged. Formal artistic approval FAIL/PENDING.

## Next

Do not add more arbitrary whole-eye fade. Create keyframe-specific near-bang and nose occlusion geometry with actual P0 facial alignment; verify face silhouette and physical clip lock attachment, then repaint any newly revealed hidden surfaces. New originals must be approved visually before production VDD.

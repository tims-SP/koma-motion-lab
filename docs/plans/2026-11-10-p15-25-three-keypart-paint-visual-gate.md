# P15-25 · Original source-derived style, three independently drawn components and real visual gate

Executed 2026-11-10 on VPS through ChatGPT VPS Bridge Worker.

## Actual work
- Read P15-24 source manifests, ArtMesh and camera-registered 55°–65° original character baseline.
- Added new procedural hand-authored transparent RGBA strokes for three semantic roles: side hair, single ahoge and far eye, five viewpoints (15 PNGs).
- Paint uses P0's mauve-pink and violet palette and P15-21 part placement guides but **not old Alpha pixels**. This is programmatically drawn art, **not** newly model-generated nor artist-approved anime original art.
- Retained the five independently drawn gold X-clips from P15-24, producing five four-role candidate composites and a standalone HTML comparing them against P15-21.
- All 5 native 443px baseline recompositions reproduce original P15-21 reference exactly: 0 pixel difference. Production VDD unchanged.
- Complete far-eye iris geometry was drawn, but true occlusion/hidden painting has **not** passed anatomical QA.

## Real visual inspection: FAIL

At 60° side-by-side rendered review, the new side hair looks like a broad angular block; the far eye is too large, outlined and spatially displaced, and the ahoge appears too thick/looplike compared with P0. These failures matter more than the tests. **None** of the 15 parts or the 5 four-role candidate composites should replace the production baseline.

| Role | 55° source-alpha IoU | 60° source-alpha IoU | 65° source-alpha IoU |
|---|---:|---:|---:|
| side hair | .64745 | .65031 | .70447 |
| ahoge | .20764 | .20164 | .19883 |
| far eye | .69208 | .69129 | .69035 |

This IoU is only a shape difference, not proof of quality.

Four-role composites versus original baseline alpha IoU: .93495, .93298, .93091, .92916, .93545.

## Engineering validation
- 6 unit tests passed: exact source identities, full RGBA roles and file hashes, genuine new alpha, unchanged baseline, nonpromotion and ZIP.
- Chromium 1440 desktop and 390 mobile, each 5 angles: 10 checks, 60 images loaded, zero JS/request errors.
- Offline HTML and 4-role asset review archive: `private-assets/exports/p15-25-four-role-review.zip`.
- QA: `evidence/p15-25-original-keypart-paint-qa.json`.

## Remaining blockers / P15-26
1. Use P0 reference-conditioned, part-specific actual painting or manual correction for slender single ahoge and coherent side-hair strands.
2. Far-eye redraw must match 60° smaller perspective, correct near/far anatomy and realistic occlusion behind nose/bangs. Hidden underpaint is not yet validated.
3. Compare five complete animated frames against P0 Hero and reject any new rogue outlines or isolated face shapes.
4. Admit art only on actual visual identity, silhouette and component overlap quality; never on alpha IoU alone.

The P15-21 anatomy baseline remains the reliable engineering source; keep these candidates isolated from production.

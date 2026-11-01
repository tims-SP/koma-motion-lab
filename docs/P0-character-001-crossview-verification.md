# P0 · Character 001 Cross-View Artwork Verification

Date: 2026-11-01  
Execution: current isolated ChatGPT container; static pixel analysis, SVG parsing, semantic registry inspection, local Chromium HTML interactions and independent visual sampling. No GitHub Actions QA was performed during this verification.

## Source and representation

- Canonical approved Hero SHA-256: `e95a4b694777f4dcd2e085b25b10d76058d65cd1f8c6ef46971caa8005cb7e54`. Its original bytes were unavailable to this local verification; identity-comparison requires the original.
- mcode artwork: sixteen discrete SVG design sources, which satisfy structural parsing but are independent design interpretations; four of the earlier views visibly have head/hair anatomy that differs from the approved character.
- ChatGPT artwork: four individual view PNGs (0°, 45°, 90°, 180°) and two individual organ PNGs (anatomical-left eye and profile nose). All six are RGBA with fully transparent corners.
- Four aligned 1600×1600 review canvases preserve **all nonzero-alpha source RGBA pixels exactly**. Only RGB in fully transparent source pixels is normalized during compositing. This provides inspection margins, not higher-resolution artwork or anatomical correspondence.

## Image metrics

| Image | Native dimensions | Native alpha≥32 margins L/T/R/B | Native 3% safe-margin gate | Tiny 1–9px alpha≥1 components |
| --- | --- | --- | --- | ---: |
| Front 0° | 1199×1312 | 60/8/61/0 | REVIEW | 582 |
| Right three-quarter 45° | 1312×1199 | 229/3/282/0 | REVIEW | 86 |
| Right profile 90° | 1312×1199 | 255/8/306/8 | REVIEW | 294 |
| Back 180° | 1312×1199 | 172/9/207/0 | REVIEW | 388 |
| Anatomical-left eye | 1536×1024 | 368/257/306/224 | PASS | 80 |
| Profile nose | 1536×1024 | 614/224/613/228 | PASS | 55 |

Very faint disconnected alpha islands require compositing and edge cleanup review. These counts include nearly transparent pixels and are not equivalent to visible holes at normal scale.

## Semantic, visual and source gates

- 18 semantic parts registered; 2 have independent ChatGPT PNG candidates, 10 have SVG design drafts, 8 still require source art.
- Parts registered to source Hero pixel coordinates: **0/18**.
- Parts with full per-view identity matching: **0/18**.
- Parts with verified view-dependent occlusion order: **0/18**.
- Production-approved independent key views: **0/4**.
- Front illustration: recognizable identity but differing hairpin design and facial/bow details versus approved Hero, and no hidden-region source layers.
- 45°: hairpin appears on screen-left although front hairpin is screen-right. Lock anatomical-left mapping and +yaw camera convention, then correct hairpin placement. Near-ear and eye size/projection lack matched landmarks; jacket crest is additional identity detail.
- 90°: eye remains unusually front-facing; ear size, nasal projection, ahoge silhouette and collar vary from the neighboring views.
- 180°: back hair-lock topology and clothing/hood registration remain independently invented.
- Isolated eye and nose: standalone transparent drawings, not measured Hero crops nor fully separated ArtMesh-ready sublayers. Concealed anatomy and stitching boundaries remain to be authored.

## Acceptance decision

Source/design experiments can continue; **P0 production source approval is pending**. Do not use render-code self-comparison, common canvas alignment, technically valid SVG, or alpha-only checks as proof of consistent identity or completed rigging layers.

## Next source gates

1. Acquire and hash-verify the approved Hero bytes; keep a single 0° source-of-truth.
2. Correct 45° hairpin anatomical side; register immutable organ IDs and same-person landmarks in the four key drawings.
3. Rework the 90° profile anatomy and its ear/nose/eye relationship, then reconcile 180° rear hair with the side view.
4. Produce truly independent RGBA layers with occluded anatomy filled; perform source-image reconstruction and alpha edge validation.
5. Reserve independently authored 20°/55°/82° views for downstream interpolation QA; validate with the local interactive HTML reviewer.

## Offline verification artifacts

The offline delivery includes `P0_deep_review.html`, `P0_crossview_verification.md`, `qa/deep_asset_audit.json`, `qa/deep_browser_qa.json`, local pixel-audit/build scripts, and actual Chromium screenshots. Browser interactions are verified via HTML injection (`page.set_content`) because this particular isolated Chromium blocks direct `file://` navigation by administrator policy. Image data and QA runs do not require external network requests.

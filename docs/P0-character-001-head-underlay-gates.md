# P0 · Head and facial underlay integrity gate

## Source and method
- Character 001 approved front artwork: `1000012009.png`, 1254×1254, RGBA.
- Layer extraction: See-through `seethrough_output.psd`, 768×768, 18 semantic layers.
- Evidence generated and inspected in the current isolated container (not on GitHub Actions):
  - `p0_hd_relayer/head_structural_review.jpg`
  - `p0_hd_relayer/head_structural_review.html`
  - `p0_hd_relayer/head_face_generated.png`
  - `p0_hd_relayer/head_face_source_visible.png`
  - `p0_hd_relayer/head_without_bangs.png`
  - `p0_hd_relayer/head_bangs_shifted.png`
  - `p0_hd_relayer/head_structural_audit.json`

## Findings
- The generated `face` underlay is a flat face-shaped base with a conspicuous pink bangs-shaped region in the forehead. It is exposed when front hair is hidden/moved and does not represent a clean continuous facial skin surface.
- Generated face pixels with alpha>32: 130,816. The separate source-visible face ownership layer contains 41,418 alpha>32 pixels; 89,398 generated-face pixels are not owned by the source-visible face label. This is NOT a direct count of hallucinated pixels because some may be occluded or misassigned.
- In forehead ROI x=450..810,y=178..440, 67,061 of 82,778 pixels match a conservative hair-pink color heuristic (81.01%). The visual isolated-face review independently shows the broad fake-bangs artifact. This heuristic is a review trigger, not a full segmentation truth.
- The back-hair model candidate contains a broadly flat-filled rear cap, whose hidden locks have not been independently authored or approved.
- The model's `front_hair` includes crown, bangs and strands in one mesh. A +42 px x / -25 px y offset exposes the underlying anatomical mismatch at the hairline; independent strand and scalp motion are not production-ready.
- The `layers_source_exact` partition has exact source compositing by construction: every original nontransparent pixel is assigned to precisely one layer, so combined RGBA equality cannot validate semantic layer identity, hidden anatomy, mesh-ready topology or order. Semantic failure must be measured separately.

## Source acceptance contract

| Gate | Check | Current |
| --- | --- | --- |
| A0 | Source native pixel preservation / round-trip compositing | pass at source-visible partition only |
| A1 | Independent head/face base has clean continuous skin underneath moveable bangs and eyes | fail |
| A2 | Coherent scalp / back hair geometry supports fringe removal/translation | requires repair |
| A3 | Hairline, crown, bangs, side locks, ahoge and clip are independently controllable and identity-matched | requires source preparation |
| A4 | Mouth/eyes/ears have original-space coordinates, stable semantic identity and plausible hidden portions | requires repair |
| A5 | Motion probe: lift bangs 25px and shift 42px without pink false-fringe, holes, broken seams or isolated strokes | fail |
| A6 | True 0°/±45°/±90° reference correspondence and final visual sign-off | pending source alignment |

## Production procedure
1. Treat See-through PSD as semantic *mask proposals and hidden-region candidates*, never as preapproved anime anatomy.
2. Freeze the original 1254px source reference and use the source pixels for visible areas.
3. Repair the facial underlay by masked inpainting while explicitly removing the bangs-shaped pigment and preserving the source facial proportions, face edge and eye/nose/mouth attachment points; keep original and generated pixels provenance-separated.
4. Establish a continuous scalp/back-hair cap with consistent silhouette before splitting bangs/strands/clip into independent layers.
5. Validate each head part *by itself* in checkerboard, against the source composition and with ±20–45px independent motion. Fail a layer if exposed content is anatomically implausible even when the complete static image matches perfectly.
6. Only after head source layers and full-view identity pass should ArtMesh/VDD binding begin. No full 3D proxy is a prerequisite.

Current status: `HEAD_UNDERLAY_REPAIR_REQUIRED`.

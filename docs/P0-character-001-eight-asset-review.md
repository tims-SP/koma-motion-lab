# P0 · Character 001 eight-asset source review

Verification environment: current isolated container (Pillow, NumPy, SciPy, headless Chromium). Input: the eight most recent 1254×1254 RGBA images produced for the approved pink-violet bob-haired character. Technical evaluation uses the original generated PNG files, rather than resized review previews.

## Source inventory and disposition

| Reference | Source title | Role | Result |
| --- | --- | --- | --- |
| 0° front | 紫罗兰眸的金徽少女.png | composite reference | reference candidate; identity and parts pending |
| 90° facing screen left | 粉紫短发少女侧颜肖像.png | composite reference | reference candidate; facial registration pending |
| 90° facing screen right | 粉紫短发少女侧身校服肖像.png | composite reference | reference candidate; clip and ear occlusion pending |
| 180° back | 粉紫短发校服少女背影.png | composite reference | reference candidate; rear hair topology pending |
| anatomical left eye | 紫粉虹彩的动漫左眼.png | organ study | usable concept; split inner layers |
| anatomical right eye | 紫粉渐变高光动漫右眼.png | organ study | usable concept; match identity and split layers |
| profile nose | 日系动漫风精致鼻部素材.png | organ study | redraw aligned to profile face |
| smiling mouth | 柔和微笑的动漫嘴唇.png | organ study | redraw aligned to main front mouth |

All eight images are genuine RGBA (not opaque black backgrounds) with zero-alpha corners. All four portraits terminate at the bottom canvas edge, so they are bust-layout references, not complete vertically deformable body assets. Alpha≥32 top margins are 1/8/8/1 px (front/facing left/facing right/back). No portrait meets a 3% native canvas margin on all sides; each can be re-centered to transparent canvas to improve review margins, but that does not recreate cut-off anatomy.

Approximate common-mask upper-hair color samples (not calibrated swatches): front #C57898, facing left #D484A7, facing right #D080A8, back #C47095. Side views appear cooler/brighter. The small weak-alpha saturated edge pixels require checker/light/dark background compositing before ArtMesh use; they must not be equated to visible artifacts without visual inspection.

## Character consistency

The X-shaped golden hairpin appears at front screen right, on the side exposed when the head faces screen right, and at back screen left. The reverse-facing profile has no visible clip. This is broadly compatible with a single anatomical side, but **its rear-view placement and occlusion need deliberate drawing/visibility gates**. Hair-lock topology, forehead/eye/nose/ear/chin landmarks and precise art-style identity were not registered to the approved Hero image pixels.

The standalone eyes are internally composite, not separated into eye white, iris, pupil, upper/lower lids, lashes and highlights. The isolated nose has a substantially exaggerated full skin wedge relative to the face's subtle anime-profile nose line. The isolated smiling mouth has a thick, glossy lip shape unlike the front's short, flat line. These two cannot currently be composited onto the face without reauthoring.

## Required next source assets

**P0 before 0°–90° head approval**
1. Identity lock against the exact approved Hero pixels; canonical color and accessory side-map.
2. Independent facing-left and facing-right 45° key illustrations, with stable feature IDs.
3. Inpainted continuous face/skin base behind bangs, eyes, nose and mouth per key view.
4. Segmented near/far hair groups: rear cap, back/side hair L/R, bangs, ear-front locks, ahoge, plus isolated X clip.
5. Separately editable anatomical left/right eyes, eyebrow L/R and ears L/R; lids/iris/pupil/highlights should be controllable individually.
6. Front/profile compatible small anime-style nose; closed/open mouth variations with interior, tongue and teeth; suitable joining seams.
7. Independent collar, ribbon, crest, neckline and hairclip occlusion semantics when upper body moves.
8. Per-angle landmark correspondence, source provenance, source reconstruction, compositing/alpha and fault-injection checks.

**P1 full 360°**
- Rear-oblique 135°/225° and additional independent evaluation angles to constrain side-to-back travel.
- Explicit rear hair visibility and head rotation identity continuity.

## Validation result

- PNG structure and real transparency: PASS (8/8).
- Multi-view concept references suitable for continued P0 authoring: 4 portraits.
- Standalone organ concept references suitable for continued refinement: 2 eyes.
- Directly riggable semantic layers: 0/8.
- Stable per-view anatomical landmark and hidden-area registration: pending.
- Formal approved-Hero identity correspondence: pending.
- Standalone offline HTML browser review: PASS for image selection, dark background, zoom, human verdict JSON export and 390px responsive layout. No external requests or uncaught browser errors.

Acceptance state: `P0_SOURCE_AUTHORING_IN_PROGRESS`. Current composite artwork and organ studies are references for constructing true independent layers, not final ArtMesh inputs.

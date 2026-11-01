# P0 · Character 001 AI artwork source stage

Recorded: 2026-11-01

## Identity
- Approved character: `p0_character_001`; pink-violet neck-length bob, one curved ahoge, anatomical-left crossed golden hairpins, violet-pink eyes, navy jacket with gold trim, white shirt and burgundy bow.
- Original Hero reference SHA-256: `e95a4b694777f4dcd2e085b25b10d76058d65cd1f8c6ef46971caa8005cb7e54`.
- Approved Hero bytes are maintained independently from generated source drafts. Its SHA is the identity gate.

## Source artwork and local validation
- 14 individual original vector design files (four views, 10 anatomical components) from mcode: local container SVG/Alpha technical checks **14/14**.
- 2 new atomic mcode design SVGs (right profile nose, anatomical-left eye) in `experiments/p0-assets/design-atomic-v2/`: local container SVG/Alpha technical checks **2/2**.
- 6 ChatGPT-generated independent RGBA candidate images: front, right 45°, right 90°, back, isolated left eye, isolated profile nose. All six have true zero-alpha corners; initial native-crop margin checks **3/6**, and 4 view candidates have been placed losslessly on 1600×1600 transparent review canvases, **4/4** safe-margin technical checks.
- Standalone HTML review contains 20 single-artwork transparent previews. Local Chromium DOM asset switching checks passed, with zero external requests and zero page exceptions. Reviewer SHA-256: `14a4800ead868846a4fe8ad1693bda7a21412966e824d845edc977e2d02f2463`.

## Visual approval and continuation
- Authoring provenance is explicit: remote mcode generates designs; ChatGPT generates transparent image candidates; the current isolated container runs technical QA.
- Independent view identity and anatomy require final comparison against approved Hero. The 45° crossed-hairpin projection, 90° facial proportions and rear-hair correspondence require human source-level inspection.
- Current state: `DESIGN_REFERENCE` for mcode illustrations, `RGBA_CANDIDATE` for ChatGPT images, `IDENTITY_APPROVAL_PENDING` for the 4 independent views and original organ mappings.
- Production approval requires view registration to the approved source and anatomically complete layered source material; technical transparency alone is not production signoff.

## Delivery
- Source SVG and JSON metadata tracked in Git under `experiments/p0-assets/`.
- Full-resolution images, aligned review canvases, local QA reports, browser review and generated thumbnails are delivered together as a downloadable artifact package; Git repository retains textual metadata.

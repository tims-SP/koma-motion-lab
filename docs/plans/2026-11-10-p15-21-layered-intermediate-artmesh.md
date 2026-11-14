# P15-21 · Five-angle editable source-derived ArtMesh

Executed 2026-11-10 via ChatGPT VPS Bridge Worker.

## Implementation
- Fixed P8 hardcoded layer-export angles. P12 anatomy now outputs middle-view semantic layers for 55°, 57.5°, 60°, 62.5°, 65°.
- 13 semantic roles per angle: 65 separate editable RGBA PNGs at 1024x1024; 60 nonempty, 5 intentional transparent far-ear roles.
- P8 works at 443x443 internally. A second native copy is kept for exact roundtrip QA. All five reconstructed full frames match P12 reference exactly, max pixel delta 0, and source frame SHA matches P15-17.
- Hidden-area pixel counts recorded, but no artistic quality signoff. Source-derived deformation is not independent hand-painted middle-angle artwork.
- Eye far and cross-gold clip fade as their alpha weights decrease; this is not proof of correct anatomical occlusion.

## Verified acceptance
- 8 Python tests passed (roles, hashes, 443 and 1024 dimensions, exact reconstruction, hidden-role and visibility checks).
- Chromium desktop and mobile: 10 angle/viewport checks, 140 image loads, 6 actual toggle interactions, zero errors.
- Interactive HTML archive: private-assets/exports/p15-21-layered-review.zip.

## Next
Independently paint middle-angle side hair, ahoge, gold cross clip and far-eye/hidden contours using these layers as reference; preserve P0 identity. Approve color, strand directions, shape, occlusion and continuous VDD visually. Do not promote current source-derived textures as independent art.

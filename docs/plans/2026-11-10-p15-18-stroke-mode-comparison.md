# P15-18 · P10 stroke correspondence mode comparison

2026-11-10, target VPS execution through ChatGPT VPS Bridge Worker.

## Shared input

- Character `p0_character_001`
- P8 original RGBA ArtMeshes: 39 layers
- P5 anatomical anchors and P11 real profile PSD
- Five frames: 55°, 57.5°, 60°, 62.5°, 65°
- 22 registered valid pairs

## Mode comparison

| Mode | Stroke anchors used | Adjacent alpha IoU | RGB result vs anatomy |
|---|---:|---|---|
| anatomy | 0 | .97511, .97407, .97323, .96316 | baseline |
| anatomy-strokes | 9 | identical | **0 changed pixels** |
| stroke-wide | 12 | .97451, .97339, .97253, .95997 | 55,255–80,478 changed pixels per frame |

## Decision

- `anatomy-strokes` is a no-op for rendered output despite 9 candidate anchors; do not retain it as a separate production mode.
- `stroke-wide` changes RGB over visible hair/part regions, while preserving alpha IoU above .95. This is a visual candidate only, not an automatic improvement. Inspect hair strand direction, clip edges, facial occlusion and source texture before selection.
- Keep `anatomy` as the current engineering baseline until stroke-wide passes art QA.
- No independent new paintings or hidden underpainting were approved.

## Browser and tests

- 6 unit tests passed.
- Desktop and mobile Chromium each loaded all 15 comparison images; zero page errors.
- Offline review archive: `private-assets/exports/p15-18-mode-comparison.zip`.

## Next

Visual review of stroke-wide RGB changes, especially side hair and clip boundary. Reject if it introduces cross-strand smearing, doubled contours or texture drift.

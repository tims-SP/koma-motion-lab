# P15-20 · Canonical P0 ArtMesh source-layer recovery

2026-11-10. Executed on target VPS through ChatGPT VPS Bridge Worker.

## Finding

P15-16 physical identity extraction was not a reliable completeness source. Its generated 768px role files contained zero-alpha `hair.side` and `hair.ahoge` at yaw 0 and 45, despite original P1/P2 manifests having full source parts. P15-16 output is retained as historical evidence; this canonical recovery supersedes it for source completeness.

## Recovered source assets

Copied byte-exact from original P1/P2 ArtMesh manifests:

- yaw 0: `private-assets/p1-front/parts.json`
- yaw 45 and 90: `private-assets/p2-views/parts.json`

39 files, 13 semantic parts per view, all 1024×1024 RGBA. No new artwork, geometric transform, mirror, interpolation, or generated fill was applied.

| Role | 0° alpha pixels | 45° alpha pixels | 90° alpha pixels |
|---|---:|---:|---:|
| hair.side | 100,588 | 77,087 | 105,938 |
| hair.ahoge | 6,862 | 10,984 | 9,333 |
| hair.clip.cross_gold | 4,856 | 3,277 | 0 |
| eye.far | 15,577 | 16,471 | 0 |

At 90°, far eye, far ear and gold clip are zero-alpha because their source manifest marks them hidden. This is expected occlusion, not missing source art.

## Validation

- Every copy checked against source file SHA-256 and any hash recorded by its source manifest.
- 6 unit tests passed: semantic registry, byte-exact provenance, RGBA dimensions, required side-hair/ahoge/clip source coverage, expected 90° hidden slots, no false art signoff.
- Chromium: 1440px desktop and 390px mobile each loaded 39/39 images; total 78 image loads, zero browser errors.
- Offline review archive includes 39 source layers, contact sheet, HTML viewer and QA.

## Status / decision

Source completeness for the original 0°/45°/90° views is restored. This does not create missing intermediate-angle original paintings and does not grant artistic approval. Continue using original source assets as identity anchors. Intermediate 55°–77.5° independent component artwork and hidden underpaint still require separate review.

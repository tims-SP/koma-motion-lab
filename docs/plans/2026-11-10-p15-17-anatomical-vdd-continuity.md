# P15-17 · 55°–65° original ArtMesh anatomical VDD continuity

2026-11-10. Executed on the target VPS through ChatGPT VPS Bridge Worker.

## Source and renderer

- Character: `p0_character_001`
- Original P0 RGBA ArtMeshes: 39
- P5 anatomical anchors, P10 correspondence data and P11 real profile PSD verified by the P12 renderer.
- P12 anatomical mode; five frames at 55°, 57.5°, 60°, 62.5°, 65°.
- 22 registered valid source pairs.
- Output 1024×1024 RGBA frames. No newly invented/AI proxy painting was promoted.

## Continuity result

| Adjacent interval | Previous P15-10 proxy alpha IoU | P12 original-ArtMesh alpha IoU |
|---|---:|---:|
| 55°→57.5° | 0.93808 | 0.97511 |
| 57.5°→60° | **0.79097** | **0.97407** |
| 60°→62.5° | 0.94006 | 0.97323 |
| 62.5°→65° | 0.93804 | 0.96316 |

All four pairs exceed the engineering threshold 0.95. This resolves the previously observed *silhouette alpha discontinuity* for this five-frame source-ArtMesh diagnostic.

## Limits / not accepted

- Alpha IoU only measures silhouette/coverage continuity. It does not prove correct facial topology, iris position, hair strands, accessory identity, or source-texture continuity.
- No independent new side-hair / ahoge / far-eye / cross-gold clip painting was created or approved in this phase.
- Hidden underpainting artistic approval remains zero.
- Formal artistic acceptance remains pending. Do not mark the 360° character or full VDD MVP complete.

## Reproduction

```bash
cd experiments/gif-multiview-keyparts-mvp/scripts
/tmp/koma-see-through-client-venv/bin/python p12_anatomical_vdd.py --root ../private-assets --out ../private-assets/p15-17-anatomical-5frame --mode anatomy --angles 55,57.5,60,62.5,65
cd ../../..
/tmp/koma-see-through-client-venv/bin/python -m unittest experiments/gif-multiview-keyparts-mvp/scripts/test_p15_17_anatomical_review.py
node experiments/gif-multiview-keyparts-mvp/scripts/p15_17_browser_review.cjs
```

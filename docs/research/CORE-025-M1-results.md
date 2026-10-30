# CORE-025 M1 — quantised stack return results

Scope: M1 (real-texture composite) re-run after the `composite_over_premult` source-stack fix.
All numbers below are copied verbatim from
`experiments/reference-factory/out/core025/assembly/qa.json` and `assembly.json`
produced by the foreground run of `prepare_core025.py`.

## Inputs

| Item | Value |
| --- | --- |
| PSD | `out/source/tutorial-aka.psd`, sha256 `979fa62702b25f8af25414637d9ba6c36cbc9eb03bfa0c454470c73bdf51e55e` (verified) |
| CORE-024 export | `out/core024/native-v2/native-export.json`, sha256 `d73fd462b980007305abaebaf909f9761f7af8feebb38092ad786495bae953c3` |
| Canvas | 1630 x 1630 |
| Layer count | 62 leaves (bottom-to-top, order 1 = bottom-most) |

Per-layer provenance: every one of the 62 layers records the raw CORE-024 PNG that was
pixel-compared against the SDK RGBA in `assembly.json → layers[i].raw_source_texture`
(relative `file` + `sha256`, `pixel_compared_against_sdk_rgba: true`). Same data is in
`config/core025-layer-contract.json → layers[i].raw_source_texture`.

## Composition maths (unchanged from the passing blend core)

The source stack keeps the correct premultiplied accumulation via
`composite_over_premult(Cb, Ab, cs_q, as_q, "NORMAL")`; the straight/premultiplied
distinction was **not** touched in this pass. Only metadata and QA layout changed.

## Texture provenance

- **51 NORMAL layers** keep their original RGB bytes unchanged (`rgb_unchanged_vs_raw_source: true`).
- **11 MULTIPLY layers** (orders 6, 12, 14–20, 60, 61) have their RGB changed: baked to NORMAL
  `effective_source_rgb` against the default lower-layer backdrop, alpha preserved.
- All 62 layers keep their original alpha.
- The original PSD and the original CORE-024 layer PNGs remain the authoritative source of record.
  The `source` and `clean` texture sets are **DERIVED_REFERENCE**, not byte copies of the PSD.

## Alpha clip (clean variant)

9 shadow layers are alpha-clipped to their base layer (`alpha *= alpha_base`, full-canvas aligned),
recorded in `assembly.json → clean_shadow_alpha_clip`. Example (order 6 "Back Side Hair Shadow"
over base order 5 "Back Side Hair"): 183,966 of 946,467 layer pixels changed, alpha sum
126,869.28 → 70,415.12.

## Numeric gate — source

| Background | RGB MAE (0..255) | RGB MAE (0..1) | max single-channel err | fraction px > 16 | alpha MAE (0..255) |
| --- | --- | --- | --- | --- | --- |
| white | **0.125177** | 0.00049089 | 2 | 0.0 | **0.025776** |
| black | **0.144745** | 0.00056763 | 2 | 0.0 | **0.025776** |

Foreground pixels measured: 1,008,000. Thresholds: RGB MAE ≤ 0.5 and alpha MAE ≤ 0.5
(0.5/255 expressed in 0..255 units; **not relaxed**).

**source_composition_gate = PASS** (`exit_conditions.failures: []`).

## Numeric gate — clean (informational)

The clean variant is deliberately different from the PSD, so it is not expected to pass the
source gate; values are recorded for reference only.

| Background | RGB MAE (0..255) | max single-channel err | fraction px > 16 | alpha MAE (0..255) |
| --- | --- | --- | --- | --- |
| white | 4.763881 | 124 | 0.15198 | 9.02153 |
| black | 7.110746 | 194 | 0.15386 | 9.02153 |

## Gates summary

| Gate | Status |
| --- | --- |
| input verify (PSD sha, 62 leaves, CORE-024 pixel compare) | PASS |
| source composition gate (white/black/alpha MAE) | **PASS** |
| clean_visual_gate | **NOT_REVIEWED** — the supervisor reviews `shadow-cleanup-sheet.png` |
| blend unit tests (`tests/test_core025_blend.py`, 3 tests) | PASS (3/3) |

## Outputs

| File | sha256 |
| --- | --- |
| `out/core025/assembly/source/source-cpu.png` (1630x1630) | `4c2f0b1f6b241170b446848373b06c0d5195e9bc2f3bf0beee181f1e50fdbce7` |
| `out/core025/assembly/clean/clean-cpu.png` (1630x1630) | `81200b4c5715c95eae154c6878ec3f09b992d48e08202694ab7819e2a032e42b` |
| `out/core025/assembly/assembly.json` | `06ffade8399609b961dafb3c5c3bf6f3f185200b98d8ae06f30fed9603e65673` |
| `out/core025/assembly/comparison-sheet.png` | `1d5b63f7dc564d63d6b9deee509fd79ef183856581ac5ed1e7896a958a9f13e9` |
| `out/core025/assembly/shadow-cleanup-sheet.png` | `55cb7fcd423060dd6107911afd9a6dda76f5a10ef5a7fca972c246b73c6635e3` |

The 9-shadow contact sheet is laid out as **3 columns**; each group is a full 300 px
(source | clean) before/after pair with its own 46 px label band, so groups neither overlap
nor get clipped, and the image is pasted before the labels are drawn.

## Reproduction

```
cd experiments/reference-factory
python3 -m unittest tests.test_core025_blend -v   # 3 tests, OK
python3 prepare_core025.py                        # exit 0, source_composition_gate = PASS
```

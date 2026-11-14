# P15-23 · Authenticated new keypart generation and source-owned RGBA candidates

2026-11-10 · Execution via connected Hugging Face accounts and ChatGPT VPS Bridge Worker. No Remote Desktop Commander / GitHub Actions.

## Real model generation

Previously VPS anonymous ZeroGPU requests for Qwen-Image-Edit / FLUX.2 Klein had failed. This phase verified 4 connected Hugging Face accounts and used authenticated plugin calls to successfully generate five new model images:

- Qwen-Image-Fast: four independent source invocations for ahoge, side hair, far eye and cross-gold clip at nominal 60°
- FLUX.1 Schnell: a second gold crossed clip source for comparison
- Account identities, exact prompts, seeds, image SHA-256 and original WebP file provenance recorded in `evidence/p15-23-model-source-registry.json`

**Important finding:** all five source images failed the prompt's "one isolated part" requirement. They depict whole or partial anime heads, not standalone transparent components. The clip samples are on brown hair and do not match approved P0 character identity. The far-eye source looks like a larger near eye. No generated output automatically passes the P0 identity and anatomy gate.

## Actual transparent role candidates

P15-23 creates four **model-generated-source-derived** RGBA 1024×1024 candidates by selecting color/position regions from the new model images, then scaling/translating to P15-21 keypart bounding boxes. New part Alpha comes from the generated image's extracted pixels, **not P15-21 Alpha**. Source palette threshold and bbox were inspected; no copying of old semantic Alpha was permitted.

| Role | New-versus-VDD Alpha IoU | New part visible pixels |
|---|---:|---:|
| hair.ahoge | 0.33319 | 11970 |
| hair.side | 0.58047 | 114559 |
| eye.far | 0.38283 | 7383 |
| hair.clip.cross_gold | 0.22865 | 1473 |

Composite with four candidate roles at 60° versus prior P15-21 anatomy frame: **Alpha IoU 0.93605**, RGB-changed pixels **172993**. This is diagnostic only, not improved image-quality evidence.

## Formal acceptance

**Engineering export PASS, independent original ArtMesh painting FAIL.**

- Four generated source cutouts are real images and have independently extracted silhouettes; however, source models did not deliver one isolated semantic part per output.
- Color and shape of side hair/ahoge/eye/clip are not verified against registered P0 Hero or canonical 0°/45°/90° source, and some source images exhibit clear identity drift.
- No hidden underpainting has been created or accepted.
- Production VDD remains P15-21 anatomy mode, unchanged. No art was promoted.

## Reproduce and QA

```bash
/tmp/koma-see-through-client-venv/bin/python experiments/gif-multiview-keyparts-mvp/scripts/p15_23_source_registry.py
/tmp/koma-see-through-client-venv/bin/python experiments/gif-multiview-keyparts-mvp/scripts/p15_23_extract_new_source_components.py
/tmp/koma-see-through-client-venv/bin/python experiments/gif-multiview-keyparts-mvp/scripts/p15_23_package_review.py
/tmp/koma-see-through-client-venv/bin/python -m unittest experiments/gif-multiview-keyparts-mvp/scripts/test_p15_23_generated_parts.py
node experiments/gif-multiview-keyparts-mvp/scripts/p15_23_browser_review.cjs
```

- 7 Python regression tests (asset SHA, 4 roles, true independent mask pixel content, bbox, 1024 RGBA, nonpromotion and ZIP integrity).
- Chromium desktop and mobile, 8 role/viewport checks, 40 actual raster loads and zero JS/network errors.
- Offline HTML compares all raw generated sources, independently masked RGBA, registered role, and full 60° diagnostic composite to untouched baseline.
- Generated source media and review archive reside in `private-assets/` on VPS; source file hashes are committed to Git.

## Next

P15-24 must enforce actual one-part-only source painting, preferably from reference-conditioned generation and then transparent-layer segmentation with **P0-specific pixel identity validation**. Repair both far-eye occlusion and crossed clip physical side before VDD promotion. Do not treat improved masks or numerical IoU as artistic acceptance.

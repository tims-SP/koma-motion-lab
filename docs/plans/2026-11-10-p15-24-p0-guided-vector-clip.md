# P15-24 · P0-referenced crossed gold clip independent stroke candidate

2026-11-10 · Executed on target VPS via ChatGPT VPS Bridge Worker.

## P0-reference image-edit inference

- Source P0 45° canonical `hair.clip.cross_gold` and target 60° P15-21 semantic clip were packaged as image references (local crops, no public asset upload).
- Called authenticated Hugging Face Space Qwen-Image-Edit-2511-LoRAs-Fast via connected account with both source image data URIs, request for exactly one isolated crossed-gold hairclip at 60°.
- **Real inference rejected with `ZeroGPU quota exceeded`**; no new model-edited image exists. This is a compute/account quota restriction, not a claim that all image generation is impossible.

## Implemented alternative

- New programmatically authored cel-shaded vector strokes, using the approved 45° P0 clip's crossed-rod identity, orientation and warm gold/brown/purple outline palette as reference.
- Generated **five 1024×1024 transparent original-stroke clip candidates** at 55°, 57.5°, 60°, 62.5°, 65° with independent rounded-capped gold rods, bevel highlight and per-angle foreshortening.
- Clip alpha **is not copied from P15-21**. Alpha IoU with P15-21 old clip is 0.59570, 0.60459, 0.61393, 0.62493, 0.65820 respectively.
- At 60°, new transparent clip bbox follows the source clip registration, no extra characters or hair in the clip PNG.
- Composited candidate at each angle into existing 13-layer native ArtMesh, keeping other roles unchanged. Correctly composite at native P8 **443×443** first, then upscale full frame to 1024×1024. This exactly reproduces P15-21 baseline when the original clip is used: zero pixel differences on all five frames.
- Five candidate whole-frame compositing examples are **diagnostic artifacts**. Production anatomy renderer is unchanged.

## Validation

- Seven Python tests passed: five view manifest, SHA source identity, true independent RGBA alpha, exact baseline native recomposition, candidate files, nonpromotion and ZIP validity.
- Chromium on desktop and mobile: 10 view checks, 50 image loads, 0 page/network errors.
- 5-view interactive HTML comparing old clip, new clip, original whole-frame P15-21 and diagnostic 13-layer composition.
- ZIP: `private-assets/exports/p15-24-cross-clip-review.zip`.

## Artistic acceptance

**Pending / NOT accepted as final P0 original art.** This is independent **programmatic vector-stroke art**, not diffusion/artist-drawn P0 source. Appearance is plausible at isolated accessory level, but does not prove the hairpin's physically correct material side, occlusion behind bangs, hidden brush underpainting or 55°–65° animation art quality. No independent far-eye, side hair or ahoge paintings completed this stage.

## Next

1. Acquire reference-conditioned image-edit compute with available quota or use actual manually drawn source assets.
2. Produce original separated far-eye, side-hair and ahoge art and hidden underpainting at 55°–65°.
3. Use P15-24 vector clip as **reviewable alternative only**, then perform identity, overlap and moving-frame artistic QA before promoting any part to VDD.

## Reproduction

```bash
/tmp/koma-see-through-client-venv/bin/python experiments/gif-multiview-keyparts-mvp/scripts/p15_24_paint_cross_clip.py
/tmp/koma-see-through-client-venv/bin/python experiments/gif-multiview-keyparts-mvp/scripts/p15_24_package_review.py
/tmp/koma-see-through-client-venv/bin/python -m unittest experiments/gif-multiview-keyparts-mvp/scripts/test_p15_24_vector_clip.py
node experiments/gif-multiview-keyparts-mvp/scripts/p15_24_browser_review.cjs
```

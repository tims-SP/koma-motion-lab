# CORE-012: GPT 180-degree Aka rear view — actual generated image QA

Date: 2026-10-30. Result: **NEW SINGLE-VIEW REAR CANDIDATE CREATED; NOT PRODUCTION READY**.

## Verified actual source/outputs
- User-uploaded authentic Aka front: 1536x1536 RGB; SHA256 `edb4c6d78874c95cca8e6d0b8398be457b40ddcb7fb93bd5d5087e3b02f1b21d`.
- Existing GPT Aka-like 90-degree side candidate: 1254x1254 RGB; SHA256 `330a90c6819f6e74bcb5af33f9cca27441f9dedefae97d7371c4f5c6c7d25c81`.
- Actual generated first 180-degree back view: `a_clean_high_quality_anime_style_illustration_on.png`, 1254x1254 RGB; candidate rejected because burgundy leaf wrongly visible behind skull.
- Actual generated revised 180-degree back view: `a_clean_high_quality_anime_style_illustration_sho.png`, 1254x1254 RGB; SHA256 `5f016f460c5632366e5c1dfbfc74d33de79d93faa1d4b71a027ef5fc0ba0d965`.

## Direct visual QA of revised rear view
- PASS: exactly one back-facing head image, not a grid/montage. No eyes, nose, mouth, or face from behind.
- PASS: orange-gold hair, fox ears, dark-purple collar; frontal red leaf has been removed.
- NEEDS FIX: introduced a curled crown hair tuft (ahoge) not evident in the official original.
- NEEDS FIX: white inner ear fur remains visible from behind; backside fox-ear anatomy must be corrected.
- NEEDS CHECK: hair volume and ear-root silhouettes are not matched/registered across front, 90-degree side and 180-degree back.
- NOT IMPLEMENTED: 3D angular calibration, accurate per-part alpha, hidden painted hair/face patches, original INX ArtMesh/UV correspondence, actual 2.75D video.

## Real artifacts delivered locally
- Revised standalone generated 180 rear image: `/mnt/data/a_clean_high_quality_anime_style_illustration_sho.png`.
- Three-view front/90/rear direct QA contact: `/mnt/data/aka_front_side_back_review.png`.
- QA JSON `/mnt/data/aka_180_back_qa.json`.
- Binary outputs remain only in ChatGPT conversation files, not in GitHub text-only repository and not falsely claimed to be in a Draft Release.

**Status:** `GENERATED_REAR_SINGLE_VIEW_NEEDS_EDIT`; visible reference candidate, NOT a completed 180-degree production skin. Previous six missing anchor angles must not be translated into a production completion percentage.

Next: local anatomy corrections, exact visible/hide hair/ear part separation and source INX UV matching; only then continuous 360 video checks.

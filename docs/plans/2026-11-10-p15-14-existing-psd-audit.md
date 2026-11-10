# P15-14 Existing PSD audit and ArtMesh mapping

2026-11-10, executed via ChatGPT VPS Bridge Worker, branch
`feature/gif-multiview-p0-ingestion-20261105`.

## Results

- Real See-through invocation attempted via `p15_14_see_through_trial.py`;
  the backend rejected it: 180s required, only 115s anonymous ZeroGPU quota.
- Independently recovered three older PSDs in private assets (0°, 45°, 77.5°).
  They are **not** new model output from this attempt.
- Parsed and exported 39 native RGBA layers from 3 × 13-layer PSDs.
- Full-cover occlusion *pixel instances* in layer stack:
  0° 190043, 45° 195182, 77.5° 216911.
  This counts overlapping layer instances, not unique image pixels or visually validated underpaint.
- Source PSD and exported PNG SHA-256 values are recorded in
  `evidence/p15-14-existing-psd-mapping-qa.json`.
- Existing PSD semantics and the accepted P0 13-ID ArtMesh contract differ.
  Right/left eye and ear splitting, front/side hair, ahoge and cross-gold clip
  require review. **0/13 independently accepted mapping** at this stage.
- Source PSD composite and exported native layer previews remain private on VPS.

## Reproduce

```bash
/tmp/koma-p15-14-venv/bin/python experiments/gif-multiview-keyparts-mvp/scripts/p15_14_existing_psd_audit.py
/tmp/koma-p15-14-venv/bin/python -m unittest experiments/gif-multiview-keyparts-mvp/scripts/test_p15_14_existing_psd_audit.py
```

## Next acceptance

1. Inspect 45° native PSD composite against the registered 45° source, compare pixels after
   appropriate scaling/color handling; fail on unexplained artistic drift.
2. Split eye / ear / hair / gold clip into 13 stable semantic identities; record per-role hashes.
3. Evaluate exposed and occluded pixels separately with an HTML visual layer toggle.
4. Only after acceptance, wire hidden underpaint into ArtMesh/VDD renderer and retest 57.5°–60°.

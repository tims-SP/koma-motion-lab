# CORE-022 — Reference Factory first executed checkpoint

This is the first manual experiment after CORE-021 under ADR-003. The canonical
source is Aka by seagetch (CC BY 4.0); the generic structural reference is pixiv's
VRM1_Constraint_Twist_Sample under its embedded VRM Public License 1.0 conditions,
**not CC0 and not an Aka model**. The production repository is untouched.

Implemented and locally executed:

- SHA-256-verified original PSD/INX/VRM acquisition with pinned source revisions.
- Source PSD identity and 16 genuine PSD-part examples; exact reversible coordinate
  crop/resize/paste mapping. Original pixels remain in the PSD; resizing is lossy.
- Immutable native INX topology/UV hashes and node UUIDs for all 76 ArtMeshes.
- A versioned HEAD_ONLY, positive-yaw-to-image-right, orthographic camera and data
  color contract. Body meshes are explicitly excluded. Long hair continues below
  the head-camera bottom crop; this is not a full-hair silhouette reference.
- Real Three.js/VRM WebGL rendering at nine 0–180° anchors, each with beauty,
  binary silhouette, linear diagnostic depth, camera-space normal and exact
  source-part-ID maps. IDs are source Face/Hair groups, not inferred Aka semantics.
- Same-process repeat of every image plus a second independent browser-process
  repeat of all 45 PNG hashes. This proves determinism only in this environment.
- Actual 108-frame H.264 with nine held anchors (12 frames each), ffprobe validation,
  final-video decoding and direct contact-sheet review. No continuous-motion claim.
- Two manually executed built-in imagegen candidates: one A and one C pilot.
  Both failed requested canvas/margin gates; no Golden or hidden design approval.

## Reproduce structural evidence

```sh
cd experiments/reference-factory
python -m pip install -r requirements.txt
python prepare.py
npm ci
npx playwright install --with-deps chromium
npm run render
cp out/structure/manifest.json out/baseline-manifest.json
npm run render
python qa.py --baseline out/baseline-manifest.json
```

`out/structure/contact.jpg` and `out/decoded_contact.jpg` are direct-review sheets.
`out/qa.json`, `out/source_freeze.json`, `out/native_topology_index.json` and the
render manifest contain machine-readable evidence. Reruns do not regenerate AI
candidates. Preserve candidate original files and run `python audit_candidates.py`
only after restoring the actual matching files in `out/candidates/`.

## mcode collaboration

MiniMax Code 0.7.2 was installed in the Work environment via the official npm
package `@minimax-ai/code`. The user completed CN OAuth; a real model returned
`MCODE_AUTH_OK`. mcode is used for a read-only engineering review, with no account
credentials copied into the repository or workflow. The CLI installation/login
is specific to this Work environment; it is not assumed to exist in CI.

## Current limits and next gates

M0 source preparation is executed; full-front native runtime parity remains
NOT_TESTED. M1 has one generic VRM sample, not the planned multi-character bank.
M2 structural-render mechanics pass; the VRM has no fox ears and no source-to-Aka
shape registration. Its exact yaw is structure truth only for that VRM.
M3 automated decomposition benchmark, M4 full multi-candidate A/B/C/D comparison,
human-approved 90° design, five-view Aka set, per-view UV correspondence, shallow
3D shells, rig/IK and continuous Aka 360° remain open. Do not promote these
diagnostic renders into production character assets.

Source image generation prompts are versioned under `prompts/`; built-in tool model,
seed and request ID were not exposed and are explicitly recorded as unavailable.
Images/video/source binaries remain outside Git blobs and belong in owner-only
Draft Release evidence. Persistent archive ownership/retention beyond a draft
release and hermetic cross-machine pixel identity are separate unverified gates.

## CORE-023 Task A — deterministic candidate canonicalization

`canonicalize_candidates.py` is offline deterministic image processing (Pillow IO,
alpha compositing and BICUBIC resampling — no hand-written resampler). It is
**not** AI redrawing: it fits the ENTIRE source canvas into one canonical
1024x1024 opaque-white canvas with a uniform scale and letterboxing, using a
single affine source→canonical matrix and its exact inverse in an explicit
edge-coordinate domain (pixel index `i` has its center at `i+0.5`). No
foreground crop, no local warp, no inpainting, no redesign.

```sh
cd experiments/reference-factory
python -m unittest discover -s tests          # 23 unit tests
python canonicalize_candidates.py \
  --input-dir out --output-dir out/core023 \
  --config config/canonicalization-v2.json \
  --evidence-dir evidence/local-2026-10-30
```

- v2 (accepted algorithm) uses `config/canonicalization-v2.json`; the rejected v1
  config/code/outputs stay preserved under `out/core023/rejected-A1`.
- Every source mode (including indexed-color PNGs with tRNS transparency) is
  composited over opaque white before the RGB conversion.
- Resampling is Pillow's maintained `Image.transform` AFFINE + `BICUBIC`; the
  edge-domain inverse is passed verbatim (no extra half-pixel shift).
- Inputs are hash-verified against committed evidence. The identity hash
  authority is `evidence/local-2026-10-30/source_freeze.json` (`identity_sha256`);
  the mutable `out/identity/reference_manifest.json` is only consistency-checked
  and can never override the committed hash. Missing input, hash mismatch, blank
  candidate, invalid transform/config or insufficient resulting margin fail
  closed; no candidate is silently skipped.
- `canonicalize_file` refuses to write a derivative over its own source (same
  path or symlink) before any write happens.
- Outputs are new versioned derivatives only; original bytes are untouched:
  `out/core023/canonical/*-canonical-v2.png`, `out/core023/report.json`,
  `out/core023/contact_sheet.png`.
- The identity derivative is a `DERIVED_REFERENCE` over `SOURCE_TRUTH`; candidate
  art is never promoted.
- A framing PASS is a framing statement only. Anatomy / identity / angle / style
  stay `NOT_TESTED`, human approval stays `MANUAL_REVIEW_REQUIRED`, benchmark
  ranking stays `NONE_ACCEPTED`, the full A/B/C/D benchmark stays `NOT_TESTED`,
  and no APPROVED/GOLDEN state is written.

## CORE-025 — layered turn prototype: full recovery commands

[Clean-environment CI PASS](https://github.com/tims-SP/koma-motion-lab/actions/runs/41084893009)
at `c876100f6c0eea0623e3cbb60e06152b86d1b472`;
[Draft Release evidence](https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-38eb4ff6aa4c88363e39).
The artistic failure below remains in effect.

Current state: the numeric/structural chain is **PASS**, the **artistic head-turn
gate is FAIL** (the motion still reads as a shallow-surface sway, the face stays
too frontal and the facial silhouette perspective change is too weak), and
production remains **NOT_ACCEPTED**. The turn prototype is an inferred *open*
shallow surface driven to ±15° of head yaw, not an artistically approved head
turn. See the supervisor reports in `docs/research/` for the full verdicts.

### Recover from a clean checkout

```sh
cd experiments/reference-factory
sudo apt-get update && sudo apt-get install -y ffmpeg  # Linux: ffmpeg + ffprobe
python -m pip install -r requirements.txt      # pinned Python deps
npm ci --no-audit --no-fund                    # pinned npm lock
npx playwright install --with-deps chromium     # pinned Playwright browser
python prepare.py                              # pinned original sources
python native_layers.py                        # 62 native RGBA part layers
python prepare_core025.py                      # CORE-025 M1 layered assembly
node capture_core025.mjs --anchors             # CORE-025 M2 curved anchor captures
python verify_core025_supervisor.py            # CORE-025 M2 independent numeric acceptance
node capture_core025_video.mjs                 # CORE-025 M3 turntable capture
python verify_core025_video.py                 # CORE-025 M3 independent video acceptance
```

`verify_core025_supervisor.py` and `verify_core025_video.py` are the actual
acceptance entry points; there is no `qa_core025.py` or `qa_core025_video.py`
entry point in this repository.

### Who wrote what

- The CORE-025 scene, anchor capture and turntable capture programs
  (`core025.js`, `capture_core025.mjs`, `capture_core025_video.mjs`,
  `prepare_core025.py`) were implemented by **mcode**.
- The independent numeric acceptance scripts (`verify_core025_supervisor.py`,
  `verify_core025_video.py`) were written and run by the **Codex supervisor**;
  they are not mcode-authored.

### Notes

- Local model access and image-generation quota do **not** affect this
  deterministic source-based reproduction: the whole chain above is pinned
  source data plus offline geometry, browser rendering and `ffmpeg`. Reruns do
  not call any generation service, and the locally generated AI candidate C is
  **not** part of this chain or of the CI package.
- The default-pose multiply→normal baking of the layered parts is a per-part
  approximation valid only in the default pose; baked shadow/occlusion
  correctness under new rotations is not guaranteed.
- New-view assets are still incomplete. Side, back and 360° views, the global
  closed UV set, bone skinning and IK, and the original Inochi runtime remain
  unaccepted.
- Machine-readable evidence lives in `out/core025/` (`assembly/qa.json`,
  `render/manifest.json`, `render/supervisor-qa.json`,
  `turntable/video-manifest.json`, `turntable/video-qa.json`). Generated media
  (PNGs, video, textures) stays out of Git and goes to the owner-only Draft
  Release archive `CORE025-layered-turn-evidence.zip`.
- A numeric PASS on the CI chain is **not** an artistic PASS; the artistic
  head-turn gate stays FAILED until per-part head-shape depth and occlusion are
  calibrated against accepted angled references.

# CORE-024 — native transparent layers and CPU cutout comparison

ISSUED 2026-10-30. User explicitly permits cutout as an intermediate and other
experiments, while retaining mcode-exec / supervisor-accept collaboration.

Do not confuse full-character alpha extraction with semantic layer decomposition,
hidden-area completion, UV correspondence, rigging or 360 acceptance.

## Task 1: native Aka transparent source baseline

Use the installed psd-tools maintained SDK to inspect and export the actual source
out/source/tutorial-aka.psd, pinned in sources.lock.json. Do not redraw it or use
white-threshold removal. Inspect whether the native composite and native leaves
have genuine alpha. Export a real transparent composite where source layers allow
it (explicit alpha=0/background handling, documented), plus genuine original leaf
layers for face/front hair/back hair/fox ears/eyes/mouth/leaf/neck where present.
Maintain layer path, source bounds, order, visibility, blend/opacity/masks, stable
source IDs and exact canvas coordinates. Export via SDK with original layer names;
never make up missing semantic names or paint hidden content. A source-baseline
export is not an AI decomposition result.

## Task 2: maintained CPU anime cutout model

Use official rembg `isnet-anime` on CPU/ONNX. You may create an isolated venv under
experiments/reference-factory/out/core024/runtime and install rembg[cpu] and its
normal PyPI dependencies there. Do not change main requirements/global packages.
You may download the official model to out/core024/models/ (set U2NET_HOME), not
the user's home. Bound download to 500 MiB and 180 s; never disable checksum checks.

Upstream references already verified by supervisor:
- SkyTNT/anime-segmentation @ 55d874013a2811cdf59c365059174c7823acf5b4
- danielgatis/rembg @ c5b48b0417a0254df7d461efa14573597f369a83
- official rembg/sessions/dis_anime.py model download URL:
  https://github.com/danielgatis/rembg/releases/download/v0.0.0/isnet-anime.onnx
- upstream expected MD5: 6f184e756bb3bd901c8849220a83e38e; also record computed SHA256.

Use maintained rembg new_session('isnet-anime', providers=['CPUExecutionProvider'])
and remove APIs. Preserve soft alpha (do not use binary post_process_mask).
Run once on actual pilot-C-001.png and on a flattened native transparent baseline
composited over white, so native alpha gives a real quantitative benchmark.
Record model/package versions, execution provider, inference time and source/output
hashes. Preserve originals. Prefer original RGB + predicted alpha; if RGB changes,
measure and state it. Report IoU/soft-alpha MAE on the native benchmark, not an
invented truth for generated profile.

## Task 3: compare actual built-in imagegen cutout

Supervisor already executed a genuine transparent-background imagegen edit of
pilot-C-001.png. File: out/core024/imagegen-cutout-C.png (1254x1254 RGBA), SHA256
220ee4ff62baae15aa0fa14f9dfb967c74ad14028f902699df2562c1aa9e8f25.
Use it ONLY for comparison, never overwrite. Check actual alpha histogram and
nontransparent foreground. Measure color MAE/changed RGB in eroded foreground at
same pixels against original profile; if geometry drifts, report that instead of
fitting it away. True alpha presence alone does not prove source preservation.

Emit black/white/checker composites and 4x edge crops for fox-ear tip, white inner
fur, hair tip, nose/eye/neck edge. These are QA composites, not edited final art.
Compare imagegen and CPU cutout on the SAME source image. White fur must remain
opaque; no whole-image white keying. Detect stray alpha components/white halos
as diagnostics, and visually review rather than auto-approve on one metric.

## Execution boundary and outputs

Allowed new code: experiments/reference-factory/cutout_benchmark.py, focused small
offline tests if useful, docs/research/CORE-024-cutout-results.md. All images,
models, env and runtime reports under experiments/reference-factory/out/core024/.
No edits to CORE-023 implementation, original art/source hashes, runtime renderer,
UV/topology, or production repo. No paid APIs, account/token use, delegation,
commit/push, whole-source white-key deletion, or huge general framework.

Run the actual program and report commands, test results, outputs and limitations.
If dependency/model download is blocked, still finish native alpha export and
imagegen QA. Never replace a missing CPU result with a fabricated pass. Distinguish
PASS_ALPHA_CONTAINER, PASS/FAIL_CUTOUT_QUALITY, NATIVE_LAYER_EXPORT and NOT_TESTED
semantic/rig/hidden-design gates. Keep all generated art unapproved.
